import sys
import os
import threading
import time
import argparse
from typing import Optional, List
import subprocess

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import DEFAULT_HOST, DEFAULT_PORT, MIN_CLIENTS, MAX_CLIENTS
from src.server.racing_server import RacingServer
from src.client.racing_client import RacingClient


class Main:
    """
    Main orchestrator class for the Racing Arena project.
    Provides functionality to run server, client, or both in various configurations.
    """
    
    def __init__(self):
        self.server_thread: Optional[threading.Thread] = None
        self.server_instance: Optional[RacingServer] = None
        self.client_instances: List[RacingClient] = []
        self.running = False
    
    def display_banner(self):
        """Display the game banner"""
        banner = """
╔══════════════════════════════════════════════╗
║              🏁 RACING ARENA 🏁              ║
║         Multiplayer Math Racing Game         ║
╚══════════════════════════════════════════════╝
        """
        print(banner)
    
    def display_menu(self):
        """Display the main menu options"""
        menu = """
📋 Choose an option:
1. 🖥️  Start Server Only
2. 🎮 Start Client Only
3. 🔄 Start Server & Client (Local Game)
4. 🏭 Start Multiple Clients (Testing)
5. ℹ️  Show Project Information
6. 🧪 Run Tests
7. ❌ Exit

Enter your choice (1-7): """
        return input(menu).strip()
    
    def start_server(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> bool:
        """Start the racing server"""
        try:
            print(f"\n🚀 Starting Racing Arena Server on {host}:{port}...")
            self.server_instance = RacingServer(host, port)
            
            # Run server in separate thread for non-blocking operation
            self.server_thread = threading.Thread(
                target=self.server_instance.run,
                daemon=True
            )
            self.server_thread.start()
            
            # Give server time to start
            time.sleep(1)
            print(f"✅ Server started successfully!")
            print(f"🔗 Server listening on {host}:{self.server_instance.port}")
            print(f"👥 Waiting for players to connect (min: {MIN_CLIENTS}, max: {MAX_CLIENTS})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def start_client(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, 
                    nickname: Optional[str] = None) -> Optional[RacingClient]:
        """Start a racing client"""
        try:
            print(f"\n🎮 Starting Racing Client...")
            client = RacingClient(host, port)
            
            if nickname:
                client.nickname = nickname
            
            # Run client in separate thread
            client_thread = threading.Thread(
                target=client.run,
                daemon=True
            )
            client_thread.start()
            
            self.client_instances.append(client)
            print(f"✅ Client connected successfully!")
            return client
            
        except Exception as e:
            print(f"❌ Failed to start client: {e}")
            return None
    
    def start_local_game(self, num_bots: int = 1):
        """Start server and client(s) for local testing"""
        print("\n🔄 Starting Local Game...")
        
        # Start server first
        if not self.start_server():
            return
        
        # Wait for server to fully initialize
        time.sleep(2)
        
        # Start human player client
        print("\n👤 Starting client for human player...")
        human_client = self.start_client(nickname="Player1")
        
        if not human_client:
            print("❌ Failed to start human client")
            return
        
        # Optionally start bot clients for testing
        if num_bots > 0:
            print(f"\n🤖 Starting {num_bots} bot client(s) for testing...")
            for i in range(num_bots):
                bot_nickname = f"Bot{i+1}"
                self.start_client(nickname=bot_nickname)
                time.sleep(0.5)  # Small delay between bot connections
        
        print(f"\n🎯 Local game ready!")
        print(f"🖥️  Server: localhost:{self.server_instance.port}")
        print(f"🎮 Human player ready")
        if num_bots > 0:
            print(f"🤖 {num_bots} bot(s) connected for testing")
    
    def start_multiple_clients(self, count: int = 3):
        """Start multiple clients for testing purposes"""
        print(f"\n🏭 Starting {count} test clients...")
        
        for i in range(count):
            nickname = f"TestPlayer{i+1}"
            client = self.start_client(nickname=nickname)
            if client:
                print(f"✅ Client {i+1} ({nickname}) connected")
            else:
                print(f"❌ Failed to connect client {i+1}")
            time.sleep(0.5)
    
    def run_tests(self):
        """Run project tests"""
        print("\n🧪 Running Tests...")
        try:
            # Check if pytest is available
            result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ All tests passed!")
                print(result.stdout)
            else:
                print("❌ Some tests failed:")
                print(result.stdout)
                if result.stderr:
                    print("Errors:")
                    print(result.stderr)
        except FileNotFoundError:
            print("❌ pytest not found. Install it with: pip install pytest")
            # Fallback to basic test runner
            print("🔄 Running basic tests...")
            try:
                import tests.test_client as test_client
                import tests.test_game as test_game
                print("✅ Test imports successful")
            except ImportError as e:
                print(f"❌ Test import failed: {e}")
    
    def cleanup(self):
        """Clean up resources before exit"""
        print("\n🧹 Cleaning up...")
        
        # Close client connections
        for client in self.client_instances:
            try:
                if hasattr(client, 'sock'):
                    client.sock.close()
            except:
                pass
        
        # Stop server
        if self.server_instance:
            try:
                if hasattr(self.server_instance, 'server'):
                    self.server_instance.server.close()
            except:
                pass
        
        self.running = False
        print("✅ Cleanup completed")
    
    def run(self):
        """Main application loop"""
        self.display_banner()
        self.running = True
        
        try:
            while self.running:
                choice = self.display_menu()
                
                if choice == '1':
                    # Start Server Only
                    self.start_server()
                    input("\n⏸️  Press Enter to continue...")
                
                elif choice == '2':
                    # Start Client Only
                    host = input(f"\nEnter server host (default: {DEFAULT_HOST}): ").strip() or DEFAULT_HOST
                    port_input = input(f"Enter server port (default: {DEFAULT_PORT}): ").strip()
                    port = int(port_input) if port_input else DEFAULT_PORT
                    
                    client = self.start_client(host, port)
                    if client:
                        input("\n⏸️  Press Enter to continue...")
                
                elif choice == '3':
                    # Start Server & Client (Local Game)
                    num_bots = input("\nNumber of bot players for testing (default: 1): ").strip()
                    num_bots = int(num_bots) if num_bots.isdigit() else 1
                    
                    self.start_local_game(num_bots)
                    input("\n⏸️  Press Enter to continue...")
                
                elif choice == '4':
                    # Start Multiple Clients
                    count = input("\nNumber of test clients (default: 3): ").strip()
                    count = int(count) if count.isdigit() else 3
                    
                    self.start_multiple_clients(count)
                    input("\n⏸️  Press Enter to continue...")
                
                elif choice == '6':
                    # Run Tests
                    self.run_tests()
                    input("\n⏸️  Press Enter to continue...")
                
                elif choice == '7':
                    # Exit
                    print("\n👋 Thanks for playing Racing Arena!")
                    break
                
                else:
                    print("\n❌ Invalid choice. Please enter a number between 1-7.")
                    time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Game interrupted by user")
        
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
        
        finally:
            self.cleanup()


def main():
    """Entry point for the application"""
    parser = argparse.ArgumentParser(description="Racing Arena - Math Racing Game")
    parser.add_argument('--mode', choices=['server', 'client', 'local'], 
                      help='Direct mode: server, client, or local game')
    parser.add_argument('--host', default=DEFAULT_HOST, 
                      help=f'Host address (default: {DEFAULT_HOST})')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                      help=f'Port number (default: {DEFAULT_PORT})')
    parser.add_argument('--bots', type=int, default=1,
                      help='Number of bot players in local mode (default: 1)')
    
    args = parser.parse_args()
    
    app = Main()
    
    try:
        if args.mode == 'server':
            # Direct server mode
            app.start_server(args.host, args.port)
            print("🖥️  Server running. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        
        elif args.mode == 'client':
            # Direct client mode
            app.start_client(args.host, args.port)
            print("🎮 Client running. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        
        elif args.mode == 'local':
            # Direct local game mode
            app.start_local_game(args.bots)
            print("🔄 Local game running. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        
        else:
            # Interactive menu mode
            app.run()
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Application interrupted")
    
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()
        