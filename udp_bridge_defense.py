import socket
import json
from sys import argv

NUM_SERVERS = 4


def open_sockets(family, type, adresses):
    sockets = []
    for adress in adresses:
        sock = socket.socket(family, type)
        sock.connect(adress)
        sockets.append(sock)
    return sockets


def authenticate_connection(sockets, auth):
    data = {"type": "authreq", "auth": auth}

    json_bytes = json.dumps(data).encode('utf-8')
    # Send authentication requests
    for sock in sockets:
        sock.sendall(json_bytes)
    
    # Receive authentication response
    for sock in sockets:
        response = sock.recv(1024)
        response.decode('utf-8')
        print(type(response))


def main():

    _, host, port1, gas = argv
    port1 = int(port1)

    ports = range(port1, port1 + NUM_SERVERS)
    adresses = [(host, port) for port in ports]

    # Try to connect to IPv6
    try:
        sockets = open_sockets(socket.AF_INET, socket.SOCK_DGRAM, adresses)
        for sock, adress in zip(sockets, adresses):
            sock.connect(adress)
    # Try connecting to IPv4 if the connection in IPv6 is not successful
    except (socket.error, OSError) as e:
        print("IPv6 connection failed. Connecting to IPv4...")
        sockets = open_sockets(socket.AF_INET, socket.SOCK_DGRAM, adresses)
        for sock, adress in zip(sockets, adresses):
            sock.connect(adress)

    try:
        authenticate_connection(sockets, auth=gas)
    # Ensure sockets are closed
    finally:
        for sock in sockets:
            sock.close()


if __name__ == '__main__':
    main()