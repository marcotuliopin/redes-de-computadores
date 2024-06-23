import socket
import sys
import threading
from DCCNET import DCCNET
from time import sleep

# -c rubick.snes.2advanced.dev:51555 client_input.txt client_output.txt
# -c 150.164.213.245:51555 client_input.txt client_output.txt
has_finished_sending = False
is_connection_cut = False
frame_was_accepted = False

def open_communication(sock, input, output):
    frames = list(read_file_in_chunks(input))
    dccnet = DCCNET(sock)

    sender_semaphore = threading.Semaphore(1)
    receiver_semaphore = threading.Semaphore(0)
    ack_lock = threading.Lock()
    finish_sending_lock = threading.Lock()
    reset_lock = threading.Lock()

    # Create threads for sending and receiving
    send_thread = threading.Thread(target=send_file, args=(dccnet, frames, ack_lock, receiver_semaphore, sender_semaphore, finish_sending_lock, reset_lock))
    recv_thread = threading.Thread(target=receive_file, args=(dccnet, output, ack_lock, receiver_semaphore, sender_semaphore, finish_sending_lock, reset_lock))
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

def send_file(dccnet: DCCNET, frames, ack_lock: threading.Lock, receiver_semaphore: threading.Semaphore, sender_semaphore: threading.Semaphore,
              finish_sending_lock: threading.Lock, reset_lock: threading.Lock):
    global has_finished_sending
    global is_connection_cut
    global frame_was_accepted

    for i in range(len(frames)):
        print(f'{(len(frames) - i)} FRAMES LEFT!')
        frame = frames[i]

        if i == len(frames) - 1: flag = dccnet.FLAG_END
        else: flag = dccnet.FLAG_EMPTY

        while True:

            print('SENDER: Trying to acquire sender flag')
            sender_semaphore.acquire()
            print('SENDER: Acquired sender flag')
            print(f'SENDER: SENDER SEMAPHORE VALUE: {sender_semaphore._value}')

            with ack_lock:
                print(f'SENDER: ACK RESULT: {frame_was_accepted}')
                if frame_was_accepted: 
                    sender_semaphore.release()
                    break
                elif i > 0: sleep(1)

            dccnet.send_frame(frame, flag)

            print('SENDER: Freed receiver flag')
            receiver_semaphore.release()
            print(f'SENDER: RECEIVER SEMAPHORE VALUE: {receiver_semaphore._value}')

            with reset_lock:
                if is_connection_cut: return
        frame_was_accepted = False

    with finish_sending_lock:
        has_finished_sending = True
        receiver_semaphore.release()
        print(f'SENDER: RECEIVER SEMAPHORE VALUE: {receiver_semaphore._value}')
    print('END SENDING')

def receive_file(dccnet: DCCNET, output_file, ack_lock: threading.Lock, receiver_semaphore: threading.Semaphore, sender_semaphore: threading.Semaphore,
                 finish_sending_lock: threading.Lock, reset_lock: threading.Lock):
    global has_finished_sending
    global is_connection_cut
    global frame_was_accepted

    has_finished_receiving = False
    while True:
        print('RECEIVER: Trying to acquire receiver flag')
        receiver_semaphore.acquire()
        print('RECEIVER: Acquired receiver flag')
        print(f'RECEIVER: RECEIVER SEMAPHORE VALUE: {receiver_semaphore._value}')
        try:
            data, flag, id, checksum = dccnet.recv_frame()
        except DCCNET.NoRecvData:
            sender_semaphore.release()
            print(f'RECEIVER: SENDER SEMAPHORE VALUE: {sender_semaphore._value}')
            continue

        print(f'RECEIVER: ID SEND: {dccnet.id_send}')

        # Socket timed out while receiving frame
        if flag == None:
            sender_semaphore.release()
            print(f'RECEIVER: SENDER SEMAPHORE VALUE: {sender_semaphore._value}')
            continue

        # Receiving ACK
        if flag & dccnet.FLAG_ACK and id != dccnet.id_send: # Receiving late ACK
            pass
        elif flag & dccnet.FLAG_ACK and id == dccnet.id_send: # Receiving corresponding ACK
            print('RECEIVER: ACK received')
            if flag & dccnet.FLAG_END:
                raise dccnet.InvalidFlag
            if data:
                raise dccnet.InvalidPayload
            dccnet.id_send ^= 1
            with ack_lock:
                frame_was_accepted = True

        # Receiving data from external file

        # Receiving end warning
        elif flag & dccnet.FLAG_END:
            has_finished_receiving = True
            dccnet.send_frame(data=None, flag=dccnet.FLAG_ACK, ack_id=id)
        elif not data:
            raise dccnet.InvalidPayload
            
        #  Receiving reset warning
        elif flag & dccnet.FLAG_RESET and id == dccnet.ID_RESET:
            with reset_lock:
                is_connection_cut = True
                raise dccnet.Reset

        # Receiving new data from external file
        elif id != dccnet.id_recv:
            if data:
                with open(output_file, 'w') as out:
                    out.write(data)
            dccnet.send_frame(data=None, flag=dccnet.FLAG_ACK, ack_id=id)
            dccnet.id_recv ^= 1

        # Receiving retransmission
        elif id == dccnet.id_recv and checksum == dccnet.last_checksum:
            dccnet.send_frame(data=None, flag=dccnet.FLAG_ACK, ack_id=id)

        with finish_sending_lock:
            if has_finished_sending:
                receiver_semaphore.release()
                print(f'RECEIVER: RECEIVER SEMAPHORE VALUE: {receiver_semaphore._value}')

        sender_semaphore.release()
        print('RECEIVER: Freed sender flag')
        print(f'RECEIVER: SENDER SEMAPHORE VALUE: {sender_semaphore._value}')
        if has_finished_receiving: break

    while True:
        print('RECEIVER: Trying to acquire receiver flag')
        receiver_semaphore.acquire()
        print('RECEIVER: Acquired receiver flag')
        print(f'RECEIVER: RECEIVER SEMAPHORE VALUE: {receiver_semaphore._value}')
        try:
            data, flag, id, checksum = dccnet.recv_frame()
            print('Got data.')
        except DCCNET.NoRecvData:
            sender_semaphore.release()
            continue

        print(f'RECEIVER: ID SEND: {dccnet.id_send}')

        # Socket timed out while receiving frame
        if flag == None:
            sender_semaphore.release()
            print(f'RECEIVER: SENDER SEMAPHORE VALUE: {sender_semaphore._value}')
            continue

        with finish_sending_lock:
            if has_finished_sending:
                sender_semaphore.release()
                break

        # Receiving ACK
        if flag & dccnet.FLAG_ACK and id == dccnet.id_send:
            if flag & dccnet.FLAG_END:
                raise dccnet.InvalidFlag
            if data:
                raise dccnet.InvalidPayload

        # Receiving end warning
        elif flag & dccnet.FLAG_END:
            has_finished_receiving = True
            dccnet.send_frame(data=None, flag=dccnet.FLAG_ACK, ack_id=id)
        elif not data:
            raise dccnet.InvalidPayload

        with finish_sending_lock:
            if has_finished_sending:
                receiver_semaphore.release()
                print(f'RECEIVER: RECEIVER SEMAPHORE VALUE: {receiver_semaphore._value}')

        sender_semaphore.release()
        print('RECEIVER: Freed sender flag')
    
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
            dccnet = DCCNET()
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