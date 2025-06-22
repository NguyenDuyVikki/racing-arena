import time
import threading
import json
import select
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.client import RacingClient
from src.utils import create_data_message, process_client_data


class TestClient:
    """Automated test client for Racing Arena"""
    
    def __init__(self, nickname: str, response_delay: float = 1.0):
        self.nickname = nickname
        self.response_delay = response_delay
        self.client = None
        
    def run(self):
        """Run the automated test client"""
        try:
            self.client = RacingClient()
            print(f"[{self.nickname}] Starting automated client...")
            
            # Send nickname
            self.client.sock.send(create_data_message({"nickname": self.nickname}))
            
            buffer = ""
            registered = False
            
            while True:
                readable, _, _ = select.select([self.client.sock], [], [], 0.1)
                for sock in readable:
                    try:
                        data = sock.recv(1024).decode()
                        if not data:
                            print(f"[{self.nickname}] Disconnected from server")
                            return
                        
                        buffer, messages = process_client_data(buffer, data)
                        for msg in messages:
                            message = msg["message"]
                            print(f"[{self.nickname}] {message}")
                            
                            # Handle registration
                            if "Registration Completed Successfully" in message:
                                registered = True
                            
                            # Handle math problems
                            if "Solve:" in message and registered:
                                # Extract the math expression and solve it
                                expr = message.split("Solve: ")[1].split(" = ?")[0]
                                try:
                                    # Add response delay
                                    time.sleep(self.response_delay)
                                    
                                    # Calculate answer (with occasional wrong answer for testing)
                                    if self.nickname.endswith("_wrong") and time.time() % 4 < 1:
                                        answer = "999"  # Wrong answer
                                    else:
                                        answer = str(eval(expr))
                                    
                                    self.client.sock.send(create_data_message({"answer": answer}))
                                    print(f"[{self.nickname}] Answered: {answer}")
                                except Exception as e:
                                    # Send wrong answer on error
                                    self.client.sock.send(create_data_message({"answer": "0"}))
                                    print(f"[{self.nickname}] Error solving, answered: 0")
                            
                    except Exception as e:
                        print(f"[{self.nickname}] Error: {e}")
                        return
                        
        except Exception as e:
            print(f"[{self.nickname}] Failed to connect: {e}")


def run_test_scenario():
    """Run a test scenario with multiple clients"""
    print("Starting Racing Arena Test Scenario...")
    print("Make sure the server is running with: python race.py server")
    time.sleep(2)
    
    # Create test clients with different characteristics
    clients = [
        ("speedy_alice", 0.5),    # Fast responder
        ("steady_bob", 1.2),      # Average responder  
        ("slow_charlie", 2.0),    # Slow responder
        ("error_dave_wrong", 0.8) # Sometimes wrong answers
    ]
    
    threads = []
    for nickname, delay in clients:
        client = TestClient(nickname, delay)
        thread = threading.Thread(target=client.run)
        threads.append(thread)
        thread.start()
        time.sleep(0.5)  # Stagger connections
    
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")


if __name__ == "__main__":
    run_test_scenario()
