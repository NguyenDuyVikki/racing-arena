import socket
import select
import time
from typing import Dict
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import (
    DEFAULT_HOST, DEFAULT_PORT, MIN_CLIENTS, MAX_CLIENTS, BUFFER_SIZE, 
    SELECT_TIMEOUT, CONNECTION_BACKLOG, MAX_MESSAGE_SIZE
)
from src.utils import is_port_available, find_available_port, process_client_data, create_message, create_data_message
from src.game import Player, GameState, RoundProcessor


class RacingServer:
    
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
            self.server.listen(CONNECTION_BACKLOG)
            print(f"[Server] Successfully bound to {host}:{port}")
            print(f"[Server] Non-blocking mode enabled with {CONNECTION_BACKLOG} connection backlog")
        except OSError as e:
            print(f"[Server] Failed to bind to {host}:{port}: {e}")
            raise
            
        self.clients: Dict[socket.socket, Player] = {}
        self.client_buffers: Dict[socket.socket, str] = {}
        self.game_state = GameState()

    def broadcast(self, message: str):
        message_data = create_message(message)
        print(f"[Server] Broadcasting message: {message}")
        failed_clients = []
        
        for client in self.clients.keys():
            try:
                client.send(message_data)
            except BlockingIOError:
                # Send would block - client buffer is full
                # Add to retry list or drop message depending on criticality
                print(f"[Server] Warning: Message send would block for client")
                # For now, we'll skip this client for this message
                pass
            except (ConnectionResetError, BrokenPipeError):
                # Client disconnected
                failed_clients.append(client)
            except Exception as e:
                print(f"[Server] Error broadcasting to client: {e}")
                failed_clients.append(client)
        
        # Remove failed clients after iteration to avoid modifying dict during iteration
        for client in failed_clients:
            self.remove_client(client)

    def run(self):
        print("[Server] Starting non-blocking server...")
        print(f"[Server] Monitoring {MAX_CLIENTS} max clients with {SELECT_TIMEOUT}s timeout")
        
        try:
            while True:
                # Use select() with timeout to prevent blocking
                # This ensures the game loop runs at least every SELECT_TIMEOUT seconds
                readable, writable, exceptional = select.select(
                    [self.server] + list(self.clients.keys()),  # Input sockets to monitor
                    [],  # Output sockets (none needed for this implementation)
                    list(self.clients.keys()),  # Error sockets to monitor
                    SELECT_TIMEOUT  # Timeout prevents blocking
                )
                
                # Handle new connections (non-blocking)
                if self.server in readable:
                    self._handle_new_connection()
                
                # Handle client data (non-blocking)
                for sock in readable:
                    if sock != self.server:
                        self._handle_client_data(sock)
                
                # Handle socket errors/exceptions
                for sock in exceptional:
                    print(f"[Server] Socket exception detected, removing client")
                    self.remove_client(sock)
                
                # Always run game loop regardless of socket activity
                # This ensures game timing is never blocked by network operations
                self._game_loop()
                
        except KeyboardInterrupt:
            print("\n[Server] Shutting down gracefully...")
            self._shutdown()
        except Exception as e:
            print(f"[Server] Unexpected error in main loop: {e}")
            self._shutdown()

    def _handle_new_connection(self):
        try:
            # Handle multiple pending connections in one go
            while True:
                try:
                    client, addr = self.server.accept()
                    
                    # Immediately set to non-blocking to prevent future blocking
                    client.setblocking(False)
                    
                    # Check client limit
                    if len(self.clients) >= MAX_CLIENTS:
                        print(f"[Server] Connection rejected: Max clients ({MAX_CLIENTS}) reached")
                        try:
                            client.send(create_message("Server full. Please try again later."))
                            client.close()
                        except:
                            pass
                        continue
                    
                    # Add client to tracking
                    self.clients[client] = Player()
                    self.client_buffers[client] = ""
                    
                    print(f"[Server] Player connected from {addr} ({len(self.clients)}/{MAX_CLIENTS})")
                    
                    # Send welcome message (non-blocking send)
                    try:
                        client.send(create_message("Welcome to Racing Arena! Enter your nickname:"))
                    except BlockingIOError:
                        # If send would block, client will receive welcome on next iteration
                        pass
                    
                except BlockingIOError:
                    # No more pending connections
                    break
                    
        except Exception as e:
            print(f"[Server] Error in connection handling: {e}")

    def _handle_client_data(self, sock: socket.socket):
        try:
            # Non-blocking read with proper error handling
            data = sock.recv(BUFFER_SIZE).decode('utf-8')
            
            if not data:
                # Client disconnected gracefully
                self.remove_client(sock)
                return
            
            # Initialize buffer if needed
            if sock not in self.client_buffers:
                self.client_buffers[sock] = ""
            
            # Safety check for buffer size to prevent memory issues
            if len(self.client_buffers[sock]) + len(data) > MAX_MESSAGE_SIZE:
                print(f"[Server] Message buffer too large for client, disconnecting")
                self.remove_client(sock)
                return
            
            # Process potentially multiple messages with buffering
            self.client_buffers[sock], messages = process_client_data(self.client_buffers[sock], data)
            
            # Process each complete message
            for msg in messages:
                self._process_client_message(sock, msg)
                    
        except BlockingIOError:
            # No data available right now - this is normal for non-blocking sockets
            pass
        except UnicodeDecodeError:
            print(f"[Server] Invalid UTF-8 data received from client")
            self.remove_client(sock)
        except ConnectionResetError:
            # Client disconnected abruptly
            self.remove_client(sock)
        except Exception as e:
            print(f"[Server] Error handling client data: {e}")
            self.remove_client(sock)

    def _handle_registration(self, sock: socket.socket, nickname: str):
        """
        Handle player registration with non-blocking sends.
        """
        try:
            # Check if nickname is valid and not taken
            if not nickname:
                try:
                    sock.send(create_message("Nickname cannot be empty. Please enter a valid nickname:"))
                except BlockingIOError:
                    pass  # Will retry on next message
                return
            
            if any(player.nickname == nickname for player in self.clients.values()):
                try:
                    sock.send(create_message(f"Nickname '{nickname}' is already taken. Please choose another:"))
                except BlockingIOError:
                    pass  # Will retry on next message
                return
            
            # Nickname is valid and available
            self.clients[sock].nickname = nickname
            print(f"[Server] Player connected: {nickname}")
            
            try:
                sock.send(create_message("Registration Completed Successfully"))
            except BlockingIOError:
                pass  # Client will see this eventually
            
            current_players = len([p for p in self.clients.values() if p.nickname])
            if current_players < MIN_CLIENTS:
                try:
                    sock.send(create_message("Waiting for other players..."))
                except BlockingIOError:
                    pass
            elif MIN_CLIENTS <= current_players <= MAX_CLIENTS and not self.game_state.game_started:
                self._start_game()
                
        except Exception as e:
            print(f"[Server] Error in registration: {e}")

    def _start_game(self):
        self.game_state.start_game()
        player_count = len(self.clients)
        print(f"[Server] Race starting with {player_count} players")
        print(f"[Server] Track length: {self.game_state.track_length} units")
        self.broadcast(f"Race Started! Track length: {self.game_state.track_length}")
        
        # Send initial position to each player
        for client in self.clients.keys():
            try:
                client.send(create_message("Your position: 1"))
            except:
                pass
        
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
        """
        Safely remove a client with proper cleanup.
        This method is non-blocking and won't affect other clients.
        """
        if sock in self.clients:
            nickname = self.clients[sock].nickname or 'Unknown'
            print(f"[Server] Player disconnected: {nickname}")
            
            # Remove from clients dict
            del self.clients[sock]
            
            # Clean up client buffer
            if sock in self.client_buffers:
                del self.client_buffers[sock]
            
            # Clean up any game state references
            if hasattr(self.game_state, 'responses') and sock in self.game_state.responses:
                del self.game_state.responses[sock]
                
            # Close socket safely
            try:
                sock.close()
            except:
                pass
                
            # Check if game needs to be paused due to insufficient players
            current_players = len([p for p in self.clients.values() if p.nickname])
            if current_players < MIN_CLIENTS and self.game_state.game_started:
                print(f"[Server] Insufficient players ({current_players}/{MIN_CLIENTS}), pausing game")
                try:
                    self.broadcast("Not enough players. Game paused.")
                except:
                    pass
                self.game_state.game_started = False

    def _process_client_message(self, sock: socket.socket, msg: dict):
        try:
            if sock not in self.clients:
                return
                
            player = self.clients[sock]
            
            if not player.nickname:
                # Handle registration
                self._handle_registration(sock, msg.get("nickname", ""))
            elif self.game_state.game_started and msg.get("answer") is not None:
                # Handle game answer
                self.game_state.add_response(sock, msg["answer"])
            else:
                # Handle other message types if needed
                pass
                
        except Exception as e:
            print(f"[Server] Error processing message: {e}")

    def _shutdown(self):
        print("[Server] Shutting down...")
        
        # Notify all clients
        try:
            self.broadcast("Server shutting down. Thank you for playing!")
        except:
            pass
        
        # Close all client connections
        for client in list(self.clients.keys()):
            try:
                client.close()
            except:
                pass
        
        # Close server socket
        try:
            self.server.close()
        except:
            pass
        
        print("[Server] Shutdown complete")
