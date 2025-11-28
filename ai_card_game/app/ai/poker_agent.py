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
        system_prompt = (
            "You are an AGGRESSIVE and COCKY Poker player AI named 'Ace'. "
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

        try:
            resp = self.client.chat(messages)
            return resp.content.strip()
        except Exception:
            return self._fallback_comment(event, state)

    def _fallback_comment(self, event: str, state: PokerState) -> str:
        """Fallback comments when AI is unavailable."""
        if event == "game_start":
            return "New hand! Let's see what you've got! 🃏"
        elif event == "player_fold":
            return "Ha! Couldn't handle the heat? Smart move, coward! 😏"
        elif event == "ai_fold":
            return "I'll let you have this one... for now! 😤"
        elif event == "player_raise":
            return "Ooh, feeling brave? Let's dance! 💰"
        elif event == "ai_raise":
            return "Think you can handle this? I'm raising! 🔥"
        elif event == "player_call":
            return "Just calling? Playing it safe, I see... 🤔"
        elif event == "ai_call":
            return "I'll see that bet. Show me what you've got! 👀"
        elif event == "flop":
            return "The flop is out! Things are getting interesting! 🎰"
        elif event == "turn":
            return "Turn card! The pressure is on! 😈"
        elif event == "river":
            return "River card! This is it! 🌊"
        elif event == "showdown":
            return "Showdown time! Let's see those cards! 🃏"
        elif event == "win":
            return "BOOM! I win! Better luck next time, loser! 🏆"
        elif event == "lose":
            return "Lucky hand... won't happen again! 😒"
        elif event == "check":
            return "Checking? Scared of your own cards? 😂"
        return "Let's play! 🎴"

    def chat_response(self, state: PokerState, player_message: str) -> str:
        """Respond to player chat about the current game using LLM."""
        system_prompt = (
            "You are an AGGRESSIVE and COCKY Poker player AI named 'Ace'. "
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

        try:
            resp = self.client.chat(messages)
            return resp.content.strip()
        except Exception:
            return "Less talking, more betting! Show me the money! 💰"
