from pathlib import Path
from PySide6.QtCore import Qt, QSize, QEvent, Signal, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from .batch_controller import BatchController
from typing import List


class MainPage(QWidget):
    status = Signal(str)

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
        self._current_dir: Path | None = None

        self.search_edit.textChanged.connect(self._apply_filter)
        self.file_list.currentRowChanged.connect(self.on_select_row)
        self.prev_btn.clicked.connect(lambda: self._step(-1))
        self.next_btn.clicked.connect(lambda: self._step(+1))

        self.add_tag_btn.clicked.connect(self._ui_add_tag_only)
        self.tag_edit.returnPressed.connect(self._ui_add_tag_only)
        self.remove_dups_btn.clicked.connect(self._ui_remove_dups_only)
        self.undo_btn.clicked.connect(self._ui_undo_only)
        self.save_btn.clicked.connect(self._ui_save_only)
        # BatchController
        self.batchController = BatchController(self)
        self.batchController.item_found.connect(self.on_item_found)
        self.batchController.status.connect(self.on_status)
        self.batchController.item_tag.connect(self.on_show_tags)

    def load_directory(self, folder: Path) -> None:
        self.file_list.clear()
        self.preview_label.setText('No images found in this folder.')
        self.tags_list.clear()
        self.batchController.start_tasks(folder=folder)

    @Slot(str)
    def on_item_found(self, id: str) -> None:
        current_row = self.file_list.currentRow()
        item = QListWidgetItem(id)
        item.setData(Qt.UserRole, id)
        self.file_list.addItem(item)

        if current_row >= 0:
            self.file_list.setCurrentRow(current_row)
        elif self.file_list.count() > 0:
            self.file_list.setCurrentRow(0)

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

    def on_select_row(self, row: int) -> None:
        if row < 0:
            return
        item = self.file_list.item(row)

        img = self.batchController.getImage(item.data(Qt.UserRole))
        self.show_image(img.path)
        self.show_tags(img.tags)

    def show_image(self, path: Path) -> None:
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
                img = self.batchController.getImage(self.file_list.item(row).data(Qt.UserRole))
                self.show_image(img.path)
                self.show_tags(img.tags)

        return super().eventFilter(obj, event)

    def show_tags(self, tags: List[str]) -> None:
        self.tags_list.clear()
        if not tags:
            self.tags_list.addItem('(no tag file)')
            return
        for t in tags:
            self.tags_list.addItem(t)

    @Slot(str)
    def on_show_tags(self, id: str) -> None:
        row = self.file_list.currentRow()
        if row >= 0:
            img = self.batchController.getImage(self.file_list.item(row).data(Qt.UserRole))
            self.show_tags(img['tags'])

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

    def on_status(self, msg: str):
        self.status.emit(msg)

    @Slot()
    def on_shutdown(self) -> None:
        self.batchController.shutdown()
