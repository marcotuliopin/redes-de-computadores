import socket
import sys
import threading
from DCCNET import DCCNET
from time import sleep

# -c rubick.snes.2advanced.dev:51555 client_input.txt client_output.txt
# -c 150.164.213.245:51555 client_input.txt client_output.txt
has_finished_sending = False
has_finished_receiving = False
is_connection_cut = False
frame_was_accepted = False
ack_to_send = -1
sender_semaphore = threading.Semaphore(10)
receiver_semaphore = threading.Semaphore(10)
ack_lock = threading.Lock()
finish_sending_lock = threading.Lock()
finish_receiving_lock = threading.Lock()
reset_lock = threading.Lock()


def open_communication(sock, input, output):
    frames = list(read_file_in_chunks(input))
    dccnet = DCCNET(sock)

    # Create threads for sending and receiving
    send_thread = threading.Thread(target=send_file, args=(dccnet, frames))
    recv_thread = threading.Thread(target=receive_file, args=(dccnet, output))
    try:
        # Start the threads
        recv_thread.start()
        send_thread.start()
    except DCCNET.Reset:
        pass
    finally:
        # Wait for both threads to complete
        recv_thread.join()
        send_thread.join()
        dccnet.sock.close()

    print('File transfer completed')

def send_file(dccnet: DCCNET, frames):
    global has_finished_sending
    global is_connection_cut
    global frame_was_accepted
    global ack_to_send

    id_to_send = 0
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
                else: sleep(1)

            # Sends own data
            print(f'SENDER: Sending frame {i}')
            dccnet.send_frame(frame, flag, id=id_to_send)

            # Sends ACK
            if ack_to_send != -1:
                dccnet.send_frame(None, dccnet.FLAG_ACK, id=ack_to_send)
                ack_to_send = -1

            if receiver_semaphore._value < 10:
                receiver_semaphore.release()

            with reset_lock:
                if is_connection_cut: raise DCCNET.Reset
        id_to_send ^= 1

    receiver_semaphore.release()

    with finish_sending_lock:
        has_finished_sending = True

    # Send ACKs
    while True:
        sender_semaphore.acquire()

        with finish_receiving_lock:
            if has_finished_receiving:
                if ack_to_send != -1:
                    dccnet.send_frame(None, dccnet.FLAG_ACK, id=ack_to_send)
                receiver_semaphore.release()
                break

        if ack_to_send != -1:
            dccnet.send_frame(None, dccnet.FLAG_ACK, id=ack_to_send)
            ack_to_send = -1

        
        receiver_semaphore.release()


def receive_file(dccnet: DCCNET, output_file):
    global ack_to_send
    global has_finished_sending
    global has_finished_receiving
    global is_connection_cut
    global frame_was_accepted

    while True:
        receiver_semaphore.acquire()

        try:
            data, flag, id, checksum = dccnet.recv_frame()
        except (DCCNET.NoRecvData, DCCNET.CorruptedFrame):
            pass


        # Socket timed out while receiving frame
        if flag == None:
            pass

        # Receiving ACK
        elif flag & dccnet.FLAG_ACK and id != dccnet.id_send: # Receiving late ACK
            print('-------------------- Late ack ----------------------')
            pass
        elif flag & dccnet.FLAG_ACK and id == dccnet.id_send: # Receiving corresponding ACK
            if flag & dccnet.FLAG_END:
                raise dccnet.InvalidFlag
            if data:
                raise dccnet.InvalidPayload
            with ack_lock:
                frame_was_accepted = True
            dccnet.id_send ^= 1

        # Receiving data from external file

        # Receiving retransmission
        elif id == dccnet.id_recv and checksum == dccnet.last_checksum:
            print('-------------------- Retransmission ----------------------')
            if ack_to_send == -1:
                ack_to_send = id # Warn to send ACK

        # Receiving end warning
        elif id != dccnet.id_recv and flag & dccnet.FLAG_END:
            with finish_receiving_lock:
                has_finished_receiving = True
            ack_to_send = id # Warn to send ACK
            dccnet.id_recv ^= 1
            dccnet.last_checksum = checksum
        elif not data:
            raise dccnet.InvalidPayload
            
        #  Receiving reset warning
        elif flag & dccnet.FLAG_RESET and id == dccnet.ID_RESET:
            print(f'Received RESET: {data}')
            with reset_lock:
                is_connection_cut = True
                raise DCCNET.Reset

        # Receiving new data from external file
        elif id != dccnet.id_recv:
            if data:
                with open(output_file, 'a') as out:
                    out.write(data)
            ack_to_send = id # Warn to send ACK
            dccnet.id_recv ^= 1
            dccnet.last_checksum = checksum

        with finish_sending_lock:
            receiver_semaphore.release()
            with finish_receiving_lock:
                sender_semaphore.release()
                if has_finished_receiving and has_finished_sending: 
                    break
        
        if sender_semaphore._value < 10:
            sender_semaphore.release()

def read_file_in_chunks(input_file, chunk_size=4096):
    with open(input_file, 'r') as f:
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