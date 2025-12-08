from settings import *
from game import *
from network.network_handler import NetworkHandler
import argparse


def main():
    parser = argparse.ArgumentParser(description='Ultra Pong')
    parser.add_argument('--host', type=int, metavar='PORT', help='Host multiplayer game on PORT')
    parser.add_argument('--join', nargs=2, metavar=('IP', 'PORT'), help='Join multiplayer game at IP:PORT')
    args = parser.parse_args()
    
    network = None
    game_mode = "local"
    
    if args.host:
        network = NetworkHandler()
        if network.host(args.host):
            print(f"Aguardando oponente na porta {args.host}...")
            game_mode = "multiplayer_1v1"
            
            while network.waiting_for_opponent:
                network.update()
                pygame.time.wait(100)
            
            print("Oponente conectado! Iniciando jogo...")
        else:
            print("Erro ao iniciar servidor")
            return
    
    elif args.join:
        ip, port = args.join[0], int(args.join[1])
        network = NetworkHandler()
        if network.join(ip, port):
            print(f"Conectado a {ip}:{port}")
            game_mode = "multiplayer_1v1"
            
            while network.waiting_for_opponent:
                network.update()
                pygame.time.wait(100)
            
            print("Jogo iniciando...")
        else:
            print(f"Erro ao conectar em {ip}:{port}")
            return
    
    game = Game(game_mode=game_mode, network=network)
    game.run()
    
    if network:
        network.disconnect()


if __name__ == '__main__':
    main()
