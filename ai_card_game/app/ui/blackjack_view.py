from pathlib import Path
from typing import Callable, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QSizePolicy, QFrame, QSpacerItem
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCore import QThread, Signal, QObject, Qt

from ..core.blackjack.controller import BlackjackController
from ..core.blackjack.rules import hand_value, is_bust
from ..core.cards import Card
from ..ai.blackjack_agent import BlackjackAgent, AIDecision
from ..db.database import save_game_result


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
CARDS_DIR = ASSETS_DIR / "cards"
BACKS_DIR = ASSETS_DIR / "backs"

# Casino-style button stylesheet (green)
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
        min-width: 100px;
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
        color: white;
        font-size: 22px;
        font-weight: bold;
        padding: 12px;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 8px;
    }
"""


class CardWidget(QSvgWidget):
    def __init__(self, card: Card | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(120, 168)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        if card is not None:
            self.set_card(card)

    def set_card(self, card: Card) -> None:
        svg_path = CARDS_DIR / card.svg_filename
        self.load(str(svg_path))


class AIWorker(QObject):
    """Worker that runs AI decision in a background thread."""
    finished = Signal(object)  # emits AIDecision
    error = Signal(str)

    def __init__(self, agent: BlackjackAgent, state) -> None:
        super().__init__()
        self.agent = agent
        self.state = state

    def run(self) -> None:
        try:
            decision = self.agent.decide(self.state)
            self.finished.emit(decision)
        except Exception as e:
            self.error.emit(str(e))


class BlackjackView(QWidget):
    """Very simple visual for player/AI hands and basic controls."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = BlackjackController()
        self.agent = BlackjackAgent()
        self._logger: Optional[Callable[[str], None]] = None
        self._chat_sink: Optional[Callable[[str, str], None]] = None
        self._ai_thread: Optional[QThread] = None
        self._ai_worker: Optional[AIWorker] = None

        self._init_ui()
        self._refresh()

    # --- Logging ---

    def set_logger(self, logger: Callable[[str], None]) -> None:
        """Set a function used to log messages (e.g. to main window console)."""
        self._logger = logger

    def set_chat_sink(self, sink: Callable[[str, str], None]) -> None:
        """Set a function to send chat messages (sender, text)."""
        self._chat_sink = sink

    def _log(self, message: str) -> None:
        if self._logger is not None:
            self._logger(message)

    def _chat(self, sender: str, message: str) -> None:
        if self._chat_sink is not None:
            self._chat_sink(sender, message)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Casino felt table background
        self.setStyleSheet("""
            BlackjackView {
                background: qradialgradient(cx:0.5, cy:0.5, radius:1,
                    stop:0 #1a5c1a, stop:0.7 #0d3d0d, stop:1 #082808);
            }
        """)

        # === DEALER AREA (top) ===
        dealer_section = QVBoxLayout()
        dealer_section.setAlignment(Qt.AlignCenter)

        self.ai_label = QLabel("DEALER", self)
        self.ai_label.setStyleSheet(LABEL_STYLE)
        self.ai_label.setAlignment(Qt.AlignCenter)

        # Card container for dealer - using a frame for better control
        self.ai_cards_container = QWidget(self)
        self.ai_cards_row = QHBoxLayout(self.ai_cards_container)
        self.ai_cards_row.setContentsMargins(0, 0, 0, 0)
        self.ai_cards_row.setSpacing(-30)  # Negative spacing for overlap
        self.ai_cards_row.setAlignment(Qt.AlignCenter)

        dealer_section.addWidget(self.ai_label)
        dealer_section.addWidget(self.ai_cards_container)

        layout.addLayout(dealer_section, stretch=2)

        # === STATUS AREA (middle) ===
        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet(STATUS_STYLE)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label, alignment=Qt.AlignCenter)

        # === PLAYER AREA (bottom) ===
        player_section = QVBoxLayout()
        player_section.setAlignment(Qt.AlignCenter)

        # Card container for player
        self.player_cards_container = QWidget(self)
        self.player_cards_row = QHBoxLayout(self.player_cards_container)
        self.player_cards_row.setContentsMargins(0, 0, 0, 0)
        self.player_cards_row.setSpacing(-30)  # Negative spacing for overlap
        self.player_cards_row.setAlignment(Qt.AlignCenter)

        self.player_label = QLabel("YOUR HAND", self)
        self.player_label.setStyleSheet(LABEL_STYLE)
        self.player_label.setAlignment(Qt.AlignCenter)

        player_section.addWidget(self.player_cards_container)
        player_section.addWidget(self.player_label)

        layout.addLayout(player_section, stretch=2)

        # === ACTION BUTTONS (bottom) ===
        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)
        btn_row.setAlignment(Qt.AlignCenter)

        self.hit_btn = QPushButton("HIT", self)
        self.stand_btn = QPushButton("STAND", self)
        self.new_game_btn = QPushButton("NEW GAME", self)

        for btn in [self.hit_btn, self.stand_btn, self.new_game_btn]:
            btn.setStyleSheet(BUTTON_STYLE)
            btn.setCursor(Qt.PointingHandCursor)

        self.hit_btn.clicked.connect(self.on_hit)
        self.stand_btn.clicked.connect(self.on_stand)
        self.new_game_btn.clicked.connect(self.on_new_game)

        btn_row.addWidget(self.hit_btn)
        btn_row.addWidget(self.stand_btn)
        btn_row.addWidget(self.new_game_btn)

        layout.addLayout(btn_row)

    # --- UI logic ---

    def _refresh(self) -> None:
        # Clear existing card widgets
        self._clear_layout(self.ai_cards_row)
        self._clear_layout(self.player_cards_row)

        state = self.controller.state

        # AI cards: hide first card (show back) until game is finished
        if state.ai_hand.cards:
            # First card: back if game not finished
            first = state.ai_hand.cards[0]
            if state.finished:
                self.ai_cards_row.addWidget(CardWidget(first, self))
            else:
                # Use a fixed-size widget for the back so it matches card size
                back_widget = CardWidget(parent=self)
                back_path = BACKS_DIR / "back.svg"
                back_widget.load(str(back_path))
                self.ai_cards_row.addWidget(back_widget)

            # Remaining cards: always face up
            for card in state.ai_hand.cards[1:]:
                self.ai_cards_row.addWidget(CardWidget(card, self))

        # Player cards
        for card in state.player_hand.cards:
            self.player_cards_row.addWidget(CardWidget(card, self))

        # Update card sizes based on current widget size
        self._update_card_sizes()

        # Status with casino-style display
        p_val = hand_value(state.player_hand)
        a_val = hand_value(state.ai_hand)
        if state.finished:
            self.hit_btn.setEnabled(False)
            self.stand_btn.setEnabled(False)
            if state.winner == "player":
                result_text = "🎉 YOU WIN!"
                result_db = "win"
            elif state.winner == "ai":
                result_text = "💔 DEALER WINS"
                result_db = "loss"
            else:
                result_text = "🤝 PUSH"
                result_db = "push"
            self.status_label.setText(f"{result_text}   •   You: {p_val}  |  Dealer: {a_val}")
            self._log(f"Game finished. Winner: {state.winner} (Player={p_val}, AI={a_val})")
            # Save to database
            save_game_result("blackjack", result_db, p_val, a_val)
        else:
            visible_ai = "?" if not state.finished else str(a_val)
            self.status_label.setText(f"You: {p_val}   •   Dealer: {visible_ai}")

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

    def _update_card_sizes(self) -> None:
        """Adjust card sizes responsively based on current widget size."""
        # Calculate card size based on window height for better proportions
        avail_height = max(self.height() - 200, 300)
        card_height = min(int(avail_height * 0.35), 200)
        card_width = int(card_height / 1.4)  # Standard card ratio

        # Ensure minimum size
        card_width = max(card_width, 80)
        card_height = max(card_height, 112)

        # Update overlap based on card width
        overlap = int(card_width * 0.3)
        self.ai_cards_row.setSpacing(-overlap)
        self.player_cards_row.setSpacing(-overlap)

        def resize_cards_in_layout(layout) -> None:
            for i in range(layout.count()):
                item = layout.itemAt(i)
                widget = item.widget()
                if isinstance(widget, CardWidget):
                    widget.setFixedSize(card_width, card_height)

        resize_cards_in_layout(self.ai_cards_row)
        resize_cards_in_layout(self.player_cards_row)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._update_card_sizes()

    # --- Button handlers ---

    def on_hit(self) -> None:
        self.controller.player_hit()
        self._log("Player hits.")
        self._refresh()

    def on_stand(self) -> None:
        self.controller.player_stand()
        self._log("Player stands. AI's turn...")
        # Disable buttons while AI thinks
        self.hit_btn.setEnabled(False)
        self.stand_btn.setEnabled(False)
        # Start AI turn in background
        self._start_ai_turn()

    def _start_ai_turn(self) -> None:
        """Kick off AI decision in a background thread."""
        if self.controller.state.finished:
            self._refresh()
            return

        self._log("AI is thinking...")
        self._ai_thread = QThread()
        self._ai_worker = AIWorker(self.agent, self.controller.state)
        self._ai_worker.moveToThread(self._ai_thread)

        self._ai_thread.started.connect(self._ai_worker.run)
        self._ai_worker.finished.connect(self._on_ai_decision)
        self._ai_worker.error.connect(self._on_ai_error)
        self._ai_worker.finished.connect(self._ai_thread.quit)
        self._ai_worker.error.connect(self._ai_thread.quit)

        self._ai_thread.start()

    def _on_ai_decision(self, decision: AIDecision) -> None:
        """Handle AI decision result from worker thread."""
        action = decision.action
        comment = decision.comment

        self._log(f"AI chooses to {action}.")
        self._chat("AI", comment)

        if action == "hit":
            self.controller.state.ai_hand.cards.append(self.controller.state.deck.draw())
            self._refresh()
            # Check if AI busted
            if is_bust(self.controller.state.ai_hand):
                self.controller._finish_game(winner="player")
                self._log("AI busts!")
                self._refresh()
            else:
                # AI continues thinking
                self._start_ai_turn()
        else:
            # AI stands -> resolve game
            self.controller.ai_stand_and_resolve()
            self._refresh()

    def _on_ai_error(self, error_msg: str) -> None:
        """Handle AI error by falling back to simple rules."""
        self._log(f"AI error: {error_msg}. Using fallback.")
        self._chat("AI", "I had trouble thinking... I'll just play safe.")
        # Fallback: use the old rule-based play
        self.controller.ai_play_out()
        self._refresh()

    def on_new_game(self) -> None:
        self.controller.new_game()
        self.hit_btn.setEnabled(True)
        self.stand_btn.setEnabled(True)
        self._log("New game started.")
        self._refresh()
