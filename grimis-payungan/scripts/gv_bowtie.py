"""Bowtie renderer: draws an SVG and a Markdown note from the Penyebab/Dampak branches of a risk.
It never invents anything: branches must already be accepted into the risk note (`draft accept`), controls are the ones a
person picked with `bowtie attach` from the controls installed on an evaluation, and the active value, score, zone, appetite
and KRI status come from the engine. KRI positions come from the KRI `watch` field. Layout is in gv_bowtie_svg,
the click-to-open panels in gv_bowtie_pop, the picks in gv_bowtie_data. Standard library only."""

from __future__ import annotations

from pathlib import Path

import gv_report
from gv_bowtie_data import attachments, branches, installed
from gv_bowtie_pop import KRI_LABEL, limits, worst
from gv_bowtie_svg import svg_of  # noqa: F401  (re-exported)
from gv_draft import norm
from gv_notes import bullet_tree, get_section, make_table
from gv_rules import VaultError


def _kri_targets(kri, causes: list, impacts: list) -> list[str]:
    """A KRI watches a branch whose text/category matches `watch`; 'RISIKO' or an empty watch sits on the centre node."""
    watch = norm(kri.fields.get("watch"))
    if not watch or watch == "risiko":
        return ["centre"]
    hits: list[str] = []

    def walk(nodes, prefix: str) -> None:
        for idx, node in enumerate(nodes):
            key = f"{prefix}{idx}"
            hay = norm(node.get("text")) + " " + norm(node.get("category"))
            if len(watch) >= 4 and (watch in hay or (len(hay) >= 4 and hay in watch)):
                hits.append(key)
            walk(node.get("children", []), key + ".")

    walk(causes, "c")
    walk(impacts, "i")
    return hits or ["centre"]


def _status(kri):
    from gv_kri import current_status
    return current_status(kri)


def _assignments(vault, risk_id: str, row: dict | None, causes: list, impacts: list) -> dict:
    kris = row["kris"] if row else []
    if not kris:
        kris = [(k, *_status(k)) for k in vault.all("kri")
                if k.fields.get("risk") == risk_id and k.fields.get("status") != "RETIRED"]
    out: dict[str, list] = {}
    for kri, status, _last in kris:
        for key in _kri_targets(kri, causes, impacts):
            out.setdefault(key, []).append((kri, status))
    return out


def _view(vault, risk, row, causes: list, impacts: list) -> tuple[dict, list]:
    """What the SVG and the note draw: KRI per branch, picked controls per branch, and the picks that no longer fit."""
    info = {cid: {"note": vault.notes[cid], "evals": evals, "branches": []} for cid, evals in installed(vault, risk.id).items()}
    keys: dict[str, list[str]] = {}
    for key, text in branches(risk):
        keys.setdefault(norm(text), []).append(key)
    ctl: dict[str, list[str]] = {}
    stale: list[tuple[str, str]] = []
    for text, cid in attachments(risk):
        hit = keys.get(norm(text))
        if cid not in info or not hit:
            stale.append((text, cid))
            continue
        for key in hit:
            if cid not in ctl.setdefault(key, []):
                ctl[key].append(cid)
        info[cid]["branches"].append(text)
    view = {"kri": _assignments(vault, risk.id, row, causes, impacts), "ctl": ctl, "info": info,
            "unattached": sorted(c for c, i in info.items() if not i["branches"])}
    return view, stale


def _md_tree(nodes, view: dict, tag: str) -> str:
    """tag is 'c' for causes and 'i' for impacts so branch keys stay distinct."""
    if not nodes:
        return "Belum ada cabang pada catatan risiko."
    out = []

    def walk(items, indent: str, prefix: str) -> None:
        for idx, node in enumerate(items):
            key = f"{prefix}{idx}"
            cat = f" [{node['category']}]" if node.get("category") else ""
            marks = [f"{k.id} ({KRI_LABEL.get(s, s)})" for k, s in view["kri"].get(key, [])]
            marks += [f"{c} ({worst(view['info'][c]['evals'])})" for c in view["ctl"].get(key, [])]
            out.append(f"{indent}- {node.get('text')}{cat}" + (f" ← {', '.join(marks)}" if marks else ""))
            walk(node.get("children", []), indent + "  ", key + ".")

    walk(nodes, "", tag)
    return "\n".join(out)


def _controls_table(view: dict, stale: list) -> str:
    rows = []
    for cid, i in sorted(view["info"].items()):
        f = i["note"].fields
        status = "; ".join(f"{x['status']} ({x['eva']})" for x in i["evals"])
        rows.append([cid, f.get("control_type") or "-", status, "; ".join(i["branches"]) or "(belum dipasang pada cabang)", f.get("title", "")])
    rows += [[cid, "-", "-", f"{text} (cabang atau kontrol sudah tidak cocok, periksa dengan `check`)", "-"] for text, cid in stale]
    head = ["Kontrol", "Jenis", "Efektivitas (evaluasi)", "Dipasang pada cabang", "Judul"]
    return make_table(head, rows) if rows else "Belum ada kontrol terpasang pada evaluasi risiko ini."


def markdown_of(risk, row, causes, impacts, view: dict, stale: list, svg_name: str, process: str | None) -> str:
    f = risk.fields
    meta = [f"- Risiko: {risk.id} — {f.get('title', '')}",
            f"- Proses: {process or '-'}",
            (f"- Nilai aktif: {row['active_type']} {row['active_cell']}, skor {row['score']}, zona {row['zone']}; "
             f"appetite {row['threshold']} ({row['appetite']})") if row else "- Nilai aktif: belum dievaluasi",
            f"- Sumber cabang: `02-Kamus/Risiko/{risk.id}.md` (bagian Penyebab dan Dampak; kontrol pada bagian Kontrol bowtie)"]
    note = (f"*Rincian KRI dan kontrol muncul sebagai popup bila `{svg_name}` dibuka di peramban. Gambar yang tertanam "
            f"di Obsidian bersifat statis, jadi rincian yang sama ada pada tabel di bawah.*")
    md = [f"# Bowtie {risk.id} — {f.get('title', '')}", ""] + meta + ["", f"![Bowtie {risk.id}]({svg_name})", "", note, "",
                                                                      "## Penyebab", "", _md_tree(causes, view, "c"), "",
                                                                      "## Dampak", "", _md_tree(impacts, view, "i"), "",
                                                                      "## Kontrol terpasang", "", _controls_table(view, stale), "",
                                                                      "## Posisi KRI", ""]
    rows = []
    for key, items in sorted(view["kri"].items()):
        for kri, status in items:
            target = "Simpul risiko" if key == "centre" else ("Penyebab" if key.startswith("c") else "Dampak") + " " + key
            last = _status(kri)[1]
            rows.append([kri.id, kri.fields.get("title", ""), kri.fields.get("watch") or "RISIKO", target,
                         KRI_LABEL.get(status, status), limits(kri), f"{last[0]} = {last[1]:g}" if last else "-"])
    md.append(make_table(["KRI", "Nama", "Watch", "Posisi", "Status", "Ambang", "Pembacaan terakhir"], rows) if rows
              else "Belum ada KRI aktif yang memantau risiko ini.")
    return "\n".join(md).rstrip() + "\n"


def render(vault, risks: list[str] | None = None, above_appetite: bool = False, out: str | None = None) -> list[Path]:
    year = vault.cfg["fiscal_year"]
    rows = gv_report.profile(vault, year)
    by_risk: dict[str, dict] = {}
    for row in rows:
        by_risk.setdefault(row["risk"].id, row)
    if above_appetite:
        ids = [r["risk"].id for r in rows if r["appetite"] == "DI_ATAS_APPETITE"]
    else:
        ids = list(risks or [])
    if not ids:
        raise VaultError("Sebutkan ID risiko (mis. RSK-009) atau pakai --above-appetite")
    folder = Path(out) if out else vault.root / "99-Laporan" / "Bowtie"
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for risk_id in dict.fromkeys(ids):
        risk = vault.get(risk_id)
        if risk.entity != "risiko":
            raise VaultError(f"{risk_id} bukan risiko")
        row = by_risk.get(risk_id)
        causes = bullet_tree(get_section(risk.body, "Penyebab"))
        impacts = bullet_tree(get_section(risk.body, "Dampak"))
        if not causes and not impacts:
            raise VaultError(f"{risk_id} belum punya cabang Penyebab/Dampak. Buat draft bowtie dan accept dulu.")
        view, stale = _view(vault, risk, row, causes, impacts)
        process = row["process"].fields.get("title") if row else None
        svg_name = risk_id + ".svg"
        (folder / svg_name).write_text(svg_of(risk, row, causes, impacts, view), encoding="utf-8", newline="\n")
        md_path = folder / (risk_id + ".md")
        md_path.write_text(markdown_of(risk, row, causes, impacts, view, stale, svg_name, process), encoding="utf-8", newline="\n")
        written.append(md_path)
    return written
