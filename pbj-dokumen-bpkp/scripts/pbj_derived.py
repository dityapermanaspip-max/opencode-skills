"""Derived placeholder values: amounts in words, Rupiah format, Indonesian date words.

A Python port of ``darkhive-fev2/src/lib/hilda/derivedValues.ts`` so a document filled here reads exactly
like one rendered by HILDA. The user types ONE number or date; every word form is computed from it, so
an amount in words can never disagree with the amount in figures. An unparsable base value yields an
empty string, never a guess.

Marker forms (key ``K`` is the typed base value):
  number: K__rupiah (Rp155.373.000,00), K__rupiah_terbilang, K__terbilang
  date:   K (long date, 17 September 2026), K__hari, K__tanggal_kata, K__bulan, K__tahun, K__tahun_kata
  text:   K__kapital
"""

from __future__ import annotations

import math
import re
from datetime import date

SEP = "__"
NUMBER_FORMS = {"rupiah", "rupiah_terbilang", "terbilang"}
DATE_FORMS = {"hari", "tanggal_kata", "bulan", "tahun", "tahun_kata"}
TEXT_FORMS = {"kapital"}

UNITS = ["", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan", "sepuluh", "sebelas"]
SCALES = [(10**12, "triliun"), (10**9, "miliar"), (10**6, "juta"), (1000, "ribu")]
MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
WEEKDAYS = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]


def parse_derived_key(key: str):
    """('base', 'form', 'family') for ``base__form`` keys, else None."""
    at = key.rfind(SEP)
    if at <= 0:
        return None
    base, form = key[:at], key[at + len(SEP):]
    for family, forms in (("number", NUMBER_FORMS), ("date", DATE_FORMS), ("text", TEXT_FORMS)):
        if form in forms:
            return base, form, family
    return None


def _below_1000(n: int) -> str:
    if n < 12:
        return UNITS[n]
    if n < 20:
        return f"{UNITS[n - 10]} belas"
    if n < 100:
        rest = n % 10
        return f"{UNITS[n // 10]} puluh" + (f" {UNITS[rest]}" if rest else "")
    if n < 200:
        return "seratus" + (f" {_below_1000(n - 100)}" if n > 100 else "")
    rest = n % 100
    return f"{UNITS[n // 100]} ratus" + (f" {_below_1000(rest)}" if rest else "")


def terbilang(value) -> str:
    """Indonesian words for a non-negative integer, lower case ('seribu', 'seratus lima puluh')."""
    try:
        n = math.floor(value)
    except (TypeError, ValueError, OverflowError):
        return ""
    if n < 0:
        return ""
    if n == 0:
        return "nol"
    parts = []
    for size, name in SCALES:
        if n < size:
            continue
        count, n = divmod(n, size)
        # "seribu", not "satu ribu"; every larger scale keeps "satu" (satu juta).
        parts.append("seribu" if size == 1000 and count == 1 else f"{terbilang(count)} {name}")
    if n > 0:
        parts.append(_below_1000(n))
    return " ".join(parts)


def _title(text: str) -> str:
    return re.sub(r"\b[^\W\d_]", lambda m: m.group().upper(), text)


def parse_amount(value):
    """155373000, '155373000.5', '1.500' (Indonesian thousands), '155.373.000,50', 'Rp155.373.000' parse;
    anything else is None. A single dot followed by exactly three digits is a thousands separator,
    because Indonesian amounts never use a decimal dot."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(value) and value >= 0 else None
    raw = re.sub(r"^Rp\.?\s*", "", str(value if value is not None else "").strip(), flags=re.I)
    if not raw:
        return None
    if re.fullmatch(r"\d+", raw):
        return float(raw)
    if re.fullmatch(r"\d+\.\d{3}", raw):
        return float(raw.replace(".", ""))
    if re.fullmatch(r"\d+\.\d+", raw):
        return float(raw)
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", raw):
        return float(raw.replace(".", "").replace(",", "."))
    if re.fullmatch(r"\d+,\d+", raw):
        return float(raw.replace(",", "."))
    return None


def _split_cents(amount: float):
    total = math.floor(amount * 100 + 0.5)  # JavaScript Math.round: halves go up
    return total // 100, total % 100


def format_rupiah(amount: float) -> str:
    rupiah, sen = _split_cents(amount)
    return f"Rp{rupiah:,}".replace(",", ".") + f",{sen:02d}"


def rupiah_terbilang(amount: float) -> str:
    rupiah, sen = _split_cents(amount)
    return f"{terbilang(rupiah)} rupiah" + (f" dan {terbilang(sen)} sen" if sen else "")


def parse_iso_date(value):
    """(year, month, day) for yyyy-mm-dd, else None."""
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", str(value if value is not None else "").strip())
    if not match:
        return None
    year, month, day = (int(g) for g in match.groups())
    try:
        date(year, month, day)
    except ValueError:
        return None
    return year, month, day


def long_date(parts) -> str:
    year, month, day = parts
    return f"{day} {MONTHS[month - 1]} {year}"


def derive_value(base_value, form: str, family: str) -> str:
    if family == "text":
        return str(base_value if base_value is not None else "").upper()
    if family == "number":
        amount = parse_amount(base_value)
        if amount is None:
            return ""
        if form == "rupiah":
            return format_rupiah(amount)
        if form == "rupiah_terbilang":
            return rupiah_terbilang(amount)
        return terbilang(amount)
    parts = parse_iso_date(base_value)
    if not parts:
        return ""
    year, month, day = parts
    if form == "hari":
        return WEEKDAYS[(date(year, month, day).weekday() + 1) % 7]
    if form == "tanggal_kata":
        return _title(terbilang(day))
    if form == "bulan":
        return MONTHS[month - 1]
    if form == "tahun":
        return str(year)
    return _title(terbilang(year))


def resolve(key: str, kind: str, data: dict) -> str | None:
    """Final text for one marker key, or None when the typed base value is missing.

    ``kind`` is the placeholder kind of the key itself ('text', 'number' or 'date')."""
    derived = parse_derived_key(key)
    if derived:
        base, form, family = derived
        if str(data.get(base, "")).strip() == "":
            return None
        return derive_value(data.get(base), form, family)
    raw = data.get(key)
    if raw is None or str(raw).strip() == "":
        return None
    if kind == "date":
        parts = parse_iso_date(raw)
        return long_date(parts) if parts else str(raw)
    return str(raw)
