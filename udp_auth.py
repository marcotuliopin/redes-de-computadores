"""
UDP Authentication Module

This module provides functions for performing authentication using UDP (User Datagram Protocol).
It includes functions for sending and receiving individual and group token requests, as well as
validating authentication tokens. The functions in this module are designed to be used in a
networking context where authentication is required.

Functions:
- send_individual_token_request(sock, id: str, nonce: str|int): Sends a request for an individual authentication token.
- send_individual_token_validation(sock, sas: str): Sends a validation request for an individual authentication token.
- send_group_token_request(sock, N: str|int, *sas_list: tuple[str]): Sends a request for a group authentication token.
- send_group_token_validation(sock, gas: str): Sends a validation request for a group authentication token.
- receive_individual_token_response(sock): Receives and processes the response to an individual token request.
- receive_individual_token_status(sock): Receives and processes the response to an individual token validation request.
- receive_group_token_response(sock, N: str|int): Receives and processes the response to a group token request.
- receive_group_token_status(sock, N: str|int): Receives and processes the response to a group token validation request.

Note: This module assumes that the communication is performed over UDP.
"""

import socket
import struct
from sys import argv


"""
Constant Definitions.
"""
MESSAGE_TYPES = {
    'individual_token_request': 1,
    'individual_token_response': 2,
    'individual_token_validation': 3,
    'individual_token_status': 4,
    'group_token_request': 5,
    'group_token_response': 6,
    'group_token_validation': 7,
    'group_token_status': 8,
    'error_message': 256
}


def send_individual_token_request(sock, id: str, nonce: str|int):
    """
    send_individual_token_request:

    Parameters:
    - sock: A UDP socket object.
    - id: A string representing the student's ID (NetID).
    - nonce: An integer representing the token nonce.
    """
    id = id.ljust(12)
    message = struct.pack('!H12sI', MESSAGE_TYPES['individual_token_request'],
                           bytes(id, encoding='ascii'), int(nonce))
    sock.send(message)


def send_individual_token_validation(sock, sas: str):
    """
    send_individual_token_validation:

    Parameters:
    - sock: A UDP socket object.
    - sas: A string representing the student authentication sequence (SAS) in the format "ID:nonce:token".
    """
    id, nonce, token = sas.split(sep=':')
    id = id.ljust(12)

    message = struct.pack('!H12sI64s', MESSAGE_TYPES['individual_token_validation'],
                          bytes(id, encoding='ascii'), int(nonce), bytes(token, encoding='ascii'))
    sock.send(message)


def send_group_token_request(sock, N: str|int, *sas_list: tuple[str]):
    """
    send_group_token_request:

    Parameters:
    - sock: A UDP socket object.
    - N: An integer representing the number of student authentication sequences (SAS) being sent.
    - *sas_list: Variable number of strings representing the SAS for each student in the group.
    """
    message = struct.pack('!HH', MESSAGE_TYPES['group_token_request'], int(N))
    
    # Pack each SAS
    for sas in sas_list:
        id, nonce, token = sas.split(sep=':')
        id = id.ljust(12)
        aux = struct.pack('!12sI64s', bytes(id, encoding='ascii'), int(nonce),
                          bytes(token, encoding='ascii'))
        message += aux

    sock.send(message)


def send_group_token_validation(sock, gas: str):
    """
    send_group_token_validation:

    Parameters:
    - sock: A UDP socket object.
    - gas: A string representing the group authentication sequence (GAS) in the format "SAS1+SAS2+...+token".
    """
    *sas_list, token = gas.split(sep='+')
    N = len(sas_list)

    message = struct.pack('!HH', MESSAGE_TYPES['group_token_validation'], N)

    # Pack each SAS
    for sas in sas_list:
        id, nonce, sas_token = sas.split(sep=':')
        aux = struct.pack('!12sI64s', bytes(id, encoding='ascii'), int(nonce),
                          bytes(sas_token, encoding='ascii'))
        message += aux
    
    message += struct.pack('!64s', bytes(token, encoding='ascii'))

    sock.send(message)

    return N


def receive_individual_token_response(sock):
    """
    receive_individual_token_response:

    Parameters:
    - sock: A UDP socket object.
    Returns:
    A tuple containing the response data received from the server, decoded into strings where necessary.
    """
    buffer = sock.recv(82)

    if len(buffer) == 4 and (e := validate_response(buffer)):
        raise ERROR_TYPES[e]

    response = struct.unpack('!H12sI64s', buffer)
    response = tuple(value.decode('ascii') if isinstance(value, bytes)
                             else value for value in response)
    return response


def receive_individual_token_status(sock):
    """
    receive_individual_token_status:

    Parameters:
    - sock: A UDP socket object.
    Returns:
    A tuple containing the response data received from the server, decoded into strings where necessary.
    """
    buffer = sock.recv(83)

    if len(buffer) == 4 and (e := validate_response(buffer)):
        raise ERROR_TYPES[e]

    response = struct.unpack('!H12sI64sB', buffer)
    response = tuple(value.decode('ascii') if isinstance(value, bytes)
                             else value for value in response)

    return response


def receive_group_token_response(sock, N: str|int):
    """
    receive_group_token_response:

    Parameters:
    - sock: A UDP socket object.
    - N: An integer representing the number of SAS expected in the response.
    Returns:
    A tuple containing the response data received from the server, decoded into strings where necessary.
    """
    SAS_LEN = 80
    N = int(N)

    buffer = sock.recv(68 + SAS_LEN*N)


    if len(buffer) == 4 and (e := validate_response(buffer)):
        raise ERROR_TYPES[e]

    response = struct.unpack(f'!HH{N*"12sI64s"}64s', buffer)
    response = tuple(value.decode('ascii') if isinstance(value, bytes)
                             else value for value in response)
    return response


def receive_group_token_status(sock, N: str|int):
    """
    receive_group_token_status:

    Parameters:
    - sock: A UDP socket object.
    - N: An integer representing the number of SAS expected in the response.
    Returns:
    A tuple containing the response data received from the server, decoded into strings where necessary.
    """
    SAS_LEN = 80
    N = int(N)

    buffer = sock.recv(69 + SAS_LEN*N)

    if len(buffer) == 4 and (e := validate_response(buffer)):
        raise ERROR_TYPES[e]

    response = struct.unpack(f'!HH{N*"12sI64s"}64sB', buffer)
    response = tuple(value.decode('ascii') if isinstance(value, bytes)
                             else value for value in response)

    return response


def validate_response(buffer):
    """
    In case of error, find of which type it is.
    """
    response = struct.unpack('!HH', buffer)
    if response[0] == 256 and response[1] in range(1, 6):
        return response[1]

    raise UnknownErrorException


def construct_sas(tokens):
    """
    Parse the tokens to construct an output string for SAS.
    """
    return ':'.join(map(str, tokens))


def construct_gas(sas_tokens, token):
    """
    Parse the tokens to construct an output string for GAS.
    """
    sas_list = [] 
    for i in range(0, len(sas_tokens) - 2, 3):
        sas = construct_sas(sas_tokens[i:i+3])
        sas_list.append(sas)

    return '+'.join(sas_list + [str(token)])


def main():
    if len(argv) < 4:
        raise WrongArgumentNumberException()
    
    _, host, port, *cmd = argv

    server_adress = (host, int(port))

    # Try to connect to IPv6
    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        sock.connect(server_adress)
    # Try connecting to IPv4 if the connection in IPv6 is not successful
    except (socket.error, OSError) as e:
        print("IPv6 connection failed. Connecting to IPv4...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(server_adress)

    try:
        sock.settimeout(5.0)
        match cmd[0]:
            case 'itr':
                send_individual_token_request(sock, *cmd[1:])
                response = receive_individual_token_response(sock)
                sas = construct_sas(response[1:])
                print(sas.replace(' ', ''))
            case 'itv':
                send_individual_token_validation(sock, *cmd[1:])
                response = receive_individual_token_status(sock)
                print(response[-1].replace(' ', '')) # Print validation token
            case 'gtr':
                send_group_token_request(sock, *cmd[1:])
                response = receive_group_token_response(sock, cmd[1])
                gas = construct_gas(response[2:-1], response[-1])
                print(gas.replace(' ', ''))
            case 'gtv':
                N = send_group_token_validation(sock, *cmd[1:])
                response = receive_group_token_status(sock, N)
                print(response[-1].replace(' ', '')) # Print validation token
            case _:
                InvalidCommandException()
    # Ensure sockets are closed
    finally:
        sock.close()


"""
Exceptions Definitions.
"""
class WrongArgumentNumberException(Exception):
    pass

class InvalidCommandException(Exception):
    pass

class InvalidMessageCodeException(Exception):
    pass

class IncorrectMessageLengthException(Exception):
    pass

class InvalidParameterException(Exception):
    pass

class InvalidSingleTokenException(Exception):
    pass

class AsciiDecodeErrorException(Exception):
    pass

class UnknownErrorException(Exception):
    pass

ERROR_TYPES = {
    1: InvalidMessageCodeException(),
    2: IncorrectMessageLengthException(),
    3: InvalidParameterException(),
    4: InvalidSingleTokenException(),
    5: AsciiDecodeErrorException(),
}

if __name__ == "__main__":
    main()