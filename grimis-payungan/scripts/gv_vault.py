"""The vault in memory: loads every note, hands out ids, validates and saves, and keeps the append-only LOG.md."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import gv_rules
from gv_notes import Note, read_note, write_note
from gv_schema import ENTITIES, F, coerce, entity_name, entity_of_id, from_store, to_store

CONFIG = (F("org", req=True), F("fiscal_year", "int", True), F("period_open", "bool", default=False),
          F("active_matrix", "link:matriks"))


VaultError = gv_rules.VaultError


class Vault:
    def __init__(self, root):
        self.root = Path(root).resolve()
        if not (self.root / "GRIMIS.md").is_file():
            raise VaultError(f"Bukan vault manajemen risiko (GRIMIS.md tidak ada): {self.root}. Buat dengan: grimis.py init <folder>")
        self.notes: dict[str, Note] = {}
        self.problems: list[str] = []
        self.cfg_note = read_note(self.root / "GRIMIS.md")
        self.cfg = {f.name: from_store(f, self.cfg_note.fields.get(f.name)) for f in CONFIG}
        self._load()

    # ---- loading -------------------------------------------------------------------------------------------
    def _load(self):
        for ent in ENTITIES.values():
            folder = self.root / ent.folder
            if not folder.is_dir():
                continue
            spec = {f.name: f for f in ent.fields}
            for path in sorted(folder.glob("*.md")):
                if not path.stem.startswith(ent.prefix + "-"):
                    continue
                try:
                    note = read_note(path, ent.name)
                except ValueError as exc:
                    self.problems.append(f"{path.name}: {exc}")
                    continue
                note.fields = {k: from_store(spec.get(k), v) for k, v in note.fields.items()}
                for f in ent.fields:  # stored empty list fields come back as [] and missing ones as defaults
                    if f.name not in note.fields and f.default is not None:
                        note.fields[f.name] = f.default
                self.notes[note.id] = note

    # ---- access --------------------------------------------------------------------------------------------
    def get(self, note_id: str) -> Note:
        if note_id not in self.notes:
            raise VaultError(f"Catatan tidak ditemukan: {note_id}")
        return self.notes[note_id]

    def all(self, entity: str) -> list[Note]:
        e = entity_name(entity)
        return sorted((n for n in self.notes.values() if n.entity == e), key=lambda n: n.id)

    def kind_of(self, note_id: str) -> str:
        return entity_of_id(note_id).name

    # ---- writing -------------------------------------------------------------------------------------------
    def save(self, note: Note) -> None:
        spec = {f.name: f for f in ENTITIES[note.entity].fields}
        ordered = {f.name: note.fields.get(f.name) for f in ENTITIES[note.entity].fields if f.name in note.fields}
        ordered.update({k: v for k, v in note.fields.items() if k not in spec})
        stored = Note(note.path, {k: to_store(spec.get(k), v) for k, v in ordered.items()}, note.body, note.entity)
        write_note(stored)
        self.notes[note.id] = note

    def save_config(self) -> None:
        spec = {f.name: f for f in CONFIG}
        fields = {k: to_store(spec.get(k), self.cfg.get(k)) for k in spec}
        fields.update({k: v for k, v in self.cfg_note.fields.items() if k not in spec})
        self.cfg_note.fields = fields
        write_note(self.cfg_note)

    def next_id(self, entity: str, raw: dict) -> str:
        ent = ENTITIES[entity_name(entity)]
        if ent.name == "evaluasi":
            pre = coerce(F("pre", "link:pasang", True), raw.get("pre"))
            year = int(raw.get("fiscal_year") or self.cfg["fiscal_year"])
            return f"EVA-{year}-{pre.split('-', 1)[1]}"
        top = max((int(n.id.rsplit("-", 1)[1]) for n in self.all(ent.name)), default=0)
        return f"{ent.prefix}-{top + 1:03d}"

    def create(self, entity: str, raw: dict, body: str = "", who: str = "new") -> Note:
        ent = ENTITIES[entity_name(entity)]
        raw = dict(raw)
        if ent.name == "evaluasi":  # year and matrix default to the working year and the active matrix
            raw.setdefault("fiscal_year", self.cfg["fiscal_year"])
            if not raw.get("matrix"):
                raw["matrix"] = self.cfg.get("active_matrix")
            if not raw["matrix"]:
                raise VaultError("Belum ada matriks aktif: jalankan 'matrix activate MTX-001' (atau beri matrix=MTX-...)")
        unknown = set(raw) - {f.name for f in ent.fields}
        if unknown:
            raise VaultError(f"Kolom tidak dikenal untuk {ent.name}: {', '.join(sorted(unknown))}")
        fields = {}
        for f in ent.fields:
            try:
                value = coerce(f, raw.get(f.name, f.default))
            except ValueError as exc:
                raise VaultError(str(exc)) from None
            fields[f.name] = f.default if value is None and f.default is not None else value
        note_id = self.next_id(ent.name, raw)
        if note_id in self.notes:
            raise VaultError(f"{note_id} sudah ada")
        note = Note(self.root / ent.folder / f"{note_id}.md", fields, body, ent.name)
        gv_rules.validate(self, note, creating=True)
        self.save(note)
        self.log(who, note_id, "dibuat")
        return note

    def update(self, note_id: str, raw: dict, who: str = "set") -> Note:
        note = self.get(note_id)
        spec = {f.name: f for f in ENTITIES[note.entity].fields}
        before = dict(note.fields)
        for key, value in raw.items():
            if key not in spec:
                raise VaultError(f"Kolom tidak dikenal untuk {note.entity}: {key}")
            if key in gv_rules.PROTECTED.get(note.entity, ()):
                raise VaultError(f"'{key}' pada {note.entity} tidak diubah dengan 'set': {gv_rules.PROTECTED[note.entity][key]}")
            try:
                note.fields[key] = coerce(spec[key], value)
            except ValueError as exc:
                note.fields = before
                raise VaultError(str(exc)) from None
        try:
            gv_rules.validate(self, note, creating=False)
        except VaultError:
            note.fields = before
            raise
        self.save(note)
        self.log(who, note_id, ", ".join(f"{k}: {before.get(k)!r} -> {note.fields.get(k)!r}" for k in raw))
        return note

    def log(self, who: str, note_id: str, detail: str) -> None:
        path = self.root / "LOG.md"
        if not path.exists():
            path.write_text("# Log perubahan\n\nCatatan tambah-saja. Jangan diubah atau dihapus.\n\n", encoding="utf-8", newline="\n")
        line = f"- {datetime.now():%Y-%m-%d %H:%M} | {who} | {note_id} | {' '.join(str(detail).split())}\n"
        with path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(line)
