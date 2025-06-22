#!/usr/bin/env python3
"""
Unit tests for Racing Arena game components
"""
import unittest
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.game import Player, GameState, ExpressionGenerator
from src.utils import process_client_data, create_message, create_data_message
import json


class TestPlayer(unittest.TestCase):
    """Test cases for Player class"""
    
    def setUp(self):
        self.player = Player("test_player")
    
    def test_initialization(self):
        """Test player initialization"""
        self.assertEqual(self.player.nickname, "test_player")
        self.assertEqual(self.player.score, 0)
        self.assertEqual(self.player.position, 1)
        self.assertEqual(self.player.wrong_streak, 0)
    
    def test_add_score(self):
        """Test adding score to player"""
        self.player.add_score(5)
        self.assertEqual(self.player.score, 5)
        self.assertEqual(self.player.position, 6)
    
    def test_penalize(self):
        """Test player penalty"""
        self.player.penalize()
        self.assertEqual(self.player.score, -1)
        self.assertEqual(self.player.wrong_streak, 1)
    
    def test_reset(self):
        """Test player reset"""
        self.player.add_score(10)
        self.player.penalize()
        self.player.reset()
        self.assertEqual(self.player.score, 0)
        self.assertEqual(self.player.position, 1)
        self.assertEqual(self.player.wrong_streak, 0)


class TestGameState(unittest.TestCase):
    """Test cases for GameState class"""
    
    def setUp(self):
        self.game_state = GameState()
    
    def test_initialization(self):
        """Test game state initialization"""
        self.assertFalse(self.game_state.game_started)
        self.assertIsNone(self.game_state.current_expression)
        self.assertIsNone(self.game_state.current_answer)
        self.assertEqual(self.game_state.round_number, 0)
        self.assertTrue(4 <= self.game_state.track_length <= 25)
    
    def test_start_game(self):
        """Test starting a game"""
        self.game_state.start_game()
        self.assertTrue(self.game_state.game_started)
    
    def test_new_round(self):
        """Test starting a new round"""
        self.game_state.new_round()
        self.assertEqual(self.game_state.round_number, 1)
        self.assertIsNotNone(self.game_state.current_expression)
        self.assertIsNotNone(self.game_state.current_answer)
        self.assertIsNotNone(self.game_state.round_start_time)


class TestExpressionGenerator(unittest.TestCase):
    """Test cases for ExpressionGenerator class"""
    
    def test_generate_expression(self):
        """Test expression generation"""
        expr, answer = ExpressionGenerator.generate()
        self.assertIsInstance(expr, str)
        self.assertIsInstance(answer, int)
        
        # Verify the expression can be evaluated
        calculated_answer = eval(expr)
        self.assertEqual(calculated_answer, answer)
    
    def test_multiple_generations(self):
        """Test generating multiple expressions"""
        expressions = set()
        for _ in range(100):
            expr, answer = ExpressionGenerator.generate()
            expressions.add(expr)
            # Verify each expression evaluates correctly
            self.assertEqual(eval(expr), answer)
        
        # Should generate diverse expressions
        self.assertGreater(len(expressions), 50)


class TestUtils(unittest.TestCase):
    """Test cases for utility functions"""
    
    def test_create_message(self):
        """Test message creation"""
        message = create_message("test message")
        self.assertIsInstance(message, bytes)
        
        # Decode and parse
        decoded = message.decode()
        self.assertTrue(decoded.endswith('\n'))
        parsed = json.loads(decoded.strip())
        self.assertEqual(parsed["message"], "test message")
    
    def test_create_data_message(self):
        """Test data message creation"""
        data = {"answer": "42", "player": "test"}
        message = create_data_message(data)
        self.assertIsInstance(message, bytes)
        
        # Decode and parse
        decoded = message.decode()
        self.assertTrue(decoded.endswith('\n'))
        parsed = json.loads(decoded.strip())
        self.assertEqual(parsed["answer"], "42")
        self.assertEqual(parsed["player"], "test")
    
    def test_process_client_data(self):
        """Test client data processing"""
        # Test single complete message
        buffer = ""
        data = '{"message": "hello"}\n'
        new_buffer, messages = process_client_data(buffer, data)
        
        self.assertEqual(new_buffer, "")
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["message"], "hello")
        
        # Test incomplete message
        buffer = ""
        data = '{"message": "partial'
        new_buffer, messages = process_client_data(buffer, data)
        
        self.assertEqual(new_buffer, '{"message": "partial')
        self.assertEqual(len(messages), 0)
        
        # Test multiple messages
        buffer = ""
        data = '{"msg": "first"}\n{"msg": "second"}\n{"msg": "third"}\n'
        new_buffer, messages = process_client_data(buffer, data)
        
        self.assertEqual(new_buffer, "")
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["msg"], "first")
        self.assertEqual(messages[1]["msg"], "second")
        self.assertEqual(messages[2]["msg"], "third")


class TestIntegration(unittest.TestCase):
    """Integration tests for Racing Arena components"""
    
    def test_game_flow(self):
        """Test basic game flow"""
        # Create game state and players
        game_state = GameState()
        player1 = Player("alice")
        player2 = Player("bob")
        
        # Start game
        game_state.start_game()
        self.assertTrue(game_state.game_started)
        
        # Start a round
        game_state.new_round()
        self.assertEqual(game_state.round_number, 1)
        self.assertIsNotNone(game_state.current_expression)
        
        # Simulate correct answer from player1
        game_state.add_response("socket1", str(game_state.current_answer))
        self.assertIn("socket1", game_state.responses)
        
        # Test winner detection
        player1.add_score(game_state.track_length)
        winner = game_state.has_winner({"socket1": player1, "socket2": player2})
        self.assertEqual(winner, player1)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
