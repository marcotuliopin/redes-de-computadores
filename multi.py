import socket
import threading
import json
import multiprocessing
from sys import argv

"""
Constant Definitions
"""
NUM_RIVERS = 4
TIMEOUT = 0.5
MAX_RETRIES = 10

barrier = threading.Barrier(NUM_RIVERS)

locks = []
for i in range(NUM_RIVERS):
    locks.append(threading.Lock())

# C 1 C 2 C 3 C 4 C
# 1-2 2-3 3-4

def play(auth, server_adress, pipe):
    try:
        sock = create_socket(server_adress)
        barrier.wait()

        my_river, status = authenticate(sock, auth)
        if status:
            raise AuthenticationFailedException
        barrier.wait()
        print('Authenticated')

        cannons = place_cannons(sock, auth)
        barrier.wait()
        print('Cannons placed')

        while True:
            pass_turn()
            barrier.wait()

            locks[my_river - 1].lock()
            locks[my_river + 1].lock()
            try:
                pass
            finally:
                locks[my_river - 1].unlock()
                locks[my_river + 1].unlock()
            break
    finally:
        sock.close()

def create_socket(server_adress):
    # Try to connect to IPv6
    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        sock.connect(server_adress)
    # Try connecting to IPv4 if the connection in IPv6 is not successful
    except socket.error as e:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(server_adress)
    sock.settimeout(TIMEOUT)
    print("Connected!")
    return sock

def authenticate(sock, auth):
    data = {'type': 'authreq', 'auth': auth}

    retries = 0
    while retries <= MAX_RETRIES:
        try:
            send(sock, data)
            response = receive(sock)
            break
        except (socket.error, socket.timeout) as e:
            print('In authentication:')
            print(f'Thread {threading.current_thread} failed with error: {e}')
            retries += 1

    if retries > MAX_RETRIES:
        raise CommunicationErrorException

    return response['river'], response['status'] 

def place_cannons(sock, auth):
    data = {'type': 'getcannons', 'auth': auth}
    
    retries = 0
    while retries <= MAX_RETRIES:
        try:
            send(sock, data)
            # TODO: checar se todas as portas recebem resposta.
            response = receive(sock)
            break
        except (socket.error, socket.timeout) as e:
            print('In cannon placement:')
            print(f'Thread {threading.current_thread} failed with error: {e}')
            retries += 1

    if retries > MAX_RETRIES:
        raise CommunicationErrorException
    
    return response['cannons']

def pass_turn():
    pass

def shoot():
    pass

def send(sock, data):
    message = json.dumps(data).encode('utf-8')
    sock.sendall(message)

def receive(sock):
    response = sock.recv(2048)
    response = json.loads(response)
    if response['type'] == 'gameover'and response['status'] == 1:
        raise InvalidMessageException(response['description'])
    
    return response

def main():

    _, host, port1, auth = argv

    parts = auth.split(':', 1)
    padded_part = parts[0].ljust(12)
    auth = ':'.join([padded_part, parts[1]])

    port1 = int(port1) 
    ports = range(port1, port1 + NUM_RIVERS)
    adresses = [(host, port) for port in ports]

    threads = []
    for i in range(NUM_RIVERS):
        t = threading.Thread(target=play, args=(auth, adresses[i]))
        threads.append(t)
    
    try:
        for t in threads:
            t.start()    
    finally:
        for t in threads:
            t.join()


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