"""War game controller."""

import random
from .state import WarState
from .rules import compare_cards
from ..cards import Deck


class WarController:
    """Controls the flow of a War game."""
    
    def __init__(self) -> None:
        self.state = WarState()
        self.new_game()
    
    def new_game(self) -> None:
        """Start a new game by shuffling and dealing cards."""
        deck = Deck()
        deck.shuffle()
        
        # Deal all cards evenly
        all_cards = deck.cards
        half = len(all_cards) // 2
        
        self.state = WarState(
            player_pile=all_cards[:half],
            ai_pile=all_cards[half:],
        )
    
    def play_round(self) -> str:
        """
        Play one round (battle).
        Returns the result: "player_wins", "ai_wins", "war", or "game_over".
        """
        state = self.state
        
        # Check if game is over
        if state.finished:
            return "game_over"
        
        if not state.player_pile:
            self._finish_game("ai")
            return "game_over"
        
        if not state.ai_pile:
            self._finish_game("player")
            return "game_over"
        
        # Clear previous battle cards
        state.player_battle_cards = []
        state.ai_battle_cards = []
        
        # Each player plays top card
        player_card = state.player_pile.pop(0)
        ai_card = state.ai_pile.pop(0)
        
        state.player_battle_cards.append(player_card)
        state.ai_battle_cards.append(ai_card)
        
        # Add any war pot cards to the battle
        battle_cards = state.war_pot + [player_card, ai_card]
        state.war_pot = []
        
        # Compare cards
        result = compare_cards(player_card, ai_card)
        
        if result == "player":
            # Player wins - collect all cards
            random.shuffle(battle_cards)
            state.player_pile.extend(battle_cards)
            state.last_result = "player_wins"
            state.in_war = False
        elif result == "ai":
            # AI wins - collect all cards
            random.shuffle(battle_cards)
            state.ai_pile.extend(battle_cards)
            state.last_result = "ai_wins"
            state.in_war = False
        else:
            # War! Cards go to pot
            state.war_pot = battle_cards
            state.in_war = True
            state.last_result = "war"
            
            # Each player adds 3 face-down cards to the pot (if they have them)
            for _ in range(3):
                if state.player_pile:
                    state.war_pot.append(state.player_pile.pop(0))
                if state.ai_pile:
                    state.war_pot.append(state.ai_pile.pop(0))
        
        # Check for game over
        if not state.player_pile and not state.in_war:
            self._finish_game("ai")
        elif not state.ai_pile and not state.in_war:
            self._finish_game("player")
        
        return state.last_result or "game_over"
    
    def _finish_game(self, winner: str) -> None:
        """Mark the game as finished."""
        self.state.finished = True
        self.state.winner = winner
