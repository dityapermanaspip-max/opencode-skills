"""Evidence for existing controls. A control counts as existing only when a person put at least one file (SOP, app screenshot,
CCTV still, photo, ...) in `08-Bukti/<EVA>/<CTL>/`. The engine only looks at the folder: it never reads, judges or creates
evidence. `sort` moves files that were dropped in the wrong place into the folder that the ids in their path or file name point
to. A control that came from a DONE plan is proven by the plan, not by this folder. Standard library only."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = "08-Bukti"
_EVA = re.compile(r"EVA-\d{4}-\d{3}")
_CTL = re.compile(r"CTL-\d{3}")
_JUNK = {"thumbs.db", "desktop.ini"}
_SKIP_TOP = (ROOT, "99-Laporan", "_Draft", ".obsidian", ".git")   # never scanned for loose files outside the evidence root


def counts(path: Path) -> bool:
    """A real file, not a hidden/temporary one."""
    n = path.name
    return path.is_file() and not n.startswith((".", "~$")) and not n.endswith((".tmp", ".crdownload", ".part")) and n.lower() not in _JUNK


def folder(vault, eva: str, ctl: str) -> Path:
    return vault.root / ROOT / eva / ctl


def files(vault, eva: str, ctl: str) -> list[Path]:
    d = folder(vault, eva, ctl)
    return sorted(p for p in d.rglob("*") if counts(p)) if d.is_dir() else []


def proven(vault, eva: str, row: dict) -> bool:
    """A control row is recognised when it came from a plan (the plan carries the proof) or has at least one evidence file."""
    return bool(row.get("plan")) or bool(files(vault, eva, row["control"]))


def missing(vault, ev) -> list[str]:
    from gv_cycle import ecm_rows
    return [r["control"] for r in ecm_rows(ev) if not proven(vault, ev.id, r)]


# ---- putting files where they belong ---------------------------------------------------------------------------

def _target(vault, rel: str, installed: dict, hint) -> tuple[tuple | None, str]:
    """(evaluation, control) a file belongs to from the ids in its path, or (None, reason)."""
    evas, ctls = sorted(set(_EVA.findall(rel))), sorted(set(_CTL.findall(rel)))
    if len(evas) > 1 or len(ctls) > 1:
        return None, "menyebut lebih dari satu ID EVA atau CTL"
    eva, ctl = (evas or [None])[0], (ctls or [None])[0]
    year = vault.cfg["fiscal_year"]
    if ctl and (ctl not in vault.notes or vault.notes[ctl].entity != "kontrol"):
        return None, f"{ctl} tidak ada di kamus kontrol"
    if eva and eva not in installed:
        return None, f"{eva} tidak ada"
    if eva and ctl:
        return (eva, ctl), ""   # evidence may come before the control is installed: that is the normal order
    if ctl:
        cands = [e for e, cs in installed.items() if ctl in cs and e.startswith(f"EVA-{year}-")]
        if hint and hint[1] == ctl and (hint[0] in cands or not cands):
            return (hint[0], ctl), ""
        if len(cands) == 1:
            return (cands[0], ctl), ""
        return None, (f"{ctl} terpasang pada {', '.join(cands)}: sertakan ID EVA pada nama berkas atau foldernya" if cands else
                      f"{ctl} belum terpasang pada evaluasi {year} mana pun: sertakan ID EVA pada nama berkas atau foldernya")
    if eva:
        ctls_here = sorted(installed[eva])
        if len(ctls_here) == 1:
            return (eva, ctls_here[0]), ""
        return None, f"{eva} punya {len(ctls_here)} kontrol: sertakan ID CTL pada nama berkas atau foldernya"
    return None, "tidak ada ID EVA atau CTL pada nama atau foldernya"


def plan_sort(vault, hint=None) -> list[dict]:
    """Files that are not in their `08-Bukti/<EVA>/<CTL>/` folder: [{src, dest dir or None, why}]. Loose files outside the evidence
    root are considered only when their path names a control (CTL-nnn); notes (.md) and generated folders are never touched."""
    from gv_cycle import ecm_rows
    root = vault.root
    installed = {ev.id: {r["control"] for r in ecm_rows(ev)} for ev in vault.all("evaluasi")}
    found = [p for p in (root / ROOT).rglob("*") if counts(p)] if (root / ROOT).is_dir() else []
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if rel.parts[0] not in _SKIP_TOP and p.suffix.lower() != ".md" and counts(p) and _CTL.search(rel.as_posix()):
            found.append(p)
    out = []
    for p in sorted(found):
        parts = p.relative_to(root).parts
        if (len(parts) >= 4 and parts[0] == ROOT and parts[1] in installed and parts[2] in vault.notes
                and vault.notes[parts[2]].entity == "kontrol"):
            continue   # already in an evaluation/control folder
        target, why = _target(vault, p.relative_to(root).as_posix(), installed, hint)
        out.append({"src": p, "dest": folder(vault, *target) if target else None, "why": why, "ctl": target[1] if target else None,
                    "eva": target[0] if target else None})
    return out


def _free(path: Path) -> Path:
    n = 2
    cand = path
    while cand.exists():
        cand = path.with_name(f"{path.stem} ({n}){path.suffix}")
        n += 1
    return cand


def sort(vault, hint=None, only: str | None = None, dry: bool = False) -> tuple[list[str], list[str]]:
    """Moves each misplaced file whose destination is certain; never overwrites (a clash gets ' (2)'); logs every move.
    `only` limits it to one control id. Returns (moved lines, left lines with the reason)."""
    moved, left = [], []
    ev_root = vault.root / ROOT
    for item in plan_sort(vault, hint):
        src = item["src"]
        rel = src.relative_to(vault.root).as_posix()
        if only and item["ctl"] != only:
            continue
        if item["dest"] is None:
            left.append(f"{rel}: {item['why']}")
            continue
        dest = _free(item["dest"] / src.name)
        line = f"{rel} -> {dest.relative_to(vault.root).as_posix()}"
        moved.append(line)
        if dry:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        vault.log("evidence sort", item["eva"], line)
        d = src.parent
        while d != ev_root and d.is_relative_to(ev_root) and not any(d.iterdir()):   # tidy folders we emptied under 08-Bukti
            d.rmdir()
            d = d.parent
    return moved, left


# ---- views ---------------------------------------------------------------------------------------------------------

def _names(paths: list[Path], limit: int = 3) -> str:
    names = [p.name for p in paths[:limit]]
    return ", ".join(names) + (f" dan {len(paths) - limit} lainnya" if len(paths) > limit else "")


def describe(vault, eva_id: str | None = None) -> str:
    """One evaluation in detail, or (no id) the working year's controls that still have no evidence."""
    from gv_cycle import ecm_rows
    year = vault.cfg["fiscal_year"]
    if eva_id:
        ev = vault.get(eva_id)
        if ev.entity != "evaluasi":
            from gv_rules import VaultError
            raise VaultError(f"{eva_id} bukan evaluasi")
        out = [f"Bukti kontrol pada {ev.id} (folder: {ROOT}/{ev.id}/<ID kontrol>/):"]
        for r in ecm_rows(ev):
            fl = files(vault, ev.id, r["control"])
            title = vault.notes[r["control"]].fields.get("title", "")
            if r["plan"]:
                state = f"dari rencana {r['plan']} (bukti ada pada rencana)"
            elif fl:
                state = f"{len(fl)} berkas ({_names(fl)})"
            else:
                state = f"TANPA BUKTI: taruh berkas di {ROOT}/{ev.id}/{r['control']}/"
            out.append(f"  {r['control']}  {title}  -> {state}")
        return "\n".join(out if len(out) > 1 else out + ["  (belum ada kontrol terpasang)"])
    gaps = [(ev.id, missing(vault, ev)) for ev in vault.all("evaluasi") if ev.fields["fiscal_year"] == year]
    gaps = [(e, m) for e, m in gaps if m]
    if not gaps:
        return f"Semua kontrol tahun {year} yang dipasang manual sudah punya berkas bukti."
    out = [f"Kontrol tanpa bukti tahun {year}: {sum(len(m) for _e, m in gaps)} pada {len(gaps)} evaluasi (tetap dihitung, ditandai 'tanpa bukti'):"]
    out += [f"  {e}: {', '.join(m)}" for e, m in gaps]
    out.append(f"Taruh berkas (SOP, tangkapan layar, foto/CCTV, dsb.) di {ROOT}/<EVA>/<CTL>/, atau jalankan 'evidence sort' untuk berkas yang salah folder.")
    return "\n".join(out)


def demo_install(vault, eva: str, ctl: str, status: str = "EFFECTIVE") -> None:
    """ONLY for the fictional demo vaults (make_demo*.py): puts a clearly labelled stand-in file in the evidence folder, then installs.
    A real vault never gets one from the engine or the agent: evidence is what a person provides."""
    from gv_cycle import add_control
    d = folder(vault, eva, ctl)
    d.mkdir(parents=True, exist_ok=True)
    (d / "bukti-contoh-demo.txt").write_text("Berkas contoh untuk vault demo (fiktif). Pada vault nyata, ganti dengan bukti sebenarnya: "
                                             "SOP, tangkapan layar aplikasi, foto atau CCTV." + chr(10), encoding="utf-8", newline=chr(10))
    add_control(vault, eva, ctl, status)
