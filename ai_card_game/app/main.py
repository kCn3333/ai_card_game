import sys
from PySide6.QtWidgets import QApplication

from .ui.main_window import MainWindow
from .db.database import init_db


def main() -> None:
    """Application entry point."""
    # Initialize database (settings + stats tables)
    init_db()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
