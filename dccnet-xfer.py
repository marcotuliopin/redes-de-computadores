import socket
import sys
import threading
import queue
from DCCNET import DCCNET
from time import sleep

# -c rubick.snes.2advanced.dev:51555 client_input.txt client_output.txt
# -c 150.164.213.245:51555 client_input.txt client_output.txt
has_finished_sending = False
has_finished_receiving = False
is_connection_cut = False
frame_was_accepted = False
ack_to_send = queue.Queue()
sender_semaphore = threading.Semaphore(10)
receiver_semaphore = threading.Semaphore(10)
send_lock = threading.Lock()

def open_communication(sock, input, output):
    frames = list(read_file_in_chunks(input))
    dccnet = DCCNET(sock)

    ack_lock = threading.Lock()
    finish_sending_lock = threading.Lock()
    finish_receiving_lock = threading.Lock()
    reset_lock = threading.Lock()

    # Create threads for sending and receiving
    send_thread = threading.Thread(target=send_file, args=(dccnet, frames, ack_lock, finish_sending_lock, finish_receiving_lock, reset_lock))
    recv_thread = threading.Thread(target=receive_file, args=(dccnet, output, ack_lock, finish_sending_lock, finish_receiving_lock, reset_lock))
    try:
        # Start the threads
        send_thread.start()
        recv_thread.start()
    except dccnet.Reset:
        pass
    finally:
        # Wait for both threads to complete
        send_thread.join()
        recv_thread.join()
        print('Closing sock')
        dccnet.sock.close()

    print('File transfer completed')

def send_file(dccnet: DCCNET, frames, ack_lock: threading.Lock, finish_receiving_lock: threading.Lock,
              finish_sending_lock: threading.Lock, reset_lock: threading.Lock):
    global has_finished_sending
    global is_connection_cut
    global frame_was_accepted

    for i in range(len(frames)):
        print(f'{(len(frames) - i)} FRAMES LEFT!')
        frame = frames[i]

        if i == len(frames) - 1: flag = dccnet.FLAG_END
        else: flag = dccnet.FLAG_EMPTY

        with ack_lock:
            frame_was_accepted = False
        while True:
            sender_semaphore.acquire()

            with ack_lock:
                if frame_was_accepted: 
                    sender_semaphore.release()
                    break
                elif i > 0: sleep(1)

            # Sends own data
            with send_lock:
                dccnet.send_frame(frame, flag)

            # Sends ACK
            # while not ack_to_send.empty():
            #     ack_id = ack_to_send.get()
            #     print(f"SENDER: Sending ACK with id {ack_id}")
            #     dccnet.send_frame(None, dccnet.FLAG_ACK, id=ack_id)

            receiver_semaphore.release()

            with reset_lock:
                if is_connection_cut: return

    receiver_semaphore.release()

    with finish_sending_lock:
        has_finished_sending = True

    print('FINISHED SENDING')

    # while True:
    #     sender_semaphore.acquire()

    #     with finish_receiving_lock:
    #         if has_finished_receiving:
    #             break
    #     if not ack_to_send.empty():
    #         ack_id = ack_to_send.get()
    #         print(f"SENDER: Sending ACK with id {ack_id}")
    #         dccnet.send_frame(None, dccnet.FLAG_ACK, id=ack_id)
        
        # receiver_semaphore.release()


def receive_file(dccnet: DCCNET, output_file, ack_lock: threading.Lock, finish_receiving_lock: threading.Lock,
                 finish_sending_lock: threading.Lock, reset_lock: threading.Lock):
    global has_finished_sending
    global has_finished_receiving
    global is_connection_cut
    global frame_was_accepted

    while True:
        receiver_semaphore.acquire()

        try:
            data, flag, id, checksum = dccnet.recv_frame()
        except DCCNET.NoRecvData:
            continue

        print(f'RECEIVER: ID SEND: {dccnet.id_send}, ID RECV: {dccnet.id_recv}')

        # Socket timed out while receiving frame
        if flag == None:
            print('FLAG NONE')
            continue

        # Receiving ACK
        if flag & dccnet.FLAG_ACK and id != dccnet.id_send: # Receiving late ACK
            print('LATE ACK')
            pass
        elif flag & dccnet.FLAG_ACK and id == dccnet.id_send: # Receiving corresponding ACK
            print('RECEIVER: ACK received')
            if flag & dccnet.FLAG_END:
                raise dccnet.InvalidFlag
            if data:
                raise dccnet.InvalidPayload
            with ack_lock:
                frame_was_accepted = True
            dccnet.id_send ^= 1

        # Receiving data from external file

        # Receiving end warning
        elif flag & dccnet.FLAG_END:
            print('FLAG END')
            with finish_receiving_lock:
                has_finished_receiving = True
            # ack_to_send.put(id)
            with send_lock:
                dccnet.send_frame(None, dccnet.FLAG_ACK, id=id)
            dccnet.id_recv ^= 1
            dccnet.last_checksum = checksum
        elif not data:
            raise dccnet.InvalidPayload
            
        #  Receiving reset warning
        elif flag & dccnet.FLAG_RESET and id == dccnet.ID_RESET:
            print('FLAG RESET')
            with reset_lock:
                is_connection_cut = True
                raise dccnet.Reset

        # Receiving new data from external file
        elif id != dccnet.id_recv:
            print('RECEIVING EXTERNAL FILE')
            if data:
                with open(output_file, 'w') as out:
                    out.write(data)
            # ack_to_send.put(id)
            with send_lock:
                dccnet.send_frame(None, dccnet.FLAG_ACK, id=id)
            dccnet.id_recv ^= 1
            dccnet.last_checksum = checksum

        # Receiving retransmission
        elif id == dccnet.id_recv and checksum == dccnet.last_checksum:
            print('RECEIVING RESTRANSMISSION')
            # ack_to_send.put(id)
            with send_lock:
                dccnet.send_frame(None, dccnet.FLAG_ACK, id=id)
        
        else:
            print('------------------------------BUG-----------------------------')
            print(dccnet.id_send, dccnet.id_recv)

        with finish_receiving_lock:
            if has_finished_receiving: break
        
        sender_semaphore.release()

    while True:
        receiver_semaphore.acquire()

        with finish_sending_lock:
            if has_finished_sending:
                break
        try:
            data, flag, id, checksum = dccnet.recv_frame()
        except DCCNET.NoRecvData:
            continue

        print(f'RECEIVER: ID SEND: {dccnet.id_send}')

        # Socket timed out while receiving frame
        if flag == None:
            print('FLAG NONE')
            continue

        # Receiving ACK
        if flag & dccnet.FLAG_ACK and id == dccnet.id_send:
            print('FLAG ACK')
            if flag & dccnet.FLAG_END:
                raise dccnet.InvalidFlag
            if data:
                raise dccnet.InvalidPayload

        # Receiving end warning
        elif flag & dccnet.FLAG_END:
            print('FLAG END')
            has_finished_receiving = True
            ack_to_send.put(id)
        elif not data:
            raise dccnet.InvalidPayload
        
        sender_semaphore.release()

def read_file_in_chunks(input_file, chunk_size=4096):
    with open(input_file, 'r') as f:
        first_line = f.readline() 
        yield first_line

        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

def main():
    _, mode, *params = sys.argv

    if mode == '-s':
        port, input, output = params
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', int(port)))
        sock.settimeout(5)
        sock.listen(5)

        while True:
            print('Listening...')
            c, addr = sock.accept()
            print(f"Listening: {addr}")
            open_communication(c,input,output)
            c.close()

    else:
        host, input, output = params
        ip, port = host.split(sep=':')
        
        try:
            print(ip, port)
            sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            sock.connect((ip, int(port)))
        except socket.error:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, int(port)))
        sock.settimeout(5)
        open_communication(sock,input,output)

if __name__ == '__main__':
    main()