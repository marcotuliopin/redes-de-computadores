import socket
import struct
from typing import Optional

class DCCNET:
    def __init__(self, sock: Optional[socket.socket] =None):
        # Constants
        self.TIMEOUT = 1
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

    def pack(self, data, flag):
        data = data.encode('ascii') if data != None else ''.encode('ascii')
        flag = flag if flag != None else self.FLAG_EMPTY
        length = len(data)
        aux = struct.pack(f'!IIHHHB{length}s', self.SYNC, self.SYNC, 0, length, self.id_send, flag, data)
        frame = struct.pack(f'!IIHHHB{length}s', self.SYNC, self.SYNC, self.checksum(aux), length, self.id_send, flag, data)
        print(f"frame setn: {frame.hex(':')}")
        print(f"len fram sent: {len(frame)}, flag sent: {flag:x}, length sent: {length}, id sent: {self.id_send:x}, checksum sent: {self.checksum(aux):x}, data sent: {data}") 

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

        if self.checksum(aux) != checksum:
            print(f"Checksum received: {checksum} != {self.checksum(aux)}")
            raise self.corrupted_frame
        print(f"flag rcv: {flag:x}, length rcv: {length}, id rcv: {id:x}, checksum rcv: {checksum:x}")
        return data.decode('ascii'), flag, id, checksum


    def send_frame(self, data, flag=None):
        if not flag:
            flag = self.FLAG_EMPTY
        frame = self.pack(data, flag)
        self.sock.sendall(frame)
        

    

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