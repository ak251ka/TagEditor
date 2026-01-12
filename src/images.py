from typing import Set, Iterator
from pathlib import Path


IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff'}


def iter_images(root: Path, recursive: bool = True, exts: Set[str] = IMAGE_EXTS) -> Iterator[Path]:
    it = root.rglob('*') if recursive else root.glob('*')
    for p in it:
        if p.is_file() and p.suffix.lower() in exts:
            yield p
