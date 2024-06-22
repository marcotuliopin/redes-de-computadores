import socket
import sys
import threading
from DCCNET import DCCNET


# -c rubick.snes.2advanced.dev:51555 client_input.txt client_output.txt
# -c 150.164.213.245:51555 client_input.txt client_output.txt
has_finished_sending = False
is_connection_cut = False

def open_communication(sock, input, output):
    frames = list(read_file_in_chunks(input))
    dccnet = DCCNET(sock)

    condition = threading.Condition()
    sender_semaphore = threading.Semaphore(1)
    receiver_semaphore = threading.Semaphore(0)
    finish_sending_lock = threading.Lock()
    reset_lock = threading.Lock()

    # Create threads for sending and receiving
    send_thread = threading.Thread(target=send_file, args=(dccnet, frames, condition, receiver_semaphore, sender_semaphore, finish_sending_lock, reset_lock))
    recv_thread = threading.Thread(target=receive_file, args=(dccnet, output, condition, receiver_semaphore, sender_semaphore, finish_sending_lock, reset_lock))
    try:
        # Start the threads
        send_thread.start()
        recv_thread.start()
    except dccnet.reset:
        with condition:
            condition.notify()
    finally:
        # Wait for both threads to complete
        send_thread.join()
        recv_thread.join()
        dccnet.sock.close()

    print('File transfer completed')

def send_file(dccnet: DCCNET, frames, condition: threading.Condition, receiver_semaphore: threading.Semaphore, sender_semaphore: threading.Semaphore,
              finish_sending_lock: threading.Lock, reset_lock: threading.Lock):
    global has_finished_sending
    global is_connection_cut

    for i in range(len(frames)):
        frame = frames[i]
        print(len(frames))

        if i == len(frames) - 1: flag = dccnet.FLAG_END
        else: flag = dccnet.FLAG_EMPTY

        while True:
            sender_semaphore.acquire()
            dccnet.send_frame(frame, flag)
            receiver_semaphore.release()
            with reset_lock:
                if is_connection_cut: return
                with condition:
                    condition.wait()

    with finish_sending_lock:
        has_finished_sending = True
    print('END SENDING')

def receive_file(dccnet: DCCNET, output_file, condition: threading.Condition, receiver_semaphore: threading.Semaphore, sender_semaphore: threading.Semaphore,
                 finish_sending_lock: threading.Lock, reset_lock: threading.Lock):
    global has_finished_sending
    global is_connection_cut

    has_finished_receiving = False
    while True:
        receiver_semaphore.acquire()
        data, flag, id, checksum = dccnet.recv_frame()

        # Socket timed out while receiving frame
        if flag == None:
            sender_semaphore.release()

        # Receiving ACK
        if flag & dccnet.FLAG_ACK and id != dccnet.id_send: # Receiving late ACK
            sender_semaphore.release()
        elif flag & dccnet.FLAG_ACK and id == dccnet.id_send: # Receiving corresponding ACK
            if flag & dccnet.FLAG_END:
                raise dccnet.InvalidFlag
            if data:
                raise dccnet.InvalidPayload
            dccnet.id_send ^= 1
            with condition:
                condition.notify()

        # Receiving data from external file

        # Receiving end warning
        elif flag & dccnet.FLAG_END:
            has_finished_receiving = True
            dccnet.send_frame(data=None, flag=dccnet.FLAG_ACK)
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
            dccnet.send_frame(data=None, flag=dccnet.FLAG_ACK)
            dccnet.id_recv ^= 1

        # Receiving retransmission
        elif id == dccnet.id_recv and checksum == dccnet.last_checksum:
            dccnet.send_frame(data=None, flag=dccnet.FLAG_ACK)

        sender_semaphore.release()
        if has_finished_receiving: break

    while True:
        receiver_semaphore.acquire()
        with finish_sending_lock:
            if has_finished_sending:
                sender_semaphore.release()
                break
        data, flag, id, checksum = dccnet.recv_frame()
        # Receiving ACK
        if flag & dccnet.FLAG_ACK and id == dccnet.id_send:
            if flag & dccnet.FLAG_END:
                raise dccnet.InvalidFlag
            if data:
                raise dccnet.InvalidPayload
            with condition:
                condition.notify()
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