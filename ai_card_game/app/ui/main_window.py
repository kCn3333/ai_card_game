from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QDockWidget,
    QTextEdit,
    QSplitter,
    QLabel,
)
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    """Main window: game area + right panel (console + chat)."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI Card Game")
        self.resize(1200, 800)

        self._init_ui()

    def _init_ui(self) -> None:
        # Central widget: for now just placeholder label (Blackjack table later)
        central = QWidget(self)
        central_layout = QVBoxLayout(central)
        central_layout.addWidget(QLabel("Game table will be here (Blackjack view)", self))
        self.setCentralWidget(central)

        # Right panel: console (top) + chat (bottom)
        right_panel = QWidget(self)
        right_layout = QVBoxLayout(right_panel)

        # Console log
        self.console = QTextEdit(self)
        self.console.setReadOnly(True)
        self.console.setPlaceholderText("System messages and game log...")

        # Chat area
        self.chat = QTextEdit(self)
        self.chat.setPlaceholderText("Chat with AI will appear here...")

        right_layout.addWidget(QLabel("Console", self))
        right_layout.addWidget(self.console, stretch=2)
        right_layout.addWidget(QLabel("Chat", self))
        right_layout.addWidget(self.chat, stretch=3)

        # Put right panel into a dock widget so it can be resized
        dock = QDockWidget("Info", self)
        dock.setWidget(right_panel)
        dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        # Simple initial log message
        self.log_message("Application started.")

    def log_message(self, message: str) -> None:
        self.console.append(message)
