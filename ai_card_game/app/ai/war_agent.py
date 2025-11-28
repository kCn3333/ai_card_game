"""War game AI agent for trash talk and commentary."""

from __future__ import annotations

import json
from ..core.war.state import WarState
from ..core.war.rules import card_value
from .client import AIClient


class WarAgent:
    """LLM-based War agent that comments on the game."""

    def __init__(self, client: AIClient | None = None) -> None:
        self.client = client or AIClient()

    def get_comment(self, state: WarState, event: str) -> str:
        """
        Get AI comment based on game event.
        event: "player_wins", "ai_wins", "war", "game_start", "game_over"
        """
        system_prompt = (
            "You are an AGGRESSIVE and COCKY card game AI playing War. "
            "You love to trash talk and taunt the player. "
            "You're confident, competitive, and love winning. "
            "Comment on what just happened in the game with attitude! "
            "Keep responses SHORT (1 sentence max). Be aggressive and cocky! "
            "Use emojis occasionally."
        )

        # Build context
        context = {
            "event": event,
            "your_cards": state.ai_card_count,
            "player_cards": state.player_card_count,
            "in_war": state.in_war,
            "game_over": state.finished,
            "winner": state.winner,
        }
        
        if state.player_battle_cards:
            context["player_played"] = f"{state.player_battle_cards[-1].rank}"
        if state.ai_battle_cards:
            context["you_played"] = f"{state.ai_battle_cards[-1].rank}"

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Game state: {json.dumps(context)}. "
                    f"React to this with trash talk!"
                ),
            },
        ]

        try:
            resp = self.client.chat(messages)
            return resp.content.strip()
        except Exception:
            return self._fallback_comment(event, state)

    def _fallback_comment(self, event: str, state: WarState) -> str:
        """Fallback comments when AI is unavailable."""
        if event == "game_start":
            return "Let's go! I'm gonna crush you! 💪"
        elif event == "player_wins":
            return "Lucky shot... won't happen again! 😤"
        elif event == "ai_wins":
            return "Ha! Too easy! Get rekt! 😎"
        elif event == "war":
            return "WAR! This is where I destroy you! ⚔️"
        elif event == "game_over":
            if state.winner == "ai":
                return "VICTORY! I told you I'd win! 🏆"
            else:
                return "Whatever... I let you win! 😒"
        return "Bring it on! 🎴"

    def chat_response(self, state: WarState, player_message: str) -> str:
        """Respond to player chat about the current game."""
        system_prompt = (
            "You are an AGGRESSIVE and COCKY card game AI playing War. "
            "You love to trash talk. The player is chatting with you. "
            "ONLY talk about the War card game. Keep responses short (1-2 sentences). "
            "Be aggressive and cocky!"
        )

        context = {
            "your_cards": state.ai_card_count,
            "player_cards": state.player_card_count,
            "game_over": state.finished,
            "winner": state.winner,
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Game state: {json.dumps(context)}. "
                    f"Player says: \"{player_message}\". "
                    "Respond with trash talk!"
                ),
            },
        ]

        try:
            resp = self.client.chat(messages)
            return resp.content.strip()
        except Exception:
            return "Less talking, more losing! 😏"
