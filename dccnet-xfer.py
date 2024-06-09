import socket
import sys
import threading
from DCCNET import DCCNET

def comm(dccnet: DCCNET, sock, input, output):
    dccnet.sock = sock
    has_finished_receiving = False
    input_file = open(input, 'r')

    lines = input_file.readlines()
    for line in lines:
        fsize = 2**16
        fsize //= 8
        frames = [line[i: i + fsize] for i in range(len(0, line, fsize))]

        for frame in frames:
            while True:
                dccnet.send_frame(frame)
                data, flag, id, checksum = dccnet.recv_frame()

                if flag & dccnet.FLAG_ACK and id == dccnet.id_send:
                    if flag & dccnet.FLAG_END:
                        raise dccnet.invalid_flag
                    if data:
                        raise dccnet.invalid_payload
                    dccnet.id_send ^= 1
                    break

                else:
                    if flag & dccnet.FLAG_END:
                        has_finished_receiving = True
                    elif not data:
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
                        raise dccnet.reset()
    input_file.close()

    while not has_finished_receiving:
        data, flag, id, checksum = dccnet.recv_frame()
        has_finished_receiving = recv_file(dccnet, flag, data, 
                                           checksum, output, has_finished_receiving)

    dccnet.sock.close()
        

def recv_file(dccnet: DCCNET, flag, data, checksum, output, has_finished_receiving):
    if flag & dccnet.FLAG_END:
        has_finished_receiving = True
    elif not data:
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
    dccnet = DCCNET()

    if mode == '-s':
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)

        port = 12345
        sock.bind(('::', port))
        sock.listen(5)

        while True:
            c, addr = sock.accept()
            threading.Thread(target=comm, args=(dccnet, c, input, output)).start()

    else:
        host, input, output = params
        ip, port = host.split(sep=':')

        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            sock.connect((ip,port))
        except socket.error:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect((ip,port))
        sock.settimeout(1)
        comm(dccnet, sock, input, output)
