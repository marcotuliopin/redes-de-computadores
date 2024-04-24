import socket
import threading
import json
import multiprocessing
from sys import argv
from collections import deque

"""
Constant Definitions
"""
NUM_RIVERS = 4
NUM_BRIDGES = 8
MAX_CANNONS = NUM_BRIDGES * NUM_RIVERS
TIMEOUT = 3.0
MAX_RETRIES = float('inf')

barrier = threading.Barrier(NUM_RIVERS)

events = [threading.Event() for i in range(NUM_RIVERS)]

for i in range(NUM_RIVERS):
    events.append(threading.Event())
    events[i].clear()

cannon_shot = [False] * MAX_CANNONS
def play(auth, server_adress):
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

        turn = 0
        gameover = False
        while not gameover:
            gameover, ships_pre_bridge = pass_turn(sock, auth, turn)
            if gameover:
                break
            barrier.wait()

            # TODO: mudar para Lock
            events[0].set()
            events[my_river-1].wait()
            if my_river == 1: # thread 1 is responsible for reseting cannon_shot each round
                for i in range(len(cannon_shot)):
                    cannon_shot[i] = False
            # TODO: paralelizar envio da mensagem
            shoot(sock, auth, my_river, ships_pre_bridge, cannons)
            events[my_river-1].clear()
            if(my_river != NUM_RIVERS):
                events[my_river].set()
            turn+=1
            barrier.wait()
        if(my_river == 1): # thread 1 is responsible for quitting the game
            quit(sock, auth)
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

def pass_turn(sock, auth, turn):
    data = {'type' : 'getturn', 'auth': auth, 'turn': turn }
    send(sock, data)
    ships_per_bridge = {}
    retries = 0
    for _ in range(NUM_BRIDGES):
        while retries <= MAX_RETRIES:
            try:
                response = receive(sock)
                if(response['type'] == "gameover"):
                    print(response['score'])
                    return True, {}
                if(response['ships']): #TODO: checar se precisa
                    ships_per_bridge[response['bridge']] = response['ships']
                break
            except (socket.error, socket.timeout) as e:
                print('In turn:')
                print(f'Thread {threading.current_thread} failed with error: {e}')
                retries += 1
    return False, ships_per_bridge    
        
def quit(sock, auth):
    data = {'type' : 'quit', 'auth': auth}
    retries = 0
    while retries <= MAX_RETRIES:
        try:
            send(sock, data)
            break
        except (socket.error, socket.timeout) as e:
            print('In quit:')
            print(f'Thread {threading.current_thread} failed with error: {e}')
            retries += 1

def shoot(sock, auth, river, ships_per_pridge, cannons):
    def send_shot(cannon, ship_id):
        data = {"type": "shot", "auth": auth, "cannon": cannon, "id": ship_id}

        retries = 0
        while retries <= MAX_RETRIES:
            try:
                send(sock, data)
                break
            except (socket.error, socket.timeout) as e:
                print('In shoot')
                print(f'Thread {threading.current_thread} failed with error: {e}')
            retries += 1
        response = receive(sock)
        if(response['status'] != 0):
            print(f"Shot error (cannon: {cannon}): {response['description']}")
        else:
            print(f"{cannon} shot {ship_id}")
    
 
    for bridge in ships_per_pridge:
        for i in range(len(cannons)):
            if(cannon_shot[i]):
                continue
            # TODO: trocar para dict
            if(cannons[i][0] == bridge and (cannons[i][1] == river or cannons[i][1] == river - 1)):
                send_shot(cannons[i], ships_per_pridge[bridge][0]['id']) # shoots firts element
                cannon_shot[i] = True
                break
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