"""Commands of ``pbj.py`` that work on the tracker (init, set, progress, doc, log, status, route, replacement)."""

from __future__ import annotations

import difflib
from datetime import date
from pathlib import Path

import pbj_catalog as catalog
from pbj_derived import parse_amount, parse_iso_date
from pbj_progress import analyse, evaluate, id_num, row_label
from pbj_tracker import META, STATUSES, Project

PL_CEILING_KONSTRUKSI = 400_000_000  # Perpres 16/2018 Pasal 38 as amended by Perpres 46/2025


def rupiah(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def pairs(items) -> dict[str, str]:
    out = {}
    for item in items or []:
        key, sep, value = item.partition("=")
        if not sep or not key.strip():
            raise SystemExit(f"expected key=value, got '{item}'")
        out[key.strip()] = value.strip()
    return out


def check_value(key: str, value: str) -> None:
    if key in META:
        return
    if not catalog.known_key(key):
        close = difflib.get_close_matches(key, catalog.vocabulary(), n=4)
        raise SystemExit(f"unknown key '{key}'" + (f"; did you mean {', '.join(close)}?" if close else "; see references/kunci-isian.md"))
    kind = catalog.kind(key)
    if value and kind == "date" and not parse_iso_date(value):
        raise SystemExit(f"{key} is a date: use yyyy-mm-dd (got '{value}')")
    if value and kind == "number" and parse_amount(value) is None:
        raise SystemExit(f"{key} is a number: got '{value}'")


def load(args) -> Project:
    return Project.find(Path(args.folder))


def cmd_init(args) -> None:
    path = Path(args.folder) / "proyek.md"
    if path.exists():
        raise SystemExit(f"{path} already exists; use `set` to change it")
    project = Project(path)
    for key, value in pairs(args.set).items():
        check_value(key, value)
        project.set(key, value)
    project.note("proyek dicatat")
    project.save()
    print(f"created {path}")


def cmd_set(args) -> None:
    project = load(args)
    for key, value in pairs(args.items).items():
        check_value(key, value)
        project.set(key, value)
        print(f"{key} = {value}")
    project.save()


def cmd_get(args) -> None:
    for key, value in load(args).data.items():
        print(f"{key}: {value}" + (f"   ({catalog.label(key)})" if catalog.known_key(key) else ""))


def cmd_progress(args) -> None:
    project = load(args)
    if args.action == "add":
        for name in ("pekan", "mulai", "selesai", "rencana", "realisasi"):
            if getattr(args, name) is None:
                raise SystemExit(f"progress add needs --{name}")
        if not (parse_iso_date(args.mulai) and parse_iso_date(args.selesai)):
            raise SystemExit("--mulai and --selesai are dates: yyyy-mm-dd")
        if not (0 <= args.rencana <= 100 and 0 <= args.realisasi <= 100):
            raise SystemExit("--rencana and --realisasi are cumulative percentages between 0 and 100")
        row = {"pekan": args.pekan, "mulai": args.mulai, "selesai": args.selesai, "rencana": args.rencana, "realisasi": args.realisasi}
        replaced = project.add_progress(row)
        project.save()
        print(("replaced" if replaced else "added") + f" week {args.pekan}: {row_label(row)}")
        return
    for r in project.progress:
        ev = evaluate(r["rencana"], r["realisasi"])
        print(f"pekan {r['pekan']:>2}  {r['mulai']} s/d {r['selesai']}  rencana {id_num(r['rencana']):>6}  realisasi {id_num(r['realisasi']):>6}  deviasi {id_num(ev['deviasi']):>7}  {row_label(r)}")


def cmd_doc(args) -> None:
    project = load(args)
    if args.action == "list":
        for i, d in enumerate(project.docs, 1):
            print(f"{i:>2}. [{d['status']}] {d['naskah']} ({d['template']}) nomor {d['nomor'] or '-'} tanggal {d['tanggal'] or '-'}  {d['berkas']}")
        return
    if args.action == "add":
        catalog.template(args.template)
        project.add_doc({"template": args.template, "naskah": args.naskah or catalog.template(args.template)["name"], "nomor": args.nomor or "", "tanggal": args.tanggal or "", "status": args.status or "draf", "berkas": args.berkas or ""})
    else:  # set
        if not args.index or not 1 <= args.index <= len(project.docs):
            raise SystemExit("doc set needs --index from `doc list`")
        doc = project.docs[args.index - 1]
        for field in ("nomor", "tanggal", "status", "berkas"):
            if getattr(args, field):
                doc[field] = getattr(args, field)
    for d in project.docs:
        if d["status"] not in STATUSES:
            raise SystemExit(f"status must be one of {', '.join(STATUSES)}")
    project.save()
    print("ok")


def cmd_log(args) -> None:
    project = load(args)
    project.note(args.text)
    project.save()


def cmd_status(args) -> None:
    project = load(args)
    d = project.data
    print(f"{d.get('nama_paket', '(nama_paket belum diisi)')}  |  kontrak {d.get('nomor_spk', '-')} ({d.get('tanggal_spk', '-')})  |  nilai {d.get('nilai_kontrak', '-')}")
    result = analyse(d, project.progress, project.docs)
    for line in result["lines"]:
        print("  " + line)
    counts: dict[str, int] = {}
    for doc in project.docs:
        counts[doc["status"]] = counts.get(doc["status"], 0) + 1
    print("  Dokumen: " + (", ".join(f"{n} {s}" for s, n in counts.items()) if counts else "belum ada"))
    for check in result["checks"]:
        print("  [periksa data] " + check)
    for advice in result["advice"]:
        print("  [langkah] " + advice)
    value = parse_amount(d.get("nilai_kontrak") or d.get("nilai_hps"))
    if d.get("metode", "").lower().startswith("pengadaan langsung") and value and value > PL_CEILING_KONSTRUKSI:
        print(f"  [periksa metode] nilai Rp{rupiah(value)} melebihi batas Pengadaan Langsung konstruksi Rp400 juta (Perpres 46/2025 Pasal 38)")


def cmd_route(args) -> None:
    if not args.name:
        for key, package in catalog.packages().items():
            print(f"{key:<20} {len(package['steps'])} langkah  {catalog.WHEN.get(key, package['name'])}")
        return
    project = load(args)
    available: dict[str, int] = {}
    for doc in project.docs:
        if doc["status"] != "batal":
            available[doc["template"]] = available.get(doc["template"], 0) + 1
    print(f"{catalog.packages()[args.name]['name']}")
    for step in catalog.steps(args.name):
        left = available.get(step["template"], 0)
        if left:
            available[step["template"]] = left - 1
        mark = "x" if left else " "
        extra = " (opsional)" if step["optional"] else ""
        after = f", setelah langkah {step['depends_on']}" if step["depends_on"] else ""
        print(f"  [{mark}] {step['no']:>2}. {step['name']}{extra}{after}  -> `fill {step['template']}`")


def cmd_templates(_args) -> None:
    for key, t in catalog.templates().items():
        print(f"{key:<26} {t['name']}  [{catalog.asal(key)}]")


def cmd_replacement(args) -> None:
    """Indicative figures and the route for a new contract that takes over unfinished work."""
    project = load(args)
    d = project.data
    value = parse_amount(d.get("nilai_kontrak"))
    done = args.realisasi if args.realisasi is not None else (project.progress[-1]["realisasi"] if project.progress else None)
    if value is None or done is None:
        raise SystemExit("replacement needs nilai_kontrak (set) and a realisasi (progress add or --realisasi)")
    rest = value * (1 - done / 100)
    print(f"Sisa pekerjaan (indikatif, hanya untuk memilih metode): {100 - done:.2f}% dari nilai kontrak = Rp{rupiah(rest)}")
    print("HPS pekerjaan lanjutan BUKAN angka ini: susun dari volume sisa pada BoQ pemilik (Excel) dan ketik nilainya sebagai nilai_hps.")
    if rest > PL_CEILING_KONSTRUKSI:
        print("Di atas Rp400 juta: bukan Pengadaan Langsung. Jalur setelah pemutusan: Penunjukan Langsung (Perpres 16/2018 Pasal 38 ayat (5) sebagaimana diubah Perpres 46/2025; Lampiran II LKPP 12/2021 angka 5.2.2) kepada pemenang cadangan; bila tidak ada atau tidak bersedia, penyedia lain dengan tahapan Penunjukan Langsung penuh atau Tender.")
    else:
        print("Di bawah batas Rp400 juta: Pengadaan Langsung dimungkinkan (`route pengadaan_langsung`); jalur Penunjukan Langsung kepada pemenang cadangan tetap tersedia setelah pemutusan.")
    print("Dokumen: lihat references/kontrak-pengganti.md. Persiapan memakai template nota_dinas, kak, permintaan_pl; formulir tender/kontrak yang belum ada diambil dari formulir pemilik di folder proyek (`blanks`, `fillform`).")
    print(f"Tanggal acuan: {date.today().isoformat()}; periksa status peraturan sebelum dipakai (references/status-regulasi.md).")

