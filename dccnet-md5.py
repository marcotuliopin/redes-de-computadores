import socket
import sys
import hashlib
from DCCNET import DCCNET

def md5_checksum(input_string: str) -> str: 
    # Create an md5 hash object
    md5_hash = hashlib.md5()
    
    # Encode the input string and update the hash object
    md5_hash.update(input_string.encode('ascii'))
    
    # Return the hexadecimal digest of the hash
    return md5_hash.hexdigest() + "\n"

"""
A frame can only be accepted if it is an acknowledgement frame for the last transmitted frame; 
a data frame with an identifier (ID) different from that of the last received frame; 
a retransmission of the last received frame; 
or a reset frame.
"""

def send_checksum(dccnet: DCCNET, message : str, last_id : int, last_check_sum : int): # send checksum and receive ack
      payload = md5_checksum(message)
      while True:
            dccnet.send_frame(payload, flag= dccnet.FLAG_EMPTY, id = dccnet.id_send)
            data, flag, id, checksum =  dccnet.recv_frame()
            if flag & dccnet.FLAG_RESET:
                  raise Exception(f"{data}")
            if flag & dccnet.FLAG_ACK and id == dccnet.id_send:
                 dccnet.id_send ^= 1
                 break
            elif id == last_id and checksum == last_check_sum: # retrasmission of last frame
                  dccnet.send_frame(None, flag=dccnet.FLAG_ACK, id=last_id)
            elif id == last_id ^ 1: # server didn't send ack
                  dccnet.send_frame(None, flag=dccnet.FLAG_ACK, id=dccnet.id_recv)

def authenticate(dccnet: DCCNET, gas):
      while True:
            dccnet.send_frame(gas)
            data, flag, id, _ = dccnet.recv_frame()
            if flag & dccnet.FLAG_RESET:
                  raise Exception(f"{data}")
            if flag & dccnet.FLAG_ACK and id == dccnet.id_send:
                  dccnet.id_send ^= 1
                  break



def comm(dccnet: DCCNET, sock, gas):
      dccnet.sock = sock 
      # Authentication
      authenticate(dccnet, gas)
      curr_msg = ""
      while True:
            while True: # Tries to receive a data frame
                  data, flag, id, checksum = dccnet.recv_frame() 
                  if flag & dccnet.FLAG_RESET:
                        raise Exception(f"{data}")
                  elif flag == dccnet.FLAG_EMPTY or flag & dccnet.FLAG_END:
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
                                    send_checksum(dccnet, split_data[i], id, checksum)
                        curr_msg = split_data[-1]
                        break

            if flag & dccnet.FLAG_END:
                  break  




def main():
      _ , server, gas  = sys.argv
      ip, port = server.split(sep=':')
      gas += '\n'
      try:
          sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
          sock.connect((ip, int(port)))
      except socket.error:
          sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          sock.connect((ip, int(port)))
      sock.settimeout(100)
      dccnet = DCCNET()
      comm(dccnet, sock, gas)

if __name__ == '__main__':
    main()
