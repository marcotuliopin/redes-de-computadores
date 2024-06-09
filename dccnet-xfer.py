import sys
import threading
from DCCNET import DCCNET

def receive_file(receiver, output):
    data = receiver.recvall()
    with open(output, 'w') as f:
        f.write(data)

    pass

def send_file(sender, input):
    with open(input, 'r') as f:
        data = f.read()
        sender.sendall(data)
    pass

def main():
    _, mode, *params = sys.argv

    if mode == '-s':
        port, input, output = params
        sender = DCCNET(port, mode=0)
        receiver = DCCNET(port, mode=0)
    else:
        host, input, output = params
        ip, port = host.split(sep=':')
        sender = DCCNET(port, mode=1, host=ip)
        receiver = DCCNET(port, mode=1, host=ip)

    receiving_t = threading.Thread(target=receive_file, args=(receiver, output))
    sending_t = threading.Thread(target=send_file, args=(sender, input))
    try:
        receiving_t.start()
        sending_t.start()
    finally:
        receiving_t.join()
        sending_t.join()
