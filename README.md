# TagEditor

TagEditor is a desktop GUI app for managing image dataset tags and captions.

Built with:
- Python + PySide6 (Qt)
- JoyTag (auto-tagging)
- BLIP image captioning (blip-image-captioning-base)

License: Apache-2.0 (this repository). Note: the ML models you use may have their own licenses. You are responsible for complying with them.

---

## What it does

- Load a folder of images (jpg/png/webp, etc.)
- Auto-generate:
  - tags (JoyTag)
  - captions (BLIP)
- Let the user edit results:
  - add tags
  - remove tags
  - reorder / clean up
- Save results back to disk (JSON sidecar / export)

---

## Features

- Folder browser + image preview
- Tag list editor (add/remove)
- Caption editor
- Batch processing (run models on many images)
- Export metadata as JSON
- Non-destructive workflow (keeps original images unchanged)

---

## Requirements

- Python 3.10+ recommended
- OS: Windows / Linux (macOS may work if your ML stack supports it)
- Optional: NVIDIA GPU + CUDA for faster inference

Common deps (varies by your setup):
- torch
- transformers
- Pillow (or opencv-python)
- PySide6

---

## Installation

### 1) Create and activate a virtual environment

Linux/macOS:
```bash
python -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```bash
pip install -U pip wheel
pip install -r requirements.txt
```

If you use GPU PyTorch, install the correct torch build for your CUDA version (follow official PyTorch instructions).

---

## Running

One of these will apply depending on how you structured the project:

```bash
python -m tageditor
```

or

```bash
python app.py
```

---

## Models

This app uses two models:
- JoyTag (tagging)
- Salesforce BLIP image captioning (blip-image-captioning-base)

How models are loaded depends on your implementation:
- Option A: auto-download on first run (Hugging Face cache)
- Option B: local folder (recommended for reproducibility)

Suggested local layout:
```
models/
  joytag/
  blip-image-captioning-base/
```

If you use local-only mode, make sure your code points to these folders and does not silently fetch from the internet.

---

## Output format (JSON)

A simple, practical schema:

```json
[
  {
    "folder": "folder1",
    "files": [
      {
        "file": "image_0001.jpg",
        "auto_tags": ["1girl", "smile", "outdoors"],
        "tags": ["1girl", "smile", "solo"],
        "auto_caption": "A person smiling outdoors.",
        "meta": {
          "tagger": "joytag",
          "captioner": "blip-image-captioning-base"
        }
      }
    ]
  }
]
```

You can extend it if you want (example fields some dataset workflows like):
- categories
- channels
- models
- rating
- source

Keep it consistent or your downstream pipeline will become a mess.

---

## Typical workflow

1. Select an image folder
2. Click "Auto Tag" (JoyTag)
3. Click "Auto Caption" (BLIP)
4. Review each image:
   - delete junk tags
   - add missing tags
   - fix captions
5. Export JSON

---

## Project structure (example)

```
TagEditor/
  tag_editor.py
  models/
  src/
  requirements.txt
  LICENSE
  README.md
```

---

## Notes

- Tagging/captioning quality depends heavily on your dataset domain.
- If your UI allows users to edit tags freely, enforce basic cleanup rules
  (trim spaces, de-duplicate, consistent separators), or your exports will be noisy and inconsistent.

---

## Contributing

PRs welcome:
- UI improvements (keyboard shortcuts, bulk edit, search/filter tags)
- Faster batch inference (queue + worker threads/processes)
- Better exports (per-image sidecar JSON, dataset-level JSON, TXT prompts)

---

## License

Apache License 2.0. See `LICENSE`.
