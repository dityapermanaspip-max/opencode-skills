"""pbj.py: draft procurement (PBJ) documents from a project folder and track the contract.

Run it from the project folder (or pass --folder). The tracker is the Markdown note ``proyek.md``.

  init / set / get          create and edit the facts (keys are the HILDA template keys)
  progress add|list         weekly plan/actual from the supervisor's reports; tests the critical-contract criteria
  status                    deviation, pace, projection, data checks and the next step
  route [package]           the packages (document sets) and how far this project is in one
  templates                 the 32 templates and where each one comes from
  need <template>           what a template still needs
  fill <template>           write the document into ./dokumen and register it
  doc list|add|set          the document table;  log "text" adds a dated note
  replacement               figures and route for a new contract that takes over unfinished work
  blanks / text / fillform / edit   fill the owner's own forms (the BPKP drafts in a dossier): blanks by index,
                            labels with --after, empty table cells with --cell, any text with --sub
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pbj_cmds as cmds  # noqa: E402
import pbj_fill as fill  # noqa: E402


def build() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--folder", default=".", help="project folder holding proyek.md (default: current)")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name, func, **kw):
        p = sub.add_parser(name, parents=[common], **kw)
        p.set_defaults(func=func)
        return p

    p = add("init", cmds.cmd_init, help="create proyek.md")
    p.add_argument("--set", nargs="*", metavar="key=value")
    p = add("set", cmds.cmd_set, help="set facts")
    p.add_argument("items", nargs="+", metavar="key=value")
    add("get", cmds.cmd_get, help="show the facts")

    p = add("progress", cmds.cmd_progress, help="weekly progress")
    p.add_argument("action", choices=["add", "list"])
    p.add_argument("--pekan", type=int)
    p.add_argument("--mulai")
    p.add_argument("--selesai")
    p.add_argument("--rencana", type=float, help="cumulative planned %% at the end of the week")
    p.add_argument("--realisasi", type=float, help="cumulative actual %% at the end of the week")

    p = add("doc", cmds.cmd_doc, help="document table")
    p.add_argument("action", choices=["list", "add", "set"])
    p.add_argument("--template")
    p.add_argument("--naskah")
    p.add_argument("--nomor")
    p.add_argument("--tanggal")
    p.add_argument("--status")
    p.add_argument("--berkas")
    p.add_argument("--index", type=int)

    p = add("log", cmds.cmd_log, help="add a dated note")
    p.add_argument("text")
    add("status", cmds.cmd_status, help="where the contract stands and what to do next")
    p = add("route", cmds.cmd_route, help="packages and their steps")
    p.add_argument("name", nargs="?")
    add("templates", cmds.cmd_templates, help="list templates")
    p = add("replacement", cmds.cmd_replacement, help="new contract to cover an unfinished one")
    p.add_argument("--realisasi", type=float, help="cumulative actual %% (default: last progress row)")

    p = add("need", fill.cmd_need, help="keys a template still needs")
    p.add_argument("template")
    p.add_argument("--set", nargs="*", metavar="key=value")
    p.add_argument("--nomor")
    p = add("fill", fill.cmd_fill, help="write a document from a template")
    p.add_argument("template")
    p.add_argument("--set", nargs="*", metavar="key=value", help="values for this document (not kept unless --save)")
    p.add_argument("--nomor", help="document number from the register")
    p.add_argument("--tanggal", help="document date for the table (yyyy-mm-dd)")
    p.add_argument("--out")
    p.add_argument("--save", action="store_true", help="also keep the --set values in proyek.md")
    p.add_argument("--no-register", action="store_true")

    p = add("blanks", fill.cmd_blanks, help="list the blanks of an owner form")
    p.add_argument("form")
    p = add("text", fill.cmd_text, help="paragraph text of a form, as the anchors see it")
    p.add_argument("form")
    p = add("fillform", fill.cmd_fillform, help="fill blanks by index from a JSON map")
    p.add_argument("form")
    p.add_argument("--map", required=True, help='JSON file {"0": "text", "3": "text"}')
    p.add_argument("--out")
    p = add("edit", fill.cmd_edit, help="exact text substitution in a form")
    p.add_argument("form")
    p.add_argument("--sub", action="append", metavar="old=>new", help="replace every occurrence of exact text")
    p.add_argument("--after", action="append", metavar="label=>value", help="insert value right after the first occurrence of a label, e.g. 'Nama Paket:=> Renovasi'")
    p.add_argument("--cell", action="append", metavar="label=>value", help="write value into the empty cell next to a table label")
    p.add_argument("--out")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build().parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
