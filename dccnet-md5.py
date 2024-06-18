import socket
import sys
import threading
import time
from DCCNET import DCCNET

GAS = "2021032110:1:fd01eed7baa1eb0a3c06480a303c94cfa2b54e34045a307683e88c69e37955d2+3b3ccb9597ef0e57f427b0cde3ae23f1498b7e25c11a639aaefe45ef0eed32d6\n"

def comm(dccnet: DCCNET, sock):
      dccnet.sock = sock
      while True:
            dccnet.send_frame(GAS)
            _, flag, _, _ = dccnet.recv_frame()
            if flag & dccnet.FLAG_ACK:
                 break
            time.sleep()
      curr_msg = ""
      while True:
            data, flag, id, checksum = dccnet.recv_frame()
            # se for dado
            # mandar ack()
            split_data = data.split('\n')
            curr_msg += split_data[0]
            if '\n' in data:
                  pass # mandar checksum
            for i in range(1, len(split_data) - 1):
                  if(split_data[i] != ''):
                        pass # mandar checkcum
            curr_msg = split_data[-1]
            
            """
            receber mensagem
                  frame = receber_frame(...)
                  split_fram = frame.split('\n')
                  curr_msg += splits[0]
                  if(frame tem \n)
                    mandar_check_sum(curr_msg)
                  for i in range(1, len(splits)-1):
                        if(splits[i] != '')
                            mandar_check_sum(splits[i])
                  curr_msg = splits[-1]
            receber mensagem
                  curr_msg
                  splits = receber_frame(...)
                  curr_msg += splits[0]
                  for i in range(1, len(splits)-1):
                        mandar_check_sum(splits[i])
                  curr_msg = splits[-1]
            mandar check_sum
            esperar ack
            se for ultima mensagem 
                  break


           """
      """"
      thread para receber linhas:

      thread para mandar linhas:
      """      



def main():
      _ , server  = sys.argv
      print(server)
      ip, port = server.split(sep=':')
      
      try:
          print(ip, port)
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