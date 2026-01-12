from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


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
