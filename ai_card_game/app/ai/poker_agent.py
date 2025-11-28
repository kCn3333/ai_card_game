"""Texas Hold'em Poker AI agent for trash talk and commentary."""

from __future__ import annotations

from ..core.poker.state import PokerState
from .client import AIClient


class PokerAgent:
    """LLM-based Poker agent that comments on the game."""

    def __init__(self, client: AIClient | None = None) -> None:
        self.client = client or AIClient()

    def get_comment(self, state: PokerState, event: str) -> str:
        """
        Get AI comment based on game event.
        event: "game_start", "player_fold", "ai_fold", "player_raise", "ai_raise",
               "player_call", "ai_call", "flop", "turn", "river", "showdown", "win", "lose"
        """
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
        """Respond to player chat about the current game."""
        return "Less talking, more betting! Show me the money! 💰"
