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
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import Qt, Signal

BACKS_DIR = Path(__file__).resolve().parent.parent / "assets" / "backs"


class GameSettingsDialog(QDialog):
    """Dialog for game settings like card back selection."""
    
    card_back_changed = Signal(str)  # Emits the new card back filename

    def __init__(self, current_back: str = "back.svg", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("♠ Game Settings")
        self.setMinimumSize(450, 350)
        self.current_back = current_back
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

    def _apply_settings(self) -> None:
        """Apply the selected settings."""
        current = self.back_list.currentItem()
        if current:
            filename = current.data(Qt.UserRole)
            self.card_back_changed.emit(filename)
        self.accept()

    def get_selected_back(self) -> str:
        """Return the currently selected card back filename."""
        current = self.back_list.currentItem()
        if current:
            return current.data(Qt.UserRole)
        return "back.svg"
