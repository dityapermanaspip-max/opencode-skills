"""AI drafts. Claude proposes into `_Draft/DRF-nnn.md` (a JSON list of items); nothing becomes register data until a person
accepts items with `draft accept`. AI proposes, a human decides.
Kinds: konteks (mandate/objective/indicator/process), risiko (risk events for a process), bowtie (causes/impacts of a
risk), kri (indicator suggestions; thresholds are never taken from a draft)."""

from __future__ import annotations

import json
import re

from gv_notes import bullet_tree, get_section, make_bullet_tree, make_table, set_section, table_rows
from gv_rules import VaultError
from gv_schema import CAUSE_CATEGORIES, IMPACT_CATEGORIES

_JSON = re.compile(r"```json\s*\n(.*?)\n```", re.S)
_TARGET = {"konteks": None, "risiko": "proses", "bowtie": "risiko", "kri": "risiko"}
_LEVELS = {"mandat": "mandat", "sasaran": "sasaran", "indikator": "indikator", "proses": "proses"}


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def items_of(note) -> list[dict]:
    m = _JSON.search(note.body)
    if not m:
        raise VaultError(f"{note.id}: blok ```json tidak ditemukan")
    data = json.loads(m.group(1))
    return data["items"] if isinstance(data, dict) else data


def results_of(note) -> dict[int, tuple[str, str]]:
    return {int(r["no"]): (r["status"], r.get("catatan", "")) for r in table_rows(get_section(note.body, "Hasil")) if r.get("no", "").isdigit()}


def _write_results(note, results: dict) -> None:
    note.body = set_section(note.body, "Hasil", make_table(["No", "Status", "Catatan"], [[n, s, c] for n, (s, c) in sorted(results.items())]))
    done = [s for s, _ in results.values()]
    note.fields["status"] = ("DRAFT" if all(s == "BELUM" for s in done) else "PARTIAL" if "BELUM" in done
                             else "REJECTED" if all(s == "DITOLAK" for s in done) else "ACCEPTED")


def create(vault, kind: str, target: str | None, items: list[dict], summary: str = "") -> object:
    if kind not in _TARGET:
        raise VaultError(f"Jenis draft harus salah satu dari {', '.join(_TARGET)}")
    want = _TARGET[kind]
    if want and (not target or target not in vault.notes or vault.notes[target].entity != want):
        raise VaultError(f"Draft {kind} butuh --target berupa {want} yang ada (mis. {'PRS' if want == 'proses' else 'RSK'}-001)")
    if not items:
        raise VaultError("Draft kosong: tidak ada item")
    body = (f"{summary or 'Usulan AI. Belum menjadi data register sampai diterima.'}\n\n```json\n"
            + json.dumps({"items": items}, ensure_ascii=False, indent=2) + "\n```\n")
    note = vault.create("draft", {"kind": kind, "target": target}, body=body, who="draft new")
    _write_results(note, {n: ("BELUM", "") for n in range(1, len(items) + 1)})
    vault.save(note)
    return note


def _pick(note, wanted):
    items, res = items_of(note), results_of(note)
    nos = wanted or [n for n in range(1, len(items) + 1) if res.get(n, ("BELUM",))[0] == "BELUM"]
    bad = [n for n in nos if not 1 <= n <= len(items)]
    if bad:
        raise VaultError(f"Nomor item di luar draft (1-{len(items)}): {bad}")
    return items, res, nos


def accept(vault, drf_id: str, wanted: list[int] | None = None) -> list[str]:
    note = vault.get(drf_id)
    items, res, nos = _pick(note, wanted)
    made, refs = [], {}
    for n in nos:
        if res.get(n, ("BELUM",))[0] == "DITERIMA":
            continue
        try:
            made_n = _accept_item(vault, note, items[n - 1], refs)
            res[n] = ("DITERIMA", ", ".join(made_n))
            made += made_n
        except VaultError as exc:
            res[n] = ("BELUM", f"gagal: {exc}")
            made.append(f"item {n} GAGAL: {exc}")
    _write_results(note, res)
    vault.save(note)
    vault.log("draft accept", drf_id, f"item {nos}: {len([m for m in made if 'GAGAL' not in m])} catatan dibuat/diubah")
    return made


def reject(vault, drf_id: str, wanted: list[int] | None, reason: str = "") -> int:
    note = vault.get(drf_id)
    items, res, nos = _pick(note, wanted)
    target = vault.notes.get(note.fields.get("target") or "")
    for n in nos:
        res[n] = ("DITOLAK", reason)
        text = items[n - 1].get("title") or items[n - 1].get("description") or items[n - 1].get("name") or ""
        if target and text:  # a rejected suggestion is remembered so the next draft does not repeat it
            old = bullet_tree(get_section(target.body, "Saran ditolak"))
            if norm(text) not in {norm(o["text"]) for o in old}:
                target.body = set_section(target.body, "Saran ditolak", make_bullet_tree(old + [{"text": text, "category": None, "children": []}]))
                vault.save(target)
    _write_results(note, res)
    vault.save(note)
    vault.log("draft reject", drf_id, f"item {nos}: {reason}")
    return len(nos)


def describe(note) -> str:
    items, res = items_of(note), results_of(note)
    lines = [f"{note.id} [{note.fields['kind']}] target {note.fields.get('target') or '-'} status {note.fields['status']}"]
    for n, it in enumerate(items, 1):
        label = it.get("title") or it.get("description") or it.get("name") or json.dumps(it, ensure_ascii=False)[:80]
        extra = f" [{it['category']}]" if it.get("category") else f" (cocok dgn {it['match']})" if it.get("match") else ""
        lines.append(f"  {n}. {label}{extra}  -> {res.get(n, ('BELUM',))[0]}")
    return "\n".join(lines)


def _accept_item(vault, note, it: dict, refs: dict) -> list[str]:
    kind, target = note.fields["kind"], note.fields.get("target")
    if kind == "konteks":
        return _konteks(vault, it, refs)
    if kind == "risiko":
        return _risiko(vault, target, it)
    if kind == "bowtie":
        return _bowtie(vault, target, it)
    return _kri(vault, target, it)


def _konteks(vault, it: dict, refs: dict) -> list[str]:
    level = _LEVELS.get(it.get("level", ""))
    if not level:
        raise VaultError(f"level harus salah satu dari {', '.join(_LEVELS)}")
    resolve = lambda ref: refs.get(ref, ref)
    raw = {"title": it.get("title")}
    if level == "mandat":
        raw["source"] = it.get("source")
    elif level == "sasaran":
        raw["mandate"] = resolve(it.get("parent"))
    elif level == "indikator":
        raw.update(objective=resolve(it.get("parent")), unit=it.get("unit"), target=it.get("target"))
    else:
        raw.update(owner=it.get("owner"), indicators=[resolve(x) for x in it.get("indicators", [])])
    created = vault.create(level, raw, who="draft accept")
    if it.get("ref"):
        refs[it["ref"]] = created.id
    return [created.id]


def _risiko(vault, process: str, it: dict) -> list[str]:
    match = it.get("match")
    made = []
    if match:
        if match not in vault.notes or vault.notes[match].entity != "risiko":
            raise VaultError(f"match {match} bukan risiko di kamus")
        risk = vault.notes[match]
    else:
        dup = next((r for r in vault.all("risiko") if norm(r.fields["title"]) == norm(it.get("title", ""))), None)
        risk = dup or vault.create("risiko", {"title": it.get("title"), "description": it.get("description")}, who="draft accept")
        made.append(risk.id)
    anchor = vault.create("pasang", {"risk": risk.id, "process": process, "indicator": it.get("indicator")}, who="draft accept")
    return made + [anchor.id]


def _bowtie(vault, risk_id: str, it: dict) -> list[str]:
    risk = vault.notes[risk_id]
    kind = it.get("type")
    if kind not in ("cause", "impact"):
        raise VaultError("type harus 'cause' atau 'impact'")
    section, allowed = ("Penyebab", CAUSE_CATEGORIES) if kind == "cause" else ("Dampak", IMPACT_CATEGORIES)
    tree = bullet_tree(get_section(risk.body, section))
    seen = {norm(x) for x in _texts(tree)} | {norm(x["text"]) for x in bullet_tree(get_section(risk.body, "Saran ditolak"))}

    def clean(node):
        text = node.get("description") or node.get("text") or ""
        if not text.strip() or norm(text) in seen:
            return None
        seen.add(norm(text))
        cat = node.get("category") if node.get("category") in allowed else None
        kids = [k for k in (clean(c) for c in node.get("children", [])) if k]
        return {"text": text.strip(), "category": cat, "children": kids}

    node = clean(it)
    if node is None:
        raise VaultError("sudah ada atau pernah ditolak (duplikat/parafrasa persis)")
    risk.body = set_section(risk.body, section, make_bullet_tree(tree + [node]))
    vault.save(risk)
    return [f"{risk_id}:{section.lower()}"]


def _texts(tree):
    for n in tree:
        yield n["text"]
        yield from _texts(n["children"])


def _kri(vault, risk_id: str, it: dict) -> list[str]:
    raw = {"risk": risk_id, "title": it.get("title") or it.get("name"), "what_measured": it.get("what_measured"), "unit": it.get("unit"),
           "kri_type": it.get("kri_type"), "direction": it.get("direction"), "frequency": it.get("frequency"), "watch": it.get("watch")}
    why = f"## Alasan\n\n{it['rationale']}\n" if it.get("rationale") else ""
    kri = vault.create("kri", raw, body=why, who="draft accept")  # thresholds stay empty on purpose: a person sets them with 'kri threshold'
    return [kri.id + (" (ambang dari draft diabaikan)" if it.get("amber") is not None or it.get("red") is not None else "")]
