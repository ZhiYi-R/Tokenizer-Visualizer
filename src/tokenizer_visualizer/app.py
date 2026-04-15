"""Main application window."""

import pathlib
import sys
from typing import Optional

from tokenizers import Tokenizer
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from tokenizer_visualizer.i18n import tr, I18n
from tokenizer_visualizer.widgets import TokenCanvas, LineStatCanvas


class TokenizerVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self._tokenizer: Optional[Tokenizer] = None
        self._theme_mode: str = "system"

        self._setup_ui()
        self._load_default_tokenizers()
        self._apply_styles()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        header.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setObjectName("titleLabel")
        header.addWidget(self.title_label)

        header.addStretch()

        self.theme_combo = QComboBox()
        self.theme_combo.setMinimumWidth(100)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_selected)
        self.theme_label = QLabel()
        header.addWidget(self.theme_label)
        header.addWidget(self.theme_combo)

        self.lang_combo = QComboBox()
        self.lang_combo.setMinimumWidth(100)
        self.lang_combo.currentIndexChanged.connect(self._on_lang_selected)
        self.lang_label = QLabel()
        header.addWidget(self.lang_label)
        header.addWidget(self.lang_combo)

        self.tokenizer_combo = QComboBox()
        self.tokenizer_combo.setMinimumWidth(220)
        self.tokenizer_combo.currentIndexChanged.connect(self._on_tokenizer_changed)
        self.model_label = QLabel()
        header.addWidget(self.model_label)
        header.addWidget(self.tokenizer_combo)

        self.browse_btn = QPushButton()
        self.browse_btn.setObjectName("browseBtn")
        self.browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_btn.clicked.connect(self._browse_tokenizer)
        header.addWidget(self.browse_btn)

        main_layout.addLayout(header)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(8)
        splitter.setChildrenCollapsible(False)

        # Input section
        input_card = QWidget()
        input_card.setObjectName("card")
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(16, 16, 16, 16)
        input_layout.setSpacing(10)

        input_header = QHBoxLayout()
        self.input_label = QLabel()
        self.input_label.setObjectName("sectionLabel")
        input_header.addWidget(self.input_label)
        input_header.addStretch()
        self.count_label = QLabel()
        self.count_label.setObjectName("countLabel")
        input_header.addWidget(self.count_label)
        input_layout.addLayout(input_header)

        self.text_edit = QTextEdit()
        self.text_edit.textChanged.connect(self._tokenize)
        input_layout.addWidget(self.text_edit)

        splitter.addWidget(input_card)

        # Visualization section
        vis_card = QWidget()
        vis_card.setObjectName("card")
        vis_layout = QVBoxLayout(vis_card)
        vis_layout.setContentsMargins(16, 16, 16, 16)
        vis_layout.setSpacing(10)

        self.vis_label = QLabel()
        self.vis_label.setObjectName("sectionLabel")
        vis_layout.addWidget(self.vis_label)

        self.token_canvas = TokenCanvas()
        self.token_canvas.set_dark(self.is_dark_mode())

        vis_scroll = QScrollArea()
        vis_scroll.setWidgetResizable(True)
        vis_scroll.setWidget(self.token_canvas)
        vis_scroll.setFrameShape(QFrame.Shape.NoFrame)
        vis_layout.addWidget(vis_scroll)

        splitter.addWidget(vis_card)

        # Details section
        detail_card = QWidget()
        detail_card.setObjectName("card")
        detail_layout = QVBoxLayout(detail_card)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        detail_layout.setSpacing(10)

        self.detail_label = QLabel()
        self.detail_label.setObjectName("sectionLabel")
        detail_layout.addWidget(self.detail_label)

        self.stat_canvas = LineStatCanvas()
        self.stat_canvas.set_dark(self.is_dark_mode())

        detail_scroll = QScrollArea()
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setWidget(self.stat_canvas)
        detail_scroll.setFrameShape(QFrame.Shape.NoFrame)

        detail_layout.addWidget(detail_scroll)

        splitter.addWidget(detail_card)
        splitter.setSizes([250, 300, 250])

        main_layout.addWidget(splitter, 1)

        self.statusBar().showMessage(tr("status_ready"))

        self._populate_selectors()
        self._retranslate_ui()

    def _populate_selectors(self) -> None:
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        self.theme_combo.addItem(tr("theme_system"), "system")
        self.theme_combo.addItem(tr("theme_light"), "light")
        self.theme_combo.addItem(tr("theme_dark"), "dark")
        idx = self.theme_combo.findData(self._theme_mode)
        self.theme_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.theme_combo.blockSignals(False)

        self.lang_combo.blockSignals(True)
        self.lang_combo.clear()
        self.lang_combo.addItem(tr("lang_en"), "en")
        self.lang_combo.addItem(tr("lang_zh"), "zh")
        current_lang = I18n().lang
        idx = self.lang_combo.findData(current_lang)
        self.lang_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.lang_combo.blockSignals(False)

    def _retranslate_ui(self) -> None:
        self.setWindowTitle(tr("app_title"))
        self.title_label.setText(tr("app_title"))
        self.theme_label.setText(tr("theme_label"))
        self.lang_label.setText(tr("language_label"))
        self.model_label.setText(tr("model_label"))
        self.browse_btn.setText(tr("browse_button"))
        self.input_label.setText(tr("input_text_label"))
        # Preserve current count if available
        count_text = self.count_label.text()
        try:
            count_val = int(count_text.split(":")[-1].strip())
        except Exception:
            count_val = 0
        self.count_label.setText(tr("tokens_count", count=count_val))
        self.vis_label.setText(tr("visualized_tokens_label"))
        self.detail_label.setText(tr("line_statistics_label"))
        self.text_edit.setPlaceholderText(tr("placeholder_input"))

        # Refresh combo item texts without changing selection
        theme_items = {
            "system": tr("theme_system"),
            "light": tr("theme_light"),
            "dark": tr("theme_dark"),
        }
        self.theme_combo.blockSignals(True)
        for i in range(self.theme_combo.count()):
            data = self.theme_combo.itemData(i)
            self.theme_combo.setItemText(i, theme_items.get(data, data))
        self.theme_combo.blockSignals(False)

        lang_items = {
            "en": tr("lang_en"),
            "zh": tr("lang_zh"),
        }
        self.lang_combo.blockSignals(True)
        for i in range(self.lang_combo.count()):
            data = self.lang_combo.itemData(i)
            self.lang_combo.setItemText(i, lang_items.get(data, data))
        self.lang_combo.blockSignals(False)

    def is_dark_mode(self) -> bool:
        if self._theme_mode == "light":
            return False
        if self._theme_mode == "dark":
            return True
        scheme = QApplication.styleHints().colorScheme()
        if scheme != Qt.ColorScheme.Unknown:
            return scheme == Qt.ColorScheme.Dark
        bg = self.palette().color(QPalette.ColorRole.Window)
        return bg.lightness() < 128

    def _update_app_palette(self, dark: bool) -> None:
        app = QApplication.instance()
        if app is None:
            return
        palette = QPalette()
        if dark:
            palette.setColor(QPalette.ColorRole.Window, QColor("#16161e"))
            palette.setColor(QPalette.ColorRole.WindowText, QColor("#c0caf5"))
            palette.setColor(QPalette.ColorRole.Base, QColor("#1f1f28"))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#262636"))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#1f1f28"))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#c0caf5"))
            palette.setColor(QPalette.ColorRole.Text, QColor("#c0caf5"))
            palette.setColor(QPalette.ColorRole.Button, QColor("#1f1f28"))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor("#c0caf5"))
            palette.setColor(QPalette.ColorRole.BrightText, QColor("#ff0000"))
            palette.setColor(QPalette.ColorRole.Highlight, QColor("#283457"))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#c0caf5"))
        else:
            palette.setColor(QPalette.ColorRole.Window, QColor("#f5f6fa"))
            palette.setColor(QPalette.ColorRole.WindowText, QColor("#2c3e50"))
            palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#fafbfc"))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#2c3e50"))
            palette.setColor(QPalette.ColorRole.Text, QColor("#2c3e50"))
            palette.setColor(QPalette.ColorRole.Button, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor("#2c3e50"))
            palette.setColor(QPalette.ColorRole.BrightText, QColor("#ff0000"))
            palette.setColor(QPalette.ColorRole.Highlight, QColor("#dfe6e9"))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#2c3e50"))
        app.setPalette(palette)

    def _apply_styles(self) -> None:
        dark = self.is_dark_mode()
        self._update_app_palette(dark)
        self.token_canvas.set_dark(dark)
        self.stat_canvas.set_dark(dark)
        if dark:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #16161e;
                }
                #titleLabel {
                    font-size: 22px;
                    font-weight: bold;
                    color: #c0caf5;
                }
                #sectionLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: #a9b1d6;
                }
                #countLabel {
                    font-size: 13px;
                    color: #7aa2f7;
                }
                #card {
                    background-color: #1f1f28;
                    border-radius: 14px;
                }
                QComboBox, QPushButton, QTextEdit {
                    font-size: 14px;
                }
                QComboBox {
                    padding: 6px 10px;
                    border: 1px solid #3b3b4f;
                    border-radius: 8px;
                    background-color: #1f1f28;
                    color: #c0caf5;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 24px;
                }
                QComboBox QAbstractItemView {
                    background-color: #1f1f28;
                    color: #c0caf5;
                    selection-background-color: #292e42;
                    border: 1px solid #3b3b4f;
                }
                QTextEdit {
                    border: 1px solid #3b3b4f;
                    border-radius: 10px;
                    padding: 10px;
                    background-color: #262636;
                    color: #c0caf5;
                    selection-background-color: #283457;
                }
                QTextEdit QScrollBar:vertical, QTextEdit QScrollBar:horizontal {
                    background: #1f1f28;
                }
                #browseBtn {
                    background-color: #7aa2f7;
                    color: #16161e;
                    border: none;
                    border-radius: 8px;
                    padding: 6px 16px;
                    font-weight: 600;
                }
                #browseBtn:hover {
                    background-color: #bb9af7;
                }
                #browseBtn:pressed {
                    background-color: #565f89;
                }
                QScrollArea {
                    background: transparent;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f5f6fa;
                }
                #titleLabel {
                    font-size: 22px;
                    font-weight: bold;
                    color: #2c3e50;
                }
                #sectionLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: #34495e;
                }
                #countLabel {
                    font-size: 13px;
                    color: #7f8c8d;
                }
                #card {
                    background-color: #ffffff;
                    border-radius: 14px;
                }
                QComboBox, QPushButton, QTextEdit {
                    font-size: 14px;
                }
                QComboBox {
                    padding: 6px 10px;
                    border: 1px solid #dcdde1;
                    border-radius: 8px;
                    background-color: #ffffff;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 24px;
                }
                QTextEdit {
                    border: 1px solid #e1e4e8;
                    border-radius: 10px;
                    padding: 10px;
                    background-color: #fafbfc;
                    selection-background-color: #dfe6e9;
                }
                #browseBtn {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 6px 16px;
                    font-weight: 500;
                }
                #browseBtn:hover {
                    background-color: #2980b9;
                }
                #browseBtn:pressed {
                    background-color: #2471a3;
                }
                QScrollArea {
                    background: transparent;
                }
            """)

    @staticmethod
    def _find_tokenizer_dir() -> pathlib.Path:
        # When frozen (Nuitka), look next to the executable first (external data dir)
        candidates = [
            pathlib.Path(sys.executable).parent,
            pathlib.Path(sys.argv[0]).parent.resolve(),
        ]
        for cand in candidates:
            ext_path = cand / "tokenizer"
            if ext_path.exists():
                return ext_path
        # Development layout: src/tokenizer_visualizer/app.py -> project_root/tokenizer
        dev_path = pathlib.Path(__file__).parent.parent.parent / "tokenizer"
        if dev_path.exists():
            return dev_path
        # Fallback frozen internal layout
        return pathlib.Path(__file__).parent.parent / "tokenizer"

    def _scan_tokenizer_dir(self) -> dict[str, str]:
        base = self._find_tokenizer_dir()
        models: dict[str, str] = {}
        if base.exists():
            for path in sorted(base.glob("*.json")):
                model_id = path.stem
                models[model_id] = str(path)
        return models

    def _load_default_tokenizers(self) -> None:
        models = self._scan_tokenizer_dir()
        for name, path in models.items():
            self.tokenizer_combo.addItem(name, path)
        if self.tokenizer_combo.count() > 0:
            self._on_tokenizer_changed(0)

    def _on_tokenizer_changed(self, index: int) -> None:
        path = self.tokenizer_combo.itemData(index)
        if not path:
            return
        try:
            self._tokenizer = Tokenizer.from_file(path)
            self.statusBar().showMessage(
                f"{self.tokenizer_combo.currentText()}"
            )
        except Exception as exc:
            QMessageBox.critical(self, tr("app_title"), f"{tr('error_load_tokenizer')}\n{exc}")
            self._tokenizer = None
        self._tokenize()

    def _browse_tokenizer(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, tr("dialog_select_tokenizer"), "", tr("dialog_json_filter")
        )
        if path:
            name = pathlib.Path(path).stem
            self.tokenizer_combo.addItem(name, path)
            self.tokenizer_combo.setCurrentIndex(self.tokenizer_combo.count() - 1)

    def _on_theme_selected(self, index: int) -> None:
        mode = self.theme_combo.itemData(index)
        if mode:
            self._theme_mode = mode
            self._apply_styles()
            self._tokenize()

    def _on_lang_selected(self, index: int) -> None:
        lang = self.lang_combo.itemData(index)
        if lang:
            I18n().load(lang)
            self._retranslate_ui()
            self._populate_selectors()
            self._tokenize()

    def _on_theme_changed(self) -> None:
        if self._theme_mode == "system":
            self._apply_styles()
            self._tokenize()

    def _tokenize(self) -> None:
        if self._tokenizer is None:
            return

        text = self.text_edit.toPlainText()
        if not text:
            self.token_canvas.set_data("", [], [])
            self.stat_canvas.set_data([])
            self.count_label.setText(tr("tokens_count", count=0))
            return

        encoding = self._tokenizer.encode(text)
        offsets = encoding.offsets
        ids = encoding.ids

        self.token_canvas.set_data(text, offsets, ids)
        visual_stats = self.token_canvas.get_visual_line_stats()
        self.stat_canvas.set_data(visual_stats)

        self.count_label.setText(tr("tokens_count", count=len(ids)))
        self.statusBar().showMessage(tr("status_tokens_generated", count=len(ids)))
