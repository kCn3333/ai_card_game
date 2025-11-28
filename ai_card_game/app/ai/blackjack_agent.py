from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Tuple

from ..core.blackjack.state import BlackjackState
from ..core.blackjack.rules import hand_value
from ..core.cards import Card
from .client import AIClient


@dataclass
class AIDecision:
    action: str  # "hit" or "stand"
    comment: str


class BlackjackAgent:
    """LLM-based Blackjack agent that chooses hit/stand and comments."""

    def __init__(self, client: AIClient | None = None) -> None:
        self.client = client or AIClient()

    def _format_hand(self, cards: list[Card]) -> str:
        return ", ".join(f"{c.rank} of {c.suit}" for c in cards)

    def decide(self, state: BlackjackState) -> AIDecision:
        """Ask the model to choose between hit/stand based on current state."""
        player_total = hand_value(state.player_hand)
        ai_total = hand_value(state.ai_hand)

        system_prompt = (
            "You are playing Blackjack as the AI opponent. "
            "You must choose either 'hit' or 'stand'. "
            "Always respond ONLY as compact JSON: {\\"action\\": \\\"hit|stand\\\", "
            "\\"comment\\": \\\"short explanation\\\"}. Do not add extra text."
        )

        user_prompt = {
            "player_total": player_total,
            "player_cards": self._format_hand(state.player_hand.cards),
            "ai_total": ai_total,
            "ai_cards": self._format_hand(state.ai_hand.cards),
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Game state: " + json.dumps(user_prompt) +
                    ". Legal actions: ['hit', 'stand']. "
                    "Choose the best action and explain briefly."
                ),
            },
        ]

        try:
            resp = self.client.chat(messages)
            raw = resp.content.strip()
            decision = self._parse_decision(raw)
        except Exception:
            # Fallback: simple rule-based decision
            decision = self._fallback_decision(player_total)

        return decision

    def _parse_decision(self, raw: str) -> AIDecision:
        # Try to locate JSON in the response
        try:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            raw_json = raw[start:end]
            data = json.loads(raw_json)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Failed to parse AI JSON: {exc}; raw={raw!r}") from exc

        action = str(data.get("action", "stand")).strip().lower()
        if action not in {"hit", "stand"}:
            action = "stand"
        comment = str(data.get("comment", "")).strip() or f"I choose to {action}."
        return AIDecision(action=action, comment=comment)

    def _fallback_decision(self, player_total: int) -> AIDecision:
        # Very simple heuristic fallback: hit below 15, else stand
        if player_total < 15:
            return AIDecision(action="hit", comment="I'll take another card.")
        return AIDecision(action="stand", comment="I'll stand here.")
