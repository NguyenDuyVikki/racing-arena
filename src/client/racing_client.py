"""
Racing Arena Client implementation
"""
import socket
import select
import sys
import json
from config.settings import DEFAULT_HOST, DEFAULT_PORT, BUFFER_SIZE, SELECT_TIMEOUT
from src.utils import process_client_data, create_data_message


class RacingClient:
    """Client class for Racing Arena"""
    
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
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

    def run(self):
        """Main client loop"""
        print("Welcome to Racing Arena!")
        self.nickname = input("Enter your nickname: ")
        if not self.nickname:
            print("Nickname cannot be empty. Exiting.")
            return
            
        print(f"Connecting as {self.nickname}...")
        self.sock.send(create_data_message({"nickname": self.nickname}))

        registered = False  # Track if registration is complete
        
        while True:
            # Check for server messages
            readable, _, _ = select.select([self.sock], [], [], SELECT_TIMEOUT)
            for sock in readable:
                try:
                    data = sock.recv(BUFFER_SIZE).decode("utf8")
                    if not data:
                        print("Disconnected from server")
                        return
                    
                    # Process potentially multiple messages
                    self.buffer, messages = process_client_data(self.buffer, data)
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
                            self.sock.send(create_data_message({"nickname": self.nickname}))
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
                        self.sock.send(create_data_message({"answer": answer}))
                        self.waiting_for_answer = False
                    except ConnectionResetError:
                        print("Connection lost while sending answer")
                        return
                    except Exception as e:
                        print(f"Error sending answer: {e}")
                        return

    def close(self):
        """Close the client connection"""
        try:
            self.sock.close()
        except:
            pass
