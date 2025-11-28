from typing import List, Optional
from .cards import Card

class AIPlayer:
    """AI player that makes decisions in the card game."""
    
    def __init__(self, name: str = "Computer"):
        self.name = name
        self.hand: List[Card] = []
    
    def add_card(self, card: Card) -> None:
        """Add a card to the AI's hand."""
        self.hand.append(card)
    
    def play_card(self) -> Card:
        """
        AI logic to choose a card to play.
        In this simple implementation, the AI plays a random card.
        """
        if not self.hand:
            raise ValueError("No cards left to play")
        
        # Simple strategy: play a random card
        import random
        card_index = random.randint(0, len(self.hand) - 1)
        return self.hand.pop(card_index)
    
    def has_cards(self) -> bool:
        """Check if the AI has any cards left."""
        return len(self.hand) > 0
    
    def __str__(self) -> str:
        return f"{self.name} ({len(self.hand)} cards)"
