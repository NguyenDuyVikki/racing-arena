"""
Racing Arena - Terminal-Based Multiplayer Math Game

A real-time multiplayer terminal game where players compete by solving math expressions.
"""

from .server import RacingServer
from .client import RacingClient
from .game import Player, GameState, ExpressionGenerator, RoundProcessor
from .utils import is_port_available, find_available_port, process_client_data, create_message, create_data_message

__version__ = "1.0.0"
__author__ = "Racing Arena Team"

__all__ = [
    'RacingServer',
    'RacingClient',
    'Player',
    'GameState',
    'ExpressionGenerator', 
    'RoundProcessor',
    'is_port_available',
    'find_available_port',
    'process_client_data',
    'create_message',
    'create_data_message'
]
