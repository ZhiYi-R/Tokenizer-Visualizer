"""Custom widgets for tokenizer visualization."""

import html
from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import Qt, QSize, QPoint, QRect
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPaintEvent, QMouseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QWidget,
)

from tokenizer_visualizer.i18n import tr
from tokenizer_visualizer.utils import PALETTE, pick_foreground, normalize_offsets


@dataclass
class _CanvasItem:
    rect: QRect
    text: str
    token_id: Optional[int]
    color_index: int
    is_token: bool
    bg_color: Optional[QColor] = None
    fg_color: Optional[QColor] = None
    is_newline_marker: bool = False


class TokenCanvas(QWidget):
    """High-performance canvas that draws tokens directly without creating thousands of QLabel widgets."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._items: list[_CanvasItem] = []
        self._visual_line_stats: list[int] = []
        self._hover_index: int = -1
        self._dark: bool = False
        self._h_space: int = 8
        self._v_space: int = 10
        self._margin: int = 8
        self._font: QFont = QFont("SF Mono", 13) if __import__("sys").platform == "darwin" else QFont("Consolas", 12)
        self._fm: QFontMetrics = QFontMetrics(self._font)
        self.setMouseTracking(True)
        self.setMinimumHeight(40)

    def set_dark(self, dark: bool) -> None:
        self._dark = dark
        self.update()

    def get_visual_line_stats(self) -> list[int]:
        return list(self._visual_line_stats)

    def _text_size(self, text: str) -> QSize:
        w = max(self._fm.horizontalAdvance(text), 16)
        h = self._fm.height()
        return QSize(w + 16, h + 10)

    def set_data(self, text: str, offsets: list[tuple[int, int]], ids: list[int]) -> None:
        try:
            offsets = normalize_offsets(text, offsets)
        except ValueError:
            pass

        self._items.clear()
        last_end = 0
        color_index = 0

        gap_color = QColor("#565f89") if self._dark else QColor("#bdc3c7")
        text_color = QColor("#c0caf5") if self._dark else QColor("#2c3e50")

        def add_gap_item(gap_text: str, is_whitespace: bool) -> None:
            if not gap_text:
                return
            if is_whitespace:
                display = gap_text.replace(" ", "\u00b7").replace("\t", "\u2192")
            else:
                display = gap_text
            size = self._text_size(display)
            self._items.append(
                _CanvasItem(
                    rect=QRect(QPoint(0, 0), size),
                    text=display,
                    token_id=None,
                    color_index=-1,
                    is_token=False,
                    fg_color=gap_color if is_whitespace else text_color,
                )
            )

        def add_newline_marker() -> None:
            size = self._text_size("\u23ce")
            self._items.append(
                _CanvasItem(
                    rect=QRect(QPoint(0, 0), size),
                    text="\u23ce",
                    token_id=None,
                    color_index=-1,
                    is_token=False,
                    fg_color=gap_color,
                    is_newline_marker=True,
                )
            )

        def add_token(token_text: str, token_id: int, idx: int) -> None:
            display = token_text.replace(" ", "\u00a0").replace("\n", "\u23ce")
            bg = QColor(*PALETTE[idx % len(PALETTE)])
            fg = QColor(*pick_foreground(PALETTE[idx % len(PALETTE)]))
            size = self._text_size(display)
            self._items.append(
                _CanvasItem(
                    rect=QRect(QPoint(0, 0), size),
                    text=display,
                    token_id=token_id,
                    color_index=idx,
                    is_token=True,
                    bg_color=bg,
                    fg_color=fg,
                )
            )

        def process_gap(gap: str, pure_whitespace: bool) -> None:
            if pure_whitespace:
                parts = gap.split("\n")
                for i, part in enumerate(parts):
                    if i > 0:
                        add_newline_marker()
                        self._items.append(
                            _CanvasItem(
                                rect=QRect(QPoint(0, 0), QSize(0, 20)),
                                text="",
                                token_id=None,
                                color_index=-1,
                                is_token=False,
                                fg_color=None,
                            )
                        )
                    if part:
                        add_gap_item(part, True)
            else:
                if "\n" in gap:
                    parts = gap.split("\n")
                    for i, part in enumerate(parts):
                        if i > 0:
                            self._items.append(
                                _CanvasItem(
                                    rect=QRect(QPoint(0, 0), QSize(0, 20)),
                                    text="",
                                    token_id=None,
                                    color_index=-1,
                                    is_token=False,
                                    fg_color=None,
                                )
                            )
                        if part:
                            add_gap_item(part, False)
                else:
                    add_gap_item(gap, False)

        for i, (start, end) in enumerate(offsets):
            if (start, end) == (0, 0):
                continue
            if start < last_end:
                continue

            if start > last_end:
                gap = text[last_end:start]
                process_gap(gap, gap.strip() == "")

            span = text[start:end]
            add_token(span, ids[i], color_index)

            for _ in range(span.count("\n")):
                self._items.append(
                    _CanvasItem(
                        rect=QRect(QPoint(0, 0), QSize(0, 20)),
                        text="",
                        token_id=None,
                        color_index=-1,
                        is_token=False,
                        fg_color=None,
                    )
                )

            last_end = end
            color_index += 1

        if last_end < len(text):
            gap = text[last_end:]
            parts = gap.split("\n")
            for i, part in enumerate(parts):
                if i > 0:
                    add_newline_marker()
                    self._items.append(
                        _CanvasItem(
                            rect=QRect(QPoint(0, 0), QSize(0, 20)),
                            text="",
                            token_id=None,
                            color_index=-1,
                            is_token=False,
                            fg_color=None,
                        )
                    )
                if part:
                    add_gap_item(part, True)

        self._relayout()

    def _relayout(self) -> None:
        self._visual_line_stats = []
        current_line_tokens = 0
        x = self._margin
        y = self._margin
        line_height = 0

        for item in self._items:
            if item.rect.width() == 0 and item.rect.height() == 20:
                # Explicit line break (from \n in text)
                item.rect.moveTopLeft(QPoint(x, y))
                self._visual_line_stats.append(current_line_tokens)
                current_line_tokens = 0
                x = self._margin
                y += max(line_height, 20) + self._v_space
                line_height = 0
                continue

            w = item.rect.width()
            h = item.rect.height()

            if x + w > self.width() - self._margin and x > self._margin and line_height > 0:
                # Auto wrap
                self._visual_line_stats.append(current_line_tokens)
                current_line_tokens = 0
                x = self._margin
                y += line_height + self._v_space
                line_height = 0

            item.rect.moveTopLeft(QPoint(x, y))
            x += w + self._h_space
            line_height = max(line_height, h)

            if item.is_token:
                current_line_tokens += 1

        self._visual_line_stats.append(current_line_tokens)
        total_height = y + line_height + self._margin if self._items else self._margin * 2
        self.setMinimumHeight(total_height)
        self.update()

    def resizeEvent(self, event) -> None:
        self._relayout()
        super().resizeEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self._font)

        # Fill entire widget background to avoid partial-erase artifacts
        bg = QColor("#1f1f28") if self._dark else QColor("#ffffff")
        painter.fillRect(self.rect(), bg)

        clip = event.rect().adjusted(-2, -2, 2, 2)
        clip_top = clip.top()
        clip_bottom = clip.bottom()

        for item in self._items:
            if item.rect.bottom() < clip_top:
                continue
            if item.rect.top() > clip_bottom:
                break

            if item.is_token and item.bg_color and item.fg_color:
                rect = item.rect.adjusted(2, 2, -2, -2)
                radius = min(10, rect.width() // 2, rect.height() // 2)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(item.bg_color)
                painter.drawRoundedRect(rect, radius, radius)
                painter.setPen(item.fg_color)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                text_rect = rect.adjusted(4, 2, -4, -2)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, item.text)
            elif item.fg_color:
                painter.setPen(item.fg_color)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                text_rect = item.rect.adjusted(0, 5, 0, -5)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, item.text)

        painter.end()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.pos()
        found = -1
        for idx, item in enumerate(self._items):
            if item.is_token and item.rect.contains(pos):
                found = idx
                break

        if found != self._hover_index:
            self._hover_index = found
            if found >= 0:
                item = self._items[found]
                tooltip = tr(
                    "tooltip_token",
                    index=item.color_index,
                    text=html.escape(repr(item.text.replace("\u00a0", " ").replace("\u23ce", "\n"))),
                    id=item.token_id,
                )
                self.setToolTip(tooltip)
            else:
                self.setToolTip("")
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover_index = -1
        self.setToolTip("")
        super().leaveEvent(event)


class LineStatCanvas(QWidget):
    """High-performance canvas that draws line-statistics badges directly."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._line_counts: list[int] = []
        self._dark: bool = False
        self._cols: int = 3
        self._margin: int = 8
        self._h_space: int = 16
        self._v_space: int = 8
        self._font: QFont = QFont("SF Mono", 11) if __import__("sys").platform == "darwin" else QFont("Consolas", 10)
        self._fm: QFontMetrics = QFontMetrics(self._font)
        self._badge_height: int = 0
        self.setMinimumHeight(40)

    def set_dark(self, dark: bool) -> None:
        self._dark = dark
        self.update()

    def set_data(self, line_counts: list[int]) -> None:
        self._line_counts = line_counts
        self._compute_badge_size()
        self._relayout()

    def _compute_badge_size(self) -> None:
        """Compute badge height; width is determined dynamically per paint."""
        self._badge_height = self._fm.height() + 14

    def _relayout(self) -> None:
        self.updateGeometry()
        total_rows = (len(self._line_counts) + self._cols - 1) // self._cols if self._cols else 0
        total_height = self._margin * 2 + total_rows * self._badge_height + max(0, total_rows - 1) * self._v_space
        self.setMinimumHeight(total_height)
        self.update()

    def resizeEvent(self, event) -> None:
        self._relayout()
        super().resizeEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self._font)

        bg = QColor("#1f1f28") if self._dark else QColor("#ffffff")
        painter.fillRect(event.rect(), bg)

        accent = QColor("#7aa2f7") if self._dark else QColor("#3498db")
        text_col = QColor("#16161e") if self._dark else QColor("#ffffff")
        info_col = QColor("#c0caf5") if self._dark else QColor("#2c2c2c")
        count_col = QColor("#a9b1d6") if self._dark else QColor("#7f8c8d")

        clip = event.rect()
        content_width = self.width() - self._margin * 2
        col_step = (content_width - (self._cols - 1) * self._h_space) // self._cols if self._cols else content_width
        badge_width = max(140, col_step)

        for li, count in enumerate(self._line_counts):
            row = li // self._cols
            col = li % self._cols
            x = self._margin + col * (badge_width + self._h_space)
            y = self._margin + row * (self._badge_height + self._v_space)
            rect = QRect(x, y, badge_width, self._badge_height)

            if rect.bottom() < clip.top():
                continue
            if rect.top() > clip.bottom():
                break

            # Draw badge background
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#292e42") if self._dark else QColor("#f0f2f5"))
            painter.drawRoundedRect(rect.adjusted(0, 0, -4, 0), 8, 8)

            # Line number pill
            pill_rect = QRect(x + 6, y + 4, 26, rect.height() - 8)
            painter.setBrush(accent)
            painter.drawRoundedRect(pill_rect, 5, 5)
            painter.setPen(text_col)
            painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, str(li + 1))

            # Info text
            painter.setPen(info_col)
            info_text = tr("line_n", n=li + 1)
            info_x = pill_rect.right() + 8
            info_y = y + rect.height() // 2
            painter.drawText(info_x, info_y + self._fm.ascent() // 2 - 1, info_text)

            # Count text (right aligned inside badge)
            token_word = tr("token_singular") if count == 1 else tr("token_plural")
            count_text = f"{count} {token_word}"
            painter.setPen(count_col)
            count_width = self._fm.horizontalAdvance(count_text)
            count_x = x + badge_width - 10 - count_width
            painter.drawText(count_x, info_y + self._fm.ascent() // 2 - 1, count_text)

        painter.end()
