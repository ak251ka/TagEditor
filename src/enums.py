from enum import Enum


class StrEnum(str, Enum):
    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value


class FileState(StrEnum):
    PENDING = 'pending'
    QUEUED = 'queued'
    RUNNING = 'running'
    DONE = 'done'
    ERROR = 'error'


class Fileds(StrEnum):
    ID = 'id'
    FILES = 'files'
    STATUS = 'status'
    TAGS = 'tags'


class WorkerName(StrEnum):
    Scan_Worker = 'ScanWorker'
    AIWorker = 'AIWorker'
