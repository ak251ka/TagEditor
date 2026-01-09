import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QEvent
from PySide6.QtGui import QAction, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif'}


@dataclass(frozen=True)
class ItemRecord:
    image_path: Path
    tag_path: Path


class HomePage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText('Select a folder containing images + .txt tag files')
        self.path_edit.setClearButtonEnabled(True)

        self.browse_btn = QPushButton('Choose Folder…')
        self.open_btn = QPushButton('Open')
        self.open_btn.setEnabled(False)

        title = QLabel('TagEditor')
        title.setStyleSheet('font-size: 18px; font-weight: 600;')

        hint = QLabel('Pick a dataset folder. The UI will populate the list on the next screen.')
        hint.setStyleSheet('color: #666;')

        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet('QFrame { border: 1px solid #ddd; border-radius: 12px; }')
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)

        row = QHBoxLayout()
        row.addWidget(self.path_edit, 1)
        row.addWidget(self.browse_btn)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(self.open_btn)

        card_layout.addWidget(title)
        card_layout.addWidget(hint)
        card_layout.addLayout(row)
        card_layout.addLayout(btn_row)

        root = QVBoxLayout(self)
        root.addStretch(1)
        root.addWidget(card, 0, alignment=Qt.AlignHCenter)
        root.addStretch(1)

        self.path_edit.textChanged.connect(self._on_path_changed)

    def _on_path_changed(self, text: str) -> None:
        p = Path(text.strip()) if text.strip() else None
        self.open_btn.setEnabled(bool(p and p.exists() and p.is_dir()))


class MainPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        # Left pane
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('Filter files…')
        self.search_edit.setClearButtonEnabled(True)

        self.file_list = QListWidget()
        self.file_list.setUniformItemSizes(True)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)
        left_layout.addWidget(QLabel('Files'))
        left_layout.addWidget(self.search_edit)
        left_layout.addWidget(self.file_list, 1)

        nav_row = QHBoxLayout()
        self.prev_btn = QPushButton('Prev')
        self.next_btn = QPushButton('Next')
        nav_row.addWidget(self.prev_btn)
        nav_row.addWidget(self.next_btn)
        left_layout.addLayout(nav_row)

        # Right pane (preview + tags)
        self.preview_label = QLabel('Preview')
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(QSize(480, 320))
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_label.setStyleSheet('QLabel { border: 1px dashed #bbb; border-radius: 12px; }')

        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setFrameShape(QFrame.NoFrame)
        self.preview_scroll.setWidget(self.preview_label)

        self.tags_list = QListWidget()
        self.tags_list.setSelectionMode(QListWidget.SingleSelection)

        self.tag_edit = QLineEdit()
        self.tag_edit.setPlaceholderText('Add tag… (UI only)')
        self.add_tag_btn = QPushButton('Add Tag')
        self.remove_dups_btn = QPushButton('Remove Duplicates')
        self.undo_btn = QPushButton('Undo')
        self.save_btn = QPushButton('Save')

        tag_row = QHBoxLayout()
        tag_row.addWidget(self.tag_edit, 1)
        tag_row.addWidget(self.add_tag_btn)

        action_row = QHBoxLayout()
        action_row.addWidget(self.remove_dups_btn)
        action_row.addStretch(1)
        action_row.addWidget(self.undo_btn)
        action_row.addWidget(self.save_btn)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(8)
        right_layout.addWidget(QLabel('Image Preview'))
        right_layout.addWidget(self.preview_scroll, 1)
        right_layout.addWidget(QLabel('Tags'))
        right_layout.addWidget(self.tags_list, 0)
        right_layout.addLayout(tag_row)
        right_layout.addLayout(action_row)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 780])

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(splitter)

        # Minimal wiring for UI feel (still 'UI mock')
        self._records: list[ItemRecord] = []
        self._current_dir: Path | None = None

        self.search_edit.textChanged.connect(self._apply_filter)
        self.file_list.currentRowChanged.connect(self._on_select_row)
        self.prev_btn.clicked.connect(lambda: self._step(-1))
        self.next_btn.clicked.connect(lambda: self._step(+1))

        self.add_tag_btn.clicked.connect(self._ui_add_tag_only)
        self.tag_edit.returnPressed.connect(self._ui_add_tag_only)
        self.remove_dups_btn.clicked.connect(self._ui_remove_dups_only)
        self.undo_btn.clicked.connect(self._ui_undo_only)
        self.save_btn.clicked.connect(self._ui_save_only)

    def load_directory(self, folder: Path) -> None:
        self._current_dir = folder
        self._records = self._scan(folder)
        self._rebuild_file_list()

    def _scan(self, folder: Path) -> list[ItemRecord]:
        records: list[ItemRecord] = []
        for p in sorted(folder.iterdir()):
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
                tag_path = p.with_suffix('.txt')
                records.append(ItemRecord(image_path=p, tag_path=tag_path))
        return records

    def _rebuild_file_list(self) -> None:
        self.file_list.clear()
        for rec in self._records:
            label = rec.image_path.name
            if rec.tag_path.exists():
                label += '  (txt)'
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, rec)
            self.file_list.addItem(item)

        if self.file_list.count() > 0:
            self.file_list.setCurrentRow(0)
        else:
            self.preview_label.setText('No images found in this folder.')
            self.tags_list.clear()

    def _apply_filter(self, text: str) -> None:
        t = text.strip().lower()
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            item.setHidden(t not in item.text().lower())

    def _step(self, delta: int) -> None:
        row = self.file_list.currentRow()
        if row < 0:
            return
        new_row = max(0, min(self.file_list.count() - 1, row + delta))
        self.file_list.setCurrentRow(new_row)

    def _on_select_row(self, row: int) -> None:
        if row < 0:
            return
        item = self.file_list.item(row)
        rec: ItemRecord = item.data(Qt.UserRole)

        self._show_image(rec.image_path)
        self._show_tags(rec.tag_path)

    def _show_image(self, path: Path) -> None:
        pix = QPixmap(str(path))
        if pix.isNull():
            self.preview_label.setText(f'Failed to load: {path.name}')
            self.preview_label.setPixmap(QPixmap())
            return

        # Fit-to-view behavior, like many dataset taggers
        target = self.preview_scroll.viewport().size()
        scaled = pix.scaled(target, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_label.setPixmap(scaled)
        self.preview_label.setStyleSheet('QLabel { border: 1px solid #ddd; border-radius: 12px; }')

    def eventFilter(self, obj, event) -> bool:
        if obj is self.preview_scroll.viewport() and event.type() == QEvent.Resize:
            # Re-fit current pixmap on resize
            row = self.file_list.currentRow()
            if row >= 0:
                rec: ItemRecord = self.file_list.item(row).data(Qt.UserRole)
                self._show_image(rec.image_path)
        return super().eventFilter(obj, event)

    def _show_tags(self, tag_path: Path) -> None:
        self.tags_list.clear()
        if not tag_path.exists():
            self.tags_list.addItem('(no tag file)')
            return

        try:
            content = tag_path.read_text(encoding='utf-8', errors='replace').strip()
        except Exception:
            self.tags_list.addItem('(failed to read tag file)')
            return

        tags = [t.strip() for t in content.split(',') if t.strip()]
        if not tags:
            self.tags_list.addItem('(empty)')
            return

        for t in tags:
            self.tags_list.addItem(t)

    # UI-only actions (placeholders)
    def _ui_add_tag_only(self) -> None:
        text = self.tag_edit.text().strip()
        if not text:
            return
        self.tags_list.addItem(text)
        self.tag_edit.clear()

    def _ui_remove_dups_only(self) -> None:
        seen = set()
        deduped = []
        for i in range(self.tags_list.count()):
            t = self.tags_list.item(i).text()
            if t not in seen:
                seen.add(t)
                deduped.append(t)
        self.tags_list.clear()
        for t in deduped:
            self.tags_list.addItem(t)

    def _ui_undo_only(self) -> None:
        QMessageBox.information(self, 'Undo', 'UI mock: no real undo stack implemented.')

    def _ui_save_only(self) -> None:
        QMessageBox.information(self, 'Save', 'UI mock: no real file writing implemented.')


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('TagEditor')
        self.resize(1150, 720)

        self.stack = QStackedWidget()
        self.home = HomePage()
        self.main = MainPage()
        self.stack.addWidget(self.home)
        self.stack.addWidget(self.main)
        self.setCentralWidget(self.stack)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        tb = QToolBar('Main')
        tb.setMovable(False)
        self.addToolBar(tb)

        self.dir_edit = QLineEdit()
        self.dir_edit.setPlaceholderText('Folder…')
        self.dir_edit.setClearButtonEnabled(True)
        self.dir_edit.setMinimumWidth(420)

        choose_act = QAction('Choose', self)
        choose_act.triggered.connect(self.choose_folder)

        home_act = QAction('Home', self)
        home_act.triggered.connect(self.go_home)

        tb.addAction(home_act)
        tb.addSeparator()
        tb.addWidget(QLabel('Folder: '))
        tb.addWidget(self.dir_edit)
        tb.addAction(choose_act)

        open_shortcut = QAction(self)
        open_shortcut.setShortcut(QKeySequence('Ctrl+O'))
        open_shortcut.triggered.connect(self.choose_folder)
        self.addAction(open_shortcut)

        save_shortcut = QAction(self)
        save_shortcut.setShortcut(QKeySequence.Save)
        save_shortcut.triggered.connect(lambda: self.main._ui_save_only())
        self.addAction(save_shortcut)

        # Wire home page
        self.home.browse_btn.clicked.connect(self.choose_folder)
        self.home.open_btn.clicked.connect(self.open_from_home)
        self.home.path_edit.textChanged.connect(self.dir_edit.setText)

        # Improve preview resizing behavior
        self.main.preview_scroll.viewport().installEventFilter(self.main)

    def go_home(self) -> None:
        self.stack.setCurrentWidget(self.home)
        self.status.showMessage('Home', 2000)

    def open_from_home(self) -> None:
        folder = Path(self.home.path_edit.text().strip())
        if not (folder.exists() and folder.is_dir()):
            return
        self._open_folder(folder)

    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, 'Choose folder')
        if not folder:
            return
        self.dir_edit.setText(folder)
        self.home.path_edit.setText(folder)
        self._open_folder(Path(folder))

    def _open_folder(self, folder: Path) -> None:
        self.main.load_directory(folder)
        self.stack.setCurrentWidget(self.main)
        self.setWindowTitle(f'TagEditor - [{folder.name}]')
        self.status.showMessage(f'Loaded: {folder}', 4000)


def main() -> int:
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
