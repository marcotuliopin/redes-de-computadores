import socket
import sys
import threading
import time
import hashlib
from DCCNET import DCCNET
#python dccnet-md5.py 150.164.213.245:51555 2021032110:1:fd01eed7baa1eb0a3c06480a303c94cfa2b54e34045a307683e88c69e37955d2+3b3ccb9597ef0e57f427b0cde3ae23f1498b7e25c11a639aaefe45ef0eed32d6

flags={
        0x80:"FLAG_ACK",
        0x40 :"FLAG_END",
        0x00 :"FLAG_EMPTY",
        0x20 :"FLAG_RESET"
}

def md5_checksum(input_string: str) -> str: 
    md5_hash = hashlib.md5() 
    md5_hash.update(input_string.encode('ascii'))
    
    return md5_hash.hexdigest() + "\n"


def send_checksum(dccnet: DCCNET, message : str, last_id : int, last_check_sum : int): # send checksum and receive ack
      payload = md5_checksum(message)
      while True:
            dccnet.send_frame(payload, flag= dccnet.FLAG_EMPTY, id = dccnet.id_send)
            data, flag, id, checksum =  dccnet.recv_frame()
            if flag & dccnet.FLAG_RESET:
                  raise Exception(f"{data}")
            elif flag & dccnet.FLAG_ACK and id == dccnet.id_send:
                 dccnet.id_send ^= 1
                 break
            elif id == last_id and checksum == last_check_sum: # retrasmission of last frame
                  dccnet.send_frame(None, flag=dccnet.FLAG_ACK, id=last_id)
            """ elif id == last_id ^ 1: # server didn't send ack
                  dccnet.send_frame(payload, flag=dccnet.FLAG_EMPTY, id= dccnet.id_send) # sends last data frame again 
                  #dccnet.send_frame(None, flag=dccnet.FLAG_ACK, id=dccnet.id_recv)  """
            time.sleep(0.5)

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
          print(f"Connected to: {ip}:{port}\n\n")
          sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
          sock.connect((ip, int(port)))
      except socket.error:
          sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          sock.connect((ip, int(port)))
      sock.settimeout(100)
      dccnet = DCCNET()
      #test(dccnet, sock)
      comm(dccnet, sock, gas)

if __name__ == '__main__':
    main()
