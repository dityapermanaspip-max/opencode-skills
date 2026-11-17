"""Monte Carlo for one evaluation: a compound Poisson model, (standard library only).
Frequency N ~ Poisson(lambda), lambda = the incidents of the anchor in the fiscal year; severity is bootstrapped from the
observed impact levels; aggregate S = sum of N severities. The result is a SUGGESTION for a matrix cell, never applied alone."""

from __future__ import annotations

import math
import random
from datetime import date

from gv_cycle import _open_eval
from gv_matrix import load as load_matrix
from gv_notes import make_table, set_section
from gv_rules import VaultError
from gv_schema import fmt_cell


def poisson_draw(rng: random.Random, lam: float) -> int:
    """Knuth's algorithm."""
    if lam <= 0:
        return 0
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def percentile(sorted_vals: list, p: float) -> float:
    """Nearest rank; p is 0..100."""
    if not sorted_vals:
        return 0.0
    idx = max(0, min(len(sorted_vals) - 1, math.ceil(p / 100.0 * len(sorted_vals)) - 1))
    return float(sorted_vals[idx])


def run(lam: float, severities: list, iterations: int, rng: random.Random) -> dict:
    freq, agg = [], []
    for _ in range(iterations):
        n = poisson_draw(rng, lam)
        freq.append(n)
        agg.append(sum(rng.choice(severities) for _ in range(n)) if n else 0)
    freq.sort()
    agg.sort()
    sev = sorted(severities)

    def block(values, mean):
        return {"mean": mean, **{f"p{q}": percentile(values, q) for q in (50, 75, 90, 95, 99)}}

    return {
        "frequency": block(freq, lam),
        "severity": {**block(sev, sum(sev) / len(sev) if sev else 0.0), "histogram": {str(v): sev.count(v) for v in sorted(set(sev))}},
        "aggregate": {**block(agg, sum(agg) / iterations), "zero_share": agg.count(0) / iterations},
    }


def simulate(vault, eva_id: str, iterations: int = 10000, pct: int = 75, seed: int | None = None) -> dict:
    if not 100 <= iterations <= 100_000:
        raise VaultError("iterations harus 100 sampai 100.000")
    if not 1 <= pct <= 99:
        raise VaultError("percentile harus 1 sampai 99")
    ev = _open_eval(vault, eva_id)
    matrix = load_matrix(vault, ev.fields["matrix"])
    year = ev.fields["fiscal_year"]
    rows = sorted((i for i in vault.all("insiden") if i.fields["pre"] == ev.fields["pre"] and i.fields.get("use_in_simulation", True)
                   and str(i.fields["date"]).startswith(f"{year}-")), key=lambda i: (i.fields["date"], i.id))
    severities = [int(i.fields["impact"]) for i in rows]
    lam = float(len(severities))
    dist = run(lam, severities, iterations, random.Random(seed))
    sev_p = percentile(sorted(severities), pct)
    ll = max(1, min(matrix.max_l, int(round(dist["frequency"]["p75"]))))
    il = max(1, min(matrix.max_i, int(round(sev_p))))
    cell = fmt_cell(ll, il)
    summary = {"lambda": lam, "incident_count": len(severities), "iterations": iterations, "suggestion_percentile": pct,
               "no_incident_data": not severities, "suggested_cell": cell, "expected_impact": round(sev_p, 3), **dist}
    ev.fields["sim_suggestion"] = cell
    ev.fields["sim_date"] = date.today().isoformat()
    ev.body = set_section(ev.body, "Simulasi Monte Carlo", _section(summary, matrix, eva_id))
    vault.save(ev)
    vault.log("simulate", eva_id, f"{len(severities)} insiden, saran {cell}")
    return summary


def _section(s: dict, matrix, eva_id: str) -> str:
    f, v, a = s["frequency"], s["severity"], s["aggregate"]
    table = make_table(["Ukuran", "Frekuensi/tahun", "Keparahan (level dampak)", "Agregat tahunan"],
                       [["Rata-rata", f["mean"], round(v["mean"], 3), round(a["mean"], 3)]]
                       + [[q.upper(), f[q], v[q], a[q]] for q in ("p50", "p75", "p90", "p95", "p99")])
    note = ("Tidak ada insiden pada tahun ini, jadi sarannya sel terendah (1x1)." if s["no_incident_data"]
            else f"Dasar: {s['incident_count']} insiden, {s['iterations']} iterasi. Porsi tahun tanpa kejadian {a['zero_share']:.3f}.")
    return (f"{table}\n\nSaran sel: **{s['suggested_cell']}** (skor {matrix.score(s['suggested_cell'])}, zona {matrix.zone(s['suggested_cell'])}). "
            f"Ini hanya SARAN dan belum dipakai. Untuk memakainya: `rate {eva_id} --residual sim` (atau --inherent / --expected).\n\n{note}")
