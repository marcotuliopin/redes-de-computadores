import socket
import sys
import threading
import time
import hashlib
from DCCNET import DCCNET

GAS = "2021032110:1:fd01eed7baa1eb0a3c06480a303c94cfa2b54e34045a307683e88c69e37955d2+3b3ccb9597ef0e57f427b0cde3ae23f1498b7e25c11a639aaefe45ef0eed32d6\n"

def md5_checksum(input_string: str) -> str:
    # Create an md5 hash object
    md5_hash = hashlib.md5()
    
    # Encode the input string and update the hash object
    md5_hash.update(input_string.encode('utf-8'))
    
    # Return the hexadecimal digest of the hash
    return md5_hash.hexdigest()
      
def send_checksum(dccnet: DCCNET, message : str):
      checksum = md5_checksum(message)
      while True:
            dccnet.send_frame(checksum)
            data, flag, id, _ =  dccnet.recv_frame()
            if flag & dccnet.FLAG_RESET:
                  raise Exception(f"erro: {data}")
            if flag & dccnet.FLAG_ACK and id == dccnet.id_send:
                 dccnet.id_send ^= 1
                 break
            time.sleep(1)

def comm(dccnet: DCCNET, sock):
      dccnet.sock = sock
      while True:
            dccnet.send_frame(GAS)
            data, flag, id, _ = dccnet.recv_frame()
            if flag & dccnet.FLAG_RESET:
                  raise Exception(f"erro: {data}")
            if flag & dccnet.FLAG_ACK and id == dccnet.id_send:
                  dccnet.id_send ^= 1
                  break
            time.sleep(1)
      curr_msg = ""

      while True:
            while True:
                  data, flag, id, checksum = dccnet.recv_frame() 
                  if flag & dccnet.FLAG_RESET:
                        raise Exception(f"erro: {data}")
                  if flag & dccnet.FLAG_ACK or flag & dccnet.FLAG_RESET or id == dccnet.id_recv:
                        time.sleep(1)
                        continue
                  else:
                        dccnet.send_frame(data = None, flag = dccnet.FLAG_ACK)
                        print(f"data: {data}")
                        split_data = data.split('\n')
                        curr_msg += split_data[0]
                        if '\n' in data:
                              send_checksum(dccnet, curr_msg)
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