"""Statistics dialog showing game history and win/loss stats."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QGroupBox,
    QFrame,
)
from PySide6.QtCore import Qt

from ..db.database import get_statistics


class StatisticsDialog(QDialog):
    """Dialog showing game statistics and history."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("♠ Statistics")
        self.setMinimumSize(500, 400)
        self._init_ui()
        self._load_stats()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Summary stats group
        summary_group = QGroupBox("Summary")
        summary_layout = QHBoxLayout(summary_group)

        self.total_label = QLabel("Total: 0")
        self.wins_label = QLabel("Wins: 0")
        self.losses_label = QLabel("Losses: 0")
        self.pushes_label = QLabel("Pushes: 0")
        self.winrate_label = QLabel("Win Rate: 0%")

        self.wins_label.setStyleSheet("color: #2e8b57; font-weight: bold;")
        self.losses_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        self.winrate_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        summary_layout.addWidget(self.total_label)
        summary_layout.addWidget(self.wins_label)
        summary_layout.addWidget(self.losses_label)
        summary_layout.addWidget(self.pushes_label)
        summary_layout.addWidget(self.winrate_label)

        layout.addWidget(summary_group)

        # Recent games table
        history_group = QGroupBox("Recent Games")
        history_layout = QVBoxLayout(history_group)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date", "Game", "Result", "Your Score", "AI Score"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        history_layout.addWidget(self.table)
        layout.addWidget(history_group)

        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _load_stats(self) -> None:
        stats = get_statistics()

        self.total_label.setText(f"Total: {stats['total_games']}")
        self.wins_label.setText(f"Wins: {stats['wins']}")
        self.losses_label.setText(f"Losses: {stats['losses']}")
        self.pushes_label.setText(f"Pushes: {stats['pushes']}")
        self.winrate_label.setText(f"Win Rate: {stats['win_rate']:.1f}%")

        # Populate table
        self.table.setRowCount(len(stats["recent_games"]))
        for row, game in enumerate(stats["recent_games"]):
            # Format date
            date_str = game["created_at"][:10] if game["created_at"] else ""
            
            self.table.setItem(row, 0, QTableWidgetItem(date_str))
            self.table.setItem(row, 1, QTableWidgetItem(game["game_type"]))
            
            result_item = QTableWidgetItem(game["result"].upper())
            if game["result"] == "win":
                result_item.setForeground(Qt.green)
            elif game["result"] == "loss":
                result_item.setForeground(Qt.red)
            self.table.setItem(row, 2, result_item)
            
            self.table.setItem(row, 3, QTableWidgetItem(str(game["player_final_score"] or "")))
            self.table.setItem(row, 4, QTableWidgetItem(str(game["ai_final_score"] or "")))

        self.table.resizeColumnsToContents()
