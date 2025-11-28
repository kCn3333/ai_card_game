"""Texas Hold'em Poker AI agent for trash talk and commentary."""

from __future__ import annotations
import json

from ..core.poker.state import PokerState
from ..core.poker.rules import evaluate_hand
from .client import AIClient


class PokerAgent:
    """LLM-based Poker agent that comments on the game."""

    def __init__(self, client: AIClient | None = None) -> None:
        self.client = client or AIClient()

    def _format_cards(self, cards: list) -> str:
        """Format cards for display."""
        return ", ".join(f"{c.rank} of {c.suit}" for c in cards)

    def get_comment(self, state: PokerState, event: str) -> str:
        """
        Get AI comment based on game event using LLM.
        """
        model_name = self.client.get_model_name()
        system_prompt = (
            f"You are an AGGRESSIVE and COCKY Poker player AI named '{model_name}'. "
            "You love to trash talk and taunt the player. "
            "You're confident, competitive, and love winning big pots. "
            "Keep responses SHORT (1 sentence max). Be aggressive and cocky! Use emojis."
        )

        # Build context
        context = {
            "event": event,
            "phase": state.phase,
            "pot": state.pot,
            "your_chips": state.ai_chips,
            "player_chips": state.player_chips,
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Game event: {event}. Context: {json.dumps(context)}. "
                    "Give a short trash talk comment about this moment."
                ),
            },
        ]

        resp = self.client.chat(messages)
        return resp.content.strip()

    def decide_action(self, state: PokerState, call_amount: int) -> dict:
        """
        LLM decides what action to take: fold, check, call, or raise.
        Returns: {"action": "fold|check|call|raise", "raise_amount": int, "comment": str}
        """
        # Evaluate AI's hand
        ai_hand_name = "unknown"
        if state.community_cards:
            _, _, ai_hand_name = evaluate_hand(state.ai_hand, state.community_cards)

        model_name = self.client.get_model_name()
        system_prompt = (
            f"You are an expert Poker player AI named '{model_name}'. You must decide your action. "
            "Analyze your hand strength, the pot odds, and make a strategic decision. "
            "You can bluff sometimes but play smart. Be aggressive when you have good cards. "
            'Respond ONLY as JSON: {"action": "fold" or "check" or "call" or "raise", '
            '"raise_amount": number (only if raising, minimum 20), '
            '"comment": "your trash talk"}. No extra text.'
        )

        context = {
            "your_hole_cards": self._format_cards(state.ai_hand),
            "your_hand_strength": ai_hand_name,
            "community_cards": self._format_cards(state.community_cards) if state.community_cards else "none yet",
            "phase": state.phase,
            "pot": state.pot,
            "your_chips": state.ai_chips,
            "player_chips": state.player_chips,
            "amount_to_call": call_amount,
            "can_check": call_amount == 0,
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Game state: {json.dumps(context)}. "
                    "Decide your action and trash talk!"
                ),
            },
        ]

        resp = self.client.chat(messages)
        raw = resp.content.strip()
        return self._parse_action(raw, call_amount, state)

    def _parse_action(self, raw: str, call_amount: int, state: PokerState) -> dict:
        """Parse LLM response into action dict."""
        try:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            data = json.loads(raw[start:end])
        except Exception:
            # If parsing fails, make a simple decision based on call amount
            if call_amount == 0:
                return {"action": "check", "raise_amount": 0, "comment": "Let's see what happens..."}
            return {"action": "call", "raise_amount": 0, "comment": "I'll see that bet."}

        action = str(data.get("action", "call")).lower()
        if action not in {"fold", "check", "call", "raise"}:
            action = "call" if call_amount > 0 else "check"
        
        # Validate action
        if action == "check" and call_amount > 0:
            action = "call"  # Can't check if there's a bet
        
        raise_amount = int(data.get("raise_amount", 40))
        if raise_amount < 20:
            raise_amount = 20
        
        comment = str(data.get("comment", "Let's play!"))
        
        return {"action": action, "raise_amount": raise_amount, "comment": comment}

    def chat_response(self, state: PokerState, player_message: str) -> str:
        """Respond to player chat about the current game using LLM."""
        model_name = self.client.get_model_name()
        system_prompt = (
            f"You are an AGGRESSIVE and COCKY Poker player AI named '{model_name}'. "
            "You love to trash talk and taunt the player. "
            "You're confident, competitive, and love winning. "
            "IMPORTANT: Only talk about the current Poker game. Do not discuss anything else. "
            "If they ask about something unrelated, redirect to the game with trash talk. "
            "Keep responses short (1-2 sentences max). Be aggressive and cocky!"
        )

        # Evaluate hands if we have community cards
        player_hand_name = "unknown"
        if state.community_cards:
            _, _, player_hand_name = evaluate_hand(state.player_hand, state.community_cards)

        context = {
            "phase": state.phase,
            "pot": state.pot,
            "your_chips": state.ai_chips,
            "player_chips": state.player_chips,
            "community_cards": self._format_cards(state.community_cards) if state.community_cards else "none yet",
            "game_finished": state.finished,
            "winner": state.winner if state.finished else None,
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Game state: {json.dumps(context)}. "
                    f"Player says: \"{player_message}\". "
                    "Respond in character (short, aggressive, about the game only)."
                ),
            },
        ]

        resp = self.client.chat(messages)
        return resp.content.strip()
