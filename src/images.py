from typing import Set, Iterator
from pathlib import Path
from PIL import Image
import torch
import torchvision.transforms.functional as TVF

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff'}


def iter_images(root: Path, recursive: bool = True, exts: Set[str] = IMAGE_EXTS) -> Iterator[Path]:
    it = root.rglob('*') if recursive else root.glob('*')
    for p in it:
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def prepare_image(image: Image.Image, target_size: int) -> torch.Tensor:
    # Pad image to square
    image = image.convert('RGB')
    w, h = image.size
    max_dim = max(w, h)
    pad_left = (max_dim - w) // 2
    pad_top = (max_dim - h) // 2

    padded = Image.new('RGB', (max_dim, max_dim), (255, 255, 255))
    padded.paste(image, (pad_left, pad_top))

    # Resize
    if max_dim != target_size:
        padded = padded.resize((target_size, target_size), Image.BICUBIC)

    # To tensor + normalize (CLIP mean/std used by JoyTag)
    x = TVF.pil_to_tensor(padded) / 255.0
    x = TVF.normalize(
        x,
        mean=[0.48145466, 0.4578275, 0.40821073],
        std=[0.26862954, 0.26130258, 0.27577711],
    )
    return x
