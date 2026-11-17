"""Rules that cross notes: link targets, the indicator-to-process mapping, the cap of three KRI, matrix limits.
A note that breaks one is refused with a message, never silently fixed."""

from __future__ import annotations

from gv_schema import ENTITIES, link_target

MAX_KRI_PER_RISK = 3
MATRIX_MIN, MATRIX_MAX = 2, 10


class VaultError(Exception):
    pass


_COMPUTED = "dihitung otomatis"
_FIXED = "tidak dapat diubah setelah dibuat"
PROTECTED: dict[str, dict[str, str]] = {
    "evaluasi": {**{k: "isi dengan 'rate'" for k in ("inherent", "residual", "expected", "actual")},
                 **{k: _COMPUTED for k in ("active_type", "active_cell", "trend", "closed", "sim_suggestion", "sim_date")},
                 **{k: _FIXED for k in ("pre", "fiscal_year", "matrix")}},
    "rencana": {"status": "pakai 'plan start' atau 'plan done'", "evaluation": _FIXED},
    "kri": {"status": "pakai 'kri retire'", "amber": "pakai 'kri threshold' (wajib beralasan)",
            "red": "pakai 'kri threshold' (wajib beralasan)", "risk": _FIXED},
    "pasang": {"risk": _FIXED, "process": _FIXED, "indicator": _FIXED},
    "insiden": {"pre": _FIXED},
    "draft": {"status": "diubah oleh 'draft accept' atau 'draft reject'", "kind": _FIXED},
}


def validate(vault, note, creating: bool, audit: bool = False) -> None:
    """audit=True is `check`: existing history is judged, so rules that only guard NEW edits (closed years) are skipped."""
    ent = ENTITIES[note.entity]
    for f in ent.fields:
        target = link_target(f)
        if target is None:
            continue
        values = note.fields.get(f.name)
        for value in ([values] if isinstance(values, str) else values or []):
            if value not in vault.notes or vault.notes[value].entity != target:
                raise VaultError(f"'{f.name}' menunjuk {value!r}, yang bukan catatan {target} yang ada")
    check = _CHECKS.get(note.entity)
    if check:
        check(vault, note, creating, audit)


def _matriks(vault, note, creating, audit):
    lo, hi = note.fields["max_likelihood"], note.fields["max_impact"]
    if not (MATRIX_MIN <= lo <= MATRIX_MAX and MATRIX_MIN <= hi <= MATRIX_MAX):
        raise VaultError(f"Jumlah level matriks harus {MATRIX_MIN} sampai {MATRIX_MAX}")


def _pasang(vault, note, creating, audit):
    f = note.fields
    if creating and f["indicator"] not in vault.notes[f["process"]].fields.get("indicators", []):
        raise VaultError(f"{f['indicator']} belum dipetakan ke {f['process']}: tambahkan ke kolom 'indicators' pada proses itu "
                         "(pemetaan indikator-proses)")
    if creating and not vault.notes[f["risk"]].fields.get("active", True):
        raise VaultError(f"{f['risk']} tidak aktif")
    twin = [n for n in vault.all("pasang") if n.id != note.id and all(n.fields[k] == f[k] for k in ("risk", "process", "indicator"))]
    if twin:
        raise VaultError(f"Pasangan risiko-proses-indikator ini sudah ada: {twin[0].id}")


def _evaluasi(vault, note, creating, audit):
    if creating and not vault.notes[note.fields["pre"]].fields.get("active", True):
        raise VaultError(f"{note.fields['pre']} tidak aktif, tidak dapat dievaluasi")


def _rencana(vault, note, creating, audit):
    ev = vault.notes[note.fields["evaluation"]]
    if ev.fields.get("closed") and not audit:
        raise VaultError(f"{ev.id} sudah ditutup (tutup buku): rencana tidak dapat ditambah atau diubah")
    if (note.fields.get("budget") or 0) < 0:
        raise VaultError("budget tidak boleh negatif")


def _check_order(f):
    amber, red = f.get("amber"), f.get("red")
    if amber is not None and red is not None:
        ok = amber <= red if f["direction"] == "higher_is_worse" else amber >= red
        if not ok:
            raise VaultError("Ambang kuning dan merah tidak urut: higher_is_worse butuh kuning <= merah, "
                             "lower_is_worse butuh kuning >= merah")


def _kri(vault, note, creating, audit):
    _check_order(note.fields)
    if note.fields.get("status", "ACTIVE") == "ACTIVE":
        others = [n for n in vault.all("kri") if n.id != note.id and n.fields["risk"] == note.fields["risk"]
                  and n.fields.get("status") == "ACTIVE"]
        if len(others) >= MAX_KRI_PER_RISK:
            raise VaultError(f"Satu risiko maksimal {MAX_KRI_PER_RISK} KRI aktif ({', '.join(n.id for n in others)})")


def _insiden(vault, note, creating, audit):
    top = max((m.fields["max_impact"] for m in vault.all("matriks")), default=MATRIX_MAX)
    if not 1 <= note.fields["impact"] <= top:
        raise VaultError(f"impact adalah level dampak 1 sampai {top} pada matriks, bukan {note.fields['impact']}")


_CHECKS = {"matriks": _matriks, "pasang": _pasang, "evaluasi": _evaluasi, "rencana": _rencana, "kri": _kri, "insiden": _insiden}
