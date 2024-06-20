import socket
import sys
import threading
import time
from DCCNET import DCCNET

def comm(dccnet: DCCNET, sock, input, output):
    dccnet.sock = sock
    has_finished_receiving = False
    print(f"ack flag: {dccnet.FLAG_ACK}, end flag: {dccnet.FLAG_END}")

    frames = list(read_file_in_chunks(input))

    for i in range(len(frames)):
        print(f"Sending frame {i + 1}/{len(frames)}")
        frame = frames[i]
        if i == len(frames) - 1:
            flag = dccnet.FLAG_END
        else:
            flag = dccnet.FLAG_EMPTY

        while True:
            dccnet.send_frame(frame, flag)
            data, flag, id, checksum = dccnet.recv_frame()
            # print(f"flag rcv: {flag}, id rcv: {id}, checksum rcv: {checksum}, data rcv: {data}") 
            # Receiving ACK from sent file
            if flag & dccnet.FLAG_ACK and id != dccnet.id_send: # receiving late ack
                continue
            elif flag & dccnet.FLAG_ACK and id == dccnet.id_send:
                if flag & dccnet.FLAG_END:
                    raise dccnet.invalid_flag
                if data:
                    raise dccnet.invalid_payload
                dccnet.id_send ^= 1
                break
            # Receiving data from external file
            else:
                print(f"Recebeu arquivo - flag: {flag} // {flag & dccnet.FLAG_END} ")
                has_finished_receiving = recv_file(dccnet, flag, data, 
                                                checksum, output, has_finished_receiving)
            time.sleep(1)
            
    while not has_finished_receiving:
        data, flag, id, checksum = dccnet.recv_frame()
        has_finished_receiving = recv_file(dccnet, flag, data, 
                                           checksum, output, has_finished_receiving)
    print('File transfer completed')
    dccnet.sock.close()

    
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
    print(f"data: {data}")
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
        sock.bind((socket.gethostname(), int(port)))
        sock.listen(5)

        while True:
            print('Listening...')
            c, addr = sock.accept()
            print(f"Listening: {addr}")
            dccnet = DCCNET()
            comm(dccnet, c, input, output)
            c.close()
            # threading.Thread(target=comm, args=(dccnet, c, input, output)).start()

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
        dccnet = DCCNET()
        comm(dccnet, sock, input, output)

if __name__ == '__main__':
    main()