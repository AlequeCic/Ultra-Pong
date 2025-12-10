import socket
import json
import threading
import select
from collections import deque


class TCPServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 5555, max_clients: int = 2):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        
        self.server_socket: socket.socket | None = None
        self.running = False
        
        self.clients: dict[socket.socket, dict] = {}
        self.client_lock = threading.Lock()
        
        self.receive_queue: deque = deque()
        
        self._accept_thread: threading.Thread | None = None
        self._receive_thread: threading.Thread | None = None
    
    def start(self) -> bool:
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_clients)
            self.server_socket.setblocking(False)
            
            self.running = True
            
            self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
            self._accept_thread.start()
            
            self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._receive_thread.start()
            
            print(f"[TCP Server] Servidor iniciado em {self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"[TCP Server] Erro ao iniciar servidor: {e}")
            return False
    
    def stop(self):
        self.running = False
        
        # Fechar o socket do servidor primeiro para desbloquear accept()
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        # Fechar conexões dos clientes sem esperar
        with self.client_lock:
            for client_socket in list(self.clients.keys()):
                try:
                    client_socket.close()
                except:
                    pass
            self.clients.clear()
        
        print("[TCP Server] Servidor encerrado")
    
    def _accept_loop(self):
        while self.running and self.server_socket:
            try:
                ready, _, _ = select.select([self.server_socket], [], [], 0.1)
                
                if not ready:
                    continue
                
                client_socket, address = self.server_socket.accept()
                
                with self.client_lock:
                    if len(self.clients) >= self.max_clients:
                        print(f"[TCP Server] Conexão recusada (servidor cheio): {address}")
                        client_socket.close()
                        continue
                
                client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                
                client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                try:
                    client_socket.setsockopt(socket.IPPROTO_TCP, 4, 10)   # TCP_KEEPIDLE
                    client_socket.setsockopt(socket.IPPROTO_TCP, 5, 3)    # TCP_KEEPINTVL
                    client_socket.setsockopt(socket.IPPROTO_TCP, 6, 3)    # TCP_KEEPCNT
                except (AttributeError, OSError):
                    pass
                
                client_socket.setblocking(False)
                
                client_id = len(self.clients) + 1
                
                with self.client_lock:
                    self.clients[client_socket] = {
                        'id': client_id,
                        'address': address,
                        'buffer': b''
                    }
                
                print(f"[TCP Server] Cliente {client_id} conectado: {address}")
                
                self.receive_queue.append({
                    'type': 'client_connected',
                    'client_id': client_id,
                    'address': address
                })
                
            except Exception as e:
                if self.running:
                    print(f"[TCP Server] Erro ao aceitar conexão: {e}")
    
    def _receive_loop(self):
        while self.running:
            with self.client_lock:
                if not self.clients:
                    continue
                client_sockets = list(self.clients.keys())
            
            try:
                if not client_sockets:
                    select.select([], [], [], 0.1)
                    continue
                    
                ready_to_read, _, _ = select.select(client_sockets, [], [], 0.1)
                
                for client_socket in ready_to_read:
                    self._handle_client_data(client_socket)
                    
            except Exception as e:
                if self.running:
                    continue
    
    def _handle_client_data(self, client_socket: socket.socket):
        try:
            chunk = client_socket.recv(4096)
            
            if not chunk:
                self._handle_disconnect(client_socket)
                return
            
            with self.client_lock:
                if client_socket not in self.clients:
                    return
                self.clients[client_socket]['buffer'] += chunk
                client_info = self.clients[client_socket]
            
            self._process_client_buffer(client_socket, client_info)
            
        except ConnectionResetError:
            self._handle_disconnect(client_socket)
        except Exception as e:
            if self.running:
                print(f"[TCP Server] Erro ao receber dados: {e}")
            self._handle_disconnect(client_socket)
    
    def _process_client_buffer(self, client_socket: socket.socket, client_info: dict):
        buffer = client_info['buffer']
        
        while len(buffer) >= 4:
            msg_length = int.from_bytes(buffer[:4], byteorder='big')
            
            if len(buffer) < 4 + msg_length:
                break
            
            payload = buffer[4:4 + msg_length]
            buffer = buffer[4 + msg_length:]
            
            try:
                data = json.loads(payload.decode('utf-8'))
                data['_client_id'] = client_info['id']
                self.receive_queue.append(data)
            except json.JSONDecodeError as e:
                print(f"[TCP Server] Erro ao decodificar JSON: {e}")
        
        with self.client_lock:
            if client_socket in self.clients:
                self.clients[client_socket]['buffer'] = buffer
    
    def _handle_disconnect(self, client_socket: socket.socket):
        with self.client_lock:
            if client_socket not in self.clients:
                return
            client_info = self.clients[client_socket]
            client_id = client_info['id']
        
        self._disconnect_client(client_socket)
        
        self.receive_queue.append({
            'type': 'client_disconnected',
            'client_id': client_id
        })
        
        print(f"[TCP Server] Cliente {client_id} desconectado")
    
    def _disconnect_client(self, client_socket: socket.socket):
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        finally:
            client_socket.close()
        
        with self.client_lock:
            if client_socket in self.clients:
                del self.clients[client_socket]
    
    def send_to_client(self, client_id: int, data: dict) -> bool:
        with self.client_lock:
            for client_socket, info in self.clients.items():
                if info['id'] == client_id:
                    return self._send_to_socket(client_socket, data)
        return False
    
    def send_to_all(self, data: dict):
        with self.client_lock:
            for client_socket in list(self.clients.keys()):
                self._send_to_socket(client_socket, data)
    
    def send_to_all_except(self, exclude_client_id: int, data: dict):
        with self.client_lock:
            for client_socket, info in list(self.clients.items()):
                if info['id'] != exclude_client_id:
                    self._send_to_socket(client_socket, data)
    
    def _send_to_socket(self, client_socket: socket.socket, data: dict) -> bool:
        try:
            payload = json.dumps(data).encode('utf-8')
            length_prefix = len(payload).to_bytes(4, byteorder='big')
            message = length_prefix + payload
            client_socket.sendall(message)
            return True
        except Exception as e:
            print(f"[TCP Server] Erro ao enviar: {e}")
            self._handle_disconnect(client_socket)
            return False
    
    def get_messages(self) -> list:
        messages = list(self.receive_queue)
        self.receive_queue.clear()
        return messages
    
    def get_client_count(self) -> int:
        with self.client_lock:
            return len(self.clients)
    
    def get_client_ids(self) -> list:
        with self.client_lock:
            return [info['id'] for info in self.clients.values()]


if __name__ == '__main__':
    import time
    import signal
    
    server = TCPServer('0.0.0.0', 5555)
    
    def signal_handler(sig, frame):
        print("\nEncerrando...")
        server.stop()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if server.start():
        print("Servidor rodando. Pressione Ctrl+C para parar.")
        
        while server.running:
            messages = server.get_messages()
            for msg in messages:
                print(f"Mensagem recebida: {msg}")
                
                if msg.get('type') == 'client_connected':
                    server.send_to_client(msg['client_id'], {
                        'type': 'welcome',
                        'your_id': msg['client_id']
                    })
                
                elif msg.get('type') not in ['client_connected', 'client_disconnected']:
                    server.send_to_all({
                        'type': 'broadcast',
                        'from': msg.get('_client_id'),
                        'data': msg
                    })
            
            time.sleep(0.016)
