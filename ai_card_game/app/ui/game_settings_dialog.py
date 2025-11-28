"""Game Settings dialog for customizing game appearance."""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QColorDialog,
    QFrame,
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

BACKS_DIR = Path(__file__).resolve().parent.parent / "assets" / "backs"


# Default colors
DEFAULT_TABLE_COLOR = "#0d5c2e"  # Dark green felt
DEFAULT_PLAYER_NAME = "Player"
DEFAULT_PLAYER_COLOR = "#2e8b57"  # Sea green


class GameSettingsDialog(QDialog):
    """Dialog for game settings like card back selection."""
    
    card_back_changed = Signal(str)  # Emits the new card back filename
    table_color_changed = Signal(str)  # Emits hex color string
    player_name_changed = Signal(str)  # Emits new player name
    player_color_changed = Signal(str)  # Emits hex color string

    def __init__(
        self,
        current_back: str = "back.svg",
        table_color: str = DEFAULT_TABLE_COLOR,
        player_name: str = DEFAULT_PLAYER_NAME,
        player_color: str = DEFAULT_PLAYER_COLOR,
        parent=None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("♠ Game Settings")
        self.setMinimumSize(500, 500)
        self.current_back = current_back
        self.table_color = table_color
        self.player_name = player_name
        self.player_color = player_color
        self._init_ui()
        self._load_backs()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Card back selection group
        back_group = QGroupBox("Card Back Design")
        back_layout = QHBoxLayout(back_group)

        # List of available backs
        self.back_list = QListWidget()
        self.back_list.setMaximumWidth(180)
        self.back_list.currentItemChanged.connect(self._on_back_selected)
        back_layout.addWidget(self.back_list)

        # Preview area
        preview_layout = QVBoxLayout()
        preview_label = QLabel("Preview:")
        preview_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(preview_label)

        self.preview_widget = QSvgWidget()
        self.preview_widget.setFixedSize(120, 168)
        preview_layout.addWidget(self.preview_widget, alignment=Qt.AlignCenter)
        preview_layout.addStretch()

        back_layout.addLayout(preview_layout)
        layout.addWidget(back_group)

        # Table color group
        table_group = QGroupBox("Table Color")
        table_layout = QHBoxLayout(table_group)
        
        self.table_color_preview = QFrame()
        self.table_color_preview.setFixedSize(60, 30)
        self.table_color_preview.setStyleSheet(
            f"background-color: {self.table_color}; border: 1px solid #333; border-radius: 4px;"
        )
        table_layout.addWidget(self.table_color_preview)
        
        table_color_btn = QPushButton("Choose Color...")
        table_color_btn.clicked.connect(self._pick_table_color)
        table_layout.addWidget(table_color_btn)
        table_layout.addStretch()
        
        layout.addWidget(table_group)

        # Player settings group
        player_group = QGroupBox("Player Settings")
        player_layout = QVBoxLayout(player_group)
        
        # Player name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.player_name_input = QLineEdit(self.player_name)
        self.player_name_input.setMaxLength(20)
        name_layout.addWidget(self.player_name_input)
        player_layout.addLayout(name_layout)
        
        # Player color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Name Color:"))
        
        self.player_color_preview = QFrame()
        self.player_color_preview.setFixedSize(60, 30)
        self.player_color_preview.setStyleSheet(
            f"background-color: {self.player_color}; border: 1px solid #333; border-radius: 4px;"
        )
        color_layout.addWidget(self.player_color_preview)
        
        player_color_btn = QPushButton("Choose Color...")
        player_color_btn.clicked.connect(self._pick_player_color)
        color_layout.addWidget(player_color_btn)
        color_layout.addStretch()
        player_layout.addLayout(color_layout)
        
        layout.addWidget(player_group)

        # Info label
        info_label = QLabel(
            "<i>Add more card back designs by placing SVG files in:<br>"
            f"{BACKS_DIR}</i>"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(info_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._apply_settings)
        btn_layout.addWidget(apply_btn)
        
        layout.addLayout(btn_layout)

    def _load_backs(self) -> None:
        """Load available card back designs from the backs folder."""
        if not BACKS_DIR.exists():
            return

        svg_files = sorted(BACKS_DIR.glob("*.svg"))
        for svg_file in svg_files:
            item = QListWidgetItem(svg_file.stem)
            item.setData(Qt.UserRole, svg_file.name)
            self.back_list.addItem(item)
            
            # Select current back
            if svg_file.name == self.current_back:
                self.back_list.setCurrentItem(item)

        # If no item selected, select first
        if self.back_list.currentItem() is None and self.back_list.count() > 0:
            self.back_list.setCurrentRow(0)

    def _on_back_selected(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        """Update preview when a back is selected."""
        if current is None:
            return
        
        filename = current.data(Qt.UserRole)
        back_path = BACKS_DIR / filename
        if back_path.exists():
            self.preview_widget.load(str(back_path))

    def _pick_table_color(self) -> None:
        """Open color picker for table color."""
        color = QColorDialog.getColor(QColor(self.table_color), self, "Choose Table Color")
        if color.isValid():
            self.table_color = color.name()
            self.table_color_preview.setStyleSheet(
                f"background-color: {self.table_color}; border: 1px solid #333; border-radius: 4px;"
            )

    def _pick_player_color(self) -> None:
        """Open color picker for player name color."""
        color = QColorDialog.getColor(QColor(self.player_color), self, "Choose Player Name Color")
        if color.isValid():
            self.player_color = color.name()
            self.player_color_preview.setStyleSheet(
                f"background-color: {self.player_color}; border: 1px solid #333; border-radius: 4px;"
            )

    def _apply_settings(self) -> None:
        """Apply the selected settings."""
        # Card back
        current = self.back_list.currentItem()
        if current:
            filename = current.data(Qt.UserRole)
            self.card_back_changed.emit(filename)
        
        # Table color
        self.table_color_changed.emit(self.table_color)
        
        # Player name and color
        new_name = self.player_name_input.text().strip() or DEFAULT_PLAYER_NAME
        self.player_name_changed.emit(new_name)
        self.player_color_changed.emit(self.player_color)
        
        self.accept()

    def get_selected_back(self) -> str:
        """Return the currently selected card back filename."""
        current = self.back_list.currentItem()
        if current:
            return current.data(Qt.UserRole)
        return "back.svg"
