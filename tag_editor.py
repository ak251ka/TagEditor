import sys
from pathlib import Path
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QToolBar,
)
from PySide6.QtCore import Slot
from src.homepage import HomePage
from src.mainpage import MainPage


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

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

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
        self.main.status.connect(self.on_status)

    def go_home(self) -> None:
        self.stack.setCurrentWidget(self.home)
        self.statusBar.showMessage('Home', 2000)

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

    @Slot(str)
    def on_status(self, msg: str) -> None:
        self.statusBar.showMessage(msg, 4000)


def main() -> int:
    app = QApplication(sys.argv)
    w = MainWindow()
    app.aboutToQuit.connect(w.main.on_shutdown)
    w.show()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
