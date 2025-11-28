"""Texas Hold'em Poker UI view."""

from pathlib import Path
from typing import Callable, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSizePolicy, QFrame, QSpinBox
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtGui import QColor, QPainter, QBrush, QRadialGradient
from PySide6.QtCore import Qt

from ..core.poker.controller import PokerController
from ..core.cards import Card
from ..ai.poker_agent import PokerAgent
from ..db.database import save_game_result


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
CARDS_DIR = ASSETS_DIR / "cards"
BACKS_DIR = ASSETS_DIR / "backs"

# Button styles
BUTTON_STYLE = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #2e8b57, stop:0.5 #228b22, stop:1 #1a6b1a);
        color: #ffffff;
        border: 2px solid #145214;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: bold;
        min-width: 80px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #3cb371, stop:0.5 #2e8b57, stop:1 #228b22);
    }
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #1a6b1a, stop:0.5 #145214, stop:1 #0d3d0d);
    }
    QPushButton:disabled {
        background: #4a4a4a;
        color: #888888;
        border-color: #333333;
    }
"""

FOLD_BUTTON_STYLE = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #dc3545, stop:0.5 #c82333, stop:1 #a71d2a);
        color: #ffffff;
        border: 2px solid #721c24;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: bold;
        min-width: 80px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #e4606d, stop:0.5 #dc3545, stop:1 #c82333);
    }
"""

LABEL_STYLE = """
    QLabel {
        color: #f0e68c;
        font-size: 16px;
        font-weight: bold;
        padding: 4px;
    }
"""

CHIPS_STYLE = """
    QLabel {
        color: #ffd700;
        font-size: 18px;
        font-weight: bold;
        padding: 8px;
        background: rgba(0, 0, 0, 0.4);
        border-radius: 6px;
    }
"""

STATUS_STYLE = """
    QLabel {
        color: #ffffff;
        font-size: 20px;
        font-weight: bold;
        padding: 10px;
        background: rgba(0, 0, 0, 0.4);
        border-radius: 8px;
    }
"""


class CardWidget(QSvgWidget):
    """Widget to display a single card."""
    
    def __init__(self, card: Card | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(80, 112)
        if card:
            svg_path = CARDS_DIR / card.svg_filename
            self.load(str(svg_path))


class PokerView(QWidget):
    """Texas Hold'em Poker view."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = PokerController()
        self.agent = PokerAgent()
        self._logger: Optional[Callable[[str], None]] = None
        self._chat_sink: Optional[Callable[[str, str], None]] = None
        self._card_back: str = "back.svg"
        self._table_color: str = "#0d5c2e"
        self._player_name: str = "Player"
        self._player_color: str = "#2e8b57"

        self._init_ui()
        self._refresh()

    def set_logger(self, logger: Callable[[str], None]) -> None:
        self._logger = logger

    def set_chat_sink(self, sink: Callable[[str, str], None]) -> None:
        self._chat_sink = sink
        if self._chat_sink:
            self._chat_sink("AI", "Welcome to Texas Hold'em! Let's play! 🃏")
            # If AI acts first, trigger AI turn
            if self.controller.state.turn == "ai":
                self._ai_turn()

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger(message)

    def _chat(self, sender: str, message: str) -> None:
        if self._chat_sink:
            self._chat_sink(sender, message)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # === AI AREA (top) ===
        ai_section = QVBoxLayout()
        ai_section.setAlignment(Qt.AlignCenter)

        # AI info row
        ai_info = QHBoxLayout()
        self.ai_label = QLabel("ACE", self)
        self.ai_label.setStyleSheet(LABEL_STYLE)
        self.ai_label.setAttribute(Qt.WA_TranslucentBackground)
        self.ai_chips_label = QLabel("$1000", self)
        self.ai_chips_label.setStyleSheet(CHIPS_STYLE)
        ai_info.addStretch()
        ai_info.addWidget(self.ai_label)
        ai_info.addWidget(self.ai_chips_label)
        ai_info.addStretch()

        # AI cards
        self.ai_cards_widget = QWidget(self)
        self.ai_cards_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.ai_cards_layout = QHBoxLayout(self.ai_cards_widget)
        self.ai_cards_layout.setSpacing(5)
        self.ai_cards_layout.setAlignment(Qt.AlignCenter)

        ai_section.addLayout(ai_info)
        ai_section.addWidget(self.ai_cards_widget)
        layout.addLayout(ai_section, stretch=1)

        # === COMMUNITY CARDS (middle) ===
        community_section = QVBoxLayout()
        community_section.setAlignment(Qt.AlignCenter)

        self.pot_label = QLabel("Pot: $0", self)
        self.pot_label.setStyleSheet(CHIPS_STYLE)
        self.pot_label.setAlignment(Qt.AlignCenter)

        self.community_widget = QWidget(self)
        self.community_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.community_layout = QHBoxLayout(self.community_widget)
        self.community_layout.setSpacing(8)
        self.community_layout.setAlignment(Qt.AlignCenter)

        self.phase_label = QLabel("Pre-Flop", self)
        self.phase_label.setStyleSheet(STATUS_STYLE)
        self.phase_label.setAlignment(Qt.AlignCenter)

        community_section.addWidget(self.pot_label, alignment=Qt.AlignCenter)
        community_section.addWidget(self.community_widget)
        community_section.addWidget(self.phase_label, alignment=Qt.AlignCenter)
        layout.addLayout(community_section, stretch=2)

        # === PLAYER AREA (bottom) ===
        player_section = QVBoxLayout()
        player_section.setAlignment(Qt.AlignCenter)

        # Player cards
        self.player_cards_widget = QWidget(self)
        self.player_cards_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.player_cards_layout = QHBoxLayout(self.player_cards_widget)
        self.player_cards_layout.setSpacing(5)
        self.player_cards_layout.setAlignment(Qt.AlignCenter)

        # Player info
        player_info = QHBoxLayout()
        self.player_label = QLabel(self._player_name.upper(), self)
        self.player_label.setAttribute(Qt.WA_TranslucentBackground)
        self._update_player_label()
        self.player_chips_label = QLabel("$1000", self)
        self.player_chips_label.setStyleSheet(CHIPS_STYLE)
        player_info.addStretch()
        player_info.addWidget(self.player_label)
        player_info.addWidget(self.player_chips_label)
        player_info.addStretch()

        player_section.addWidget(self.player_cards_widget)
        player_section.addLayout(player_info)
        layout.addLayout(player_section, stretch=1)

        # === ACTION BUTTONS ===
        btn_section = QVBoxLayout()
        btn_section.setSpacing(8)

        # Raise amount row
        raise_row = QHBoxLayout()
        raise_row.setAlignment(Qt.AlignCenter)
        raise_label = QLabel("Raise:", self)
        raise_label.setStyleSheet("color: white; font-weight: bold;")
        self.raise_spin = QSpinBox(self)
        self.raise_spin.setRange(20, 1000)
        self.raise_spin.setValue(40)
        self.raise_spin.setSingleStep(20)
        self.raise_spin.setFixedWidth(100)
        raise_row.addWidget(raise_label)
        raise_row.addWidget(self.raise_spin)

        # Action buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.setAlignment(Qt.AlignCenter)

        self.fold_btn = QPushButton("FOLD", self)
        self.check_btn = QPushButton("CHECK", self)
        self.call_btn = QPushButton("CALL", self)
        self.raise_btn = QPushButton("RAISE", self)
        self.allin_btn = QPushButton("ALL IN", self)

        self.fold_btn.setStyleSheet(FOLD_BUTTON_STYLE)
        for btn in [self.check_btn, self.call_btn, self.raise_btn, self.allin_btn]:
            btn.setStyleSheet(BUTTON_STYLE)
            btn.setCursor(Qt.PointingHandCursor)
        self.fold_btn.setCursor(Qt.PointingHandCursor)

        self.fold_btn.clicked.connect(lambda: self._player_action("fold"))
        self.check_btn.clicked.connect(lambda: self._player_action("check"))
        self.call_btn.clicked.connect(lambda: self._player_action("call"))
        self.raise_btn.clicked.connect(lambda: self._player_action("raise", self.raise_spin.value()))
        self.allin_btn.clicked.connect(lambda: self._player_action("all_in"))

        btn_row.addWidget(self.fold_btn)
        btn_row.addWidget(self.check_btn)
        btn_row.addWidget(self.call_btn)
        btn_row.addWidget(self.raise_btn)
        btn_row.addWidget(self.allin_btn)

        # New hand button
        new_row = QHBoxLayout()
        new_row.setAlignment(Qt.AlignCenter)
        self.new_hand_btn = QPushButton("NEW HAND", self)
        self.new_hand_btn.setStyleSheet(BUTTON_STYLE)
        self.new_hand_btn.setCursor(Qt.PointingHandCursor)
        self.new_hand_btn.clicked.connect(self.on_new_game)
        new_row.addWidget(self.new_hand_btn)

        btn_section.addLayout(raise_row)
        btn_section.addLayout(btn_row)
        btn_section.addLayout(new_row)
        layout.addLayout(btn_section)

    def _refresh(self) -> None:
        """Update UI to reflect current game state."""
        state = self.controller.state

        # Update chip counts
        self.player_chips_label.setText(f"${state.player_chips}")
        self.ai_chips_label.setText(f"${state.ai_chips}")
        self.pot_label.setText(f"Pot: ${state.pot}")

        # Update phase
        phase_names = {
            "preflop": "Pre-Flop",
            "flop": "Flop",
            "turn": "Turn",
            "river": "River",
            "showdown": "Showdown"
        }
        phase_text = phase_names.get(state.phase, state.phase.title())
        
        if state.finished:
            if state.winner == "player":
                phase_text = f"🎉 YOU WIN! ({state.winning_hand or ''})"
            elif state.winner == "ai":
                phase_text = f"💔 AI WINS! ({state.winning_hand or ''})"
            else:
                phase_text = f"🤝 TIE! ({state.winning_hand or ''})"
        
        self.phase_label.setText(phase_text)

        # Update cards
        self._update_cards()

        # Update buttons
        self._update_buttons()

    def _update_cards(self) -> None:
        """Update card displays."""
        state = self.controller.state

        # Clear layouts
        self._clear_layout(self.player_cards_layout)
        self._clear_layout(self.ai_cards_layout)
        self._clear_layout(self.community_layout)

        # Player cards (always visible)
        for card in state.player_hand:
            self.player_cards_layout.addWidget(CardWidget(card, self))

        # AI cards (hidden until showdown)
        for card in state.ai_hand:
            if state.phase == "showdown" or state.finished:
                self.ai_cards_layout.addWidget(CardWidget(card, self))
            else:
                back_widget = QSvgWidget(self)
                back_widget.setFixedSize(80, 112)
                back_widget.load(str(BACKS_DIR / self._card_back))
                self.ai_cards_layout.addWidget(back_widget)

        # Community cards
        for card in state.community_cards:
            self.community_layout.addWidget(CardWidget(card, self))

        # Placeholder for missing community cards
        for _ in range(5 - len(state.community_cards)):
            placeholder = QFrame(self)
            placeholder.setFixedSize(80, 112)
            placeholder.setStyleSheet("background: rgba(0,0,0,0.2); border-radius: 6px; border: 2px dashed #555;")
            self.community_layout.addWidget(placeholder)

    def _update_buttons(self) -> None:
        """Update button states."""
        state = self.controller.state
        is_player_turn = state.turn == "player" and not state.finished

        self.fold_btn.setEnabled(is_player_turn)
        self.check_btn.setEnabled(is_player_turn and self.controller.can_check())
        self.call_btn.setEnabled(is_player_turn and not self.controller.can_check())
        self.raise_btn.setEnabled(is_player_turn and state.player_chips > 0)
        self.allin_btn.setEnabled(is_player_turn and state.player_chips > 0)

        # Update call button text
        call_amt = self.controller.call_amount()
        self.call_btn.setText(f"CALL ${call_amt}" if call_amt > 0 else "CALL")

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

    def _player_action(self, action: str, amount: int = 0) -> None:
        """Handle player action."""
        result = self.controller.player_action(action, amount)
        self._log(result)
        
        # AI comment using LLM
        if action == "fold":
            self._chat("AI", self.agent.get_comment(self.controller.state, "player_fold"))
        elif action == "raise" or action == "all_in":
            self._chat("AI", self.agent.get_comment(self.controller.state, "player_raise"))
        elif action == "call":
            self._chat("AI", self.agent.get_comment(self.controller.state, "player_call"))
        
        self._refresh()
        
        # AI turn
        if not self.controller.state.finished and self.controller.state.turn == "ai":
            self._ai_turn()

    def _ai_turn(self) -> None:
        """Handle AI turn."""
        while self.controller.state.turn == "ai" and not self.controller.state.finished:
            action, message = self.controller.ai_action()
            if message:
                self._log(message)
                if action == "fold":
                    self._chat("AI", self.agent.get_comment(self.controller.state, "ai_fold"))
                elif action == "raise":
                    self._chat("AI", self.agent.get_comment(self.controller.state, "ai_raise"))
                elif action == "call":
                    self._chat("AI", self.agent.get_comment(self.controller.state, "ai_call"))
                elif action == "check":
                    self._chat("AI", self.agent.get_comment(self.controller.state, "check"))
            
            self._refresh()
            
            # Comment on new phase
            if self.controller.state.phase == "flop" and len(self.controller.state.community_cards) == 3:
                self._chat("AI", self.agent.get_comment(self.controller.state, "flop"))
            elif self.controller.state.phase == "turn" and len(self.controller.state.community_cards) == 4:
                self._chat("AI", self.agent.get_comment(self.controller.state, "turn"))
            elif self.controller.state.phase == "river" and len(self.controller.state.community_cards) == 5:
                self._chat("AI", self.agent.get_comment(self.controller.state, "river"))
        
        # Check for game end
        if self.controller.state.finished:
            if self.controller.state.winner == "player":
                self._chat("AI", self.agent.get_comment(self.controller.state, "lose"))
                save_game_result("poker", "win", self.controller.state.player_chips, self.controller.state.ai_chips)
            elif self.controller.state.winner == "ai":
                self._chat("AI", self.agent.get_comment(self.controller.state, "win"))
                save_game_result("poker", "loss", self.controller.state.player_chips, self.controller.state.ai_chips)
            self._refresh()

    def on_new_game(self) -> None:
        """Start a new hand."""
        # Reset chips if either player is broke
        if self.controller.state.player_chips <= 0 or self.controller.state.ai_chips <= 0:
            self.controller.reset_chips()
            self._log("Chips reset to $1000 each.")
        
        self.controller.new_game()
        self._log("New hand dealt.")
        self._chat("AI", self.agent.get_comment(self.controller.state, "game_start"))
        self._refresh()
        
        # If AI acts first
        if self.controller.state.turn == "ai":
            self._ai_turn()

    def ask_ai_chat(self, message: str) -> None:
        """Handle player chat."""
        self._chat("AI", self.agent.chat_response(self.controller.state, message))

    # --- Settings ---
    
    def get_card_back(self) -> str:
        return self._card_back

    def set_card_back(self, filename: str) -> None:
        self._card_back = filename
        self._refresh()

    def get_table_color(self) -> str:
        return self._table_color

    def set_table_color(self, color: str) -> None:
        self._table_color = color
        self.update()

    def get_player_name(self) -> str:
        return self._player_name

    def set_player_name(self, name: str) -> None:
        self._player_name = name
        self._update_player_label()

    def get_player_color(self) -> str:
        return self._player_color

    def set_player_color(self, color: str) -> None:
        self._player_color = color
        self._update_player_label()

    def _update_player_label(self) -> None:
        self.player_label.setText(self._player_name.upper())
        self.player_label.setStyleSheet(f"""
            QLabel {{
                color: {self._player_color};
                font-size: 16px;
                font-weight: bold;
                padding: 4px;
            }}
        """)

    def paintEvent(self, event) -> None:
        """Paint table background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        base = QColor(self._table_color)
        r, g, b = base.red(), base.green(), base.blue()
        
        light = QColor(min(r + 40, 255), min(g + 40, 255), min(b + 40, 255))
        dark = QColor(max(r - 30, 0), max(g - 30, 0), max(b - 30, 0))
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = max(self.width(), self.height())
        
        gradient = QRadialGradient(center_x, center_y, radius)
        gradient.setColorAt(0, light)
        gradient.setColorAt(0.5, base)
        gradient.setColorAt(1, dark)
        
        painter.fillRect(self.rect(), QBrush(gradient))
        painter.end()
