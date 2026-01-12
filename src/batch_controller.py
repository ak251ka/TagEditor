from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
from PySide6.QtCore import QObject, Signal, Slot, QThreadPool
from .workers import ScanWorker
from .storage import load_index, save_index
from .enums import WorkerName, Fileds, FileState
from .imagefile import ImageFile


class BatchController(QObject):
    item_found = Signal(str)
    error = Signal(str, str)
    status = Signal(str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.folder: Optional[Path] = None
        self.database: Optional[Dict[str, Any]] = None
        # inference single worker thread
        self.pool = QThreadPool.globalInstance()
        self.database_dirty = False
        self.scan_worker: Optional[ScanWorker] = None

    def stop_scan(self) -> None:
        if self.scan_worker is not None:
            self.scan_worker.cancel()
            self.pool.waitForDone(1500)
            self.scan_worker.signals.found.disconnect(self.on_scan_found)
            self.scan_worker.signals.error.disconnect(self.on_error_workers)
            self.scan_worker = None

    def start_folder(self, folder: Path, recursive: bool = True) -> None:
        self.stop_scan()
        self.root = folder
        self.database = load_index(folder / 'tags_index.json')
        self.database_dirty = False
        self.status.emit(f'Scanning: {folder}')
        worker = ScanWorker(folder, recursive=recursive)
        self.scan_worker = worker
        worker.signals.found.connect(self.on_scan_found)
        worker.signals.error.connect(self.on_error_workers)
        self.pool.start(worker)

    def getImage(self, id: str) -> ImageFile:
        return self.database.get(Fileds.FILES, {}).get(id)

    @Slot(Path)
    def on_scan_found(self, path: Path) -> None:
        id = path.relative_to(self.folder).as_posix() if path.parent == self.folder else (
            Path(path.parent.name) / path.name).as_posix()
        image = self.getImage(id)
        if not image:
            image = ImageFile(id=id, path=path, status=FileState.PENDING)
        if image.status != FileState.DONE:
            image.status = FileState.QUEUED
            # process here
            pass
        self.database[Fileds.FILES][id] = image
        self.item_found.emit(id)

    @Slot(str, str)
    def on_error_workers(self, id: str, msg: str):
        if id == WorkerName.Scan_Worker:
            self.stop_scan()
            if msg == 'Done':
                self.status.emit('Scan done!')

    def shutdown(self):
        self.stop_scan()
        save_index(self.database, self.root / 'tags_index.json')
