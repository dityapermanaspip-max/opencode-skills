"""Read-only views: the status (dashboard) and the ISO 31000 style report with its CSV (delimiter ';', UTF-8 BOM, for Excel).
Counts follow the usual risk dashboard and report; nothing here changes a risk value."""

from __future__ import annotations

import csv
from datetime import date, timedelta

import gv_evidence
from gv_cycle import ecm_rows, plans_of
from gv_kri import current_status
from gv_matrix import Matrix
from gv_notes import make_table

DUE_DAYS = 14


def appetite_status(score, threshold) -> str:
    if score is None:
        return "BELUM_DIEVALUASI"
    if threshold is None:
        return "BELUM_ADA_APPETITE"
    return "DI_BAWAH_APPETITE" if score <= threshold else "DI_ATAS_APPETITE"


def profile(vault, year: int) -> list[dict]:
    rows = []
    for ev in vault.all("evaluasi"):
        f = ev.fields
        if f["fiscal_year"] != year:
            continue
        pre = vault.notes[f["pre"]]
        mx = Matrix(vault.notes[f["matrix"]])
        risk, proc, ind = (vault.notes[pre.fields[k]] for k in ("risk", "process", "indicator"))
        obj = vault.notes[ind.fields["objective"]]
        cell = f.get("active_cell")
        plans = plans_of(vault, ev.id)
        kris = [k for k in vault.all("kri") if k.fields["risk"] == risk.id and k.fields.get("status") == "ACTIVE"]
        rows.append({
            "eva": ev, "id": ev.id, "risk": risk, "process": proc, "indicator": ind, "objective": obj, "matrix": mx,
            "active_type": f.get("active_type"), "active_cell": cell,
            "score": mx.score(cell) if cell else None, "zone": mx.zone(cell) if cell else None,
            "threshold": mx.appetite(year), "controls": ecm_rows(ev), "no_evidence": gv_evidence.missing(vault, ev), "plans": plans,
            "incidents": [i for i in vault.all("insiden") if i.fields["pre"] == f["pre"] and str(i.fields["date"]).startswith(f"{year}-")],
            "kris": [(k, *current_status(k)) for k in kris], "trend": f.get("trend"),
        })
        rows[-1]["appetite"] = appetite_status(rows[-1]["score"], rows[-1]["threshold"])
    return rows


def status(vault) -> dict:
    year = vault.cfg["fiscal_year"]
    rows = profile(vault, year)
    soon = date.today() + timedelta(days=DUE_DAYS)
    s = {"fiscal_year": year, "period_open": vault.cfg["period_open"], "total": len(rows),
         "not_evaluated": sum(r["score"] is None for r in rows),
         "below_appetite": sum(r["appetite"] == "DI_BAWAH_APPETITE" for r in rows),
         "above_appetite": sum(r["appetite"] == "DI_ATAS_APPETITE" for r in rows),
         "no_appetite": sum(r["appetite"] == "BELUM_ADA_APPETITE" for r in rows),
         "actual_missing": sum(vault.cfg["period_open"] and not r["eva"].fields.get("actual") for r in rows),
         "residual_no_control": sum(bool(r["eva"].fields.get("residual")) and not r["controls"] for r in rows),
         "control_no_residual": sum(bool(r["controls"]) and not r["eva"].fields.get("residual") for r in rows),
         "controls_no_evidence": sum(len(r["no_evidence"]) for r in rows),
         "evaluations_no_evidence": sum(bool(r["no_evidence"]) for r in rows),
         "expected_no_plan": sum(bool(r["eva"].fields.get("expected")) and not r["plans"] for r in rows),
         "plan_no_expected": sum(bool(r["plans"]) and not r["eva"].fields.get("expected") for r in rows),
         "plans_due": sum(1 for r in rows for p in r["plans"] if p.fields["status"] in ("PLANNED", "IN_PROGRESS")
                          and str(p.fields["target_date"]) <= soon.isoformat()),
         "pending_reports": sum(n.fields["status"] == "PENDING" for n in vault.all("laporan")),
         "kri": {c: sum(st == c for r in rows for _k, st, _l in r["kris"]) for c in ("red", "amber", "green", "grey")},
         "risks_without_evaluation": [a.id for a in vault.all("pasang") if a.fields.get("active", True)
                                      and f"EVA-{year}-{a.id.split('-', 1)[1]}" not in vault.notes]}
    return s


def status_text(s: dict) -> str:
    lines = [f"Tahun fiskal {s['fiscal_year']} | periode tutup buku {'DIBUKA' if s['period_open'] else 'belum dibuka'}",
             f"Risiko dievaluasi: {s['total'] - s['not_evaluated']} dari {s['total']} (belum dinilai {s['not_evaluated']})",
             f"Appetite: di bawah {s['below_appetite']}, DI ATAS {s['above_appetite']}, belum ada batas {s['no_appetite']}",
             f"ACTUAL belum diisi: {s['actual_missing']} | rencana jatuh tempo <= {DUE_DAYS} hari: {s['plans_due']}",
             f"KRI merah {s['kri']['red']}, kuning {s['kri']['amber']}, hijau {s['kri']['green']}, abu-abu {s['kri']['grey']}",
             f"Laporan insiden menunggu: {s['pending_reports']}"]
    if s["controls_no_evidence"]:
        lines.append(f"Kontrol tanpa bukti: {s['controls_no_evidence']} pada {s['evaluations_no_evidence']} evaluasi (tetap dihitung; taruh berkas di 08-Bukti/<EVA>/<CTL>/)")
    flags = [(k, s[k]) for k in ("residual_no_control", "control_no_residual", "expected_no_plan", "plan_no_expected") if s[k]]
    if flags:
        lines.append("Cek konsistensi: " + ", ".join(f"{k}={v}" for k, v in flags))
    if s["risks_without_evaluation"]:
        lines.append(f"Pasangan risiko tanpa evaluasi tahun ini: {', '.join(s['risks_without_evaluation'])}")
    return "\n".join(lines)


def write_dashboard(vault, s: dict) -> None:
    body = ("Dibuat otomatis oleh `status`. Jangan diedit: akan ditimpa.\n\n```\n" + status_text(s) + "\n```\n")
    path = vault.root / "00-Dashboard.md"
    path.write_text(f"---\ntype: dashboard\ngenerated: {date.today().isoformat()}\n---\n\n# Dashboard\n\n{body}", encoding="utf-8", newline="\n")


CSV_HEAD = ["Tahun", "Sasaran", "Indikator", "Proses", "Kode risiko", "Risiko", "Inheren", "Residual", "Ekspektasi", "Aktual",
            "Nilai aktif", "Sel aktif", "Skor", "Zona", "Batas appetite", "Status appetite", "Kontrol", "Rencana", "Insiden", "Tren", "Kontrol tanpa bukti"]


def _csv_row(year, r):
    f = r["eva"].fields
    return [year, r["objective"].fields["title"], r["indicator"].fields["title"], r["process"].fields["title"], r["risk"].id,
            r["risk"].fields["title"], f.get("inherent"), f.get("residual"), f.get("expected"), f.get("actual"), r["active_type"],
            r["active_cell"], r["score"], r["zone"], r["threshold"], r["appetite"], len(r["controls"]), len(r["plans"]),
            len(r["incidents"]), r["trend"], len(r["no_evidence"])]


def report(vault, year: int) -> tuple:
    rows = profile(vault, year)
    if not rows:
        raise ValueError(f"Belum ada evaluasi tahun {year}")
    mx = rows[0]["matrix"]
    counts: dict[str, int] = {}
    for r in rows:
        if r["active_cell"]:
            counts[r["active_cell"]] = counts.get(r["active_cell"], 0) + 1
    ctl = {}
    for r in rows:
        for c in r["controls"]:
            ctl[c["status"]] = ctl.get(c["status"], 0) + 1
    plan_status, budget = {}, 0.0
    for r in rows:
        for p in r["plans"]:
            plan_status[p.fields["status"]] = plan_status.get(p.fields["status"], 0) + 1
            budget += p.fields.get("budget") or 0
    s = status(vault) if year == vault.cfg["fiscal_year"] else None
    md = [f"# Laporan Manajemen Risiko {vault.cfg['org']} - {year}", "",
          f"Disusun {date.today().isoformat()} dari vault manajemen risiko (kerangka ISO 31000: konteks, identifikasi, analisis, evaluasi, perlakuan, "
          f"pemantauan). Matriks {mx.id} ({mx.max_l}x{mx.max_i}), batas appetite {mx.appetite(year) or 'belum ditetapkan'}.", "",
          "## 1. Konteks", "",
          f"- Mandat {len(vault.all('mandat'))}, sasaran {len(vault.all('sasaran'))}, indikator {len(vault.all('indikator'))}, proses {len(vault.all('proses'))}.",
          f"- Kamus: {len(vault.all('risiko'))} peristiwa risiko, {len(vault.all('kontrol'))} kontrol.", "",
          "## 2. Peta risiko (jumlah risiko per sel, nilai aktif)", "", "```", mx.grid(counts), "```", "",
          "## 3. Profil risiko", ""]
    md.append(make_table(["Risiko", "Proses", "Aktif", "Sel", "Skor", "Zona", "Appetite", "Kontrol", "Rencana", "Insiden", "Tren"],
                         [[f"{r['risk'].id} {r['risk'].fields['title']}", r["process"].fields["title"], r["active_type"], r["active_cell"],
                           r["score"], r["zone"], r["appetite"], len(r["controls"]) if not r["no_evidence"] else f"{len(r['controls'])} ({len(r['no_evidence'])} tanpa bukti)",
                           len(r["plans"]), len(r["incidents"]), r["trend"]]
                          for r in sorted(rows, key=lambda r: -(r["score"] or 0))]))
    above = [r for r in rows if r["appetite"] == "DI_ATAS_APPETITE"]
    md += ["", "## 4. Risiko di atas appetite", ""] + ([f"- {r['risk'].id} {r['risk'].fields['title']} (skor {r['score']})" for r in above]
                                                       or ["Tidak ada."])
    md += ["", "## 5. Efektivitas kontrol", "", ("Kontrol terpasang menurut penilaian: " + ", ".join(f"{k} {v}" for k, v in sorted(ctl.items()))) if ctl
           else "Belum ada kontrol terpasang."]
    no_proof = sum(len(r["no_evidence"]) for r in rows)
    if no_proof:
        md += ["", f"Catatan: {no_proof} kontrol pada {sum(bool(r['no_evidence']) for r in rows)} evaluasi belum punya berkas bukti "
               f"(SOP, tangkapan layar, foto/CCTV, dsb. di 08-Bukti/<EVA>/<CTL>/). Kontrol itu masih dihitung pada nilai aktif tetapi belum "
               f"dapat dianggap terbukti ada."]
    md += ["", "## 6. Realisasi rencana perlakuan", "",
           ("Rencana: " + ", ".join(f"{k} {v}" for k, v in sorted(plan_status.items())) + (f"; anggaran Rp{budget:,.0f}." if budget else "; anggaran belum diisi.")) if plan_status else "Belum ada rencana."]
    kri_rows = [[k.id, k.fields["title"], r["risk"].id, st, last[1] if last else "-"] for r in rows for k, st, last in r["kris"]]
    md += ["", "## 7. Indikator risiko kunci (KRI)", "", make_table(["KRI", "Nama", "Risiko", "Status", "Pembacaan terakhir"], kri_rows) if kri_rows else "Belum ada KRI."]
    inc = [[i.id, i.fields["date"], i.fields["title"], i.fields["pre"], i.fields["impact"]] for r in rows for i in r["incidents"]]
    md += ["", "## 8. Insiden tahun ini", "", make_table(["ID", "Tanggal", "Judul", "Pasangan", "Level dampak"], inc) if inc else "Tidak ada insiden tercatat."]
    if s:
        md += ["", "## 9. Catatan data", "", "```", status_text(s), "```"]
    out = vault.root / "99-Laporan"
    out.mkdir(exist_ok=True)
    md_path, csv_path = out / f"Laporan-{year}.md", out / f"Laporan-{year}.csv"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(CSV_HEAD)
        w.writerows(_csv_row(year, r) for r in rows)
    return md_path, csv_path
