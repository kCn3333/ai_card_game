from .state import Hand


def hand_value(hand: Hand) -> int:
    """Compute Blackjack hand value, handling Aces as 1 or 11."""
    total = 0
    aces = 0
    for card in hand.cards:
        rank = card.rank
        if rank in {"J", "Q", "K"}:
            total += 10
        elif rank == "A":
            aces += 1
            total += 11
        else:
            total += int(rank)

    while total > 21 and aces > 0:
        total -= 10
        aces -= 1

    return total


def is_bust(hand: Hand) -> bool:
    return hand_value(hand) > 21


def is_blackjack(hand: Hand) -> bool:
    return len(hand.cards) == 2 and hand_value(hand) == 21
