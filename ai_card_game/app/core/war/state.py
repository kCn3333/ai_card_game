"""War game state definitions."""

from dataclasses import dataclass, field
from typing import Optional
from ..cards import Card, Deck


@dataclass
class WarState:
    """Represents the current state of a War game."""
    
    player_pile: list[Card] = field(default_factory=list)  # Player's card pile
    ai_pile: list[Card] = field(default_factory=list)      # AI's card pile
    
    # Cards currently in play (for the current battle)
    player_battle_cards: list[Card] = field(default_factory=list)
    ai_battle_cards: list[Card] = field(default_factory=list)
    
    # War pot (cards at stake during a war)
    war_pot: list[Card] = field(default_factory=list)
    
    # Game state
    in_war: bool = False  # True if currently in a "war" situation
    finished: bool = False
    winner: Optional[str] = None  # "player", "ai", or None
    
    # Last battle result for display
    last_result: Optional[str] = None  # "player_wins", "ai_wins", "war"
    
    @property
    def player_card_count(self) -> int:
        return len(self.player_pile)
    
    @property
    def ai_card_count(self) -> int:
        return len(self.ai_pile)
