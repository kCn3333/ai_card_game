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
        """Filename we expect in assets/cards.

        For numbered cards this is '<suit>_<rank>.svg', e.g. 'clubs_2.svg'.
        For A and face cards we map to full names: A -> ace, J -> jack,
        Q -> queen, K -> king, e.g. 'spades_ace.svg', 'diamonds_king.svg',
        'hearts_queen.svg'.
        """
        face_map = {"A": "ace", "J": "jack", "Q": "queen", "K": "king"}
        rank_part = face_map.get(self.rank, self.rank)
        return f"{self.suit}_{rank_part}.svg"


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
