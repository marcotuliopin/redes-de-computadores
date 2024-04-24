import socket
import json
import select
from queue import Queue
from sys import argv


"""
Constant Definitions.
"""
NUM_RIVERS = 4
NUM_BRIDGES = 8
MAX_RETRIES = 100000000000
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
                print("IDX",idx,"\n")
                response = receive_response(sockets[idx])
                print(response,"\n")
                if response['status'] == 1:
                    raise AuthenticationFailedException
                river_control[idx] =  response['river']

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
            if not send_queue.empty():
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


def request_turn_state(sockets, river_control, auth, turn=0):
    data = {"type": "getturn", "auth": auth, "turn": turn}
    state = {}
    for i in range(1, NUM_BRIDGES + 1):
        state[i] = {}
        for j in range(1, NUM_RIVERS + 1):
            state[i][j] = []
    recv_queue = Queue(NUM_RIVERS * NUM_BRIDGES)
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
                for _ in range(NUM_BRIDGES):
                    recv_queue.put(idx)
            
            while not recv_queue.empty():
                idx = recv_queue.get()
                response = receive_response(sockets[idx])
                if(response["type"] == "gameover" and response["status"]==0):
                    return True, response["score"]
                state[response['bridge']][river_control[idx]] = response['ships']
               

        except (socket.error, socket.timeout) as e:
            print(f'Socket {idx} failed with error: {e}')
            retries[idx] += 1
            send_queue.put(idx)
            continue

    if max(retries) >= MAX_RETRIES:
        raise CommunicationErrorException

    return False,state


def shoot(state, cannon_placement, river_control, sockets, auth):
    def get_river_targets(cannon_river):
        if(cannon_river == 0):
            return [1]
        elif (cannon_river == NUM_RIVERS):
            return [NUM_RIVERS]
        else:
            return [cannon_river, cannon_river + 1]
        
        
    def send_shot(cannon, ship_river, ship_id):
        data = {"type": "shot", "auth": auth, "cannon": cannon, "id": ship_id}
        idx = -1
        for key, value in river_control.items():
            if value == ship_river:
                idx = key
        if idx == -1:
            raise Exception(f"{ship_river} not found in river control")
        json_bytes = json.dumps(data).encode('utf-8')
        sockets[idx].sendall(json_bytes)
        response = receive_response(sockets[idx])
        if(response['status'] != 0):
            print(f"Shot error: {response['description']}")
        else:
            print(f"Shot {ship_id}")
        # print("Response shot: ")
        # print(response)
    
    def calculate_ship_health(hull, hits):
        if hull == 'frigate':
            return 1 - hits
        elif hull == 'destroyer':
            return 2 - hits
        elif hull == 'battleship':
            return 3 - hits
        else:
            raise Exception(f"{hull} is not a valid hull")
    
    for [cannon_bridge, cannon_river] in cannon_placement:
        rivers = get_river_targets(cannon_river)
        for target_river in rivers:
            if (state[cannon_bridge][target_river]):
                first_ship = state[cannon_bridge][target_river][0]
                send_shot([cannon_bridge, cannon_river], target_river, first_ship['id']) 
                state[cannon_bridge][target_river].pop(0)
                break
                
          
    


def quit(sockets,auth): #assumindo que nao tem nenhuma resposta por terminar, ja que nao tem nada especificado
    data = {"type": "quit","auth": auth}
    state = [[] for _ in range(NUM_RIVERS)]

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

        except (socket.error, socket.timeout) as e:
            print(f'Socket {idx} failed with error: {e}')
            retries[idx] += 1
            send_queue.put(idx)
            continue

    if max(retries) >= MAX_RETRIES:
        raise CommunicationErrorException


def receive_response(sock):
    response = sock.recv(2048)
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
        sockets = open_sockets(socket.AF_INET, socket.SOCK_DGRAM, adresses)
        for sock, adress in zip(sockets, adresses):
            sock.connect(adress)
    print("Connected!")
    try:
        while True:
            try:
                river_control = authenticate_connection(sockets, gas)#Aparentemente funciona corretamente
                print("\nAuthenticated Connections\n")
                print(river_control)
                cannon_placement = request_cannon_placement(sockets, gas)#Aparentemente funciona corretamente
                print("\nGot Cannon Placement\n")
                print(cannon_placement)
                
                turn = 0
                while True:
                    endgame,state = request_turn_state(sockets, river_control, gas, turn)
                    print("End of turn "+ str(turn) +"\n")
                    if(endgame):
                        print(state)
                        print("Quitting")
                        quit(sockets,gas)
                        break
                    shoot(state, cannon_placement, river_control, sockets, gas)
                   
                    turn += 1

                break
            except InvalidMessageException as e:
                print('Error occurred: ' + str(e))
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