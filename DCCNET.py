import socket
import struct

ACK = 1 << 7
END = 1 << 6

EMPTY_FRAME_ERROR = -1

class DCCNET:
    def __init__(self,host,port): #gabriel
        self.TIMEOUT= 1
        self.id_counter_send = 0
        self.id_counter_recv = 1
        self.SYNC=0xDCC023C2
        self.SYNC_SIZE = 4
        self.CHECKSUM_SIZE = 2
        self.HEADER_SIZE = 15
        self.FLAG_ACK = 0x80
        self.FLAG_END = 0x40

        
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
        data=data.encode('utf-8')
        length = len(data)

        # Empacotar SYNC, ID e Length em big-endian
        aux = struct.pack(f'!IIHHHB{length}s', self.SYNC,self.SYNC, 0, length, self.ID,flag,data)
        frame = struct.pack(f'!IIHHHB{length}s', self.SYNC,self.SYNC, self.checksum(aux), length, self.ID,flag,data)
        return frame
    

    #to retornando a data como string e deixando a identificação e tratamento de erros para fora da função
    def unpack(self, frame): #gabriel
        offset=0
        sync1,sync2,checksum,length,id,flag=struct.unpack_from("!IIHHHB",frame,offset)
        offset+=struct.calcsize('!IIHHHB')
        data=struct.unpack_from(f"!{length}s",frame,offset)[0]
        data=data.decode('utf-8')
        return sync1,sync2,checksum,length,id,flag,data
         
    def recv_frame(self): #araju
        sync_count = 0
        while sync_count < 2:
            sync = self.sock.recv(self.SYNC_SIZE)
            if sync == self.SYNC:
                sync_count += 1
            else:
                sync_count = 0
        #add try except para recebimentos
        header = self.sock.recv(self.HEADER_SIZE - self.SYNC_SIZE)
        checksum_rec, length_rec, id_rec, flag_rec = struct.unpack('!HHHB', header[:5])
        data_rec = self.sock.recv(length_rec)
        frame_wo_checksum = struct.pack(f'!IIHHBB{length_rec}s', self.SYNC, self.SYNC, 0 , length_rec, id_rec, flag_rec, data_rec)
        if self.checksum(frame_wo_checksum) != checksum_rec:
            return None,  -1
        return data_rec, flag_rec, id_rec

    def recvall(self):
        dataall = "".encode('utf-8')
        while True:
            while True:
                data_rec, flag_rec, id_rec = self.recv_frame()
                if(flag_rec == self.FLAG_ACK): # Nunca é pra entrar aqui
                    raise "recvall recebeu ACK"
                if(id_rec != self.id_counter_recv): # Recebendo o frame certo
                    dataall += data_rec
                    break
            if(flag_rec == self.FLAG_END):
                break
        return dataall
            # em loop 
                #recebe um frame com o recv
                #data+=data
                #quando receber um frame com end termina o loop
            #retorna dado completo
        
        #return data

    def send_frame(self, data, flag):
        frame = self.pack(data, flag)
        self.sock.sendall(frame)
        

    def sendall(self, dataall): #marco
        
        max_dsize = 2**16
        max_dsize //= 8

        for i in range(0, len(dataall), max_dsize):
            data = dataall[i: i + max_dsize]
            flag = 0x00
            if(i + max_dsize >= len(dataall)): # ultimo frame
                flag = self.FLAG_END 
            while True:
                try:
                    self.send_frame(data, flag)
                    _, flag_rec, id_rec = self.receive_frame()
                    if(flag_rec == self.FLAG_ACK and id_rec != self.id_counter_recv): # recebeu ack do frame certo
                        self.id_counter_recv = id_rec
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
    


    #sender

    #sendall para enviar o dado

