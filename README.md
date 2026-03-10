# PDF Overlayer

Composites an overlay PDF on top of a source PDF, page by page. Useful for applying envelope templates with clear zones (white/opaque areas that mask source content) and window knockouts (transparent areas that reveal source content).

## Usage

### GUI

```bash
python gui.py
```

Pick a source PDF, an overlays PDF, select which overlay page to use, optionally set an output path, and click **Run**.

### CLI

```bash
python overlay_pdf.py source.pdf envelope.pdf
python overlay_pdf.py source.pdf envelope.pdf -o output.pdf -v
python overlay_pdf.py source.pdf envelope.pdf -p 1 -v
```

**Arguments:**

| Argument | Description |
|---|---|
| `source_pdf` | Source PDF with content to overlay |
| `overlays_pdf` | Overlay template PDF |
| `-p N` / `--overlay-page N` | Page from overlays PDF to use, 1-indexed (default: `1`) |
| `-o PATH` / `--output PATH` | Output path (default: `<source>_overlaid.pdf` alongside source) |
| `-v` / `--verbose` | Print per-page progress and size-mismatch warnings |

## Setup

Requires Python 3.13+ built with Tcl/Tk 8.6 support.

```bash Linux
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```
```powershell Windows
python -m venv env
./env\Scripts\activate
pip install -r requirements.txt
```


