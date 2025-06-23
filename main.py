#!/usr/bin/env python3
"""
Racing Arena - Main entry point
A sophisticated real-time multiplayer terminal game where players compete by solving math expressions.
"""
import sys
import os
import argparse
import threading
import time

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.server.racing_server import RacingServer
from src.client.racing_client import RacingClient
from config.settings import DEFAULT_HOST, DEFAULT_PORT


def show_banner():
    """Display the Racing Arena banner"""
    print("""
╔══════════════════════════════════════════════╗
║              🏁 RACING ARENA 🏁              ║
║         Multiplayer Math Racing Game         ║
╚══════════════════════════════════════════════╝
""")


def show_menu():
    """Display the interactive menu"""
    show_banner()
    print("📋 Choose an option:")
    print("1. 🖥️  Start Server Only")
    print("2. 🎮 Start Client Only")
    print("3. 🔄 Start Server & Client (Local Game)")
    print("4. 🏭 Start Multiple Clients (Testing)")
    print("5. ℹ️  Show Project Information")
    print("6. 🧪 Run Tests")
    print("7. ❌ Exit")
    print()


def show_project_info():
    """Display project information"""
    show_banner()
    print("🎮 Game Overview:")
    print("Racing Arena is a competitive multiplayer math game featuring:")
    print("• Real-time competition: 2-10 players compete simultaneously")
    print("• Dynamic math expressions: Randomly generated problems")
    print("• Strategic scoring system: Speed and accuracy both matter")
    print("• Progressive race mechanics: Players advance based on performance")
    print()
    print("🛠️ Technical Features:")
    print("• Non-blocking networking for concurrent connections")
    print("• Modular architecture with separation of concerns")
    print("• Comprehensive error handling and recovery")
    print("• Built-in testing and bot support")
    print()


def start_server(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """Start the Racing Arena server"""
    try:
        print(f"🖥️  Starting Racing Arena Server on {host}:{port}...")
        server = RacingServer(host, port)
        server.run()
    except KeyboardInterrupt:
        print("\n🛑 Server shutdown requested")
    except Exception as e:
        print(f"❌ Server error: {e}")


def start_client(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """Start the Racing Arena client"""
    try:
        print(f"🎮 Connecting to Racing Arena Server at {host}:{port}...")
        client = RacingClient(host, port)
        client.run()
    except KeyboardInterrupt:
        print("\n🛑 Client disconnected")
    except Exception as e:
        print(f"❌ Client error: {e}")


def start_server_and_client(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """Start both server and client for local testing"""
    print("🔄 Starting local game (Server + Client)...")
    
    # Start server in a separate thread
    server_thread = threading.Thread(
        target=start_server, 
        args=(host, port),
        daemon=True
    )
    server_thread.start()
    
    # Give server time to start
    time.sleep(2)
    
    # Start client
    start_client(host, port)


def start_multiple_clients(host=DEFAULT_HOST, port=DEFAULT_PORT, num_clients=3):
    """Start multiple clients for testing"""
    print(f"🏭 Starting {num_clients} test clients...")
    
    def client_worker(client_id):
        try:
            time.sleep(client_id * 0.5)  # Stagger connections
            print(f"Client {client_id} connecting...")
            client = RacingClient(host, port)
            client.run()
        except Exception as e:
            print(f"Client {client_id} error: {e}")
    
    threads = []
    for i in range(1, num_clients + 1):
        thread = threading.Thread(target=client_worker, args=(i,), daemon=True)
        thread.start()
        threads.append(thread)
    
    try:
        # Wait for all threads
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\n🛑 Stopping all clients...")


def run_tests():
    """Run the test suite"""
    print("🧪 Running tests...")
    try:
        import subprocess
        result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], 
                              capture_output=False)
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed")
    except ImportError:
        print("📦 pytest not installed, running basic tests...")
        try:
            # Run basic unittest
            subprocess.run([sys.executable, "-m", "unittest", "discover", "tests/", "-v"])
        except Exception as e:
            print(f"❌ Test error: {e}")


def interactive_mode():
    """Run the interactive menu"""
    while True:
        show_menu()
        try:
            choice = input("Enter your choice (1-7): ").strip()
            
            if choice == "1":
                start_server()
            elif choice == "2":
                start_client()
            elif choice == "3":
                start_server_and_client()
            elif choice == "4":
                try:
                    num = int(input("Number of clients (default 3): ") or "3")
                    start_multiple_clients(num_clients=num)
                except ValueError:
                    start_multiple_clients()
            elif choice == "5":
                show_project_info()
                input("\nPress Enter to continue...")
            elif choice == "6":
                run_tests()
                input("\nPress Enter to continue...")
            elif choice == "7":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-7.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            print("\n👋 Goodbye!")
            break


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Racing Arena - Multiplayer Math Racing Game")
    parser.add_argument("--mode", choices=["server", "client", "local", "interactive"], 
                       default="interactive", help="Running mode")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Server host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port")
    parser.add_argument("--bots", type=int, default=2, help="Number of bot clients for local mode")
    
    args = parser.parse_args()
    
    if args.mode == "server":
        start_server(args.host, args.port)
    elif args.mode == "client":
        start_client(args.host, args.port)
    elif args.mode == "local":
        # Start server in background, then start bot clients
        server_thread = threading.Thread(
            target=start_server, 
            args=(args.host, args.port),
            daemon=True
        )
        server_thread.start()
        time.sleep(2)
        start_multiple_clients(args.host, args.port, args.bots)
    else:  # interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
