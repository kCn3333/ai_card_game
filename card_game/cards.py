import random
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Card:
    """A playing card with a suit and value."""
    suit: str
    value: str
    
    @property
    def rank(self) -> int:
        """Get the numeric rank of the card for comparison."""
        values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
                 '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        return values.get(self.value, 0)
    
    def __str__(self) -> str:
        return f"{self.value} of {self.suit}"

class Deck:
    """A standard deck of 52 playing cards."""
    SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    VALUES = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    
    def __init__(self):
        self.cards = [Card(suit, value) for suit in self.SUITS for value in self.VALUES]
        self.shuffle()
    
    def shuffle(self) -> None:
        """Shuffle the deck of cards."""
        random.shuffle(self.cards)
    
    def draw(self) -> Optional[Card]:
        """Draw a card from the top of the deck."""
        return self.cards.pop() if self.cards else None
    
    def is_empty(self) -> bool:
        """Check if the deck is empty."""
        return len(self.cards) == 0
    
    def __len__(self) -> int:
        return len(self.cards)
