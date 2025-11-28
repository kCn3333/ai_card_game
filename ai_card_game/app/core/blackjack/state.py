from dataclasses import dataclass, field
from typing import List, Literal

from ..cards import Card, Deck


PlayerId = Literal["player", "ai"]


@dataclass
class Hand:
    owner: PlayerId
    cards: List[Card] = field(default_factory=list)


@dataclass
class BlackjackState:
    deck: Deck
    player_hand: Hand
    ai_hand: Hand
    current_turn: PlayerId
    finished: bool = False
    winner: PlayerId | Literal["push", "none"] = "none"
    initial_deal_done: bool = False
