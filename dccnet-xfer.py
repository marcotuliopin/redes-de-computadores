import socket
import sys
import threading
from DCCNET import DCCNET
from time import sleep

has_finished_sending = False
has_finished_receiving = False
is_connection_cut = False
frame_was_accepted = False
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

def send_file(dccnet: DCCNET, frames):
    global has_finished_sending
    global is_connection_cut
    global frame_was_accepted

    id_to_send = 0
    for i in range(len(frames)):
        frame = frames[i]

        # Check if it is the last frame
        if i == len(frames) - 1: flag = dccnet.FLAG_END
        else: flag = dccnet.FLAG_EMPTY

        with ack_lock:
            frame_was_accepted = False

        retry = False
        while True:
            if retry: sleep(.5)
            sender_semaphore.acquire()

            with ack_lock:
                if frame_was_accepted: # ACK was received
                    sender_semaphore.release()
                    break

            # Sends own data
            dccnet.send_frame(frame, flag, id=id_to_send)

            retry = True

            if receiver_semaphore._value < 10:
                receiver_semaphore.release()

            # Checks for cut in the connection
            with reset_lock:
                if is_connection_cut: raise DCCNET.Reset
        id_to_send ^= 1

    receiver_semaphore.release()

    with finish_sending_lock:
        has_finished_sending = True

def receive_file(dccnet: DCCNET, output_file):
    global has_finished_sending
    global has_finished_receiving
    global is_connection_cut
    global frame_was_accepted

    first_write = True
    while True:
        # End the program if there is no data being transmitted to either side
        with finish_sending_lock:
            with finish_receiving_lock:
                if has_finished_receiving and has_finished_sending: 
                    break

        receiver_semaphore.acquire()

        try:
            data, flag, id, checksum = dccnet.recv_frame()
        except (DCCNET.NoRecvData, DCCNET.CorruptedFrame):
            if sender_semaphore._value < 10:
                sender_semaphore.release()
            continue

        # Socket timed out while receiving frame
        if flag == None:
            pass

        # Receiving ACK
        elif flag & dccnet.FLAG_ACK and id != dccnet.id_send: # Receiving late ACK
            pass
        elif flag & dccnet.FLAG_ACK and id == dccnet.id_send: # Receiving corresponding ACK
            if flag & dccnet.FLAG_END: raise DCCNET.InvalidFlag
            if data: raise DCCNET.InvalidPayload
            with ack_lock:
                frame_was_accepted = True
            dccnet.id_send ^= 1

        # Receiving data from external file

        # Receiving retransmission
        elif id == dccnet.id_recv and checksum == dccnet.last_checksum:
            dccnet.send_frame(None, dccnet.FLAG_ACK, id=id)
            
        #  Receiving reset warning
        elif flag & dccnet.FLAG_RESET and id == dccnet.ID_RESET:
            with reset_lock:
                is_connection_cut = True
                raise DCCNET.Reset

        # Receiving new data from external file
        elif id != dccnet.id_recv:
            if data:
                with open(output_file, 'a' if not first_write else 'w') as out:
                    out.write(data)
                first_write = False
            # If there is no data, the flag must be END
            elif not flag & dccnet.FLAG_END:
                raise DCCNET.InvalidPayload

            dccnet.send_frame(None, dccnet.FLAG_ACK, id=id)
            dccnet.id_recv ^= 1
            dccnet.last_checksum = checksum

            # Receiving end warning
            if flag & dccnet.FLAG_END:
                with finish_receiving_lock:
                    has_finished_receiving = True

        with finish_sending_lock:
            if has_finished_sending:
                receiver_semaphore.release()

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

    # Is to be run in server mode
    if mode == '-s':
        port, input, output = params
        sock = None
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            sock.bind(('::', int(port)))
        except socket.error as e:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', int(port)))
        sock.settimeout(10)
        sock.listen(5)


        print('Listening...')
        c, addr = sock.accept()
        print(f"Listening: {addr}")
        open_communication(c,input,output)
        c.close()

    # Is to be run in client mode
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