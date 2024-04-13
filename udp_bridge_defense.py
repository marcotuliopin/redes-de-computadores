import socket
import json
import select
from sys import argv

NUM_SERVERS = 4
MAX_RETRIES = 3
TIMEOUT = 0.5


def open_sockets(family, type, adresses):
    sockets = []
    for adress in adresses:
        sock = socket.socket(family, type)
        sock.settimeout(TIMEOUT)
        sock.connect(adress)
        sockets.append(sock)
    return sockets


def authenticate_connection(sockets, auth):
    data = {"type": "authreq", "auth": auth}
    river_control = {}

    for i in range(len(sockets)):
        retries = 0
        while retries < MAX_RETRIES:
            try:
                json_bytes = json.dumps(data).encode('utf-8')
                sockets[i].sendall(json_bytes)
            except socket.error as e:
                print(f'Socket {i} failed while sending data with error: {e}')
                retries += 1
                continue

            response = None
            try: 
                response = sockets[i].recv(1024)
                response = json.loads(response)
                if response['status'] == 1:
                    raise AuthenticationFailedException
                river_control[i] = response['river']
            except socket.timeout as e:
                print(f'Socket {i} failed while receiving data with error: {e}')
                retries += 1

        if not response:
            print(f'Socket {i} failed.')
            raise CommunicationErrorException

    return river_control


def request_cannon_placement(sockets, auth):
    data = {"type": "getcannons", "auth": auth}
    response = None
    
    post_retries = [0] * len(sockets)
    get_retries = 0
    while max(post_retries) < MAX_RETRIES and get_retries < MAX_RETRIES:
        for i in range(len(sockets)):
            try:
                json_bytes = json.dumps(data).encode('utf-8')
                sockets[i].sendall(json_bytes)
            except socket.error as e:
                print(f'Socket {i} failed while sending data with error: {e}')
                post_retries[i] += 1

        try: 
            read_socket, _, _ = select.select(sockets, [], [], TIMEOUT)
            response = read_socket[0].recv(1024)
            response = json.loads(response)
        except socket.timeout as e:
            print(f'Socket failed while receiving data with error: {e}')
            get_retries += 1

    if not response:
        print(f'Socket failed.')
        raise CommunicationErrorException

    return response['cannons']


def request_turn_state(sockets, auth, turn=0):
    data = {"type": "getturn", "auth": auth, "turn": turn}
    state = []

    for i in range(len(sockets)):
        retries = 0
        response = None
        while retries < MAX_RETRIES:
            try:
                json_bytes = json.dumps(data).encode('utf-8')
                sockets[i].sendall(json_bytes)
            except socket.error as e:
                print(f'Socket {i} failed while sending data with error: {e}')
                retries += 1
                continue

            response = None
            try: 
                response = sockets[i].recv(1024)
                response = json.loads(response)
            except socket.timeout as e:
                print(f'Socket {i} failed while receiving data with error: {e}')
                retries += 1

        if not response:
            print(f'Socket {i} failed.')
            raise CommunicationErrorException

        state.append({'bridge': response['bridge'], 
                      'ships': [{'hull': ship['hull'], 'hits': ship['hits']} 
                                for ship in response['ships']]})
    return state


class AuthenticationFailedException(Exception):
    pass

class CommunicationErrorException(Exception):
    pass


def main():

    _, host, port1, gas = argv
    port1 = int(port1)

    ports = range(port1, port1 + NUM_SERVERS)
    adresses = [(host, port) for port in ports]

    # Try to connect to IPv6
    try:
        sockets = open_sockets(socket.AF_INET6, socket.SOCK_DGRAM, adresses)
        for sock, adress in zip(sockets, adresses):
            sock.connect(adress)
    # Try connecting to IPv4 if the connection in IPv6 is not successful
    except socket.error as e:
        print("IPv6 connection failed. Connecting to IPv4...")
        sockets = open_sockets(socket.AF_INET, socket.SOCK_DGRAM, adresses)
        for sock, adress in zip(sockets, adresses):
            sock.connect(adress)
    print("Connected!")

    try:
        river_control = authenticate_connection(sockets, auth=gas)
        cannon_placement = request_cannon_placement(sockets, auth=gas)
        

    # Ensure sockets are closed
    finally:
        for sock in sockets:
            sock.close()


if __name__ == '__main__':
    main()