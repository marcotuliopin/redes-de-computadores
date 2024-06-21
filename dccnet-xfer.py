import socket
import sys
import threading
import time
from DCCNET import DCCNET


# -c rubick.snes.2advanced.dev:51555 client_input.txt client_output.txt
# -c 150.164.213.245:51555 client_input.txt client_output.txt
has_finished_sending = False

def open_communication(sock, input, output):
    frames = list(read_file_in_chunks(input))

    dccnet = DCCNET(sock)
    condition = threading.Condition()
    sock_lock = threading.Lock()
    finish_lock = threading.Lock()
    # Create threads for sending and receiving
    send_thread = threading.Thread(target=send_file, args=(dccnet, frames, condition, sock_lock, finish_lock))
    recv_thread = threading.Thread(target=receive_file, args=(dccnet, output, condition, sock_lock, finish_lock))
    try:
        # Start the threads
        send_thread.start()
        recv_thread.start()
    finally:
        # Wait for both threads to complete
        send_thread.join()
        recv_thread.join()

    dccnet.sock.close()

    print('File transfer completed')

def send_file(dccnet: DCCNET, frames, condition: threading.Condition, sock_lock: threading.Lock, 
              finish_lock: threading.Lock):
    #nao entendi esse close no inicio
    #dccnet.sock.close()
    for i in range(len(frames)):
        frame = frames[i]

        if i == len(frames) - 1: flag = dccnet.FLAG_END
        else: flag = dccnet.FLAG_EMPTY

        while True:
            with sock_lock:
                dccnet.send_frame(frame, flag)
            with condition:
                condition.wait()
            dccnet.id_send ^= 1

    with finish_lock:
        has_finished_sending = True


#adicionar escrita no output
def receive_file(dccnet: DCCNET, output_file, condition: threading.Condition, 
                 sock_lock: threading.Lock, finish_lock: threading.Lock):
    has_finished_receiving = False

    while True:
        with sock_lock:
            data, flag, id, checksum = dccnet.recv_frame()
        # Receiving ACK from sent file
        if flag & dccnet.FLAG_ACK and id != dccnet.id_send: # receiving late ack
            continue
        # Receiving ACK
        elif flag & dccnet.FLAG_ACK and id == dccnet.id_send:
            if flag & dccnet.FLAG_END:
                raise dccnet.invalid_flag
            if data:
                raise dccnet.invalid_payload
            with condition:
                condition.notify()



        # Receiving data from external file
        else:
            has_finished_receiving = recv_file(dccnet, flag, data, 
                                            checksum, output_file, has_finished_receiving)
        if has_finished_receiving: break

    while True:
        with finish_lock:
            if has_finished_sending:
                break
        with sock_lock:
            data, flag, id, checksum = dccnet.recv_frame()
        # Receiving ACK
        if flag & dccnet.FLAG_ACK and id == dccnet.id_send:
            if flag & dccnet.FLAG_END:
                raise dccnet.invalid_flag
            if data:
                raise dccnet.invalid_payload
            with condition:
                condition.notify()
    
def read_file_in_chunks(input_file, chunk_size=4096):
    with open(input_file, 'r') as f:
        first_line = f.readline() 
        yield first_line

        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk
        


def recv_file(dccnet: DCCNET, flag, data, checksum, output, has_finished_receiving):
    # print(f"data: {data}")
    if flag & dccnet.FLAG_END:
        has_finished_receiving = True
    elif not data:
        print(f"flag recv_file: {flag}")
        raise dccnet.invalid_payload
    if id != dccnet.id_recv:
        if data:
            with open(output, 'w') as out:
                out.write(data)
        
        dccnet.send_frame(data=None, flag=dccnet.FLAG_ACK)
        dccnet.id_recv ^= 1

    elif id == dccnet.id_recv and checksum == dccnet.last_checksum:
        dccnet.send_frame(data=None, flag=dccnet.FLAG_ACK)
    
    elif id == dccnet.ID_RESET and flag == dccnet.FLAG_RESET:
        dccnet.sock.close()
        raise dccnet.reset
    
    return has_finished_receiving

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
        sock.settimeout(10)
        open_communication(sock,input,output)
        sock.close()

if __name__ == '__main__':
    main()