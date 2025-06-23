import random
import time
from typing import Dict, List, Tuple
from config.settings import MIN_TRACK_LENGTH, MAX_TRACK_LENGTH, TIME_LIMIT, MAX_WRONG_STREAK, BASE_POINTS, PENALTY_POINTS
from .player import Player
from .expressions import ExpressionGenerator


class GameState:
    
    def __init__(self):
        self.track_length = random.randint(MIN_TRACK_LENGTH, MAX_TRACK_LENGTH)
        self.game_started = False
        self.current_expression = None
        self.current_answer = None
        self.round_start_time = None
        self.time_limit = TIME_LIMIT
        self.responses = {}  # socket: (time, answer)
        self.round_number = 0
        self.expression_generator = ExpressionGenerator()
    
    def reset_game(self):
        """Reset game state for a new race"""
        self.track_length = random.randint(MIN_TRACK_LENGTH, MAX_TRACK_LENGTH)
        self.game_started = False
        self.current_expression = None
        self.current_answer = None
        self.round_start_time = None
        self.responses.clear()
        self.round_number = 0
    
    def start_game(self):
        """Start a new game"""
        self.game_started = True
        self.round_number = 0
        print(f"[Server] Race starting with track length: {self.track_length}")
    
    def new_round(self):
        """Start a new round"""
        self.responses.clear()
        self.current_expression, self.current_answer = self.expression_generator.generate()
        self.round_start_time = time.time() + 5
        self.round_number += 1
        print(f"[Round {self.round_number}]")
        print(f"Sent expression: {self.current_expression}")
    
    def is_round_timeout(self) -> bool:
        """Check if current round has timed out"""
        if not self.round_start_time:
            return False
        return time.time() - self.round_start_time >= self.time_limit
    
    def add_response(self, client_socket, answer: str):
        self.responses[client_socket] = (time.time(), answer)
    
    def has_winner(self, players: Dict) -> Player:
        """Check if any player has won the race"""
        for player in players.values():
            if player.position >= self.track_length:
                return player
        return None
