import socket 
import struct
import json
import time
from collections import deque

# tipos de pacotes
TYPE_UNRELIABLE = 0
TYPE_RELIABLE = 1
TYPE_ACK = 2

class PongProtocol:
    def __init__(self, port=0, ip =''):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip,port))
        self.sock.setblocking(False)

        #Controle de Confiabilidade
        self.seq_num = 0
        self.pending_acks = {} # {seq_id: {data, timestamp, retries, addr}}
        self.max_retries = 5
        self.resend_timeout = 0.2

        #buffer de mensagens recebidadas prontas para uso
        self.receive_queue = deque()

    def send(self, data, addr, reliable = False):
        #empacota e envia dados para o endereço especificado
        packet_type = TYPE_RELIABLE if reliable else TYPE_UNRELIABLE

        #inCRementa SEQ apenas para Realiable(simplificação)
        current_seq = 0
        if reliable:
            self.seq_num +=1
            current_seq = self.seq_num

        # Header: Type(1B) + seq(4B)
        header = struct.pack('!BI', packet_type, current_seq)
        payload = json.dumps(data).encode('utf-8')
        packet = header + payload

        try:
            self.sock.sendto(packet, addr)

            if reliable:
                self.pending_acks[current_seq] = {
                    'data':packet,
                    'time': time.time(),
                    'retries': 0,
                    'addr': addr
                }
        except BlockingIOError: pass

    def update(self):
        #gerencia reenvios e leitura do socket. cahamar a cada frame.
        self._process_resends()
        self._read_socket()

    def _process_resends(self):
        now = time.time()
        to_remove = []
        for seq, info in self.pending_acks.items():
            if now - info['time'] > self.resend_timeout:
                if info['retries'] < self.max_retries:
                    self.sock.sendto(info['data'], info['addr'])
                    info['time'] = now
                    info['retries'] += 1
                else:
                    to_remove.append(seq) #desiste após N tentativas

        for seq in to_remove:
            del self.pending_acks[seq]
    
    def _read_socket(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(2048)
                if len(data) < 5: continue
                msg_type, seq_id = struct.unpack('!BI', data[:5])

                if msg_type == TYPE_ACK:
                    if seq_id in self.pending_acks:
                        del self.pending_acks[seq_id]

                elif msg_type == TYPE_RELIABLE:
                    #ENVIA ACK imediadtamente
                    ack = struct.pack('!BI', TYPE_ACK, seq_id)
                    self.sock.sendto(ack, addr)

                    # Decodifica e adiciona à fila
                    try:
                        decoded = json.loads(data[5:])
                        self.receive_queue.append((decoded, addr))
                    except: pass
                    
                else: # Unreliable
                    try:
                        decoded = json.loads(data[5:])
                        self.receive_queue.append((decoded, addr))
                    except: pass
                    
            except BlockingIOError: break
            except Exception as e: 
                print(f"Socket Error: {e}")
                break

    def get_messages(self):
        #Retorna todas as mensagens processadas [(data, addr), ...]
        msgs = list(self.receive_queue)
        self.receive_queue.clear()
        return msgs
