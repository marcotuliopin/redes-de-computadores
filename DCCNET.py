import socket
import struct
from typing import Optional

class DCCNET:
    def __init__(self, sock: Optional[socket.socket] =None):
        # Constants
        self.TIMEOUT= 1
        self.SYNC=0xDCC023C2
        self.SYNC_SIZE = 4
        self.CHECKSUM_SIZE = 2
        self.HEADER_SIZE = 15
        self.FLAG_ACK = 0x80
        self.FLAG_END = 0x40
        self.FLAG_EMPTY = 0x00
        self.FLAG_RESET = 0x20
        self.ID_RESET = 65535

        # Exceptions
        self.invalid_flag = InvalidFlag()
        self.corrupted_frame = CorruptedFrame()
        self.invalid_payload = InvalidPayload()

        # Implementation Variables
        self.sock = sock
        self.id_send = 0
        self.id_recv = 1
        self.last_checksum = 0

    def pack(self, data, flag):
        data = data.encode('ascii')
        length = len(data)
        aux = struct.pack(f'!IIHHHB{length}s', self.SYNC, self.SYNC, 0, length, self.id_send, flag, data)

        frame = struct.pack(f'!IIHHHB{length}s', self.SYNC, self.SYNC, self.checksum(aux), length, self.id_send, flag, data)
        return frame
    
    def unpack(self, frame):
        offset = 0
        _, _, checksum, length, id, flag = struct.unpack_from("!IIHHHB", frame, offset)
        offset += struct.calcsize('!IIHHHB')
        data = struct.unpack_from(f"!{length}s", frame, offset)[0]
        data = data.decode('utf-8')
        return checksum, length, id, flag, data
         
    def recv_frame(self):
        sync_count = 0
        while sync_count < 2:
            sync = self.sock.recv(self.SYNC_SIZE)
            if sync == self.SYNC:
                sync_count += 1
            else:
                sync_count = 0

        header = self.sock.recv(self.HEADER_SIZE - self.SYNC_SIZE)
        checksum, length, id, flag = struct.unpack('!HHHB', header[:5])

        data = self.sock.recv(length)

        frame = struct.pack(f'!IIHHBB{length}s', self.SYNC, self.SYNC, 0 , length, id, flag, data)
        if self.checksum(frame) != checksum:
            raise self.corrupted_frame
        return data, flag, id, checksum

    def recvall(self):
        dataall = "".encode('utf-8')
        while True:
            while True:
                data_rec, flag_rec, id_rec = self.recv_frame()
                if flag_rec == self.FLAG_ACK:
                    raise self.invalid_flag
                if id_rec != self.id_recv: # Recebendo o frame certo
                    dataall += data_rec
                    break
            if flag_rec == self.FLAG_END:
                break
        return dataall

    def send_frame(self, data, flag=None):
        if not flag:
            flag = self.FLAG_EMPTY
        frame = self.pack(data, flag)
        self.sock.sendall(frame)
        
    def sendall(self, data):
        max_frame_size = 2**16
        max_frame_size //= 8

        for i in range(0, len(data), max_frame_size):
            flag = self.FLAG_EMPTY

            frame = data[i: i + max_frame_size]
            if i + max_frame_size >= len(data):
                flag = self.FLAG_END 

            while True:
                try:
                    self.send_frame(frame, flag)
                    _, flag_rec, id_rec = self.recv_frame()
                    if flag_rec == self.FLAG_ACK and id_rec != self.id_recv:
                        self.id_recv = id_rec
                        break
                except (socket.timeout, self.corrupted_frame):
                    pass
    

    def checksum(data):
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