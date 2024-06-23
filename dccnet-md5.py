import socket
import sys
import threading
import time
import hashlib
from DCCNET import DCCNET
#python dccnet-md5.py 150.164.213.245:51555
GAS = "2021032110:1:fd01eed7baa1eb0a3c06480a303c94cfa2b54e34045a307683e88c69e37955d2+3b3ccb9597ef0e57f427b0cde3ae23f1498b7e25c11a639aaefe45ef0eed32d6\n"

def md5_checksum(input_string: str) -> str: 
    # Create an md5 hash object
    md5_hash = hashlib.md5()
    
    # Encode the input string and update the hash object
    md5_hash.update(input_string.encode('ascii'))
    
    # Return the hexadecimal digest of the hash
    return md5_hash.hexdigest()

"""
A frame can only be accepted if it is an acknowledgement frame for the last transmitted frame; 
a data frame with an identifier (ID) different from that of the last received frame; 
a retransmission of the last received frame; 
or a reset frame.
"""

def send_checksum(dccnet: DCCNET, message : str, last_id : int, last_check_sum : int): # send checksum and receive ack
      payload = md5_checksum(message)
      while True:
            dccnet.send_frame(payload)
            data, flag, id, checksum =  dccnet.recv_frame()
            if flag & dccnet.FLAG_RESET:
                  raise Exception(f"{data}")
            if flag & dccnet.FLAG_ACK and id == dccnet.id_send:
                 dccnet.id_send ^= 1
                 break
            elif id == last_id and checksum == last_check_sum: # retrasmission of last frame
                  dccnet.send_frame(None, flag=dccnet.FLAG_ACK)

def comm(dccnet: DCCNET, sock):
      dccnet.sock = sock 
      # Authentication
      while True:
            dccnet.send_frame(GAS)
            data, flag, id, _ = dccnet.recv_frame()
            if flag & dccnet.FLAG_RESET:
                  raise Exception(f"{data}")
            if flag & dccnet.FLAG_ACK and id == dccnet.id_send:
                  dccnet.id_send ^= 1
                  break

      curr_msg = ""

      while True:
            while True: # Tries to receive a data frame
                  data, flag, id, checksum = dccnet.recv_frame() 
                  if flag & dccnet.FLAG_RESET:
                        raise Exception(f"{data}")
                  if flag == dccnet.FLAG_EMPTY:
                        dccnet.send_frame(data = None, flag = dccnet.FLAG_ACK, id=id)
                        if id == dccnet.id_recv:
                              continue
                        dccnet.id_recv = id
                        split_data = data.split('\n')
                        curr_msg += split_data[0]
                        if '\n' in data:
                              send_checksum(dccnet, curr_msg, id, checksum)
                        for i in range(1, len(split_data) - 1):
                              if(split_data[i] != ''):
                                    send_checksum(dccnet, split_data[i])
                        curr_msg = split_data[-1]
                        break

            if flag & dccnet.FLAG_END:
                  break  
      """"
      thread para receber linhas:

      thread para mandar linhas:
      """      



def main():
      _ , server  = sys.argv
      ip, port = server.split(sep=':')
      
      try:
          print(f"Connected to: {ip}:{port}\n\n")
          sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
          sock.connect((ip, int(port)))
      except socket.error:
          sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          sock.connect((ip, int(port)))
      sock.settimeout(10)
      dccnet = DCCNET()
      comm(dccnet, sock)

if __name__ == '__main__':
    main()