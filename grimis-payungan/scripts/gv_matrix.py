"""The risk matrix: cells (likelihood x impact), scores, zones and the appetite threshold per fiscal year.
Cell score and the default zone bands are fixed here (zone by share of the maximum score)."""

from __future__ import annotations

from gv_notes import get_section, make_table, set_section, table_rows
from gv_rules import VaultError
from gv_schema import fmt_cell, parse_cell

ZONES = ((0.16, "LOW"), (0.36, "MODERATE_LOW"), (0.56, "MODERATE"), (0.76, "HIGH"), (1.01, "EXTREME"))


def default_zone(score: int, max_score: int) -> str:
    share = score / max_score
    return next(label for limit, label in ZONES if share <= limit)


class Matrix:
    def __init__(self, note):
        self.note = note
        self.id = note.id
        self.max_l = note.fields["max_likelihood"]
        self.max_i = note.fields["max_impact"]
        self._over = {}
        for r in table_rows(get_section(note.body, "Zona sel")):
            try:
                self._over[(int(r["kemungkinan"]), int(r["dampak"]))] = (int(r["skor"]), r["zona"])
            except (KeyError, ValueError):
                continue

    def check(self, cell) -> tuple[int, int]:
        l, i = parse_cell(cell)
        if not (1 <= l <= self.max_l and 1 <= i <= self.max_i):
            raise VaultError(f"Sel {cell} di luar matriks {self.id} (kemungkinan 1-{self.max_l}, dampak 1-{self.max_i})")
        return l, i

    def score(self, cell) -> int:
        l, i = self.check(cell)
        return self._over.get((l, i), (l * i, None))[0]

    def zone(self, cell) -> str:
        l, i = self.check(cell)
        over = self._over.get((l, i))
        return over[1] if over and over[1] else default_zone(l * i, self.max_l * self.max_i)

    def appetite(self, year: int):
        for r in table_rows(get_section(self.note.body, "Appetite")):
            if r.get("tahun") == str(year) and r.get("batas skor", "").isdigit():
                return int(r["batas skor"])
        return None

    def set_appetite(self, year: int, threshold: int) -> None:
        top = self.max_l * self.max_i
        if not 1 <= threshold <= top:
            raise VaultError(f"Batas appetite harus 1 sampai {top} (skor maksimum matriks ini)")
        rows = {r["tahun"]: r.get("batas skor", "") for r in table_rows(get_section(self.note.body, "Appetite")) if r.get("tahun")}
        rows[str(year)] = str(threshold)
        table = make_table(["Tahun", "Batas skor"], [[y, rows[y]] for y in sorted(rows)])
        self.note.body = set_section(self.note.body, "Appetite", table)

    def grid(self, counts: dict | None = None) -> str:
        """A text grid, impact across and likelihood down (highest likelihood on top); counts per cell if given."""
        counts = counts or {}
        head = "K\\D " + " ".join(f"{i:>5}" for i in range(1, self.max_i + 1))
        lines = [head]
        for l in range(self.max_l, 0, -1):
            lines.append(f"{l:>3} " + " ".join(f"{(counts.get(fmt_cell(l, i)) or self.score(fmt_cell(l, i))):>5}" for i in range(1, self.max_i + 1)))
        return "\n".join(lines)


def matrix_body(max_l: int, max_i: int) -> str:
    lv = lambda n: [[k, ""] for k in range(1, n + 1)]
    parts = [
        ("Label kemungkinan", make_table(["Level", "Label"], lv(max_l))),
        ("Label dampak", make_table(["Level", "Label"], lv(max_i))),
        ("Kriteria dampak", make_table(["Kategori", "Level", "Uraian"], [])),
        ("Appetite", make_table(["Tahun", "Batas skor"], [])),
        ("Zona sel", make_table(["Kemungkinan", "Dampak", "Skor", "Zona"], [])),
    ]
    intro = ("Skor sel = kemungkinan x dampak. Zona bawaan menurut persentase skor maksimum "
             "(<=16% LOW, <=36% MODERATE_LOW, <=56% MODERATE, <=76% HIGH, selebihnya EXTREME). "
             "Isi 'Zona sel' hanya untuk sel yang zonanya ingin diubah.\n")
    return intro + "\n" + "\n\n".join(f"## {t}\n\n{b}" for t, b in parts) + "\n"


def load(vault, matrix_id: str) -> Matrix:
    if not matrix_id or matrix_id not in vault.notes or vault.notes[matrix_id].entity != "matriks":
        raise VaultError(f"Matriks tidak ditemukan: {matrix_id}")
    return Matrix(vault.notes[matrix_id])
