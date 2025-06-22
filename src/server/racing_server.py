"""
Racing Arena Server implementation
"""
import socket
import select
import time
from typing import Dict
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import DEFAULT_HOST, DEFAULT_PORT, MIN_CLIENTS, MAX_CLIENTS, BUFFER_SIZE, SELECT_TIMEOUT
from src.utils import is_port_available, find_available_port, process_client_data, create_message, create_data_message
from src.game import Player, GameState, RoundProcessor


class RacingServer:
    """Main server class for Racing Arena"""
    
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        # Check if the specified port is available
        if not is_port_available(host, port):
            print(f"[Server] Port {port} is already in use")
            # Try to find an available port
            available_port = find_available_port(host, port, 10)
            if available_port:
                print(f"[Server] Using alternative port: {available_port}")
                port = available_port
            else:
                raise OSError(f"No available ports found starting from {port}")
        
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Enable SO_REUSEADDR to avoid "Address already in use" errors
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.setblocking(False)
        
        try:
            self.server.bind((host, port))
            self.server.listen(MAX_CLIENTS)
            print(f"[Server] Successfully bound to {host}:{port}")
        except OSError as e:
            print(f"[Server] Failed to bind to {host}:{port}: {e}")
            raise
            
        self.clients: Dict[socket.socket, Player] = {}
        self.client_buffers: Dict[socket.socket, str] = {}
        self.game_state = GameState()

    def broadcast(self, message: str):
        for client in list(self.clients.keys()):
            try:
                client.send(create_message(message))
            except (ConnectionResetError, BrokenPipeError):
                self.remove_client(client)

    def run(self):
        print("[Server] Starting...")
        while True:
            readable, _, _ = select.select([self.server] + list(self.clients.keys()), [], [], SELECT_TIMEOUT)
            
            for sock in readable:
                if sock is self.server:
                    self._handle_new_connection()
                else:
                    self._handle_client_data(sock)
            
            self._game_loop()

    def _handle_new_connection(self):
        try:
            client, addr = self.server.accept()
            client.setblocking(False)
            self.clients[client] = Player()
            print(f"[Server] Player connected from {addr}")
            client.send(create_message("Welcome to Racing Arena! Enter your nickname:"))
        except Exception as e:
            print(f"[Server] Error accepting connection: {e}")

    def _handle_client_data(self, sock: socket.socket):
        try:
            data = sock.recv(BUFFER_SIZE).decode()
            if not data:
                self.remove_client(sock)
                return
            
            # Process potentially multiple messages
            if sock not in self.client_buffers:
                self.client_buffers[sock] = ""
            
            self.client_buffers[sock], messages = process_client_data(self.client_buffers[sock], data)
            
            for msg in messages:
                if not self.clients[sock].nickname:
                    self._handle_registration(sock, msg.get("nickname", ""))
                elif self.game_state.game_started and msg.get("answer") is not None:
                    self.game_state.add_response(sock, msg["answer"])
                    
        except (ConnectionResetError, KeyError):
            self.remove_client(sock)
        except BlockingIOError:
            pass  # No data available yet
        except Exception as e:
            print(f"[Server] Error handling client data: {e}")
            self.remove_client(sock)

    def _handle_registration(self, sock: socket.socket, nickname: str):
        # Check if nickname is valid and not taken
        if not nickname:
            sock.send(create_message("Nickname cannot be empty. Please enter a valid nickname:"))
            return
        
        if any(player.nickname == nickname for player in self.clients.values()):
            sock.send(create_message(f"Nickname '{nickname}' is already taken. Please choose another:"))
            return
        
        # Nickname is valid and available
        self.clients[sock].nickname = nickname
        print(f"[Server] Player registered: {nickname}")
        sock.send(create_message("Registration Completed Successfully"))
        
        current_players = len([p for p in self.clients.values() if p.nickname])
        if current_players < MIN_CLIENTS:
            sock.send(create_message("Waiting for other players..."))
        elif MIN_CLIENTS <= current_players <= MAX_CLIENTS and not self.game_state.game_started:
            self._start_game()

    def _start_game(self):
        self.game_state.start_game()
        player_count = len(self.clients)
        print(f"[Server] Race starting with {player_count} players")
        self.broadcast(f"Race Started! Track length: {self.game_state.track_length}")
        self.broadcast("Your position: 1")
        
        # Reset all players
        for player in self.clients.values():
            player.reset()
        
        self._new_round()

    def _new_round(self):
        self.game_state.new_round()
        self.broadcast(f"[Round {self.game_state.round_number}]")
        self.broadcast(f"Solve: {self.game_state.current_expression} = ?")

    def _game_loop(self):
        if not self.game_state.game_started or not self.game_state.round_start_time:
            return

        if self.game_state.is_round_timeout():
            self._process_round()

    def _process_round(self):
        continue_game = RoundProcessor.process_round(
            self.game_state, 
            self.clients, 
            self.broadcast
        )
        
        if continue_game:
            self._new_round()
        else:
            self._reset_game()

    def _reset_game(self):
        print(f"[Server] Game ended. Starting new race...")
        self.game_state.reset_game()
        
        for player in self.clients.values():
            player.reset()
        
        time.sleep(2)  # Brief pause between games
        if len(self.clients) >= MIN_CLIENTS:
            self._start_game()

    def remove_client(self, sock: socket.socket):
        if sock in self.clients:
            nickname = self.clients[sock].nickname or 'Unknown'
            print(f"[Server] Player disconnected: {nickname}")
            del self.clients[sock]
            
            # Clean up client buffer
            if sock in self.client_buffers:
                del self.client_buffers[sock]
                
            try:
                sock.close()
            except:
                pass
                
            if len(self.clients) < MIN_CLIENTS and self.game_state.game_started:
                self.broadcast("Not enough players. Game paused.")
                self.game_state.game_started = False
