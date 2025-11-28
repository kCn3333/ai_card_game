from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QGroupBox,
    QFormLayout,
)
from PySide6.QtCore import QThread, Signal, QObject

from ..config import settings
from ..ai.client import AIClient


class TestConnectionWorker(QObject):
    """Worker to test AI connection in background."""
    success = Signal(str)
    error = Signal(str)

    def __init__(self, host: str, model: str) -> None:
        super().__init__()
        self.host = host
        self.model = model

    def run(self) -> None:
        try:
            client = AIClient(host=self.host, model=self.model)
            # Send a tiny test message
            resp = client.chat([{"role": "user", "content": "Say 'OK' if you can hear me."}])
            self.success.emit(f"Connection successful! Response: {resp.content[:100]}")
        except Exception as e:
            self.error.emit(str(e))


class SettingsDialog(QDialog):
    """Dialog for configuring AI settings."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI Settings")
        self.setMinimumWidth(400)

        self._thread: QThread | None = None
        self._worker: TestConnectionWorker | None = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # AI Connection group
        ai_group = QGroupBox("AI Connection")
        ai_layout = QFormLayout(ai_group)

        self.host_edit = QLineEdit(self)
        self.host_edit.setText(settings.DEFAULT_AI_HOST)
        self.host_edit.setPlaceholderText("http://127.0.0.1:11434")

        self.model_edit = QLineEdit(self)
        self.model_edit.setText(settings.DEFAULT_AI_MODEL)
        self.model_edit.setPlaceholderText("gemma3:4b")

        ai_layout.addRow("Host:", self.host_edit)
        ai_layout.addRow("Model:", self.model_edit)

        layout.addWidget(ai_group)

        # Test connection button
        self.test_btn = QPushButton("Test Connection", self)
        self.test_btn.clicked.connect(self._on_test_connection)
        layout.addWidget(self.test_btn)

        # Status label
        self.status_label = QLabel("", self)
        layout.addWidget(self.status_label)

        # Buttons row
        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Save", self)
        self.cancel_btn = QPushButton("Cancel", self)

        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(self.reject)

        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

    def _on_test_connection(self) -> None:
        host = self.host_edit.text().strip()
        model = self.model_edit.text().strip()

        if not host or not model:
            QMessageBox.warning(self, "Missing Info", "Please enter both host and model.")
            return

        self.status_label.setText("Testing connection...")
        self.test_btn.setEnabled(False)

        self._thread = QThread()
        self._worker = TestConnectionWorker(host, model)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.success.connect(self._on_test_success)
        self._worker.error.connect(self._on_test_error)
        self._worker.success.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)

        self._thread.start()

    def _on_test_success(self, message: str) -> None:
        self.status_label.setText("✓ " + message[:80])
        self.test_btn.setEnabled(True)
        QMessageBox.information(self, "Success", message)

    def _on_test_error(self, error: str) -> None:
        self.status_label.setText("✗ Connection failed")
        self.test_btn.setEnabled(True)
        QMessageBox.critical(self, "Connection Failed", f"Error: {error}")

    def _on_save(self) -> None:
        # For now, just update the module-level defaults (in-memory)
        # Later we'll persist to SQLite
        host = self.host_edit.text().strip()
        model = self.model_edit.text().strip()

        if host:
            settings.DEFAULT_AI_HOST = host
        if model:
            settings.DEFAULT_AI_MODEL = model

        self.accept()
