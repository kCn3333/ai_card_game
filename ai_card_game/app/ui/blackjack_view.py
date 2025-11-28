from pathlib import Path
from typing import Callable, Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtGui import QPalette, QColor

from ..core.blackjack.controller import BlackjackController
from ..core.blackjack.rules import hand_value
from ..core.cards import Card


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
CARDS_DIR = ASSETS_DIR / "cards"
BACKS_DIR = ASSETS_DIR / "backs"


class CardWidget(QSvgWidget):
    def __init__(self, card: Card | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # Default size; will be overridden by BlackjackView on resize
        self.setFixedSize(100, 150)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        if card is not None:
            self.set_card(card)

    def set_card(self, card: Card) -> None:
        svg_path = CARDS_DIR / card.svg_filename
        self.load(str(svg_path))


class BlackjackView(QWidget):
    """Very simple visual for player/AI hands and basic controls."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = BlackjackController()
        self._logger: Optional[Callable[[str], None]] = None

        self._init_ui()
        self._refresh()

    # --- Logging ---

    def set_logger(self, logger: Callable[[str], None]) -> None:
        """Set a function used to log messages (e.g. to main window console)."""
        self._logger = logger

    def _log(self, message: str) -> None:
        if self._logger is not None:
            self._logger(message)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Simple table background (dark green)
        pal = self.palette()
        pal.setColor(QPalette.Window, QColor(0, 80, 0))
        self.setAutoFillBackground(True)
        self.setPalette(pal)

        # Dealer (AI) area
        self.ai_label = QLabel("AI Hand", self)
        self.ai_cards_row = QHBoxLayout()
        self.ai_cards_row.setSpacing(12)

        layout.addWidget(self.ai_label)
        layout.addLayout(self.ai_cards_row)

        # Player area
        self.player_label = QLabel("Player Hand", self)
        self.player_cards_row = QHBoxLayout()
        self.player_cards_row.setSpacing(12)

        layout.addWidget(self.player_label)
        layout.addLayout(self.player_cards_row)

        # Action buttons
        btn_row = QHBoxLayout()
        self.hit_btn = QPushButton("Hit", self)
        self.stand_btn = QPushButton("Stand", self)
        self.new_game_btn = QPushButton("New Game", self)

        self.hit_btn.clicked.connect(self.on_hit)
        self.stand_btn.clicked.connect(self.on_stand)
        self.new_game_btn.clicked.connect(self.on_new_game)

        btn_row.addWidget(self.hit_btn)
        btn_row.addWidget(self.stand_btn)
        btn_row.addWidget(self.new_game_btn)
        layout.addLayout(btn_row)

        # Status label
        self.status_label = QLabel("", self)
        layout.addWidget(self.status_label)

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

        # Status
        p_val = hand_value(state.player_hand)
        a_val = hand_value(state.ai_hand)
        if state.finished:
            self.hit_btn.setEnabled(False)
            self.stand_btn.setEnabled(False)
            self.status_label.setText(f"Finished. Winner: {state.winner} (P={p_val}, AI={a_val})")
            self._log(f"Game finished. Winner: {state.winner} (Player={p_val}, AI={a_val})")
        else:
            self.status_label.setText(f"Player total: {p_val} | AI total: {a_val}")

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

    def _update_card_sizes(self) -> None:
        """Adjust card sizes responsively based on current widget size."""
        # Rough heuristic: fit up to 5 cards per row with margins (bigger cards)
        max_cards_per_row = 5
        avail_width = max(self.width() - 120, 300)  # leave space for margins
        card_width = avail_width / max_cards_per_row
        # Limit card width to a sensible range
        card_width = max(90, min(card_width, 200))
        card_height = int(card_width * 1.5)

        def resize_cards_in_layout(layout) -> None:
            for i in range(layout.count()):
                item = layout.itemAt(i)
                widget = item.widget()
                if isinstance(widget, CardWidget):
                    widget.setFixedSize(int(card_width), card_height)

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
        self._log("Player stands. Dealer plays out.")
        # Dealer/AI plays out according to rules
        self.controller.ai_play_out()
        self._refresh()

    def on_new_game(self) -> None:
        self.controller.new_game()
        self.hit_btn.setEnabled(True)
        self.stand_btn.setEnabled(True)
        self._log("New game started.")
        self._refresh()
