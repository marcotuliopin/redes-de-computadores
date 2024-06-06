import socket
import struct

ACK = 1 << 7
END = 1 << 6

EMPTY_FRAME_ERROR = -1

class DCCNET:
    def __init__(self,host,port): #gabriel
        self.TIMEOUT= 1
        self.ID=0
        self.SYNC=0xDCC023C2
        #cria socket para conexao e salva para acesso nas funcoes
        try:
            self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            self.sock.connect((host,port))
        except socket.error as e:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.connect((host,port))
        self.sock.settimeout(self.TIMEOUT)

    
    #quando o dado tiver mais de 2^16 bits dividimos em dois frames
    #quando confirmar recebimento trocar o id

    #flag no geral sera enviada como zero mas quando for o ultimo frame de dado sera 6

    #to assumindo que a data vai ser mandada como uma string, caso a gnt passe direto como bytes é so tirar a linha com encode 
    def pack(self,data,flag): #gabriel

        # Definindo os campos do frame
        data=data.encode('ascii')
        length = len(data)

        # Empacotar SYNC, ID e Length em big-endian
        message = struct.pack(f'!IIHHHB{length}s', self.SYNC,self.SYNC, self.checksum(data), length, self.ID,flag,data)
        return message
    

    #to retornando a data como string e deixando a identificação e tratamento de erros para fora da função
    def unpack(self,message): #gabriel
        offset=0
        sync1,sync2,checksum,length,id,flag=struct.unpack_from("!IIHHHB",message,offset)
        offset+=struct.calcsize('!IIHHHB')
        data=struct.unpack_from(f"!{length}s",message,offset)[0]
        data=data.decode('ascii')
        return sync1,sync2,checksum,length,id,flag,data
    
    def receive(): #araju
        pass

    def send(self, data, flag): #marco
        if len(data) == 0:
            if flag != END and flag != ACK:
                return EMPTY_FRAME_ERROR
        
        max_dsize = 2**16
        max_dsize //= 8

        frames = []
        for i in range(0, len(data), max_dsize):
            frames.append(self.pack(data[i: i + max_dsize], flag)) 

        for frame in frames:
            self.ID ^= 1
            while True:
                try:
                    self.sock.sendall(frame)
                    _, flag = self.sock.receive()
                    if flag == ACK:
                        break
                except socket.timeout:
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