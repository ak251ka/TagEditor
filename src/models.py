from pathlib import Path
import torch


MODEL_ROOT = Path.cwd().resolve()


class TaskModel():
    def __init__(self, model_name: str):
        self._model = None
        self.model_name = model_name
        self.model_dir = Path(MODEL_ROOT / f'models/{self.model_name}').expanduser().resolve()
        if not self.model_dir.is_dir():
            raise SystemExit(f"model directory not found: {self.model_dir}")

    def activate(self):
        pass

    def deactivate(self):
        self._model = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def process(self, path: Path):
        pass

    def get_filed_name(self) -> str:
        pass

    def get_result(self, obj: object) -> list[str]:
        pass
