import socket
import sys
import threading
import time
from DCCNET import DCCNET

def main():
    _, mode, *params = sys.argv

    if mode == '-s':
        port, input, output = params
        # acho que nosso server aceita somente ipv4
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #ISSO É UMA FORÇA BRUTA PRA QUANDO O SERVER NAO TERMINAR DIREITO
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", int(port)))
        sock.listen(5)

        while True:
            print('Listening...')
            c, addr = sock.accept()
            dccnet = DCCNET(sock)
            print(f"Listening: {addr}")
            try:
                recv_data=dccnet.recv_all()
                with open(output,'w') as f:
                    f.write(recv_data)
                #nao sei se tem que ter esse close aqui
                c.close()
                break
            finally:
                c.close()






    else:
        host, input, output = params
        ip, port = host.split(sep=':')

        connected = False
        sock = None
        # Attempt IPv6 connection
        try:
            print(f"Trying IPv6 connection to {ip}:{port}")
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.connect((ip, int(port)))
            dccnet=DCCNET(sock)
            connected = True
        except socket.error as e:
            print(f"IPv6 connection failed: {e}")

        # Attempt IPv4 connection if IPv6 failed
        if not connected:
            try:
                print(f"Trying IPv4 connection to {ip}:{port}")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((ip, int(port)))
                dccnet=DCCNET(sock)
                connected = True
            except socket.error as e:
                print(f"IPv4 connection failed: {e}")
        
        with open(input,'r') as f:
            data=f.read()

        if connected:
            sock.settimeout(10)
            dccnet.send_all(data)
            sock.close()
        else:
            print(f"Failed to connect to {ip}:{port} with both IPv6 and IPv4")
        
        # try:
        #     print(ip, port)
        #     sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        #     sock.connect((ip, int(port)))
        # except socket.error:
        #     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #     sock.connect((ip, int(port)))
        # sock.settimeout(10)
        # open_communication(sock,input,output)

if __name__ == '__main__':
    main()