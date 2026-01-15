from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional, List
from PySide6.QtCore import QObject, Signal, Slot, QThreadPool
from .workers import ScanWorker, AIWorker, ImageTask
from .storage import load_index, save_index
from .enums import WorkerName, Fileds, FileState
from .imagefile import ImageFile
from .models import TaskModel
from .joytag import JoyTagModel as JoyTag
from .blip import BlipCaptionModel as BlipCaption


class BatchController(QObject):
    item_found = Signal(str)
    item_tag = Signal(str)
    error = Signal(str, str)
    status = Signal(str)
    models = List[TaskModel]
    model_by_id = Dict[str, TaskModel]

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.folder: Optional[Path] = None
        self.database: Optional[Dict[str, Any]] = None

        # inference single worker thread
        self.pool = QThreadPool.globalInstance()
        self.database_dirty = False
        self.scan_worker: Optional[ScanWorker] = None
        self.ai_worker: Optional[AIWorker] = None
        self.models = []
        self.models.append(JoyTag(0.5))
        self.models.append(BlipCaption())
        ai_worker = AIWorker(self.models)
        self.ai_worker = ai_worker
        ai_worker.signals.result.connect(self.on_ai_result)
        ai_worker.signals.error.connect(self.on_error_workers)
        self.pool.start(ai_worker)

        md = {}
        for m in self.models:
            md[m.model_name] = m

        self.model_by_id = md

    def stop_tasks(self) -> None:
        if self.scan_worker is not None:
            self.scan_worker.signals.found.disconnect(self.on_scan_found)
            self.scan_worker.signals.error.disconnect(self.on_error_workers)
            self.scan_worker.cancel()
            self.pool.waitForDone(1500)
            self.scan_worker = None

    def start_tasks(self, folder: Path, recursive: bool = True) -> None:
        self.stop_tasks()
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
        if path.parent == self.folder:
            id = path.relative_to(self.folder).as_posix()
        else:
            id = (Path(path.parent.name) / path.name).as_posix()
        image = self.getImage(id)
        if not image:
            image = ImageFile(id=id, path=path, status=FileState.PENDING)

        if image.status != FileState.DONE:
            image.status = FileState.QUEUED
            self.ai_worker.put(ImageTask(id=id, path=path))
            self.database[Fileds.FILES][id] = image
        self.item_found.emit(id)

    @Slot(str, str)
    def on_error_workers(self, id: str, msg: str):

        if id == WorkerName.Scan_Worker:
            self.stop_tasks()

        if msg == 'Done':
            self.status.emit('Scan done!')

        if id == WorkerName.AIWorker:
            if msg == 'Done':
                self.status.emit('Image Processing done!')
                self.stop_tasks()
            else:
                self.status.emit(msg)
        print(f'{id} , {msg}')

    def shutdown(self):
        self.stop_tasks()
        if self.ai_worker is not None:
            self.ai_worker.cancel()
            self.ai_worker.signals.result.disconnect(self.on_ai_result)
            self.ai_worker.signals.error.disconnect(self.on_error_workers)
            self.ai_worker.cancel()
            self.pool.waitForDone(1500)
            self.ai_worker = None
        if self.database:
            save_index(self.database, self.root / 'tags_index.json')

    @Slot(object)
    def on_ai_result(self, item: object):
        item = dict(item)
        img = self.getImage(item.get('id'))
        result_list = item.get('result')
        for rl in result_list:
            m = self.model_by_id[rl.get('models')]
            img[m.get_filed_name()] = m.get_result(rl.get('result'))
        img.status = FileState.DONE
        self.item_tag.emit(img.id)
