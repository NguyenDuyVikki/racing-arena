import socket
from config.settings import DEFAULT_HOST, DEFAULT_PORT, MAX_PORT_ATTEMPTS


def is_port_available(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> bool:
    """Check if a port is available for binding"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_sock:
            test_sock.bind((host, port))
            return True
    except OSError:
        return False


def find_available_port(host: str = DEFAULT_HOST, start_port: int = DEFAULT_PORT, 
                       max_attempts: int = MAX_PORT_ATTEMPTS) -> int:
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(host, port):
            return port
    return None
