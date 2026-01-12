import json
from pathlib import Path
from typing import Any, Dict
from .imagefile import ImageFile


def _default_index(index_path: Path) -> Dict[str, Any]:
    return {'root': str(index_path.parent), 'files': {}}


def load_index(index_path: Path) -> Dict[str, Any]:
    if not index_path.exists():
        return _default_index(index_path)

    try:
        with index_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return _default_index(index_path)

    if not isinstance(data, dict) or 'root' not in data:
        return _default_index(index_path)

    files_raw = data.get('files')
    if not isinstance(files_raw, dict):
        files_raw = {}

    # decode: Dict[str, dict] -> Dict[str, ImageFile]
    data['files'] = {k: ImageFile.from_dict(v) for k, v in files_raw.items()}

    return data


def save_index(data: Dict[str, Any], index_path: Path) -> None:
    files_obj = data.get('files', {})
    if not isinstance(files_obj, dict):
        raise TypeError("data['files'] must be a dict[str, ImageFile]")

    payload = dict(data)
    # encode: Dict[str, ImageFile] -> Dict[str, dict]
    payload['files'] = {k: v.to_dict() for k, v in files_obj.items()}

    tmp = index_path.with_suffix(index_path.suffix + '.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=3)
        f.flush()

    tmp.replace(index_path)
