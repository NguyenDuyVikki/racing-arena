"""
Round processing logic for Racing Arena
"""
import time
from typing import Dict, List, Tuple, Any
from config.settings import MAX_WRONG_STREAK, BASE_POINTS, PENALTY_POINTS
from .player import Player


class RoundProcessor:
    """Handles processing of game rounds and scoring"""
    
    @staticmethod
    def process_round(game_state, players: Dict, broadcast_callback) -> bool:
        """
        Process a round and return True if game should continue, False if game ended
        """
        penalties = 0
        correct_answers = []
        fastest = None
        fastest_time = float('inf')
        round_results = []
        disconnected_players = []

        # Process all players who didn't respond (timeout)
        for sock, player in players.items():
            if sock not in game_state.responses:
                player.penalize()
                penalties += 1
                round_results.append(f"{player.nickname}: timeout (-1 point)")
                if player.wrong_streak >= MAX_WRONG_STREAK:
                    broadcast_callback(f"Player {player.nickname} disqualified!")
                    disconnected_players.append(sock)

        # Process responses
        for sock, (response_time, answer) in game_state.responses.items():
            if sock not in players:
                continue
                
            player = players[sock]
            try:
                user_answer = int(answer)
                is_correct = user_answer == game_state.current_answer
            except ValueError:
                is_correct = False

            response_delay = response_time - game_state.round_start_time
            if is_correct:
                correct_answers.append((sock, response_delay))
                if response_delay < fastest_time:
                    fastest_time = response_delay
                    fastest = sock
                round_results.append(f"{player.nickname}: {answer} ({response_delay:.1f}s)")
            else:
                player.penalize()
                penalties += 1
                round_results.append(f"{player.nickname}: {answer} (-1 point)")
                if player.wrong_streak >= MAX_WRONG_STREAK:
                    broadcast_callback(f"Player {player.nickname} disqualified!")
                    disconnected_players.append(sock)

        # Award points to correct answers
        for sock, _ in correct_answers:
            if sock not in players:
                continue
                
            player = players[sock]
            if sock == fastest:
                points_earned = BASE_POINTS + penalties  # Base point + penalty points
                player.add_score(points_earned)
                round_results.append(f"  → {player.nickname} fastest: +{points_earned} points")
            else:
                player.add_score(BASE_POINTS)
            player.reset_wrong_streak()

        # Check for winner
        winner = game_state.has_winner(players)
        if winner:
            broadcast_callback(f"Race ended! Winner: {winner.nickname}")
            return False

        # Broadcast results
        RoundProcessor._broadcast_results(game_state, round_results, players, broadcast_callback)
        
        return True

    @staticmethod
    def _broadcast_results(game_state, round_results: List[str], players: Dict, broadcast_callback):
        """Broadcast round results to all players"""
        print("Received:")
        for result in round_results:
            print(f"  {result}")
        
        # Show points summary
        points_summary = "Points:"
        for player in players.values():
            points_summary += f"\n  {player.nickname} +{max(0, player.score)} | position {player.position}"
        print(points_summary)
        
        broadcast_callback(f"Correct answer: {game_state.current_answer}")
        broadcast_callback("Received:")
        for result in round_results:
            broadcast_callback(result)

        # Show current standings
        standings = "\nPositions:"
        for player in players.values():
            standings += f"\n{player.nickname} → {player.position}"
        broadcast_callback(standings)
