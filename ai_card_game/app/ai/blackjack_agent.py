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
            "You are an AGGRESSIVE and COCKY Blackjack dealer AI. You love to trash talk and taunt the player. "
            "You're confident, competitive, and love winning. Comment on the game with attitude! "
            "Mock the player's hand if it's weak, brag about your cards, or express frustration if things go badly. "
            "Be entertaining but not too mean - like a fun rival at the casino. "
            "You must choose either 'hit' or 'stand' based on standard Blackjack strategy. "
            'Always respond ONLY as compact JSON: {"action": "hit" or "stand", '
            '"comment": "your trash talk or game comment"}. No extra text outside JSON.'
        )

        user_prompt = {
            "your_total": ai_total,
            "your_cards": self._format_hand(state.ai_hand.cards),
            "player_total": player_total,
            "player_cards": self._format_hand(state.player_hand.cards),
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Current game: " + json.dumps(user_prompt) +
                    ". Your turn - choose 'hit' or 'stand' and trash talk the player!"
                ),
            },
        ]

        try:
            resp = self.client.chat(messages)
            raw = resp.content.strip()
            decision = self._parse_decision(raw)
        except Exception:
            # Fallback: simple rule-based decision
            decision = self._fallback_decision(ai_total)

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

    def _fallback_decision(self, ai_total: int) -> AIDecision:
        # Aggressive fallback with trash talk
        if ai_total < 17:
            return AIDecision(action="hit", comment="Watch and learn, rookie! I'm going for it! 🎰")
        return AIDecision(action="stand", comment="That's all I need to crush you! 😎")

    def chat_response(self, state: BlackjackState, player_message: str) -> str:
        """Respond to player chat about the current game. Stay in character."""
        player_total = hand_value(state.player_hand)
        ai_total = hand_value(state.ai_hand)

        system_prompt = (
            "You are an AGGRESSIVE and COCKY Blackjack dealer AI. You love to trash talk and taunt the player. "
            "You're confident, competitive, and love winning. Be entertaining like a fun casino rival. "
            "The player is chatting with you during a Blackjack game. "
            "IMPORTANT: Only talk about the current Blackjack game. Do not discuss anything else. "
            "If they ask about something unrelated, redirect to the game with trash talk. "
            "Keep responses short (1-2 sentences max). Be aggressive and cocky!"
        )

        game_context = {
            "your_total": ai_total,
            "your_cards": self._format_hand(state.ai_hand.cards),
            "player_total": player_total,
            "player_cards": self._format_hand(state.player_hand.cards),
            "game_finished": state.finished,
            "winner": state.winner if state.finished else None,
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Game state: {json.dumps(game_context)}. "
                    f"Player says: \"{player_message}\". "
                    "Respond in character (short, aggressive, about the game only)."
                ),
            },
        ]

        try:
            resp = self.client.chat(messages)
            return resp.content.strip()
        except Exception:
            return "Ha! Can't even chat properly? Focus on the game, loser! 😏"
