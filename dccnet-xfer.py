import sys
import threading
from DCCNET import DCCNET

def system_mode(port, input, output):
    sender = DCCNET()
    receiver = DCCNET()

def client_mode(ip, port, input, output):
    sender = DCCNET(ip, port)
    receiver = DCCNET(ip, port)
    receiving_t = threading.Thread(target=receive_file, args=(receiver, output))
    sending_t = threading.Thread(target=send_file, args=(sender, input))

    try:
        receiving_t.start()
        sending_t.start()
    finally:
        receiving_t.join()
        sending_t.join()


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
        system_mode(port, input, output)
    else:
        host, input, output = params
        ip, port = host.split(sep=':')
        client_mode(ip, port, input, output)

