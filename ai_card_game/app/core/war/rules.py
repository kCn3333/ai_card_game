"""War game rules."""

from ..cards import Card

# Card rank values for War (Ace is highest)
RANK_VALUES = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8,
    "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14
}


def card_value(card: Card) -> int:
    """Get the numeric value of a card for comparison."""
    return RANK_VALUES.get(card.rank, 0)


def compare_cards(player_card: Card, ai_card: Card) -> str:
    """
    Compare two cards.
    Returns: "player" if player wins, "ai" if AI wins, "war" if tie.
    """
    player_val = card_value(player_card)
    ai_val = card_value(ai_card)
    
    if player_val > ai_val:
        return "player"
    elif ai_val > player_val:
        return "ai"
    else:
        return "war"
