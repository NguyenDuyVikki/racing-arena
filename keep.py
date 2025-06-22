import socket
import select
import time
import random
from typing import Dict, List, Tuple
import json

def is_port_available(host='localhost', port=12345):
    """Check if a port is available for binding"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_sock:
            test_sock.bind((host, port))
            return True
    except OSError:
        return False

def find_available_port(host='localhost', start_port=12345, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(host, port):
            return port
    return None

# Server implementation
class RacingServer:
    def __init__(self, host='localhost', port=12345):
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
            self.server.listen(10)
            print(f"[Server] Successfully bound to {host}:{port}")
        except OSError as e:
            print(f"[Server] Failed to bind to {host}:{port}: {e}")
            raise
            
        self.clients: Dict[socket.socket, dict] = {}  # socket: {nickname, score, position, wrong_streak}
        self.client_buffers: Dict[socket.socket, str] = {}  # Buffer for each client
        self.track_length = random.randint(4, 25)
        self.game_started = False
        self.current_expression = None
        self.current_answer = None
        self.round_start_time = None
        self.time_limit = 10.0  # seconds
        self.responses: Dict[socket.socket, Tuple[float, str]] = {}  # socket: (time, answer)
        self.round_number = 0

    def generate_expression(self) -> Tuple[str, int]:
        num1 = random.randint(-10000, 10000)
        num2 = random.randint(-10000, 10000)
        operator = random.choice(['+', '-', '*', '/', '%'])
        if operator == '/':  # Ensure integer division
            num2 = random.randint(1, 10000) if num2 == 0 else num2
            num1 = num2 * random.randint(-10000, 10000)
        expr = f"{num1} {operator} {num2}"
        answer = eval(expr)  # Safe in this context as inputs are controlled
        return expr, int(answer)

    def process_client_data(self, sock: socket.socket, data: str):
        """Process potentially multiple JSON messages from client data"""
        if sock not in self.client_buffers:
            self.client_buffers[sock] = ""
        
        self.client_buffers[sock] += data
        messages = []
        
        # Split by newlines to handle multiple messages
        lines = self.client_buffers[sock].split('\n')
        
        # Keep the last incomplete line in buffer
        self.client_buffers[sock] = lines[-1]
        
        # Process complete lines
        for line in lines[:-1]:
            line = line.strip()
            if line:
                try:
                    message = json.loads(line)
                    messages.append(message)
                except json.JSONDecodeError as e:
                    print(f"[Server] Error parsing message from client: {line} - {e}")
        
        return messages

    def broadcast(self, message: str):
        for client in list(self.clients.keys()):  # Create a copy to avoid modification during iteration
            try:
                client.send((json.dumps({"message": message}) + "\n").encode())
            except (ConnectionResetError, BrokenPipeError):
                self.remove_client(client)

    def run(self):
        print("[Server] Starting...")
        while True:
            readable, _, _ = select.select([self.server] + list(self.clients.keys()), [], [], 0.1)
            
            for sock in readable:
                if sock is self.server:
                    client, addr = self.server.accept()
                    client.setblocking(False)
                    self.clients[client] = {"nickname": None, "score": 0, "position": 1, "wrong_streak": 0}
                    print(f"[Server] Player connected from {addr}")
                    client.send((json.dumps({"message": "Welcome to Racing Arena! Enter your nickname:"}) + "\n").encode())
                else:
                    try:
                        data = sock.recv(1024).decode()
                        if not data:
                            self.remove_client(sock)
                            continue
                        
                        # Process potentially multiple messages
                        messages = self.process_client_data(sock, data)
                        for msg in messages:
                            if not self.clients[sock]["nickname"]:
                                self.handle_registration(sock, msg.get("nickname", ""))
                            elif self.game_started and msg.get("answer") is not None:
                                self.responses[sock] = (time.time(), msg["answer"])
                    except (ConnectionResetError, json.JSONDecodeError, KeyError):
                        self.remove_client(sock)
                    except BlockingIOError:
                        pass  # No data available yet
            self.game_loop()

    def handle_registration(self, sock: socket.socket, nickname: str):
        # Check if nickname is valid and not taken
        if not nickname:
            sock.send((json.dumps({"message": "Nickname cannot be empty. Please enter a valid nickname:"}) + "\n").encode())
            return
        
        if any(client["nickname"] == nickname for client in self.clients.values()):
            sock.send((json.dumps({"message": f"Nickname '{nickname}' is already taken. Please choose another:"}) + "\n").encode())
            return
        
        # Nickname is valid and available
        self.clients[sock]["nickname"] = nickname
        print(f"[Server] Player registered: {nickname}")
        sock.send((json.dumps({"message": "Registration Completed Successfully"}) + "\n").encode())
        
        current_players = len([c for c in self.clients.values() if c["nickname"]])
        if current_players < 2:
            sock.send((json.dumps({"message": "Waiting for other players..."}) + "\n").encode())
        elif 2 <= current_players <= 10 and not self.game_started:
            self.start_game()

    def start_game(self):
        self.game_started = True
        player_count = len(self.clients)
        print(f"[Server] Race starting with {player_count} players")
        print(f"[Server] Track length: {self.track_length} units")
        self.broadcast(f"Race Started! Track length: {self.track_length}")
        self.broadcast("Your position: 1")
        for client in self.clients.values():
            client["position"] = 1
            client["score"] = 0
            client["wrong_streak"] = 0
        self.new_round()

    def new_round(self):
        self.responses.clear()
        self.current_expression, self.current_answer = self.generate_expression()
        self.round_start_time = time.time()
        round_num = getattr(self, 'round_number', 0) + 1
        self.round_number = round_num
        print(f"[Round {round_num}]")
        print(f"Sent expression: {self.current_expression}")
        self.broadcast(f"[Round {round_num}]")
        self.broadcast(f"Solve: {self.current_expression} = ?")

    def game_loop(self):
        if not self.game_started or not self.round_start_time:
            return

        if time.time() - self.round_start_time >= self.time_limit:
            self.process_round()

    def process_round(self):
        penalties = 0
        correct_answers = []
        fastest = None
        fastest_time = float('inf')
        round_results = []

        # Process all players who didn't respond (timeout)
        for sock in self.clients:
            if sock not in self.responses:
                client = self.clients[sock]
                client["wrong_streak"] += 1
                client["score"] -= 1
                penalties += 1
                round_results.append(f"{client['nickname']}: timeout (-1 point)")
                if client["wrong_streak"] >= 3:
                    self.broadcast(f"Player {client['nickname']} disqualified!")
                    self.remove_client(sock)

        # Process responses
        for sock, (response_time, answer) in self.responses.items():
            client = self.clients[sock]
            try:
                user_answer = int(answer)
                is_correct = user_answer == self.current_answer
            except ValueError:
                is_correct = False

            response_delay = response_time - self.round_start_time
            if is_correct:
                correct_answers.append((sock, response_delay))
                if response_delay < fastest_time:
                    fastest_time = response_delay
                    fastest = sock
                round_results.append(f"{client['nickname']}: {answer} ({response_delay:.1f}s)")
            else:
                client["wrong_streak"] += 1
                client["score"] -= 1
                penalties += 1
                round_results.append(f"{client['nickname']}: {answer} (-1 point)")
                if client["wrong_streak"] >= 3:
                    self.broadcast(f"Player {client['nickname']} disqualified!")
                    self.remove_client(sock)

        # Award points
        for sock, _ in correct_answers:
            if sock == fastest:
                points_earned = 1 + penalties  # Base point + penalty points
                self.clients[sock]["score"] += points_earned
                round_results.append(f"  → {self.clients[sock]['nickname']} fastest: +{points_earned} points")
            else:
                self.clients[sock]["score"] += 1
            self.clients[sock]["wrong_streak"] = 0

        # Update positions based on total score
        for client in self.clients.values():
            client["position"] = max(1, 1 + client["score"])
            if client["position"] >= self.track_length:
                self.broadcast(f"Race ended! Winner: {client['nickname']}")
                self.reset_game()
                return

        # Broadcast detailed results
        print("Received:")
        for result in round_results:
            print(f"  {result}")
        
        # Show points awarded
        points_summary = "Points:"
        for client in self.clients.values():
            points_summary += f"\n  {client['nickname']} +{max(0, client['score'])} | position {client['position']}"
        print(points_summary)
        
        self.broadcast(f"Correct answer: {self.current_answer}")
        self.broadcast("Received:")
        for result in round_results:
            self.broadcast(result)

        # Show current standings
        standings = "\nPositions:"
        for client in self.clients.values():
            standings += f"\n{client['nickname']} → {client['position']}"
        self.broadcast(standings)
        
        self.new_round()

    def reset_game(self):
        print(f"[Server] Game ended. Starting new race...")
        self.track_length = random.randint(4, 25)
        self.round_number = 0
        for client in self.clients.values():
            client["score"] = 0
            client["position"] = 1
            client["wrong_streak"] = 0
        self.game_started = False
        time.sleep(2)  # Brief pause between games
        if len(self.clients) >= 2:
            self.start_game()

    def remove_client(self, sock: socket.socket):
        if sock in self.clients:
            nickname = self.clients[sock].get('nickname', 'Unknown')
            print(f"[Server] Player disconnected: {nickname}")
            del self.clients[sock]
            # Clean up client buffer
            if sock in self.client_buffers:
                del self.client_buffers[sock]
            try:
                sock.close()
            except:
                pass
            if len(self.clients) < 2 and self.game_started:
                self.broadcast("Not enough players. Game paused.")
                self.game_started = False

# Client implementation
class RacingClient:
    def __init__(self, host='localhost', port=12345):
        # Try to connect to the specified port first
        connection_successful = False
        original_port = port
        
        # If the default port doesn't work, try to find the server
        for attempt_port in range(port, port + 10):
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((host, attempt_port))
                self.sock.setblocking(False)
                self.nickname = None
                self.waiting_for_answer = False
                self.buffer = ""  # Buffer for incomplete messages
                
                if attempt_port != original_port:
                    print(f"Connected to server on port {attempt_port}")
                connection_successful = True
                break
                
            except ConnectionRefusedError:
                self.sock.close()
                continue
            except Exception as e:
                self.sock.close()
                if attempt_port == original_port:
                    print(f"Error connecting to {host}:{attempt_port}: {e}")
                continue
        
        if not connection_successful:
            print(f"Error: Could not connect to server at {host}:{original_port}")
            print("Make sure the server is running with: python main.py server")
            raise ConnectionRefusedError(f"Could not connect to server on any port from {original_port} to {original_port + 9}")

    def process_messages(self, data):
        """Process potentially multiple JSON messages from received data"""
        self.buffer += data
        messages = []
        
        # Split by newlines to handle multiple messages
        lines = self.buffer.split('\n')
        
        # Keep the last incomplete line in buffer
        self.buffer = lines[-1]
        
        # Process complete lines
        for line in lines[:-1]:
            line = line.strip()
            if line:
                try:
                    message = json.loads(line)
                    messages.append(message)
                except json.JSONDecodeError as e:
                    print(f"Error parsing message: {line} - {e}")
        
        return messages

    def run(self):
        print("Welcome to Racing Arena!")
        self.nickname = input("Enter your nickname: ")
        if not self.nickname:
            print("Nickname cannot be empty. Exiting.")
            return
        print(f"Connecting as {self.nickname}...")
        self.sock.send((json.dumps({"nickname": self.nickname}) + "\n").encode())

        import sys
        import select
        registered = False  # Track if registration is complete
        
        while True:
            # Check for server messages
            readable, _, _ = select.select([self.sock], [], [], 0.1)
            for sock in readable:
                try:
                    data = sock.recv(1024).decode("utf8")
                    if not data:
                        print("Disconnected from server")
                        return
                    
                    # Process potentially multiple messages
                    messages = self.process_messages(data)
                    for msg in messages:
                        message = msg["message"]
                        print(message)
                        
                        # Handle nickname retry scenarios
                        if not registered and ("already taken" in message or "cannot be empty" in message or "invalid" in message):
                            # Ask for a new nickname
                            new_nickname = input("Enter a different nickname: ").strip()
                            if not new_nickname:
                                print("Nickname cannot be empty. Exiting.")
                                return
                            self.nickname = new_nickname
                            self.sock.send((json.dumps({"nickname": self.nickname}) + "\n").encode())
                            continue
                        
                        # Check if registration is successful
                        if "Registration Completed Successfully" in message:
                            registered = True
                        
                        if "Solve:" in message:
                            self.waiting_for_answer = True
                        
                except json.JSONDecodeError as e:
                    print(f"Error parsing server message: {e}")
                    continue
                except ConnectionResetError:
                    print("Connection reset by server")
                    return
                except Exception as e:
                    print(f"Error communicating with server: {e}")
                    return
            
            # Check for user input when waiting for answer
            if self.waiting_for_answer:
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    answer = input("> ").strip()
                    try:
                        self.sock.send((json.dumps({"answer": answer}) + "\n").encode())
                        self.waiting_for_answer = False
                    except ConnectionResetError:
                        print("Connection lost while sending answer")
                        return
                    except Exception as e:
                        print(f"Error sending answer: {e}")
                        return

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        server = RacingServer()
        server.run()
    else:
        try:
            client = RacingClient()
            client.run()
        except KeyboardInterrupt:
            print("\nGame interrupted by user")
        except Exception as e:
            print(f"Failed to start client: {e}")
            sys.exit(1)
        