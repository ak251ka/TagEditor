from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, QRunnable
from queue import Queue, Empty
from pathlib import Path
from .images import iter_images
from .enums import WorkerName
from .models import TaskModel
from typing import List


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


class AISignals(QObject):
    result = Signal(object)
    error = Signal(str, str)


@dataclass(frozen=True)
class ImageTask:
    id: str
    path: Path


class AIWorker(QRunnable):
    def __init__(self, models: List[TaskModel], remove_watermark: bool = True):
        super().__init__()

        self.models = models
        self.signals = AISignals()
        self.running = True
        self.queue: Queue[ImageTask] = Queue()

    def cancel(self):
        self.running = False
        self.put(None)

    def run(self):
        try:
            for m in self.models:
                m.activate()
            while self.running:
                try:
                    item = self.queue.get(timeout=0.3)
                    result = []
                    if item is None:
                        break

                    for m in self.models:
                        if not self.running:
                            break
                        res = m.process(item.path)
                        result.append({
                            'models': m.model_name,
                            'result': res
                            })
                    self.signals.result.emit({
                        'id': item.id,
                        'result': result
                    })
                except Empty:
                    continue
            for m in self.models:
                m.deactivate()
            self.signals.error.emit(WorkerName.AIWorker, 'Done' if self.running else 'cancel')
        except Exception as e:
            self.signals.error.emit(WorkerName.AIWorker, str(e))

    def put(self, item: ImageTask):
        self.queue.put(item)
