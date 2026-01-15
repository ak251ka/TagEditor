from __future__ import annotations

from pathlib import Path
from typing import Optional

from PIL import Image
import torch
from torch.amp.autocast_mode import autocast
from transformers import BlipProcessor, BlipForConditionalGeneration

from .models import TaskModel


class BlipCaptionModel(TaskModel):
    def __init__(
        self,
        max_new_tokens: int = 40,
        num_beams: int = 3,
    ) -> None:
        super().__init__(model_name='blip-image-captioning-base')
        self.max_new_tokens = max_new_tokens
        self.num_beams = num_beams

        self.device = torch.device('cuda')
        self._processor: Optional[BlipProcessor] = None

    def activate(self) -> None:
        processor = BlipProcessor.from_pretrained(
            str(self.model_dir),
            local_files_only=True,
        )
        model = BlipForConditionalGeneration.from_pretrained(
            str(self.model_dir),
            local_files_only=True,
        )
        model.eval()

        self._processor = processor
        self._model = model.to(self.device)

    def deactivate(self) -> None:
        self._processor = None
        super().deactivate()

    @torch.no_grad()
    def process(self, path: Path) -> str:
        if self._model is None or self._processor is None:
            raise RuntimeError('Model is not activated. Call activate() first.')

        with Image.open(path) as im:
            image = im.convert('RGB')

        inputs = self._processor(images=image, return_tensors='pt')
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with autocast(device_type=self.device.type, enabled=True):
            out = self._model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                num_beams=self.num_beams,
            )

        caption = self._processor.decode(out[0], skip_special_tokens=True).strip()
        return caption

    def get_filed_name(self) -> str:
        return '_caption'

    def get_result(self, obj: object) -> list[str]:
        return [str(obj)]
