import struct
import time
import socket
import threading

# Constants
SYNC = 0xDCC023C2
# 
# dcc023c2 dcc023c2f aef 0004 0000 01 02 03 04
SYNC_BYTES = SYNC.to_bytes(4, 'big')
ACK_FLAG = 0x80
END_FLAG = 0x40
FRAME_HEADER_FORMAT = '!IHHBH'
HEADER_SIZE = struct.calcsize(FRAME_HEADER_FORMAT)
SYNC_SIZE = 4
CHECKSUM_SIZE = 2
ACK_FRAME_LENGTH = 0

def internet_checksum(data):
    checksum = 0
    n = len(data) % 2
    for i in range(0, len(data) - n, 2):
        checksum += (data[i] << 8) + (data[i+1])
        checksum = (checksum & 0xffff) + (checksum >> 16)
    if n:
        checksum += data[-1] << 8
        checksum = (checksum & 0xffff) + (checksum >> 16)
    return ~checksum & 0xffff

def create_frame(length, frame_id, flags, data):
    header = struct.pack('!IHHB', SYNC, length, frame_id, flags)
    checksum = internet_checksum(header + data + b'\x00\x00')
    return header + data + struct.pack('!H', checksum)

def verify_checksum(frame):
    frame_without_checksum = frame[:-2] + b'\x00\x00'
    received_checksum = struct.unpack('!H', frame[-2:])[0]
    calculated_checksum = internet_checksum(frame_without_checksum)
    return received_checksum == calculated_checksum

class DCCNETEmulator:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.lock = threading.Lock()
        self.end_transmission = False
        self.id_counter = 0

    def send_frame(self, data, end_flag=False):
        length = len(data)
        flags = END_FLAG if end_flag else 0
        frame = create_frame(length, self.id_counter, flags, data)
        
        with self.lock:
            while True:
                self.socket.sendall(frame)
                ack = self.socket.recv(HEADER_SIZE + CHECKSUM_SIZE)
                if verify_checksum(ack) and (ack[11] & ACK_FLAG):
                    self.id_counter ^= 1
                    break
                time.sleep(1)

    def receive_frame(self):
        sync_count = 0
        while sync_count < 2:
            data = self.socket.recv(SYNC_SIZE)
            if data == SYNC_BYTES:
                sync_count += 1
            else:
                sync_count = 0
        
        header = self.socket.recv(HEADER_SIZE - SYNC_SIZE)
        length, frame_id, flags = struct.unpack('!HHB', header[:5])
        data = self.socket.recv(length)
        checksum = self.socket.recv(CHECKSUM_SIZE)
        frame = SYNC_BYTES + header + data + checksum
        
        if verify_checksum(frame):
            return data.decode()

    def send_file(self, filename):
        with open(filename, 'rb') as file:
            data = file.read()
            self.send_frame(data, end_flag=True)

    def receive_file(self, filename):
        with open(filename, 'wb') as file:
            while True:
                data = self.receive_frame()
                if not data:
                    break
                file.write(data.encode())

    def run(self, send_filename, receive_filename):
        send_thread = threading.Thread(target=self.send_file, args=(send_filename,))
        receive_thread = threading.Thread(target=self.receive_file, args=(receive_filename,))
        send_thread.start()
        receive_thread.start()
        send_thread.join()
        receive_thread.join()

# Example usage
if __name__ == "__main__":
    HOST = 'localhost'  # Change this to the grading server's hostname or IP address
    PORT = 12345  # Change this to the grading server's port
    send_filename = 'file_to_send.txt'
    receive_filename = 'received_file.txt'
    dccnet_emulator = DCCNETEmulator(HOST, PORT)
    dccnet_emulator.run(send_filename, receive_filename)
