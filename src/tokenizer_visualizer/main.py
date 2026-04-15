"""Entry point for tokenizer-visualizer."""

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from tokenizer_visualizer.app import TokenizerVisualizer
from tokenizer_visualizer.i18n import I18n


def main() -> int:
    app = QApplication(sys.argv)
    app.setFont(QFont("SF Pro Text", 14) if sys.platform == "darwin" else QFont("Segoe UI", 12))

    I18n().load()

    window = TokenizerVisualizer()
    window.show()

    app.styleHints().colorSchemeChanged.connect(window._on_theme_changed)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
