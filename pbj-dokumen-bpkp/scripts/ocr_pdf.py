"""Read a scanned PDF (no text layer): render pages and run Tesseract (Indonesian).

    python ocr_pdf.py <file.pdf> --out <dir> [--pages 2,5-7] [--dpi 200] [--crop x0,y0,x1,y1] [--lang ind]

Writes page PNGs and ``page_N.txt`` into <dir> and prints a short summary. ``--crop`` takes fractions of
the page (0-1) and OCRs only that region at a higher resolution: use it for a table of numbers.

OCR drops decimal separators and confuses 0/8, 1/7, so NEVER trust a figure read this way. Open the PNG
(or the crop) and read the number by eye before it goes into proyek.md or a document.
The source PDF is only read; point --out at a scratch folder, not at the dossier.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import pymupdf

DEFAULT_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def page_numbers(spec: str | None, total: int) -> list[int]:
    if not spec:
        return list(range(1, total + 1))
    pages: list[int] = []
    for part in spec.split(","):
        low, _, high = part.partition("-")
        pages += range(int(low), int(high or low) + 1)
    return [p for p in pages if 1 <= p <= total]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pages")
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--crop", help="x0,y0,x1,y1 as fractions of the page")
    parser.add_argument("--lang", default="ind")
    parser.add_argument("--psm", default="6")
    args = parser.parse_args()
    tesseract = shutil.which("tesseract") or DEFAULT_TESSERACT
    if not Path(tesseract).exists() and not shutil.which("tesseract"):
        raise SystemExit("tesseract not found; install Tesseract-OCR with the 'ind' language data")
    args.out.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(str(args.pdf))
    for number in page_numbers(args.pages, len(doc)):
        page = doc[number - 1]
        clip = None
        if args.crop:
            x0, y0, x1, y1 = (float(v) for v in args.crop.split(","))
            rect = page.rect
            clip = pymupdf.Rect(rect.x0 + rect.width * x0, rect.y0 + rect.height * y0, rect.x0 + rect.width * x1, rect.y0 + rect.height * y1)
        png = args.out / f"page_{number}.png"
        page.get_pixmap(dpi=args.dpi, clip=clip).save(str(png))
        subprocess.run([tesseract, str(png), str(args.out / f"page_{number}"), "-l", args.lang, "--psm", args.psm], capture_output=True, check=False)
        text = (args.out / f"page_{number}.txt").read_text(encoding="utf-8", errors="replace") if (args.out / f"page_{number}.txt").exists() else ""
        print(f"page {number}: {len(text.strip())} characters  {png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
