from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..cards import Deck
from .state import BlackjackState, Hand
from .rules import hand_value, is_bust, is_blackjack


@dataclass
class GameResult:
    finished: bool
    winner: str | None  # "player", "ai", "push", or None
    player_total: int
    ai_total: int


class BlackjackController:
    """Core Blackjack flow without UI or AI details."""

    def __init__(self) -> None:
        self.started_at = datetime.utcnow()
        self.new_game()

    # --- Core actions ---

    def new_game(self) -> None:
        """Start a fresh Blackjack game with a new deck."""
        deck = Deck()
        player_hand = Hand(owner="player")
        ai_hand = Hand(owner="ai")
        self.state = BlackjackState(
            deck=deck,
            player_hand=player_hand,
            ai_hand=ai_hand,
            current_turn="player",
        )

        self.started_at = datetime.utcnow()
        self._deal_initial_cards()

    def _deal_initial_cards(self) -> None:
        for _ in range(2):
            self.state.player_hand.cards.append(self.state.deck.draw())
            self.state.ai_hand.cards.append(self.state.deck.draw())
        self.state.initial_deal_done = True

        # Check for immediate blackjack outcomes
        p_bj = is_blackjack(self.state.player_hand)
        a_bj = is_blackjack(self.state.ai_hand)
        if p_bj or a_bj:
            if p_bj and a_bj:
                self._finish_game(winner="push")
            elif p_bj:
                self._finish_game(winner="player")
            else:
                self._finish_game(winner="ai")

    def player_hit(self) -> None:
        if self.state.finished or self.state.current_turn != "player":
            return
        self.state.player_hand.cards.append(self.state.deck.draw())
        if is_bust(self.state.player_hand):
            self._finish_game(winner="ai")
        # player can still choose to hit/stand again from UI if not bust

    def player_stand(self) -> None:
        if self.state.finished or self.state.current_turn != "player":
            return
        self.state.current_turn = "ai"

    def ai_play_out(self) -> None:
        """Dealer/AI plays according to standard rules: hit until 17+ then stand."""
        if self.state.finished or self.state.current_turn != "ai":
            return

        while hand_value(self.state.ai_hand) < 17:
            self.state.ai_hand.cards.append(self.state.deck.draw())
            if is_bust(self.state.ai_hand):
                self._finish_game(winner="player")
                return

        # Stand and resolve against player total
        if self.state.finished:
            return
        p = hand_value(self.state.player_hand)
        a = hand_value(self.state.ai_hand)
        if p > a:
            self._finish_game(winner="player")
        elif a > p:
            self._finish_game(winner="ai")
        else:
            self._finish_game(winner="push")

    def ai_stand_and_resolve(self) -> None:
        """AI stands and we resolve the game by comparing totals."""
        if self.state.finished:
            return
        p = hand_value(self.state.player_hand)
        a = hand_value(self.state.ai_hand)
        if p > a:
            self._finish_game(winner="player")
        elif a > p:
            self._finish_game(winner="ai")
        else:
            self._finish_game(winner="push")

    # --- Helpers ---

    def _finish_game(self, winner: str) -> None:
        self.state.finished = True
        self.state.winner = winner  # type: ignore[assignment]

    def get_result(self) -> GameResult | None:
        if not self.state.finished:
            return None
        return GameResult(
            finished=True,
            winner=self.state.winner if isinstance(self.state.winner, str) else None,
            player_total=hand_value(self.state.player_hand),
            ai_total=hand_value(self.state.ai_hand),
        )
