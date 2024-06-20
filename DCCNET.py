import socket
import struct
from typing import Optional

class DCCNET:
    def __init__(self, sock: Optional[socket.socket]=None):
        # Constants
        self.TIMEOUT = 100
        self.SYNC = 0xDCC023C2
        self.SYNC_SIZE = 4
        self.SYNC_BYTES = self.SYNC.to_bytes(self.SYNC_SIZE, 'big')
        self.CHECKSUM_SIZE = 2
        self.HEADER_SIZE = 15
        self.FLAG_ACK = 0x80 # 128
        self.FLAG_END = 0x40 # 64
        self.FLAG_EMPTY = 0x00 # 0
        self.FLAG_RESET = 0x20 # 32
        self.ID_RESET = 65535

        # Exceptions
        self.invalid_flag = InvalidFlag()
        self.corrupted_frame = CorruptedFrame()
        self.invalid_payload = InvalidPayload()
        self.reset = Reset()

        # Implementation Variables
        self.sock = sock
        self.id_send = 0
        self.id_recv = 1
        self.last_checksum = 0

    def pack(self,id, data, flag):
        data = data.encode('ascii') if data != None else ''.encode('ascii')
        flag = flag if flag != None else self.FLAG_EMPTY
        length = len(data)
        aux = struct.pack(f'!IIHHHB{length}s', self.SYNC, self.SYNC, 0, length, id, flag, data)
        frame = struct.pack(f'!IIHHHB{length}s', self.SYNC, self.SYNC, self.checksum(aux), length, id, flag, data)
        # print(f"frame sent: {frame.hex(':')}")
        print(f"len frame sent: {len(frame)}, flag sent: {flag:x}, length sent: {length}, id sent: {id:x}, checksum sent: {self.checksum(aux):x}, data sent: {data}") 

        return frame
    
    def unpack(self, frame):
        offset = 0
        _, _, checksum, length, id, flag = struct.unpack_from("!IIHHHB", frame, offset)
        offset += struct.calcsize('!IIHHHB')
        data = struct.unpack_from(f"!{length}s", frame, offset)[0]
        data = data.decode('ascii')
        return checksum, length, id, flag, data
         
    def recv_frame(self):
        sync_count = 0
        while sync_count < 2:
            sync = self.sock.recv(self.SYNC_SIZE)
            if sync == self.SYNC_BYTES:
                sync_count += 1
            else:
                sync_count = 0

        header = self.sock.recv(self.HEADER_SIZE - 2*self.SYNC_SIZE)
        checksum, length, id, flag = struct.unpack('!HHHB', header)
        data = self.sock.recv(length)
        
        aux = struct.pack(f'!IIHHHB{length}s', self.SYNC, self.SYNC, 0 , length, id, flag, data)
        data = data.decode('utf-8')

        if self.checksum(aux) != checksum:
            print(f"Checksum received: {checksum} != {self.checksum(aux)}")
            raise self.corrupted_frame
        print(f"flag recv: 0x{flag:x} == {flag}, length recv: {length}, id recv: {id:x}, checksum recv: {checksum:x}, data recv: {data}")
        print()
        return data, flag, id, checksum


    def send_frame(self, data, flag=None,id=None):
        if not id:
            id=self.id_send
        if not flag:
            flag = self.FLAG_EMPTY
        frame = self.pack(id,data, flag)
        self.sock.sendall(frame)
    




    def read_in_chunks(self,data, chunk_size=4096):
        text_bytes = data.encode('utf-8')  # Converte o texto para bytes usando codificação UTF-8
        chunks = []
        for i in range(0, len(text_bytes), chunk_size):
            chunks.append(text_bytes[i:i + chunk_size])
        return chunks
        

    def send_all(self,data):
        frames=self.read_in_chunks(data)
        #envia todos os frames
        for i in range(len(frames)):
            frame_data = frames[i].decode('utf-8')
            if i == len(frames) - 1: flag = self.FLAG_END
            else: flag = self.FLAG_EMPTY
            #tenta enviar cada frame_data ate receber um ack
            while True:
                self.send_frame(frame_data,flag)
                recv_data,recv_flag,recv_id,recv_checksum=self.recv_frame()
                if(recv_flag==self.FLAG_ACK and recv_id==self.id_send):
                    if flag & self.FLAG_END:
                        raise self.invalid_flag
                    if data:
                        raise self.invalid_payload
                    else:
                        break
        #adicionar envio de frame de reset no final

    

    def recv_all(self):
        #acknowledgement frame for the last transmitted frame; EU ACHO QUE ISSO TA ERRADO E NAO PRECISA NA NOSSA IMPLEMENTACAO
        #a data frame with an identifier (ID) different from that of the last received frame;
        #a retransmission of the last received frame;
        #or a reset frame.
        recv_data=""
        while True:
            data, flag, id, checksum= self.recv_frame()
            if id != self.id_recv:
                self.id_recv=id
                recv_data+=data
            self.send_frame(None,self.FLAG_ACK,self.id_recv)
            #bom checar se realmente para quando receber o end
            if(flag==self.FLAG_END):
                break
        return recv_data
        #temos que adicionar um reinicio se receber a flag de reset




    def checksum(self, data):
        """Calculate the Internet checksum as specified by RFC 1071."""
        if len(data) % 2 == 1:
            data += b'\x00'
        checksum = 0
        for i in range(0, len(data), 2):
            word = (data[i] << 8) + data[i + 1]
            checksum += word
        while (checksum >> 16) > 0:
            checksum = (checksum & 0xFFFF) + (checksum >> 16)
        return ~checksum & 0xFFFF

class InvalidFlag(Exception):
    pass

class CorruptedFrame(Exception):
    pass

class InvalidPayload(Exception):
    pass

class Reset(Exception):
    pass