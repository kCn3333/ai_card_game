"""War card game UI view."""

from pathlib import Path
from typing import Callable, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSizePolicy, QFrame
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtGui import QColor, QPainter, QBrush, QRadialGradient
from PySide6.QtCore import QThread, Signal, QObject, Qt

from ..core.war.controller import WarController
from ..core.war.rules import card_value
from ..core.cards import Card
from ..ai.war_agent import WarAgent
from ..db.database import save_game_result


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
CARDS_DIR = ASSETS_DIR / "cards"
BACKS_DIR = ASSETS_DIR / "backs"

# Button style (green)
BUTTON_STYLE = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #2e8b57, stop:0.5 #228b22, stop:1 #1a6b1a);
        color: #ffffff;
        border: 2px solid #145214;
        border-radius: 8px;
        padding: 12px 28px;
        font-size: 16px;
        font-weight: bold;
        min-width: 120px;
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

LABEL_STYLE = """
    QLabel {
        color: #f0e68c;
        font-size: 18px;
        font-weight: bold;
        padding: 8px;
    }
"""

STATUS_STYLE = """
    QLabel {
        color: #ffffff;
        font-size: 24px;
        font-weight: bold;
        padding: 12px;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 8px;
    }
"""


class CardWidget(QSvgWidget):
    """Widget to display a single card."""
    
    def __init__(self, card: Card | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(100, 140)
        if card:
            svg_path = CARDS_DIR / card.svg_filename
            self.load(str(svg_path))


class CommentWorker(QObject):
    """Worker for async AI comments."""
    finished = Signal(str)
    
    def __init__(self, agent: WarAgent, state, event: str) -> None:
        super().__init__()
        self.agent = agent
        self.state = state
        self.event = event
    
    def run(self) -> None:
        try:
            comment = self.agent.get_comment(self.state, self.event)
            self.finished.emit(comment)
        except Exception:
            self.finished.emit("")


class ChatWorker(QObject):
    """Worker for async chat responses."""
    finished = Signal(str)
    
    def __init__(self, agent: WarAgent, state, message: str) -> None:
        super().__init__()
        self.agent = agent
        self.state = state
        self.message = message
    
    def run(self) -> None:
        try:
            response = self.agent.chat_response(self.state, self.message)
            self.finished.emit(response)
        except Exception:
            self.finished.emit("Focus on the game! 😏")


class WarView(QWidget):
    """War card game view."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = WarController()
        self.agent = WarAgent()
        self._logger: Optional[Callable[[str], None]] = None
        self._chat_sink: Optional[Callable[[str, str], None]] = None
        self._comment_thread: Optional[QThread] = None
        self._comment_worker: Optional[CommentWorker] = None
        self._chat_thread: Optional[QThread] = None
        self._chat_worker: Optional[ChatWorker] = None
        self._card_back: str = "back.svg"
        self._table_color: str = "#0d5c2e"
        self._player_name: str = "Player"
        self._player_color: str = "#2e8b57"

        self._init_ui()
        self._refresh()
        # Note: AI comment will be triggered when chat_sink is connected

    def set_logger(self, logger: Callable[[str], None]) -> None:
        self._logger = logger

    def set_chat_sink(self, sink: Callable[[str, str], None]) -> None:
        self._chat_sink = sink
        # Get LLM greeting
        if self._chat_sink:
            greeting = self.agent.get_comment(self.controller.state, "game_start")
            self._chat_sink("AI", greeting)

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger(message)

    def _chat(self, sender: str, message: str) -> None:
        if self._chat_sink:
            self._chat_sink(sender, message)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # === AI AREA (top) ===
        ai_section = QVBoxLayout()
        ai_section.setAlignment(Qt.AlignCenter)

        # Use LLM model name
        model_name = self.agent.client.get_model_name()
        self.ai_label = QLabel(model_name, self)
        self.ai_label.setStyleSheet(LABEL_STYLE)
        self.ai_label.setAlignment(Qt.AlignCenter)
        self.ai_label.setAttribute(Qt.WA_TranslucentBackground)

        # AI pile count and battle card
        ai_cards_layout = QHBoxLayout()
        ai_cards_layout.setAlignment(Qt.AlignCenter)
        ai_cards_layout.setSpacing(40)

        # AI pile (face down)
        self.ai_pile_widget = QWidget(self)
        self.ai_pile_widget.setAttribute(Qt.WA_TranslucentBackground)
        ai_pile_layout = QVBoxLayout(self.ai_pile_widget)
        self.ai_pile_card = QSvgWidget(self)
        self.ai_pile_card.setFixedSize(100, 140)
        self.ai_pile_card.load(str(BACKS_DIR / self._card_back))
        self.ai_pile_count = QLabel("26", self)
        self.ai_pile_count.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        self.ai_pile_count.setAlignment(Qt.AlignCenter)
        ai_pile_layout.addWidget(self.ai_pile_card, alignment=Qt.AlignCenter)
        ai_pile_layout.addWidget(self.ai_pile_count)

        # AI battle card
        self.ai_battle_widget = QWidget(self)
        self.ai_battle_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.ai_battle_widget.setFixedSize(100, 140)
        self.ai_battle_layout = QVBoxLayout(self.ai_battle_widget)
        self.ai_battle_layout.setContentsMargins(0, 0, 0, 0)

        ai_cards_layout.addWidget(self.ai_pile_widget)
        ai_cards_layout.addWidget(self.ai_battle_widget)

        ai_section.addWidget(self.ai_label)
        ai_section.addLayout(ai_cards_layout)
        layout.addLayout(ai_section, stretch=2)

        # === STATUS AREA (middle) ===
        self.status_label = QLabel("Click BATTLE to play!", self)
        self.status_label.setStyleSheet(STATUS_STYLE)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label, alignment=Qt.AlignCenter)

        # === PLAYER AREA (bottom) ===
        player_section = QVBoxLayout()
        player_section.setAlignment(Qt.AlignCenter)

        # Player pile and battle card
        player_cards_layout = QHBoxLayout()
        player_cards_layout.setAlignment(Qt.AlignCenter)
        player_cards_layout.setSpacing(40)

        # Player battle card
        self.player_battle_widget = QWidget(self)
        self.player_battle_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.player_battle_widget.setFixedSize(100, 140)
        self.player_battle_layout = QVBoxLayout(self.player_battle_widget)
        self.player_battle_layout.setContentsMargins(0, 0, 0, 0)

        # Player pile (face down)
        self.player_pile_widget = QWidget(self)
        self.player_pile_widget.setAttribute(Qt.WA_TranslucentBackground)
        player_pile_layout = QVBoxLayout(self.player_pile_widget)
        self.player_pile_card = QSvgWidget(self)
        self.player_pile_card.setFixedSize(100, 140)
        self.player_pile_card.load(str(BACKS_DIR / self._card_back))
        self.player_pile_count = QLabel("26", self)
        self.player_pile_count.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        self.player_pile_count.setAlignment(Qt.AlignCenter)
        player_pile_layout.addWidget(self.player_pile_card, alignment=Qt.AlignCenter)
        player_pile_layout.addWidget(self.player_pile_count)

        player_cards_layout.addWidget(self.player_battle_widget)
        player_cards_layout.addWidget(self.player_pile_widget)

        self.player_label = QLabel(self._player_name.upper(), self)
        self.player_label.setAlignment(Qt.AlignCenter)
        self.player_label.setAttribute(Qt.WA_TranslucentBackground)
        self._update_player_label()

        player_section.addLayout(player_cards_layout)
        player_section.addWidget(self.player_label)
        layout.addLayout(player_section, stretch=2)

        # === BUTTONS ===
        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)
        btn_row.setAlignment(Qt.AlignCenter)

        self.battle_btn = QPushButton("⚔️ BATTLE", self)
        self.new_game_btn = QPushButton("NEW GAME", self)

        for btn in [self.battle_btn, self.new_game_btn]:
            btn.setStyleSheet(BUTTON_STYLE)
            btn.setCursor(Qt.PointingHandCursor)

        self.battle_btn.clicked.connect(self.on_battle)
        self.new_game_btn.clicked.connect(self.on_new_game)

        btn_row.addWidget(self.battle_btn)
        btn_row.addWidget(self.new_game_btn)
        layout.addLayout(btn_row)

    def _refresh(self) -> None:
        """Update the UI to reflect current game state."""
        state = self.controller.state

        # Update pile counts
        self.player_pile_count.setText(str(state.player_card_count))
        self.ai_pile_count.setText(str(state.ai_card_count))

        # Update pile visibility
        if state.player_card_count == 0:
            self.player_pile_card.hide()
        else:
            self.player_pile_card.show()
            self.player_pile_card.load(str(BACKS_DIR / self._card_back))

        if state.ai_card_count == 0:
            self.ai_pile_card.hide()
        else:
            self.ai_pile_card.show()
            self.ai_pile_card.load(str(BACKS_DIR / self._card_back))

        # Clear battle areas
        self._clear_layout(self.player_battle_layout)
        self._clear_layout(self.ai_battle_layout)

        # Show battle cards if any
        if state.player_battle_cards:
            card = state.player_battle_cards[-1]
            card_widget = CardWidget(card, self)
            self.player_battle_layout.addWidget(card_widget)

        if state.ai_battle_cards:
            card = state.ai_battle_cards[-1]
            card_widget = CardWidget(card, self)
            self.ai_battle_layout.addWidget(card_widget)

        # Update status
        if state.finished:
            self.battle_btn.setEnabled(False)
            if state.winner == "player":
                self.status_label.setText("🎉 YOU WIN THE WAR!")
                save_game_result("war", "win", state.player_card_count, state.ai_card_count)
            else:
                self.status_label.setText("💔 AI WINS THE WAR!")
                save_game_result("war", "loss", state.player_card_count, state.ai_card_count)
        elif state.in_war:
            self.status_label.setText(f"⚔️ WAR! {len(state.war_pot)} cards at stake!")
        elif state.last_result == "player_wins":
            self.status_label.setText(f"You win this battle! ({state.player_card_count} vs {state.ai_card_count})")
        elif state.last_result == "ai_wins":
            self.status_label.setText(f"AI wins this battle! ({state.player_card_count} vs {state.ai_card_count})")
        else:
            self.status_label.setText(f"Cards: You {state.player_card_count} - AI {state.ai_card_count}")

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

    def on_battle(self) -> None:
        """Play one battle round."""
        result = self.controller.play_round()
        self._log(f"Battle result: {result}")
        self._refresh()
        self._get_ai_comment(result)

    def on_new_game(self) -> None:
        """Start a new game."""
        self.controller.new_game()
        self.battle_btn.setEnabled(True)
        self._log("New War game started.")
        self._refresh()
        self._get_ai_comment("game_start")

    def _get_ai_comment(self, event: str) -> None:
        """Get AI comment using LLM."""
        comment = self.agent.get_comment(self.controller.state, event)
        if comment:
            self._chat("AI", comment)

    def ask_ai_chat(self, message: str) -> None:
        """Handle player chat message using LLM."""
        response = self.agent.chat_response(self.controller.state, message)
        self._chat("AI", response)

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
                font-size: 18px;
                font-weight: bold;
                padding: 8px;
            }}
        """)

    def paintEvent(self, event) -> None:
        """Paint the table background."""
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
