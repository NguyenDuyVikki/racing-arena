"""
Game configuration settings for Racing Arena
"""

# Server settings
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 12345
MAX_PORT_ATTEMPTS = 10
MAX_CLIENTS = 10
MIN_CLIENTS = 2

# Game settings
MIN_TRACK_LENGTH = 4
MAX_TRACK_LENGTH = 25
TIME_LIMIT = 100.0  # seconds per round
MAX_WRONG_STREAK = 3  # disqualification threshold

# Math expression settings
MIN_NUMBER = -10000
MAX_NUMBER = 10000
OPERATORS = ['+', '-', '*', '/', '%']

# Network settings
BUFFER_SIZE = 1024
SELECT_TIMEOUT = 0.1

# Scoring settings
BASE_POINTS = 1
PENALTY_POINTS = -1
