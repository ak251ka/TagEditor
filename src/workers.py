from PySide6.QtCore import QObject, Signal, QRunnable
from pathlib import Path
from .images import iter_images
from .enums import WorkerName


class ScanSignals(QObject):
    found = Signal(Path)
    error = Signal(str, str)


class ScanWorker(QRunnable):
    def __init__(self, folder, recursive=True):
        super().__init__()
        self.folder = folder
        self.recursive = recursive
        self.signals = ScanSignals()
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            for p in iter_images(self.folder, recursive=self.recursive):
                if self._cancel:
                    break
                self.signals.found.emit(p)
            self.signals.error.emit(WorkerName.Scan_Worker, 'Done' if not self._cancel else 'cancel')
        except Exception as e:
            self.signals.error.emit(WorkerName.Scan_Worker, str(e))
