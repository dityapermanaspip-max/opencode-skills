#!/usr/bin/env python3
"""grimis-payungan: the rules engine of a GRIMIS vault (an Obsidian folder of Markdown notes).
Usage: python -P grimis.py [--vault FOLDER] <command> ...   (the vault defaults to $GRIMIS_VAULT, then the current folder)
Run `python -P grimis.py --help` for the commands. Output is Indonesian."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gv_bowtie  # noqa: E402
import gv_bowtie_data  # noqa: E402
import gv_cmds as C  # noqa: E402
import gv_draft  # noqa: E402
import gv_check  # noqa: E402
import gv_close  # noqa: E402
import gv_pdf  # noqa: E402
import gv_report  # noqa: E402
from gv_rules import VaultError  # noqa: E402
from gv_vault import Vault  # noqa: E402


def build() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="grimis.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--vault", default=os.environ.get("GRIMIS_VAULT", "."))
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("init", help="create a vault in an empty folder"); a.add_argument("path"); a.add_argument("--org", required=True)
    a.add_argument("--year", type=int, required=True)
    a = sub.add_parser("new", help="new note: new <jenis> kolom=nilai ..."); a.add_argument("entity"); a.add_argument("pairs", nargs="*")
    a = sub.add_parser("set", help="edit fields: set <ID> kolom=nilai ..."); a.add_argument("id"); a.add_argument("pairs", nargs="+")
    a = sub.add_parser("show"); a.add_argument("id")
    a = sub.add_parser("list"); a.add_argument("entity")
    a = sub.add_parser("rate", help="set evaluation values (KxD, 'sim' or '-')"); a.add_argument("eva")
    for lvl in ("inherent", "residual", "expected", "actual"):
        a.add_argument(f"--{lvl}")
    a = sub.add_parser("control"); a.add_argument("action", choices=["add", "remove"]); a.add_argument("eva"); a.add_argument("ctl")
    a.add_argument("--status", default="EFFECTIVE"); a.add_argument("--notes", default="")
    a = sub.add_parser("plan"); a.add_argument("action", choices=["start", "done"]); a.add_argument("plan")
    a.add_argument("--evidence"); a.add_argument("--notes")
    a = sub.add_parser("kri"); a.add_argument("action", choices=["read", "threshold", "retire"]); a.add_argument("kri")
    a.add_argument("value", nargs="?"); a.add_argument("--date"); a.add_argument("--amber"); a.add_argument("--red"); a.add_argument("--reason")
    a = sub.add_parser("simulate"); a.add_argument("eva"); a.add_argument("--iterations", type=int, default=10000)
    a.add_argument("--percentile", type=int, default=75); a.add_argument("--seed", type=int)
    a = sub.add_parser("appetite"); a.add_argument("matrix"); a.add_argument("year", type=int); a.add_argument("score", type=int)
    a = sub.add_parser("matrix"); a.add_argument("action", choices=["show", "activate"]); a.add_argument("id")
    a = sub.add_parser("draft", help="AI drafts: new/list/show/accept/reject"); a.add_argument("action", choices=["new", "list", "show", "accept", "reject"])
    a.add_argument("id", nargs="?"); a.add_argument("--kind"); a.add_argument("--target"); a.add_argument("--file"); a.add_argument("--summary", default="")
    a.add_argument("--items", help="comma separated item numbers; default all pending"); a.add_argument("--reason", default="")
    a = sub.add_parser("bowtie", help="render bowtie SVG + Markdown; pick controls for branches (attach/detach/show)")
    a.add_argument("action", choices=["render", "attach", "detach", "show"])
    a.add_argument("risks", nargs="*", help="render: ID risiko (RSK-009 RSK-010); attach/detach: ID risiko lalu ID kontrol (RSK-050 CTL-005); show: ID risiko")
    a.add_argument("--branch", action="append", help="attach/detach: cabang (kunci c1/i0 atau teksnya), boleh diulang")
    a.add_argument("--above-appetite", action="store_true", help="render semua risiko di atas appetite tahun berjalan")
    a.add_argument("--out", help="folder keluaran (default: 99-Laporan/Bowtie)")
    a = sub.add_parser("status"); a.add_argument("--write", action="store_true", help="also write 00-Dashboard.md")
    sub.add_parser("check")
    a = sub.add_parser("report"); a.add_argument("--year", type=int)
    a.add_argument("--pdf", action="store_true", help="also write the ISO 31000 report as HTML and PDF (needs Edge or Chrome)")
    sub.add_parser("open-period")
    a = sub.add_parser("close"); a.add_argument("--year", type=int)
    return p


def _items(text):
    return [int(x) for x in text.split(",")] if text else None


def run(args) -> str:
    if args.cmd == "init":
        return C.init(args.path, args.org, args.year)
    v = Vault(args.vault)
    c = args.cmd
    if c == "new":
        return C.new(v, args.entity, args.pairs)
    if c == "set":
        return C.set_fields(v, args.id, args.pairs)
    if c == "show":
        return C.show(v, args.id)
    if c == "list":
        return C.list_(v, args.entity)
    if c == "rate":
        return C.rate(v, args.eva, **{k: getattr(args, k) for k in ("inherent", "residual", "expected", "actual")})
    if c == "control":
        return C.control(v, args.action, args.eva, args.ctl, args.status, args.notes)
    if c == "plan":
        return C.plan(v, args.action, args.plan, args.evidence, args.notes)
    if c == "kri":
        return C.kri(v, args.action, args.kri, args.value, args.date, args.amber, args.red, args.reason)
    if c == "simulate":
        return C.simulate(v, args.eva, args.iterations, args.percentile, args.seed)
    if c == "appetite":
        return C.appetite(v, args.matrix, args.year, args.score)
    if c == "matrix":
        return C.matrix(v, args.action, args.id)
    if c == "draft":
        return _draft(v, args)
    if c == "bowtie":
        if args.action == "render":
            paths = gv_bowtie.render(v, args.risks, args.above_appetite, args.out)
            return "Bowtie ditulis:\n" + "\n".join(str(p) for p in paths)
        if not args.risks:
            raise VaultError("Sebutkan ID risiko, mis. RSK-050")
        risk, controls = args.risks[0], args.risks[1:]
        if args.action == "show":
            return gv_bowtie_data.describe(v, risk)
        if not args.branch or (args.action == "attach" and not controls):
            raise VaultError(f"bowtie {args.action} butuh --branch dan ID kontrol, mis.: bowtie {args.action} RSK-050 CTL-005 --branch c1")
        pick = gv_bowtie_data.attach if args.action == "attach" else gv_bowtie_data.detach
        return "\n".join(pick(v, risk, args.branch, controls))
    if c == "status":
        s = gv_report.status(v)
        if args.write:
            gv_report.write_dashboard(v, s)
        return gv_report.status_text(s)
    if c == "check":
        found = gv_check.check(v)
        errors = sum(f[0] == "ERROR" for f in found)
        text = "\n".join(f"{lvl}  {i}  {msg}" for lvl, i, msg in found) or "Tidak ada temuan."
        if errors:
            raise VaultError(f"{text}\n{errors} ERROR")
        return text + f"\n{len(found)} peringatan, 0 error"
    if c == "report":
        year = args.year or v.cfg["fiscal_year"]
        md, csv_path = gv_report.report(v, year)
        text = f"Laporan: {md}\nCSV: {csv_path}"
        if args.pdf:
            html_path, pdf_path, msg = gv_pdf.write_pdf(v, year)
            text += f"\nHTML: {html_path}\nPDF: {pdf_path or '-'}\n{msg}"
        return text
    if c == "open-period":
        return f"Periode tutup buku {gv_close.open_period(v)} dibuka"
    if c == "close":
        s = gv_close.close_year(v, args.year or v.cfg["fiscal_year"])
        return (f"Tutup buku selesai: {s['closed']} evaluasi ditutup, {s['carried']} kontrol dibawa ke tahun depan, "
                f"{s['not_realised']} rencana NOT_REALISED, {s['blank_new']} evaluasi baru kosong (matriks berganti). "
                f"Tren: {s['trends']}. Perlu dipasang ulang kontrolnya: {', '.join(s['needs_controls']) or 'tidak ada'}. Tahun kerja sekarang {v.cfg['fiscal_year']}; periode belum dibuka.")
    raise VaultError(f"Perintah tidak dikenal: {c}")


def _draft(v, args) -> str:
    if args.action == "list":
        return "\n".join(f"{n.id}  {n.fields['kind']}  {n.fields['status']}  {n.fields.get('target') or '-'}" for n in v.all("draft")) or "(tidak ada draft)"
    if args.action == "new":
        if not (args.kind and args.file):
            raise VaultError("draft new butuh --kind dan --file (berkas JSON berisi daftar item)")
        data = json.loads(Path(args.file).read_text(encoding="utf-8"))
        note = gv_draft.create(v, args.kind, args.target, data["items"] if isinstance(data, dict) else data, args.summary)
        return f"Draft {note.id} dibuat ({args.kind}). Tinjau lalu: draft accept {note.id} [--items 1,2]"
    if not args.id:
        raise VaultError("Sebutkan ID draft (DRF-001)")
    note = v.get(args.id)
    if args.action == "show":
        return gv_draft.describe(note)
    if args.action == "accept":
        return "\n".join(gv_draft.accept(v, args.id, _items(args.items))) or "Tidak ada item untuk diterima"
    return f"{gv_draft.reject(v, args.id, _items(args.items), args.reason)} item ditolak dan diingat"


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    args = build().parse_args(argv)
    try:
        print(run(args))
        return 0
    except (VaultError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"GALAT: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
