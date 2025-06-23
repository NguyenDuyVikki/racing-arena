import time
from typing import Dict, List, Tuple, Any
from config.settings import MAX_WRONG_STREAK, BASE_POINTS, PENALTY_POINTS
from .player import Player


class RoundProcessor:
    """Handles processing of game rounds and scoring"""
    
    @staticmethod
    def process_round(game_state, players: Dict, broadcast_callback) -> bool:
        print(f"[RoundProcessor] Processing round for {len(players)} players")
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
                round_results.append(f"{player.nickname}: timeout (5.0s)")
                # Send individual feedback for timeout
                RoundProcessor._send_individual_feedback(sock, player, game_state, False, -1)
                if player.wrong_streak >= MAX_WRONG_STREAK:
                    broadcast_callback(f"Player {player.nickname} disqualified!")
                    disconnected_players.append(sock)

        # Process responses
        for sock, (response_time, answer) in game_state.responses.items():
            if sock not in players:
                continue
                
            player = players[sock]
            try:
                # Ensure robust type conversion and comparison
                answer_stripped = str(answer).strip()
                if not answer_stripped:
                    is_correct = False
                else:
                    user_answer = int(answer_stripped)
                    correct_answer = int(game_state.current_answer)
                    is_correct = user_answer == correct_answer
                    
            except (ValueError, TypeError, AttributeError) as e:
                print(f"[DEBUG] Error converting answer '{answer}' for player {player.nickname}: {e}")
                is_correct = False

            response_delay = response_time - game_state.round_start_time
            if is_correct:
                correct_answers.append((sock, response_delay))
                if response_delay < fastest_time:
                    fastest_time = response_delay
                    fastest = sock
                round_results.append(f"{player.nickname}: {answer} ({response_delay:.1f}s)")
                # Send individual feedback for correct answer (points will be calculated later)
                RoundProcessor._send_individual_feedback(sock, player, game_state, True, 1, response_delay)
            else:
                player.penalize()
                penalties += 1
                round_results.append(f"{player.nickname}: {answer} ({response_delay:.1f}s)")
                # Send individual feedback for wrong answer
                RoundProcessor._send_individual_feedback(sock, player, game_state, False, -1, response_delay)
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
                # Update the feedback with actual points earned for fastest player
                try:
                    from src.utils.messaging import create_message
                    sock.send(create_message(f"Correct! +{points_earned} points"))
                except:
                    pass
            else:
                player.add_score(BASE_POINTS)
            player.reset_wrong_streak()

        # Update positions after all score changes
        RoundProcessor._update_positions(players)
        
        # Send updated positions to all players
        for sock, player in players.items():
            try:
                from src.utils.messaging import create_message
                sock.send(create_message(f"Your position: {player.position}"))
            except:
                pass

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
            print(result)
        
        # Calculate points changes for this round
        points_changes = []
        positions_info = []
        
        for sock, player in players.items():
            # Determine points change for this round
            points_change = 0
            if sock in game_state.responses:
                response_time, answer = game_state.responses[sock]
                try:
                    user_answer = int(answer)
                    is_correct = True
                    is_correct = user_answer == game_state.current_answer
                    if is_correct:
                        # Find if this was the fastest correct answer
                        correct_responses = []
                        for s, (rt, ans) in game_state.responses.items():
                            if s in players:
                                try:
                                    if int(ans) == game_state.current_answer:
                                        correct_responses.append((s, rt))
                                except ValueError:
                                    pass
                        
                        if correct_responses:
                            fastest_sock = min(correct_responses, key=lambda x: x[1])[0]
                            penalties = sum(1 for p in players.values() if p.wrong_streak > 0)
                            if sock == fastest_sock:
                                points_change = BASE_POINTS + penalties
                            else:
                                points_change = BASE_POINTS
                    else:
                        points_change = -1
                except ValueError:
                    points_change = -1
            else:
                # Timeout
                points_change = -1
            
            # Format points change
            if points_change > 0:
                points_changes.append(f"{player.nickname} +{points_change}")
            else:
                points_changes.append(f"{player.nickname} {points_change}")
            
            positions_info.append(f"{player.nickname} → {player.position}")
        
        # Print server-side results
        print("Points:")
        print(" | ".join(points_changes))
        print("Positions:")
        for pos_info in positions_info:
            print(pos_info)
        
        # Broadcast to clients
        broadcast_callback(f"Correct answer: {game_state.current_answer}")
        broadcast_callback("Received:")
        for result in round_results:
            broadcast_callback(result)

        broadcast_callback("Points:")
        broadcast_callback(" | ".join(points_changes))
        
        broadcast_callback("Positions:")
        for pos_info in positions_info:
            broadcast_callback(pos_info)

    @staticmethod
    def _send_individual_feedback(sock, player, game_state, is_correct: bool, points_change: int, response_time: float = None):
        """Send individual feedback to a player"""
        try:
            from src.utils.messaging import create_message
            
            if is_correct:
                if points_change > 1:
                    message = f"Correct! +{points_change} points"
                else:
                    message = f"Correct! +{points_change} point"
            else:
                if points_change < 0:
                    if points_change == -1:
                        message = f"Incorrect! {points_change} point"
                    else:
                        message = f"Incorrect! {points_change} points"
                else:
                    message = "Time's up! -1 point"
            
            sock.send(create_message(message))
            
        except Exception as e:
            # Silent failure for network issues
            pass

    @staticmethod
    def _update_positions(players: Dict):
        """Update player positions based on their scores"""
        # Sort players by score (descending) and then by nickname (ascending) for tie-breaking
        sorted_players = sorted(players.values(), key=lambda p: (-p.score, p.nickname))
        
        # Assign positions
        current_position = 1
        for i, player in enumerate(sorted_players):
            # Handle ties - players with same score get same position
            if i > 0 and player.score == sorted_players[i-1].score:
                player.position = sorted_players[i-1].position
            else:
                player.position = current_position
            current_position = i + 2  # Next different position
