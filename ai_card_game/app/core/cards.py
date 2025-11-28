from dataclasses import dataclass
from typing import List
import random


SUITS = ["hearts", "diamonds", "clubs", "spades"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


@dataclass(frozen=True)
class Card:
    suit: str  # e.g. "hearts"
    rank: str  # e.g. "A", "10", "K"

    @property
    def id(self) -> str:
        """Stable id like 'H_A' (H=hearts, D=diamonds, C=clubs, S=spades)."""
        suit_map = {"hearts": "H", "diamonds": "D", "clubs": "C", "spades": "S"}
        return f"{suit_map[self.suit]}_{self.rank}"

    @property
    def svg_filename(self) -> str:
        """Filename we expect in assets/cards, e.g. 'hearts_A.svg'."""
        return f"{self.suit}_{self.rank}.svg"


class Deck:
    def __init__(self) -> None:
        self._cards: List[Card] = [
            Card(suit=s, rank=r) for s in SUITS for r in RANKS
        ]
        self.shuffle()

    def shuffle(self) -> None:
        random.shuffle(self._cards)

    def draw(self) -> Card:
        if not self._cards:
            raise IndexError("No cards left in deck")
        return self._cards.pop()

    def __len__(self) -> int:
        return len(self._cards)
