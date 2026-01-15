
from __future__ import annotations
from pathlib import Path
from PIL import Image
import torch
import torch.amp.autocast_mode
from .vendor_loader import load_models_module
from .images import prepare_image
from .models import TaskModel
from .storage import load_top_tags
from typing import Dict


JoyTagModels = load_models_module('joytag_models')
VisionModel = JoyTagModels.VisionModel


class JoyTagModel(TaskModel):
    def __init__(
        self,
        threshold: float = 0.4,
    ):
        super().__init__(model_name='joytag')
        self.top_tags = load_top_tags(self.model_dir)
        self.threshold = threshold

    def activate(self) -> None:
        model = VisionModel.load_model(str(self.model_dir))
        model.eval()
        self._model = model.to('cuda')

    @torch.no_grad()
    def process(self, path: Path) -> Dict[str, float]:
        if self._model is None:
            raise RuntimeError('Model is not activated. Call activate() first.')

        with Image.open(path) as im:
            image = im.convert('RGB').copy()

        x = prepare_image(image, self._model.image_size).unsqueeze(0).to('cuda')

        with torch.amp.autocast_mode.autocast(device_type='cuda', enabled=True):
            preds = self._model({'image': x})
            vals = preds['tags'].sigmoid().float().cpu()[0].numpy()

        idxs = [i for i, s in enumerate(vals) if s > self.threshold]
        idxs.sort(key=lambda i: vals[i], reverse=True)

        return {self.top_tags[i]: float(vals[i]) for i in idxs}

    def get_filed_name(self) -> str:
        return '_tags'

    def get_result(self, obj: object) -> list[str]:
        d = dict(obj)

        res: list[str] = []
        for k, v in d.items():
            res.append(f'{k} ({v * 100:.2f}%)')
        return res
