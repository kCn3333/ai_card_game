"""Texas Hold'em Poker hand evaluation rules."""

from collections import Counter
from ..cards import Card

# Card rank values
RANK_VALUES = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8,
    "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14
}

# Hand rankings (higher is better)
HAND_RANKS = {
    "high_card": 1,
    "pair": 2,
    "two_pair": 3,
    "three_of_a_kind": 4,
    "straight": 5,
    "flush": 6,
    "full_house": 7,
    "four_of_a_kind": 8,
    "straight_flush": 9,
    "royal_flush": 10,
}


def card_value(card: Card) -> int:
    """Get numeric value of a card."""
    return RANK_VALUES.get(card.rank, 0)


def evaluate_hand(hole_cards: list[Card], community: list[Card]) -> tuple[int, list[int], str]:
    """
    Evaluate the best 5-card hand from hole cards + community cards.
    Returns: (hand_rank, tiebreaker_values, hand_name)
    """
    all_cards = hole_cards + community
    if len(all_cards) < 5:
        # Not enough cards yet
        values = sorted([card_value(c) for c in all_cards], reverse=True)
        return (1, values, "High Card")
    
    # Get all 5-card combinations and find the best
    from itertools import combinations
    
    best_rank = 0
    best_tiebreaker = []
    best_name = "High Card"
    
    for combo in combinations(all_cards, 5):
        rank, tiebreaker, name = _evaluate_five_cards(list(combo))
        if rank > best_rank or (rank == best_rank and tiebreaker > best_tiebreaker):
            best_rank = rank
            best_tiebreaker = tiebreaker
            best_name = name
    
    return (best_rank, best_tiebreaker, best_name)


def _evaluate_five_cards(cards: list[Card]) -> tuple[int, list[int], str]:
    """Evaluate exactly 5 cards."""
    values = sorted([card_value(c) for c in cards], reverse=True)
    suits = [c.suit for c in cards]
    
    is_flush = len(set(suits)) == 1
    is_straight = _is_straight(values)
    
    # Check for ace-low straight (A-2-3-4-5)
    if values == [14, 5, 4, 3, 2]:
        is_straight = True
        values = [5, 4, 3, 2, 1]  # Ace counts as 1
    
    value_counts = Counter(values)
    counts = sorted(value_counts.values(), reverse=True)
    
    # Royal Flush
    if is_flush and is_straight and values[0] == 14 and values[4] == 10:
        return (10, values, "Royal Flush")
    
    # Straight Flush
    if is_flush and is_straight:
        return (9, values, "Straight Flush")
    
    # Four of a Kind
    if counts == [4, 1]:
        quad = [v for v, c in value_counts.items() if c == 4][0]
        kicker = [v for v, c in value_counts.items() if c == 1][0]
        return (8, [quad, kicker], "Four of a Kind")
    
    # Full House
    if counts == [3, 2]:
        trips = [v for v, c in value_counts.items() if c == 3][0]
        pair = [v for v, c in value_counts.items() if c == 2][0]
        return (7, [trips, pair], "Full House")
    
    # Flush
    if is_flush:
        return (6, values, "Flush")
    
    # Straight
    if is_straight:
        return (5, values, "Straight")
    
    # Three of a Kind
    if counts == [3, 1, 1]:
        trips = [v for v, c in value_counts.items() if c == 3][0]
        kickers = sorted([v for v, c in value_counts.items() if c == 1], reverse=True)
        return (4, [trips] + kickers, "Three of a Kind")
    
    # Two Pair
    if counts == [2, 2, 1]:
        pairs = sorted([v for v, c in value_counts.items() if c == 2], reverse=True)
        kicker = [v for v, c in value_counts.items() if c == 1][0]
        return (3, pairs + [kicker], "Two Pair")
    
    # One Pair
    if counts == [2, 1, 1, 1]:
        pair = [v for v, c in value_counts.items() if c == 2][0]
        kickers = sorted([v for v, c in value_counts.items() if c == 1], reverse=True)
        return (2, [pair] + kickers, "Pair")
    
    # High Card
    return (1, values, "High Card")


def _is_straight(values: list[int]) -> bool:
    """Check if sorted values form a straight."""
    for i in range(len(values) - 1):
        if values[i] - values[i + 1] != 1:
            return False
    return True


def compare_hands(
    player_hole: list[Card], 
    ai_hole: list[Card], 
    community: list[Card]
) -> tuple[str, str, str]:
    """
    Compare player and AI hands.
    Returns: (winner, player_hand_name, ai_hand_name)
    winner is "player", "ai", or "tie"
    """
    p_rank, p_tie, p_name = evaluate_hand(player_hole, community)
    a_rank, a_tie, a_name = evaluate_hand(ai_hole, community)
    
    if p_rank > a_rank:
        return ("player", p_name, a_name)
    elif a_rank > p_rank:
        return ("ai", p_name, a_name)
    elif p_tie > a_tie:
        return ("player", p_name, a_name)
    elif a_tie > p_tie:
        return ("ai", p_name, a_name)
    else:
        return ("tie", p_name, a_name)
