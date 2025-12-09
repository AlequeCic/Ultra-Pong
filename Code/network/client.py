import socket
import json
import threading
import select
from collections import deque


class TCPClient:
    def __init__(self, server_ip: str = 'localhost', server_port: int = 5555):
        self.server_addr = (server_ip, server_port)
        self.socket: socket.socket | None = None
        self.connected = False
        self.receive_queue: deque = deque()
        self._receive_thread: threading.Thread | None = None
        self._running = False
        self._recv_buffer = b''
        
    def connect(self) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.socket.settimeout(5.0)
            self.socket.connect(self.server_addr)
            self.socket.setblocking(False)
            
            self.connected = True
            self._running = True
            
            self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._receive_thread.start()
            
            print(f"[TCP Client] Conectado ao servidor {self.server_addr}")
            return True
            
        except socket.timeout:
            print(f"[TCP Client] Timeout ao conectar em {self.server_addr}")
            return False
        except ConnectionRefusedError:
            print(f"[TCP Client] Conexão recusada por {self.server_addr}")
            return False
        except Exception as e:
            print(f"[TCP Client] Erro ao conectar: {e}")
            return False
    
    def disconnect(self):
        self._running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            finally:
                self.socket.close()
                self.socket = None
        
        if self._receive_thread and self._receive_thread.is_alive():
            self._receive_thread.join(timeout=1.0)
        
        self._recv_buffer = b''
        print("[TCP Client] Desconectado")
    
    def send(self, data: dict) -> bool:
        if not self.connected or not self.socket:
            return False
        
        try:
            payload = json.dumps(data).encode('utf-8')
            length_prefix = len(payload).to_bytes(4, byteorder='big')
            message = length_prefix + payload
            self.socket.sendall(message)
            return True
            
        except (BrokenPipeError, ConnectionResetError):
            print("[TCP Client] Conexão perdida ao enviar")
            self.connected = False
            return False
        except Exception as e:
            print(f"[TCP Client] Erro ao enviar: {e}")
            return False
    
    def _receive_loop(self):
        while self._running and self.socket:
            try:
                ready_to_read, _, _ = select.select([self.socket], [], [], 0.1)
                
                if not ready_to_read:
                    continue
                
                chunk = self.socket.recv(4096)
                
                if not chunk:
                    print("[TCP Client] Servidor encerrou a conexão")
                    self.connected = False
                    break
                
                self._recv_buffer += chunk
                self._process_buffer()
                
            except (BlockingIOError, OSError):
                if self._running:
                    continue
                break
            except ConnectionResetError:
                print("[TCP Client] Conexão resetada pelo servidor")
                self.connected = False
                break
            except Exception as e:
                if self._running:
                    print(f"[TCP Client] Erro na recepção: {e}")
                break
    
    def _process_buffer(self):
        while len(self._recv_buffer) >= 4:
            msg_length = int.from_bytes(self._recv_buffer[:4], byteorder='big')
            
            if len(self._recv_buffer) < 4 + msg_length:
                break
            
            payload = self._recv_buffer[4:4 + msg_length]
            self._recv_buffer = self._recv_buffer[4 + msg_length:]
            
            try:
                data = json.loads(payload.decode('utf-8'))
                self.receive_queue.append(data)
            except json.JSONDecodeError as e:
                print(f"[TCP Client] Erro ao decodificar JSON: {e}")
    
    def get_messages(self) -> list:
        messages = list(self.receive_queue)
        self.receive_queue.clear()
        return messages
    
    def send_player_input(self, player_id: int, direction: float):
        self.send({
            'type': 'input',
            'player_id': player_id,
            'direction': direction
        })
    
    def send_game_event(self, event_type: str, **kwargs):
        data = {'type': event_type, **kwargs}
        self.send(data)
    
    @property
    def is_connected(self) -> bool:
        return self.connected and self.socket is not None


if __name__ == '__main__':
    import time
    
    client = TCPClient('localhost', 5555)
    
    if client.connect():
        print("Conectado! Enviando mensagens de teste...")
        
        for i in range(5):
            client.send({'type': 'test', 'message': f'Hello {i}'})
            time.sleep(0.5)
            
            messages = client.get_messages()
            for msg in messages:
                print(f"Recebido: {msg}")
        
        client.disconnect()
    else:
        print("Falha ao conectar")
