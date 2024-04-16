import socket
import json
import select
from queue import Queue
from sys import argv


"""
Constant Definitions.
"""
NUM_RIVERS = 4
MAX_RETRIES = 3
TIMEOUT = 0.5
INVALID_MESSAGE = 23


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

    recv_queue = Queue(NUM_RIVERS)
    send_queue = Queue(NUM_RIVERS)
    for i in range(NUM_RIVERS):
        send_queue.put(i)

    retries = [0] * NUM_RIVERS
    while not send_queue.empty() and max(retries) < MAX_RETRIES:
        try:
            while not send_queue.empty():
                idx = send_queue.get()
                json_bytes = json.dumps(data).encode('utf-8')
                sockets[idx].sendall(json_bytes)
                recv_queue.put(idx)
            
            while not recv_queue.empty():
                idx = recv_queue.get()
                response = receive_response(sockets[idx])
                if response['status'] == 1:
                    raise AuthenticationFailedException
                river_control[idx] = response['river']

        except (socket.error, socket.timeout) as e:
            print(f'Socket {idx} failed with error: {e}')
            retries[idx] += 1
            send_queue.put(idx)

    if max(retries) >= MAX_RETRIES:
        raise CommunicationErrorException

    return river_control


def request_cannon_placement(sockets, auth):
    data = {"type": "getcannons", "auth": auth}
    response = None
    
    send_queue = Queue(NUM_RIVERS)
    for i in range(NUM_RIVERS):
        send_queue.put(i)

    retries = [0] * NUM_RIVERS
    while not send_queue.empty() and max(retries) < MAX_RETRIES:
        try:
            while not send_queue.empty():
                idx = send_queue.get()
                json_bytes = json.dumps(data).encode('utf-8')
                sockets[i].sendall(json_bytes)

        except (socket.error, socket.timeout) as e:
            print(f'Socket {idx} failed while sending data with error: {e}')
            retries[idx] += 1
            send_queue.put(idx)

        try:
            read_socket, _, _ = select.select(sockets, [], [], TIMEOUT)
            response = receive_response(read_socket[0])

        except (socket.error, socket.timeout) as e:
            print(f'Socket {idx} failed while receiving response with error: {e}')
            for i in range(sockets):
                retries[i] += 1
                send_queue.put(i)

    if max(retries) >= MAX_RETRIES:
        raise CommunicationErrorException

    return response['cannons']


def request_turn_state(sockets, auth, turn=0):
    data = {"type": "getturn", "auth": auth, "turn": turn}
    state = [[] for _ in range(NUM_RIVERS)]

    recv_queue = Queue(NUM_RIVERS)
    send_queue = Queue(NUM_RIVERS)
    for i in range(NUM_RIVERS):
        send_queue.put(i)

    retries = [0] * NUM_RIVERS
    while not send_queue.empty() and max(retries) < MAX_RETRIES:
        try:
            while not send_queue.empty():
                idx = send_queue.get()
                json_bytes = json.dumps(data).encode('utf-8')
                sockets[idx].sendall(json_bytes)
                recv_queue.put(idx)
            
            while not recv_queue.empty():
                idx = recv_queue.get()
                response = receive_response(sockets[idx])
                print(response)
                state[idx].append({'bridge': response['bridge'], 
                            'ships': response['ships']})

        except (socket.error, socket.timeout) as e:
            print(f'Socket {idx} failed with error: {e}')
            retries[idx] += 1
            send_queue.put(idx)
            continue

    if max(retries) >= MAX_RETRIES:
        raise CommunicationErrorException

    return state


def receive_response(sock):
    response = sock.recv(1024)
    response = json.loads(response)
    if response['type'] == 'gameover'and response['status'] == 1:
        raise InvalidMessageException(response['description'])
    return response


def main():

    _, host, port1, gas = argv
    port1 = int(port1)

    ports = range(port1, port1 + NUM_RIVERS)
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
        while True:
            try:
                river_control = authenticate_connection(sockets, gas)
                cannon_placement = request_cannon_placement(sockets, gas)
                turn = 0
                while True:
                    state = request_turn_state(sockets, gas, turn)
                    turn += 1

                break
            except InvalidMessageException as e:
                print('Error occurred: ' + {e})
                print('Restarting game...')

    # Ensure sockets are closed
    finally:
        for sock in sockets:
            sock.close()


"""
Exceptions Definitions.
"""
class AuthenticationFailedException(Exception):
    pass

class CommunicationErrorException(Exception):
    pass

class InvalidMessageException(Exception):
    def __init__(self, message):
        super().__init__(message)


if __name__ == '__main__':
    main()