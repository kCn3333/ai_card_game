"""Texas Hold'em Poker game state definitions."""

from dataclasses import dataclass, field
from typing import Optional
from ..cards import Card


@dataclass
class PokerState:
    """Represents the current state of a Texas Hold'em game."""
    
    # Hole cards (2 cards each)
    player_hand: list[Card] = field(default_factory=list)
    ai_hand: list[Card] = field(default_factory=list)
    
    # Community cards (up to 5)
    community_cards: list[Card] = field(default_factory=list)
    
    # Chips/betting
    player_chips: int = 1000
    ai_chips: int = 1000
    pot: int = 0
    current_bet: int = 0
    player_bet: int = 0
    ai_bet: int = 0
    
    # Blinds
    small_blind: int = 10
    big_blind: int = 20
    dealer_is_player: bool = True  # Who has the button
    
    # Game phase: "preflop", "flop", "turn", "river", "showdown"
    phase: str = "preflop"
    
    # Whose turn: "player" or "ai"
    turn: str = "player"
    
    # Game state
    finished: bool = False
    winner: Optional[str] = None  # "player", "ai", or "tie"
    winning_hand: Optional[str] = None  # Description of winning hand
    
    # Fold tracking
    player_folded: bool = False
    ai_folded: bool = False
    
    # Round state
    player_acted: bool = False
    ai_acted: bool = False
