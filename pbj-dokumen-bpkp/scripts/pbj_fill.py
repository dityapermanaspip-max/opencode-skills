"""Commands of ``pbj.py`` that produce documents: need, fill (HILDA templates) and blanks, fillform, edit
(the owner's own forms, e.g. the BPKP drafts kept in a dossier folder)."""

from __future__ import annotations

import json
from pathlib import Path

import pbj_catalog as catalog
import pbj_docx as docx
from pbj_cmds import check_value, load, pairs
from pbj_derived import parse_derived_key, resolve
from pbj_progress import evaluate
from pbj_tracker import META

AUTO = "nomor_surat"  # HILDA numbers a document from its register; here the person gives the number


def _from_progress(project) -> dict[str, str]:
    """Facts that follow from the last progress row (the supervisor's report); typed values win."""
    if not project.progress:
        return {}
    row = project.progress[-1]
    ev = evaluate(row["rencana"], row["realisasi"])
    comma = lambda x: f"{x:.2f}".replace(".", ",")  # noqa: E731
    return {
        "rencana_fisik_persen": comma(row["rencana"]),
        "realisasi_fisik_persen": comma(row["realisasi"]),
        "deviasi_persen": comma(max(-ev["deviasi"], 0)),
        "ambang_kritis_persen": f"{ev['ambang']:g}",
        "persentase_realisasi": f"{comma(row['realisasi'])}%",
    }


def _values(project, args) -> dict[str, str]:
    values = {**_from_progress(project), **{k: v for k, v in project.data.items() if k not in META}}
    for key, value in pairs(getattr(args, "set", None)).items():
        check_value(key, value)
        values[key] = value
    if getattr(args, "nomor", None):
        values[AUTO] = args.nomor
    return values


def _base_keys(template_key: str) -> list[str]:
    keys = docx.marker_keys(docx.open_docx(catalog.template_path(template_key)))
    return sorted({(parse_derived_key(k) or (k,))[0] for k in keys})


def cmd_need(args) -> None:
    project = load(args)
    values = _values(project, args)
    keys = _base_keys(args.template)
    missing = [k for k in keys if str(values.get(k, "")).strip() == ""]
    print(f"{catalog.template(args.template)['name']}  [{catalog.asal(args.template)}]")
    print(f"{len(keys) - len(missing)} of {len(keys)} keys filled; missing ({len(missing)}):")
    for key in missing:
        note = "  <- number from the register, pass --nomor" if key == AUTO else ""
        print(f"  {key} ({catalog.kind(key)}): {catalog.label(key)}{note}")


def cmd_fill(args) -> None:
    project = load(args)
    values = _values(project, args)
    template = catalog.template(args.template)
    document = docx.open_docx(catalog.template_path(args.template))
    labels, unfilled = catalog.manifest()["placeholder_labels"], set()

    def resolve_marker(key: str):
        text = resolve(key, catalog.kind(key), values)
        if text is None:
            unfilled.add(key)
            return f"[{labels.get(key) or catalog.label(key)}]"
        return text

    count, unknown = docx.fill_markers(document, resolve_marker)
    out = Path(args.out) if args.out else Path(args.folder) / "dokumen" / f"{len(project.docs) + 1:02d}_{Path(template['file']).stem}.docx"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise SystemExit(f"{out} exists; pass --out for another name")
    document.save(str(out))
    if not args.no_register:
        try:
            berkas = out.resolve().relative_to(Path(args.folder).resolve()).as_posix()
        except ValueError:
            berkas = str(out)
        project.add_doc({"template": args.template, "naskah": template["name"], "nomor": values.get(AUTO, ""), "tanggal": args.tanggal or "", "status": "draf", "berkas": berkas})
        if args.save:
            for key, value in pairs(args.set).items():
                project.set(key, value)
        project.save()
    print(f"wrote {out}  ({count} markers filled)  [{catalog.asal(args.template)}]")
    if template["key"] in catalog.manifest().get("manual_review", []):
        print("NOTE: parts of this document keep the LKPP model's text and need manual review.")
    if unfilled:
        print(f"{len(unfilled)} value(s) missing, shown in [brackets] in the document:")
        for key in sorted(unfilled):
            print(f"  {key}: {catalog.label(key)}")
    if unknown:
        print("unknown markers left untouched: " + ", ".join(sorted(unknown)))


def cmd_blanks(args) -> None:
    for blank in docx.list_blanks(docx.open_docx(args.form)):
        print(f"{blank['index']:>3}  {blank['jenis']:<11} {blank['bagian']:<22} {blank['konteks']}")


def cmd_text(args) -> None:
    """Paragraph text as the anchors of `edit --after/--sub` will see it."""
    for number, (where, text) in enumerate(docx.paragraph_texts(docx.open_docx(args.form))):
        print(f"{number:>3} {where:<22} {text}")


def _out_path(args, suffix: str) -> Path:
    form = Path(args.form)
    out = Path(args.out) if args.out else Path(args.folder) / "dokumen" / f"{form.stem}{suffix}.docx"
    if out.resolve() == form.resolve():
        raise SystemExit("--out must not be the source form")
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def cmd_fillform(args) -> None:
    document = docx.open_docx(args.form)
    mapping = {int(k): str(v) for k, v in json.loads(Path(args.map).read_text(encoding="utf-8")).items()}
    total = len(docx.list_blanks(docx.open_docx(args.form)))
    bad = [i for i in mapping if not 0 <= i < total]
    if bad:
        raise SystemExit(f"indexes out of range (the form has {total} blanks): {bad}")
    done = docx.fill_blanks(document, mapping)
    out = _out_path(args, "_isi")
    document.save(str(out))
    print(f"wrote {out}  ({done} of {total} blanks filled; {total - done} left as they were)")


def cmd_edit(args) -> None:
    document = docx.open_docx(args.form)
    for item in args.sub or []:
        old, sep, new = item.partition("=>")
        if not sep or not old:
            raise SystemExit(f"--sub expects 'old=>new', got '{item}'")
        print(f"{docx.literal_replace(document, old, new)} x  replace {old!r} => {new!r}")
    for item in args.after or []:
        anchor, sep, value = item.partition("=>")
        if not sep or not anchor:
            raise SystemExit(f"--after expects 'label=>value', got '{item}'")
        print(f"{docx.insert_after(document, anchor, value)} x  after {anchor!r}: {value!r}")
    for item in args.cell or []:
        label, sep, value = item.partition("=>")
        if not sep or not label:
            raise SystemExit(f"--cell expects 'label=>value', got '{item}'")
        print(f"{docx.fill_cell(document, label, value)} x  cell {label!r}: {value!r}")
    out = _out_path(args, "_ubah")
    document.save(str(out))
    print(f"wrote {out}")
