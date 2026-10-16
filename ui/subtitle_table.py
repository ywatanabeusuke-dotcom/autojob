from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QMenu, QAbstractItemView, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
import web_search


COL_IDX = 0
COL_START = 1
COL_END = 2
COL_TEXT = 3
HEADERS = ["#", "開始", "終了", "テキスト"]


def _fmt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    if h:
        return f"{h}:{m:02d}:{s:06.3f}"
    return f"{m:02d}:{s:06.3f}"


def _parse(text: str) -> float:
    parts = text.replace(",", ".").split(":")
    try:
        if len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        return float(parts[0])
    except ValueError:
        return 0.0


class SubtitleTable(QTableWidget):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(0, 4, parent)
        self.setHorizontalHeaderLabels(HEADERS)
        self.horizontalHeader().setSectionResizeMode(COL_TEXT, QHeaderView.ResizeMode.Stretch)
        for col in (COL_IDX, COL_START, COL_END):
            self.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.itemChanged.connect(lambda _: self.data_changed.emit())
        self._font_size = 11

    def load_subtitles(self, subtitles):
        self.blockSignals(True)
        self.setRowCount(0)
        for sub in subtitles:
            self._append_row(sub.index, sub.start, sub.end, sub.text)
        self.blockSignals(False)

    def _append_row(self, idx: int, start: float, end: float, text: str):
        row = self.rowCount()
        self.insertRow(row)
        n_item = QTableWidgetItem(str(idx))
        n_item.setFlags(n_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, COL_IDX, n_item)
        self.setItem(row, COL_START, QTableWidgetItem(_fmt(start)))
        self.setItem(row, COL_END, QTableWidgetItem(_fmt(end)))
        self.setItem(row, COL_TEXT, QTableWidgetItem(text))

    def get_subtitles(self):
        from transcriber import Subtitle
        result = []
        for row in range(self.rowCount()):
            idx = row + 1
            start = _parse(self.item(row, COL_START).text() if self.item(row, COL_START) else "0")
            end = _parse(self.item(row, COL_END).text() if self.item(row, COL_END) else "0")
            text = self.item(row, COL_TEXT).text() if self.item(row, COL_TEXT) else ""
            result.append(Subtitle(index=idx, start=start, end=end, text=text))
        return result

    def set_text_font_size(self, size: int):
        self._font_size = size
        font = QFont()
        font.setPointSize(size)
        for row in range(self.rowCount()):
            item = self.item(row, COL_TEXT)
            if item:
                item.setFont(font)

    def highlight_suspicious(self, row: int, suspicious: bool):
        color = QColor("#fff3cd") if suspicious else QColor("#ffffff")
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setBackground(color)

    def _context_menu(self, pos):
        item = self.itemAt(pos)
        if item is None:
            return
        row = item.row()
        text_item = self.item(row, COL_TEXT)
        if text_item is None:
            return
        text = text_item.text()

        menu = QMenu(self)
        search_act = menu.addAction(f"「{text[:20]}」をGoogle検索")
        add_row_act = menu.addAction("行を追加")
        del_row_act = menu.addAction("行を削除")

        action = menu.exec(self.viewport().mapToGlobal(pos))
        if action == search_act:
            web_search.open_google_search(text)
        elif action == add_row_act:
            self._append_row(self.rowCount() + 1, 0, 0, "")
        elif action == del_row_act:
            self.removeRow(row)
            self._renumber()

    def _renumber(self):
        for row in range(self.rowCount()):
            item = self.item(row, COL_IDX)
            if item:
                item.setText(str(row + 1))
