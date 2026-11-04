#!/usr/bin/env python3
"""Deterministic slicer for the long-document loop (stdlib only).

Splits extracted text into model-sized parts and writes a manifest that a loop
runner can resume from. Page markers beat line counting; a single indivisible
page larger than the caps is emitted alone with a warning instead of being cut.

Usage:
    python slice.py input.txt [--pages 8] [--lines 300] [--chars 28000]
                              [--out parts] [--force]

Output:
    <out>/part-001.txt ...
    <out>/manifest.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

MARKER = re.compile(r"^\s*=+\s*HALAMAN\s+(\d+)\s*=+\s*$", re.IGNORECASE | re.MULTILINE)
PAGE_BREAK = "\f"


def count_lines(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def page_segments(text: str) -> list[tuple[int, str]]:
    """Return (page_number, text) segments. Marker-based when available."""
    marks = list(MARKER.finditer(text))
    if marks:
        segments = []
        for index, match in enumerate(marks):
            start = 0 if index == 0 else match.start()
            end = marks[index + 1].start() if index + 1 < len(marks) else len(text)
            segments.append((int(match.group(1)), text[start:end].strip()))
        return segments

    if PAGE_BREAK in text:
        return [
            (number, page.strip())
            for number, page in enumerate(text.split(PAGE_BREAK), start=1)
            if page.strip()
        ]
    return []


def group_pages(
    segments: list[tuple[int, str]], max_pages: int, max_lines: int, max_chars: int
) -> list[dict]:
    parts: list[dict] = []
    current: dict | None = None

    for page, body in segments:
        lines = count_lines(body)
        fits = (
            current is not None
            and current["pages"] < max_pages
            and current["lines"] + lines <= max_lines
            and current["chars"] + len(body) <= max_chars
        )
        if fits and current is not None:
            current["text"] += "\n" + body
            current["to"] = page
            current["pages"] += 1
            current["lines"] += lines
            current["chars"] += len(body)
            continue

        current = {
            "from": page,
            "to": page,
            "pages": 1,
            "lines": lines,
            "chars": len(body),
            "text": body,
            "warnings": [],
        }
        if lines > max_lines or len(body) > max_chars:
            current["warnings"].append(
                f"page {page} alone exceeds the caps ({lines} lines, {len(body)} chars)"
            )
        parts.append(current)

    return parts


def slice_lines(text: str, max_lines: int, max_chars: int) -> list[dict]:
    parts: list[dict] = []
    buffer: list[str] = []
    lines = chars = 0

    def flush() -> None:
        nonlocal buffer, lines, chars
        if not buffer:
            return
        parts.append(
            {
                "from": len(parts) + 1,
                "to": len(parts) + 1,
                "pages": 1,
                "lines": lines,
                "chars": chars,
                "text": "\n".join(buffer).strip(),
                "warnings": [],
            }
        )
        buffer, lines, chars = [], 0, 0

    for line in text.splitlines():
        cost = len(line) + 1
        non_blank = 1 if line.strip() else 0
        if buffer and (lines + non_blank > max_lines or chars + cost > max_chars):
            flush()
        buffer.append(line)
        chars += cost
        lines += non_blank
    flush()
    return parts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--pages", type=int, default=8)
    parser.add_argument("--lines", type=int, default=300)
    parser.add_argument("--chars", type=int, default=28000)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not args.source.is_file():
        print(f"not a file: {args.source}", file=sys.stderr)
        return 2

    raw = args.source.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    out = args.out or args.source.with_suffix("").with_name(args.source.stem + "-parts")
    manifest_path = out / "manifest.json"

    if manifest_path.exists() and not args.force:
        print(f"manifest exists: {manifest_path} (use --force to regenerate)", file=sys.stderr)
        return 1

    segments = page_segments(text)
    parts = (
        group_pages(segments, args.pages, args.lines, args.chars)
        if segments
        else slice_lines(text, args.lines, args.chars)
    )
    if not parts:
        print("nothing to slice", file=sys.stderr)
        return 1

    out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": str(args.source),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "mode": "pages" if segments else "lines",
        "caps": {"pages": args.pages, "lines": args.lines, "chars": args.chars},
        "parts": [],
    }

    for index, part in enumerate(parts, start=1):
        name = f"part-{index:03d}.txt"
        (out / name).write_text(part["text"] + "\n", encoding="utf-8")
        manifest["parts"].append(
            {
                "id": index,
                "from": part["from"],
                "to": part["to"],
                "lines": part["lines"],
                "chars": part["chars"],
                "sha256": hashlib.sha256(part["text"].encode("utf-8")).hexdigest(),
                "warnings": part["warnings"],
                "status": "pending",
                "output": None,
            }
        )

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    total_lines = sum(part["lines"] for part in manifest["parts"])
    total_chars = sum(part["chars"] for part in manifest["parts"])
    print(
        f"{len(parts)} parts -> {out} "
        f"({total_lines} lines, {total_chars} chars, mode={manifest['mode']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
