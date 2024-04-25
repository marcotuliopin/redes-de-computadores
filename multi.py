import socket
import threading
import json
import multiprocessing
from sys import argv
from collections import deque
import time

"""
Constant Definitions
"""
NUM_RIVERS = 4
NUM_BRIDGES = 8
NUM_CANNONS = NUM_BRIDGES * NUM_RIVERS
TIMEOUT = 1.0
MAX_RETRIES = float('inf')

barrier = threading.Barrier(NUM_RIVERS)
lock = threading.Lock()
flag = False

cannon_shot = [False] * NUM_CANNONS

def play(auth, server_adress):
    global flag
    global cannon_shot
    try:
        sock = create_socket(server_adress)
        barrier.wait()

        river, status = authenticate(sock, auth)
        if status:
            raise AuthenticationFailedException
        barrier.wait()

        cannons = place_cannons(sock, auth) 
        barrier.wait()

        turn = 0
        gameover = False
        while not gameover:
            gameover, ships = pass_turn(sock, auth, turn)
            if gameover:
                break
            barrier.wait()

            lock.acquire()
            if not flag:
                cannon_shot = [False for _ in range(NUM_CANNONS)]
            flag = True
            shots = shoot(river, ships, cannons)
            lock.release()

            for shot in shots:
                send_shot(shot[0], shot[1], auth, sock) 

            barrier.wait()

            turn += 1
            flag = False
        barrier.wait()
        if (river == 1):
            quit(sock, auth)
    finally:
        sock.close()

def create_socket(server_adress):
    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        sock.connect(server_adress)
    except socket.error as e:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(server_adress)
    sock.settimeout(TIMEOUT)
    return sock

def authenticate(sock, auth):
    data = {
        'type': 'authreq', 
        'auth': auth
    }

    retries = 0
    while retries <= MAX_RETRIES:
        try:
            send(sock, data)
            response = receive(sock)
            break
        except (socket.error, socket.timeout) as e:
            retries += 1

    if retries > MAX_RETRIES:
        raise CommunicationErrorException

    return response['river'], response['status'] 

def place_cannons(sock, auth):
    data = {
        'type': 'getcannons', 
        'auth': auth
    }
    
    retries = 0
    while retries <= MAX_RETRIES:
        try:
            send(sock, data)
            response = receive(sock)
            break
        except (socket.error, socket.timeout) as e:
            retries += 1
    if retries > MAX_RETRIES:
        raise CommunicationErrorException
    
    cannons = []
    for cannon in response['cannons']:
        cannons.append({
            'bridge': cannon[0],
            'river': cannon[1]
        })
    return cannons

def pass_turn(sock, auth, turn):
    data = {
        'type' : 'getturn', 
        'auth': auth, 
        'turn': turn 
    }

    ships = {}
    retries = 0
    while retries <= MAX_RETRIES:
        try:
            send(sock, data)
            for _ in range(NUM_BRIDGES):
                response = receive(sock)
                if(response['type'] == "gameover"):
                    print(response['score'])
                    return True, {}
                if(response['ships']):
                    ships[response['bridge']] = response['ships']
            break
        except (socket.error, socket.timeout) as e:
            retries += 1
    return False, ships    
        
def quit(sock, auth):
    data = {
        'type' : 'quit', 
        'auth': auth
    }
    retries = 0
    while retries <= MAX_RETRIES:
        try:
            send(sock, data)
            break
        except (socket.error, socket.timeout) as e:
            retries += 1

def shoot(river, ships, cannons):
    global cannon_shot
    shots = []
    for bridge in ships:
        for i in range(len(cannons)):
            for ship in ships[bridge]:
                if not is_alive(ship):
                    continue
                if cannon_shot[i]:
                    continue
                if validate_shot(cannons[i], bridge, river):
                    cannon_shot[i] = True
                    ship['hits'] += 1
                    shots.append((cannons[i], ship['id']))
    return shots

def is_alive(ship):
    match ship['hull']:
        case 'frigate':
            return ship['hits'] < 1
        case 'destroyer':
            return ship['hits'] < 2 
        case 'battleship':
            return ship['hits'] < 3 

def validate_shot(cannon, bridge, river):
    if cannon['bridge'] != bridge:
        return False
    if cannon['river'] != river:
        if cannon['river'] == 4:
            return False
        if cannon['river'] != river - 1:
            return False
    return True

def send_shot(cannon, ship, auth, sock):
    data = {
        'type': 'shot',
        'auth': auth,
        'cannon': (cannon['bridge'], cannon['river']), 
        'id': ship
    }

    retries = 0
    while retries <= MAX_RETRIES:
        try:
            send(sock, data)
            response = receive(sock)
            break
        except (socket.error, socket.timeout) as e:
            retries += 1

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
start=time.time()
if __name__ == '__main__':
    main()
stop=time.time()
print("Tempo total de execução: ",start-stop)