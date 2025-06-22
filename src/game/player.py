"""
Player model for Racing Arena
"""
from typing import Dict, Any


class Player:    
    
    def __init__(self, nickname: str = None):
        self.nickname = nickname
        self.score = 0
        self.position = 1
        self.wrong_streak = 0
    
    def reset(self):
        """Reset player stats for a new game"""
        self.score = 0
        self.position = 1
        self.wrong_streak = 0
    
    def add_score(self, points: int):
        """Add points to player score"""
        self.score += points
        self.position = max(1, 1 + self.score)
    
    def penalize(self):
        """Apply penalty for wrong answer or timeout"""
        self.score -= 1
        self.wrong_streak += 1
    
    def reset_wrong_streak(self):
        """Reset wrong answer streak"""
        self.wrong_streak = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert player to dictionary representation"""
        return {
            "nickname": self.nickname,
            "score": self.score,
            "position": self.position,
            "wrong_streak": self.wrong_streak
        }
    
    def __str__(self) -> str:
        return f"Player({self.nickname}, score={self.score}, pos={self.position})"
