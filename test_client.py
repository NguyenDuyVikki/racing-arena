#!/usr/bin/env python3
"""
Quick test client for Racing Arena
"""
import time
import threading
from main import RacingClient

def run_test_client(nickname):
    """Run a test client with automated responses"""
    try:
        client = RacingClient()
        client.nickname = nickname
        print(f"[{nickname}] Starting client...")
        
        # Override the run method for testing
        import socket
        import json
        import select
        
        client.sock.send(json.dumps({"nickname": nickname}).encode())
        
        while True:
            readable, _, _ = select.select([client.sock], [], [], 0.1)
            for sock in readable:
                try:
                    data = sock.recv(1024).decode()
                    if not data:
                        print(f"[{nickname}] Disconnected from server")
                        return
                    msg = json.loads(data)
                    message = msg["message"]
                    print(f"[{nickname}] {message}")
                    
                    if "Solve:" in message:
                        # Extract the math expression and solve it
                        expr = message.split("Solve: ")[1].split(" = ?")[0]
                        try:
                            # Simple automated response (could be wrong sometimes for testing)
                            answer = str(eval(expr))
                            if nickname == "speedy_7":
                                time.sleep(0.5)  # Fast response
                            else:
                                time.sleep(1.5)  # Slower response
                            client.sock.send(json.dumps({"answer": answer}).encode())
                            print(f"[{nickname}] Answered: {answer}")
                        except:
                            # Send wrong answer occasionally
                            client.sock.send(json.dumps({"answer": "999"}).encode())
                            print(f"[{nickname}] Answered: 999 (wrong)")
                        
                except Exception as e:
                    print(f"[{nickname}] Error: {e}")
                    return
                    
    except Exception as e:
        print(f"[{nickname}] Failed to connect: {e}")

if __name__ == "__main__":
    # Test with two clients
    print("Starting test clients...")
    
    client1 = threading.Thread(target=run_test_client, args=("speedy_7",))
    client2 = threading.Thread(target=run_test_client, args=("racer_9",))
    
    client1.start()
    time.sleep(1)
    client2.start()
    
    try:
        client1.join()
        client2.join()
    except KeyboardInterrupt:
        print("\nTest interrupted")
