"""`report --pdf`: the ISO 31000:2018 report as one self-contained HTML file, printed to PDF by Edge or Chrome in headless mode.
Standard library only. No browser found: the HTML is still written and can be printed from any browser (Ctrl+P, A4, background graphics)."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path

import gv_check
import gv_draft
import gv_report
import gv_pdf_sections as S
from gv_pdf_css import CSS
from gv_pdf_util import e

_WINDOWS = [r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe", r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
            r"%ProgramFiles%\Google\Chrome\Application\chrome.exe", r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
            r"%LocalAppData%\Google\Chrome\Application\chrome.exe"]
_MAC = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Chromium.app/Contents/MacOS/Chromium"]
_NAMES = ["microsoft-edge", "msedge", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"]


def find_browser() -> str | None:
    """GRIMIS_BROWSER first, then the usual Edge/Chrome/Chromium locations."""
    forced = os.environ.get("GRIMIS_BROWSER")
    if forced:
        return forced if Path(forced).is_file() else None
    for raw in _WINDOWS + _MAC:
        path = os.path.expandvars(raw)
        if "%" not in path and Path(path).is_file():
            return path
    return next((p for p in (shutil.which(n) for n in _NAMES) if p), None)


def _drafts(vault) -> list:
    out = []
    for d in vault.all("draft"):
        if d.fields.get("status") in ("DRAFT", "PARTIAL"):
            left = sum(1 for s, _c in gv_draft.results_of(d).values() if s == "BELUM")
            out.append([e(d.id), e(d.fields["kind"]), e(d.fields.get("target") or "-"), e(d.fields["status"]), str(left)])
    return out


def build_html(vault, year: int) -> str:
    rows = gv_report.profile(vault, year)
    if not rows:
        raise ValueError(f"Belum ada evaluasi tahun {year}")
    mx = rows[0]["matrix"]
    working = year == vault.cfg["fiscal_year"]
    s = gv_report.status(vault) if working else None
    foot = f"Laporan Manajemen Risiko {vault.cfg['org']} {year}".replace("\\", "").replace("'", "").replace("\n", " ")
    body = "".join([
        S.cover(vault, year, rows, mx, date.today().isoformat()), S.summary(vault, year, rows, mx, s), S.context(vault, year, rows, mx),
        S.register(vault, year, rows, mx), S.details(vault, rows, mx), S.simulations(rows, mx), S.treatment(rows, mx),
        S.monitoring(vault, year, rows),
        S.recording(vault, rows, s, gv_check.check(vault), gv_report.status_text(s) if s else "", _drafts(vault)),
    ])
    return (f"<!doctype html><html lang='id'><head><meta charset='utf-8'><title>{e(foot)}</title>"
            f"<style>{CSS.replace('var(--foot)', repr(foot))}</style></head><body>{body}</body></html>")


def write_pdf(vault, year: int) -> tuple[Path, Path | None, str]:
    """Returns (html path, pdf path or None, message)."""
    out = vault.root / "99-Laporan"
    out.mkdir(exist_ok=True)
    html_path, pdf_path = out / f"Laporan-{year}.html", out / f"Laporan-{year}.pdf"
    html_path.write_text(build_html(vault, year), encoding="utf-8", newline="\n")
    browser = find_browser()
    if not browser:
        return html_path, None, ("PDF tidak dibuat: Edge, Chrome atau Chromium tidak ditemukan (atau set GRIMIS_BROWSER ke programnya). "
                                 "HTML sudah ditulis: buka di peramban lalu cetak ke PDF (A4, aktifkan grafik latar).")
    pdf_path.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as profile:  # a throw-away profile so a running browser does not swallow the job
        cmd = [browser, "--headless=new", "--disable-gpu", f"--user-data-dir={profile}", "--no-pdf-header-footer",
               f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()]
        try:
            subprocess.run(cmd, capture_output=True, timeout=180, check=False)
        except subprocess.TimeoutExpired:
            return html_path, None, "PDF gagal: peramban tidak selesai dalam 180 detik. HTML sudah ditulis."
    if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        return html_path, None, f"PDF gagal dibuat oleh {Path(browser).name}. HTML sudah ditulis: cetak dari peramban."
    return html_path, pdf_path, f"PDF dibuat dengan {Path(browser).name}"
