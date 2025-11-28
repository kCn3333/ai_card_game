from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QDockWidget,
    QTextEdit,
    QSplitter,
    QLabel,
    QMenuBar,
    QMenu,
    QLineEdit,
    QPushButton,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon

from .blackjack_view import BlackjackView
from .war_view import WarView
from .settings_dialog import SettingsDialog
from .statistics_dialog import StatisticsDialog
from .game_settings_dialog import GameSettingsDialog

ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"

class MainWindow(QMainWindow):
    """Main window: game area + right panel (console + chat)."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("♠ AI Card Game")
        self.resize(1200, 800)

        # Player settings (defaults)
        self._player_name = "Player"
        self._player_color = "#2e8b57"
        
        # Current game view
        self._current_game = "blackjack"
        self._game_view = None

        # Set app icon
        icon_path = ICONS_DIR / "spade.svg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._init_ui()

    def _init_ui(self) -> None:
        # Menu bar
        self._create_menu()

        # Right panel: console (top) + chat (bottom) - must be created BEFORE game view
        right_panel = QWidget(self)
        right_layout = QVBoxLayout(right_panel)

        # Console log
        self.console = QTextEdit(self)
        self.console.setReadOnly(True)
        self.console.setPlaceholderText("System messages and game log...")

        # Chat display area (read-only)
        self.chat = QTextEdit(self)
        self.chat.setReadOnly(True)
        self.chat.setPlaceholderText("Chat with AI will appear here...")

        # Chat input area
        chat_input_layout = QHBoxLayout()
        self.chat_input = QLineEdit(self)
        self.chat_input.setPlaceholderText("Type a message to AI...")
        self.chat_input.returnPressed.connect(self._send_chat_message)
        self.send_btn = QPushButton("Send", self)
        self.send_btn.clicked.connect(self._send_chat_message)
        chat_input_layout.addWidget(self.chat_input)
        chat_input_layout.addWidget(self.send_btn)

        right_layout.addWidget(QLabel("Console", self))
        right_layout.addWidget(self.console, stretch=2)
        right_layout.addWidget(QLabel("Chat", self))
        right_layout.addWidget(self.chat, stretch=3)
        right_layout.addLayout(chat_input_layout)

        # Put right panel into a dock widget so it can be resized
        dock = QDockWidget("Info", self)
        dock.setWidget(right_panel)
        dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        # Central widget: Game view (default: Blackjack) - after console is ready
        self._switch_game("blackjack")

        # Simple initial log message
        self.log_message("Application started.")

    def log_message(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.append(f"<span style='color:#888'>[{timestamp}]</span> {message}")

    def append_chat(self, sender: str, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Color names: Player uses custom color, AI=red
        if sender.lower() == "player" or sender == self._player_name:
            name_color = self._player_color
            display_name = self._player_name
        else:
            name_color = "#dc3545"  # Red for AI
            display_name = sender
        self.chat.append(
            f"<span style='color:#888'>[{timestamp}]</span> "
            f"<b style='color:{name_color}'>{display_name}:</b> {message}"
        )

    def _send_chat_message(self) -> None:
        """Send player message to AI and get response about the game."""
        message = self.chat_input.text().strip()
        if not message:
            return
        
        self.chat_input.clear()
        self.append_chat(self._player_name, message)
        
        # Ask AI to respond about the current game
        if self._game_view:
            self._game_view.ask_ai_chat(message)

    def _create_menu(self) -> None:
        menu_bar = self.menuBar()

        # Game menu
        game_menu = menu_bar.addMenu("Game")
        
        # Game selection submenu
        switch_menu = game_menu.addMenu("Switch Game")
        
        blackjack_action = QAction("♠ Blackjack", self)
        blackjack_action.triggered.connect(lambda: self._switch_game("blackjack"))
        switch_menu.addAction(blackjack_action)
        
        war_action = QAction("⚔️ War", self)
        war_action.triggered.connect(lambda: self._switch_game("war"))
        switch_menu.addAction(war_action)
        
        game_menu.addSeparator()
        
        new_game_action = QAction("New Game", self)
        new_game_action.triggered.connect(self._on_new_game)
        game_menu.addAction(new_game_action)

        # Statistics menu item
        game_menu.addSeparator()
        stats_action = QAction("Statistics...", self)
        stats_action.triggered.connect(self._open_statistics)
        game_menu.addAction(stats_action)

        # Settings menu
        settings_menu = menu_bar.addMenu("Settings")
        ai_settings_action = QAction("AI Settings...", self)
        ai_settings_action.triggered.connect(self._open_settings)
        settings_menu.addAction(ai_settings_action)

        game_settings_action = QAction("Game Settings...", self)
        game_settings_action.triggered.connect(self._open_game_settings)
        settings_menu.addAction(game_settings_action)

    def _switch_game(self, game: str) -> None:
        """Switch to a different card game."""
        if self._current_game == game and self._game_view:
            return
        
        self._current_game = game
        
        # Create new game view
        if game == "blackjack":
            self._game_view = BlackjackView(self)
            self.setWindowTitle("♠ AI Card Game - Blackjack")
        elif game == "war":
            self._game_view = WarView(self)
            self.setWindowTitle("⚔️ AI Card Game - War")
        
        # Connect logger and chat
        self._game_view.set_logger(self.log_message)
        self._game_view.set_chat_sink(self.append_chat)
        
        # Apply current settings
        self._game_view.set_player_name(self._player_name)
        self._game_view.set_player_color(self._player_color)
        
        self.setCentralWidget(self._game_view)
        self.log_message(f"Switched to {game.title()} game.")

    def _on_new_game(self) -> None:
        if self._game_view:
            self._game_view.on_new_game()

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self)
        dialog.exec()

    def _open_statistics(self) -> None:
        dialog = StatisticsDialog(self)
        dialog.exec()

    def _open_game_settings(self) -> None:
        if not self._game_view:
            return
        
        current_back = self._game_view.get_card_back()
        table_color = self._game_view.get_table_color()
        player_name = self._game_view.get_player_name()
        player_color = self._game_view.get_player_color()
        
        dialog = GameSettingsDialog(
            current_back, table_color, player_name, player_color, self
        )
        dialog.card_back_changed.connect(self._game_view.set_card_back)
        dialog.table_color_changed.connect(self._game_view.set_table_color)
        dialog.player_name_changed.connect(self._on_player_name_changed)
        dialog.player_color_changed.connect(self._on_player_color_changed)
        dialog.exec()

    def _on_player_name_changed(self, name: str) -> None:
        if self._game_view:
            self._game_view.set_player_name(name)
        self._player_name = name

    def _on_player_color_changed(self, color: str) -> None:
        if self._game_view:
            self._game_view.set_player_color(color)
        self._player_color = color
