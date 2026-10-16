import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QComboBox, QSpinBox, QProgressBar, QStatusBar, QGroupBox,
    QCheckBox, QMessageBox, QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QAction

from ui.subtitle_table import SubtitleTable
import transcriber
import srt_exporter
import web_search


class TranscribeWorker(QObject):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, path, model_size, language):
        super().__init__()
        self.path = path
        self.model_size = model_size
        self.language = language

    def run(self):
        try:
            subs = transcriber.transcribe(
                self.path,
                model_size=self.model_size,
                language=self.language,
                progress_callback=self.progress.emit,
            )
            self.finished.emit(subs)
        except Exception as e:
            self.error.emit(str(e))


class CheckWorker(QObject):
    result = pyqtSignal(int, bool, str)  # row, found, suggestion
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, subtitles):
        super().__init__()
        self.subtitles = subtitles

    def run(self):
        for i, sub in enumerate(self.subtitles):
            try:
                found, suggestion = web_search.check_word(sub.text)
                self.result.emit(i, found, suggestion)
            except Exception as e:
                self.error.emit(str(e))
        self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("自動文字起こし")
        self.resize(1100, 720)
        self._subtitles = []
        self._audio_path = ""
        self._thread = None
        self._worker = None
        self._setup_ui()
        self._setup_menu()

    def _setup_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("ファイル")
        open_act = QAction("音声/動画を開く...", self)
        open_act.setShortcut("Ctrl+O")
        open_act.triggered.connect(self._open_file)
        file_menu.addAction(open_act)

        export_act = QAction("SRTとして書き出し...", self)
        export_act.setShortcut("Ctrl+S")
        export_act.triggered.connect(self._export_srt)
        file_menu.addAction(export_act)
        file_menu.addSeparator()
        quit_act = QAction("終了", self)
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        tools_menu = menu.addMenu("ツール")
        check_act = QAction("単語をGoogle検索でチェック", self)
        check_act.triggered.connect(self._check_words)
        tools_menu.addAction(check_act)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # --- File + Transcribe row ---
        top = QHBoxLayout()
        self._file_label = QLabel("ファイル未選択")
        self._file_label.setStyleSheet("color: #555;")
        open_btn = QPushButton("開く...")
        open_btn.setFixedWidth(72)
        open_btn.clicked.connect(self._open_file)

        top.addWidget(QLabel("音声/動画:"))
        top.addWidget(self._file_label, 1)
        top.addWidget(open_btn)
        layout.addLayout(top)

        # --- Settings bar ---
        settings = QHBoxLayout()

        settings.addWidget(QLabel("モデル:"))
        self._model_combo = QComboBox()
        self._model_combo.addItems(transcriber.MODELS)
        self._model_combo.setCurrentText("medium")
        self._model_combo.setFixedWidth(110)
        settings.addWidget(self._model_combo)

        settings.addWidget(QLabel("言語:"))
        self._lang_combo = QComboBox()
        self._lang_combo.addItems(transcriber.LANGUAGES.keys())
        self._lang_combo.setFixedWidth(100)
        settings.addWidget(self._lang_combo)

        settings.addSpacing(16)

        settings.addWidget(QLabel("テキストフォントサイズ:"))
        self._font_spin = QSpinBox()
        self._font_spin.setRange(8, 32)
        self._font_spin.setValue(11)
        self._font_spin.setFixedWidth(60)
        self._font_spin.valueChanged.connect(self._on_font_changed)
        settings.addWidget(self._font_spin)

        settings.addWidget(QLabel("SRT最大文字数/行:"))
        self._max_chars_spin = QSpinBox()
        self._max_chars_spin.setRange(0, 120)
        self._max_chars_spin.setValue(0)
        self._max_chars_spin.setSpecialValueText("制限なし")
        self._max_chars_spin.setFixedWidth(80)
        settings.addWidget(self._max_chars_spin)

        settings.addStretch()

        self._transcribe_btn = QPushButton("文字起こし開始")
        self._transcribe_btn.setFixedWidth(130)
        self._transcribe_btn.setEnabled(False)
        self._transcribe_btn.clicked.connect(self._transcribe)
        settings.addWidget(self._transcribe_btn)

        self._export_btn = QPushButton("SRT書き出し")
        self._export_btn.setFixedWidth(110)
        self._export_btn.setEnabled(False)
        self._export_btn.clicked.connect(self._export_srt)
        settings.addWidget(self._export_btn)

        layout.addLayout(settings)

        # --- Progress bar ---
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setRange(0, 100)
        layout.addWidget(self._progress)

        # --- Subtitle table ---
        self._table = SubtitleTable()
        self._table.data_changed.connect(self._on_data_changed)
        layout.addWidget(self._table, 1)

        # --- Check result log ---
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(100)
        self._log.setPlaceholderText("単語チェック結果がここに表示されます...")
        layout.addWidget(self._log)

        # --- Status bar ---
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("準備完了")

    # ------------------------------------------------------------------
    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "音声/動画ファイルを開く", "",
            "メディアファイル (*.mp3 *.mp4 *.wav *.m4a *.aac *.flac *.mkv *.mov *.ogg);;すべてのファイル (*)"
        )
        if path:
            self._audio_path = path
            self._file_label.setText(path)
            self._transcribe_btn.setEnabled(True)
            self._status.showMessage(f"読み込み: {Path(path).name}")

    def _transcribe(self):
        if not self._audio_path:
            return
        lang_key = self._lang_combo.currentText()
        language = transcriber.LANGUAGES[lang_key]
        model_size = self._model_combo.currentText()

        self._transcribe_btn.setEnabled(False)
        self._export_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._status.showMessage("文字起こし中...")
        self._log.clear()

        self._worker = TranscribeWorker(self._audio_path, model_size, language)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_transcribe_done)
        self._worker.error.connect(self._on_transcribe_error)
        self._thread.start()

    def _on_progress(self, current, total):
        pct = int(current / total * 100) if total else 0
        self._progress.setValue(pct)

    def _on_transcribe_done(self, subtitles):
        self._subtitles = subtitles
        self._table.load_subtitles(subtitles)
        self._table.set_text_font_size(self._font_spin.value())
        self._progress.setVisible(False)
        self._transcribe_btn.setEnabled(True)
        self._export_btn.setEnabled(True)
        self._status.showMessage(f"完了: {len(subtitles)} 件のテロップ")
        self._thread.quit()

    def _on_transcribe_error(self, msg):
        self._progress.setVisible(False)
        self._transcribe_btn.setEnabled(True)
        QMessageBox.critical(self, "エラー", f"文字起こしに失敗しました:\n{msg}")
        self._status.showMessage("エラー")
        self._thread.quit()

    def _on_data_changed(self):
        self._subtitles = self._table.get_subtitles()

    def _on_font_changed(self, size):
        self._table.set_text_font_size(size)

    def _export_srt(self):
        subtitles = self._table.get_subtitles()
        if not subtitles:
            QMessageBox.warning(self, "警告", "書き出すテロップがありません。")
            return

        default_name = Path(self._audio_path).stem + ".srt" if self._audio_path else "output.srt"
        path, _ = QFileDialog.getSaveFileName(
            self, "SRTファイルを保存", default_name, "SRT (*.srt)"
        )
        if not path:
            return

        max_chars = self._max_chars_spin.value()
        srt_exporter.export_srt(subtitles, path, max_chars=max_chars)
        self._status.showMessage(f"書き出し完了: {path}")
        QMessageBox.information(self, "完了", f"SRTファイルを保存しました:\n{path}")

    def _check_words(self):
        subtitles = self._table.get_subtitles()
        if not subtitles:
            QMessageBox.warning(self, "警告", "テロップがありません。")
            return

        self._log.clear()
        self._log.append("単語チェック開始...")
        self._status.showMessage("Google検索でチェック中...")

        self._check_worker = CheckWorker(subtitles)
        self._check_thread = QThread()
        self._check_worker.moveToThread(self._check_thread)
        self._check_thread.started.connect(self._check_worker.run)
        self._check_worker.result.connect(self._on_check_result)
        self._check_worker.finished.connect(self._on_check_done)
        self._check_worker.error.connect(lambda e: self._log.append(f"[エラー] {e}"))
        self._check_thread.start()

    def _on_check_result(self, row, found, suggestion):
        self._table.highlight_suspicious(row, not found)
        if not found:
            text = (self._table.item(row, 3) or type("", (), {"text": lambda: "?"})()).text()
            self._log.append(f"行{row+1}: 「{text}」 → 検索結果なし")
        elif suggestion:
            text = (self._table.item(row, 3) or type("", (), {"text": lambda: "?"})()).text()
            self._log.append(f"行{row+1}: 「{text}」 → もしかして: 「{suggestion}」?")

    def _on_check_done(self):
        self._status.showMessage("単語チェック完了")
        self._log.append("チェック完了")
        self._check_thread.quit()
