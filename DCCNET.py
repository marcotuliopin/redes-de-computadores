import socket
import struct
from typing import Optional

# For debbuging: 
flags={
        0x80:"FLAG_ACK",
        0x40 :"FLAG_END",
        0x00 :"FLAG_EMPTY",
        0x20 :"FLAG_RESET"
}

class DCCNET:
    def __init__(self, sock: Optional[socket.socket]=None):
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
        self.ID_RESET = 0xffff #65535

        # Implementation Variables
        self.sock = sock
        self.id_send = 0
        self.id_recv = 1
        self.last_checksum = 0

    def pack(self, data, flag, id):
        data = data.encode('ascii') if data != None else ''.encode('ascii')
        flag = flag if flag != None else self.FLAG_EMPTY
        length = len(data)
        aux = struct.pack(f'!IIHHHB{length}s', self.SYNC, self.SYNC, 0, length, id, flag, data)
        frame = struct.pack(f'!IIHHHB{length}s', self.SYNC, self.SYNC, self.checksum(aux), length, id, flag, data)
        print("ENVIADO")
        # print(f"flag sent: {flag:x} == {flags[flag]}, length sent: {length}, id sent: {id:x}, checksum sent: {self.checksum(aux):x}, data sent: {data}") 
        print(f"flag sent: {flag:x} == {flags[flag]}, length sent: {length}, id sent: {id:x}, checksum sent: {self.checksum(aux):x}") 

        return frame
    
    def unpack(self, frame):
        offset = 0
        _, _, checksum, length, id, flag = struct.unpack_from("!IIHHHB", frame, offset)
        offset += struct.calcsize('!IIHHHB')
        data = struct.unpack_from(f"!{length}s", frame, offset)[0]
        data = data.decode('ascii')
        return checksum, length, id, flag, data
         
    def recv_frame(self):
        try:
            sync_count = 0
            a = 0
            while sync_count < 2:
                sync = self.sock.recv(self.SYNC_SIZE)
                if not sync: raise self.NoRecvData
                if sync == self.SYNC_BYTES:
                    sync_count += 1
                else:
                    sync_count = 0
                a += 1
                if a > 6:
                    raise KeyboardInterrupt

            header = self.sock.recv(self.HEADER_SIZE - 2*self.SYNC_SIZE)
        except socket.timeout:
            return None, None, None, None
        print('Received response')

        checksum, length, id, flag = struct.unpack('!HHHB', header)
        data = self.sock.recv(length)
        
        recv_checksum = self.checksum(struct.pack(f'!IIHHHB{length}s', self.SYNC, self.SYNC, 0 , length, id, flag, data))
        if recv_checksum != checksum:
            raise self.CorruptedFrame

        data = data.decode('ascii')

        print("RECEBIDO:")
        # print(f"flag recv: 0x{flag:x} == {flags[flag]}, length recv: {length}, id recv: 0x{id:x}, checksum recv: 0x{recv_checksum:x}, data recv: {data}")
        print(f"flag recv: 0x{flag:x} == {flags[flag]}, length recv: {length}, id recv: 0x{id:x}, checksum recv: 0x{recv_checksum:x}")
        return data, flag, id, checksum


    def send_frame(self, data, flag=None, id = None):
        if id == None:
            id = self.id_send
        if flag == None:
            flag = self.FLAG_EMPTY
        frame = self.pack(data, flag, id)

        try:
            self.sock.sendall(frame)
        except socket.timeout:
            pass
        
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

    # Exceptions
    class InvalidFlag(Exception):
        pass
    class CorruptedFrame(Exception):
        pass
    class InvalidPayload(Exception):
        pass
    class NoRecvData(Exception):
        pass
    class Reset(Exception):
        pass
