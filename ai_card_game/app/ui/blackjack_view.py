from pathlib import Path
from typing import Callable, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QSizePolicy, QFrame, QSpacerItem
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtGui import QPalette, QColor, QFont, QPainter, QBrush, QRadialGradient
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


class ChatWorker(QObject):
    """Worker that runs AI chat response in a background thread."""
    finished = Signal(str)  # emits response string
    error = Signal(str)

    def __init__(self, agent: BlackjackAgent, state, message: str) -> None:
        super().__init__()
        self.agent = agent
        self.state = state
        self.message = message

    def run(self) -> None:
        try:
            response = self.agent.chat_response(self.state, self.message)
            self.finished.emit(response)
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
        self._chat_thread: Optional[QThread] = None
        self._chat_worker: Optional[ChatWorker] = None
        self._card_back: str = "back.svg"
        self._table_color: str = "#0d5c2e"  # Dark green felt
        self._player_name: str = "Player"
        self._player_color: str = "#2e8b57"  # Sea green

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
        self._update_table_style()

        # === DEALER AREA (top) ===
        dealer_section = QVBoxLayout()
        dealer_section.setAlignment(Qt.AlignCenter)

        # Use LLM model name as dealer name
        model_name = self.agent.client.get_model_name()
        self.ai_label = QLabel(model_name, self)
        self.ai_label.setStyleSheet(LABEL_STYLE)
        self.ai_label.setAlignment(Qt.AlignCenter)
        self.ai_label.setAttribute(Qt.WA_TranslucentBackground)

        # Card container for dealer - using a frame for better control
        self.ai_cards_container = QWidget(self)
        self.ai_cards_container.setAttribute(Qt.WA_TranslucentBackground)
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
        self.player_cards_container.setAttribute(Qt.WA_TranslucentBackground)
        self.player_cards_row = QHBoxLayout(self.player_cards_container)
        self.player_cards_row.setContentsMargins(0, 0, 0, 0)
        self.player_cards_row.setSpacing(-30)  # Negative spacing for overlap
        self.player_cards_row.setAlignment(Qt.AlignCenter)

        self.player_label = QLabel(self._player_name.upper(), self)
        self.player_label.setAlignment(Qt.AlignCenter)
        self.player_label.setAttribute(Qt.WA_TranslucentBackground)
        self._update_player_label()

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
                back_path = BACKS_DIR / self._card_back
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
        """Handle AI error - show error to user."""
        self._log(f"AI error: {error_msg}")
        self._chat("AI", f"Error: {error_msg} - Make sure Ollama is running!")

    def on_new_game(self) -> None:
        self.controller.new_game()
        self.hit_btn.setEnabled(True)
        self.stand_btn.setEnabled(True)
        self._log("New game started.")
        self._refresh()

    # --- Chat with AI ---

    def ask_ai_chat(self, message: str) -> None:
        """Ask AI to respond to a player chat message."""
        self._chat_thread = QThread()
        self._chat_worker = ChatWorker(self.agent, self.controller.state, message)
        self._chat_worker.moveToThread(self._chat_thread)

        self._chat_thread.started.connect(self._chat_worker.run)
        self._chat_worker.finished.connect(self._on_chat_response)
        self._chat_worker.error.connect(self._on_chat_error)
        self._chat_worker.finished.connect(self._chat_thread.quit)
        self._chat_worker.error.connect(self._chat_thread.quit)

        self._chat_thread.start()

    def _on_chat_response(self, response: str) -> None:
        """Handle AI chat response."""
        self._chat("AI", response)

    def _on_chat_error(self, error_msg: str) -> None:
        """Handle AI chat error."""
        self._chat("AI", f"Error: {error_msg} - Make sure Ollama is running!")

    # --- Card back settings ---

    def get_card_back(self) -> str:
        """Return current card back filename."""
        return self._card_back

    def set_card_back(self, filename: str) -> None:
        """Set the card back design and refresh display."""
        self._card_back = filename
        self._refresh()

    # --- Table color settings ---

    def get_table_color(self) -> str:
        """Return current table color."""
        return self._table_color

    def set_table_color(self, color: str) -> None:
        """Set the table background color."""
        self._table_color = color
        self._update_table_style()

    def _update_table_style(self) -> None:
        """Update the table background with current color."""
        # Just trigger a repaint - paintEvent will handle the gradient
        self.update()

    def paintEvent(self, event) -> None:
        """Paint the table background with a radial gradient."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create gradient based on current table color
        base = QColor(self._table_color)
        r, g, b = base.red(), base.green(), base.blue()
        
        light = QColor(min(r + 40, 255), min(g + 40, 255), min(b + 40, 255))
        dark = QColor(max(r - 30, 0), max(g - 30, 0), max(b - 30, 0))
        
        # Create radial gradient centered in widget
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = max(self.width(), self.height())
        
        gradient = QRadialGradient(center_x, center_y, radius)
        gradient.setColorAt(0, light)
        gradient.setColorAt(0.5, base)
        gradient.setColorAt(1, dark)
        
        painter.fillRect(self.rect(), QBrush(gradient))
        painter.end()

    # --- Player name and color settings ---

    def get_player_name(self) -> str:
        """Return current player name."""
        return self._player_name

    def set_player_name(self, name: str) -> None:
        """Set the player name and update display."""
        self._player_name = name
        self._update_player_label()

    def get_player_color(self) -> str:
        """Return current player name color."""
        return self._player_color

    def set_player_color(self, color: str) -> None:
        """Set the player name color and update display."""
        self._player_color = color
        self._update_player_label()

    def _update_player_label(self) -> None:
        """Update the player label with current name and color."""
        self.player_label.setText(self._player_name.upper())
        self.player_label.setStyleSheet(f"""
            QLabel {{
                color: {self._player_color};
                font-size: 18px;
                font-weight: bold;
                padding: 8px;
            }}
        """)
