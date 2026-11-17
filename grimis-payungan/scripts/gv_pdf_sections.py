"""Sections of the ISO 31000:2018 report as HTML strings. Everything here comes from the vault; nothing is estimated or added."""

from __future__ import annotations

import re

from gv_notes import bullet_tree, get_section, table_rows
from gv_pdf_charts import heatmap, kri_chart, labels_of, score_bars, zone_legend
from gv_pdf_util import APPETITE_TEXT, ZONE_ORDER, cell_text, chip, date_long, e, inline, num

ENGINE_SECTIONS = ("Kontrol yang ada", "Simulasi Monte Carlo")
VALUE_NAMES = (("inherent", "Inheren", "INHERENT"), ("residual", "Residual", "RESIDUAL"), ("expected", "Ekspektasi", "EXPECTED"), ("actual", "Aktual", ""))
KRI_TEXT = {"red": "Merah", "amber": "Kuning", "green": "Hijau", "grey": "Belum ada ambang atau data"}


def tbl(head: list[str], rows: list[list[str]], right: tuple = ()) -> str:
    nowrap = lambda c: ' class=nw' if re.fullmatch(r'[A-Z]{3}-\d{3}(-\d{3})?', c) else ''
    th = "".join(f"<th{' class=r' if k in right else ''}>{h}</th>" for k, h in enumerate(head))
    body = "".join("<tr>" + "".join(f"<td{' class=r' if k in right else nowrap(c)}>{c}</td>" for k, c in enumerate(r)) + "</tr>" for r in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"


def _val(mx, cell) -> str:
    return f"<span class=nw>{e(cell)} ({mx.score(cell)})</span>" if cell else "-"


def _extra_sections(body: str) -> list[tuple[str, str]]:
    found = re.findall(r"^## (.+?)\n(.*?)(?=^## |\Z)", body, re.S | re.M)
    return [(t.strip(), c.strip()) for t, c in found if t.strip() not in ENGINE_SECTIONS and c.strip()]


def cover(vault, year: int, rows: list, mx, generated: str) -> str:
    thr = mx.appetite(year)
    meta = [("Organisasi", vault.cfg["org"]), ("Tahun", year), ("Matriks", f"{mx.id}, {mx.max_l}x{mx.max_i}"),
            ("Batas appetite", thr if thr is not None else "belum ditetapkan"), ("Evaluasi", len(rows)),
            ("Periode tutup buku", "dibuka" if vault.cfg["period_open"] and year == vault.cfg["fiscal_year"] else "belum dibuka"),
            ("Disusun", date_long(generated)), ("Sumber", "vault catatan Markdown (mesin grimis.py)")]
    cells = "".join(f"<div><b>{e(k)}</b>{e(v)}</div>" for k, v in meta)
    return (f"<div class='cover'><div class='kicker'>Laporan manajemen risiko &middot; kerangka ISO 31000:2018</div><h1>{e(vault.cfg['org'])}</h1>"
            f"<div style='font-size:13pt;color:#52514e'>Laporan Manajemen Risiko Tahun {year}</div><div class='meta'>{cells}</div></div>")


def summary(vault, year: int, rows: list, mx, s: dict | None) -> str:
    thr = mx.appetite(year)
    above = [r for r in rows if r["appetite"] == "DI_ATAS_APPETITE"]
    plans = [p for r in rows for p in r["plans"]]
    by_plan: dict[str, int] = {}
    for p in plans:
        by_plan[p.fields["status"]] = by_plan.get(p.fields["status"], 0) + 1
    incidents = sum(len(r["incidents"]) for r in rows)
    kri = {c: sum(st == c for r in rows for _k, st, _l in r["kris"]) for c in ("red", "amber", "green", "grey")}
    tiles = [(len(rows), "risiko dievaluasi"), (len(above) if thr is not None else "-", "di atas batas appetite" if thr is not None else "appetite belum ditetapkan"),
             (len(plans), "rencana perlakuan"), (incidents, "insiden tercatat tahun ini")]
    zones = {z: sum(r["zone"] == z for r in rows) for z in ZONE_ORDER}
    zone_text = ", ".join(f"{z} {n}" for z, n in zones.items() if n)
    top = sorted((r for r in rows if r["score"] is not None), key=lambda r: -r["score"])[:3]
    out = ["<h2>Ringkasan</h2><div class='tiles'>" + "".join(f"<div class='tile'><div class='v'>{v}</div><div class='l'>{e(l)}</div></div>" for v, l in tiles) + "</div>"]
    out.append(f"<p>Register tahun {year} memuat <b>{len(rows)}</b> pasangan risiko-proses-indikator. Sebaran nilai aktif menurut zona: {e(zone_text or 'belum ada yang dinilai')}.</p>")
    if top:
        items = "".join(f"<li><b>{e(r['risk'].id)}</b> {e(r['risk'].fields['title'])} ({e(r['active_cell'])}, skor {r['score']}, {e(r['zone'])})</li>" for r in top)
        out.append(f"<p>Tiga skor tertinggi:</p><ul>{items}</ul>")
    out.append(f"<p>Rencana perlakuan: {e(', '.join(f'{k} {v}' for k, v in sorted(by_plan.items())) or 'belum ada')}. "
               f"Indikator risiko kunci (KRI) aktif: merah {kri['red']}, kuning {kri['amber']}, hijau {kri['green']}, belum ada ambang atau data {kri['grey']}.</p>")
    if s and s["not_evaluated"]:
        out.append(f"<p><b>{s['not_evaluated']}</b> risiko belum dinilai; angka di atas belum mencakupnya.</p>")
    return "".join(out)


def context(vault, year: int, rows: list, mx) -> str:
    out = ["<h2>1. Lingkup, konteks dan kriteria <small>(ISO 31000 butir 6.3)</small></h2>"]
    mandates = [[e(m.id), e(m.fields["title"]), e(m.fields.get("source") or "-")] for m in vault.all("mandat")]
    out.append("<h3>1.1 Mandat dan sasaran</h3>" + (tbl(["ID", "Mandat", "Sumber"], mandates) if mandates else "<p>Belum ada mandat.</p>"))
    ind_rows = []
    for ind in vault.all("indikator"):
        obj = vault.notes[ind.fields["objective"]]
        ind_rows.append([e(obj.fields["title"]), e(f"{ind.id} {ind.fields['title']}"), e(ind.fields.get("unit") or "-"), e(ind.fields.get("target") or "-")])
    out.append("<h3>1.2 Sasaran dan indikator kinerja</h3>" + (tbl(["Sasaran", "Indikator", "Satuan", "Target"], ind_rows) if ind_rows else "<p>Belum ada indikator.</p>"))
    proc = [[e(p.id), e(p.fields["title"]), e(p.fields.get("owner") or "-"), e(", ".join(p.fields.get("indicators", [])) or "-")] for p in vault.all("proses")]
    out.append("<h3>1.3 Proses</h3>" + (tbl(["ID", "Proses", "Pemilik", "Indikator"], proc) if proc else "<p>Belum ada proses.</p>"))
    lk, im = labels_of(mx, "Label kemungkinan"), labels_of(mx, "Label dampak")
    lab = lambda d: tbl(["Level", "Label"], [[str(k), e(v or "-")] for k, v in sorted(d.items())])
    out.append(f"<h3>1.4 Kriteria risiko</h3><p>Matriks <b>{e(mx.id)}</b> ({mx.max_l}x{mx.max_i}); skor sel = kemungkinan x dampak, zona menurut skor. "
               f"Batas appetite tahun {year}: <b>{num(mx.appetite(year)) if mx.appetite(year) is not None else 'belum ditetapkan'}</b> "
               "(skor sampai batas itu berada dalam appetite).</p>")
    out.append(f"<div class='cols keep'><div><h4>Kemungkinan</h4>{lab(lk)}</div><div><h4>Dampak</h4>{lab(im)}</div></div>")
    crit = [[e(r.get("kategori")), e(r.get("level")), inline(r.get("uraian"))] for r in table_rows(get_section(mx.note.body, "Kriteria dampak"))]
    if crit:
        out.append("<h4>Kriteria dampak per kategori</h4>" + tbl(["Kategori", "Level", "Uraian"], crit))
    out.append(zone_legend(mx))
    return "".join(out)


def register(vault, year: int, rows: list, mx) -> str:
    counts: dict[str, int] = {}
    for r in rows:
        if r["active_cell"]:
            counts[r["active_cell"]] = counts.get(r["active_cell"], 0) + 1
    srt = sorted(rows, key=lambda r: (-(r["score"] or 0), r["risk"].id))
    body = [[e(r["risk"].id), e(r["risk"].fields["title"]) + f"<br><small>{e(r['process'].fields['title'])}</small>", _val(mx, r["eva"].fields.get("inherent")),
             _val(mx, r["eva"].fields.get("residual")), _val(mx, r["eva"].fields.get("expected")),
             f"<b>{e(r['active_type'] or '-')}</b> {e(r['active_cell'] or '')}", str(r["score"] if r["score"] is not None else "-"),
             chip(r["zone"], r["zone"]) if r["zone"] else "-", e(APPETITE_TEXT[r["appetite"]])] for r in srt]
    return ("<h2 class='pb'>2. Penilaian risiko <small>(ISO 31000 butir 6.4)</small></h2><h3>2.1 Identifikasi dan analisis: register risiko</h3>"
            "<p>Nilai aktif ditentukan mesin: tanpa kontrol = inheren; ada kontrol dan belum semua rencana selesai = residual; semua rencana selesai = ekspektasi. "
            "Angka dalam kurung adalah skor sel.</p>"
            + tbl(["Kode", "Risiko dan proses", "Inheren", "Residual", "Ekspektasi", "Aktif", "Skor", "Zona", "Appetite"], body, right=(6,))
            + "<h3>2.2 Evaluasi: peta risiko dan skor terhadap appetite</h3>" + heatmap(mx, counts) + score_bars(srt, mx))


def details(vault, rows: list, mx) -> str:
    out = ["<h3 class='pb'>2.3 Rincian per risiko</h3>"]
    for r in sorted(rows, key=lambda r: (-(r["score"] or 0), r["risk"].id)):
        f, risk = r["eva"].fields, r["risk"]
        vals = "".join(f"<div class='{'on' if key.upper() == r['active_type'] else ''}'><b>{label}</b>{_val(mx, f.get(key))}</div>" for key, label, _t in VALUE_NAMES)
        trees = []
        for name in ("Penyebab", "Dampak"):
            tree = bullet_tree(get_section(risk.body, name))
            if tree:
                li = "".join(f"<li>{e(n['text'])}{' <small>[' + e(n['category']) + ']</small>' if n.get('category') else ''}</li>" for n in tree)
                trees.append(f"<h4>{name}</h4><ul>{li}</ul>")
        ctl = "".join(f"<li>{e(c['control'])} {e(vault.notes[c['control']].fields['title'])}: <b>{e(c['status'])}</b></li>" for c in r["controls"])
        pln = "".join(f"<li>{e(p.id)} {e(p.fields['action'])}; PIC {e(p.fields['pic'])}; target {e(date_long(p.fields['target_date']))}; <b>{e(p.fields['status'])}</b></li>" for p in r["plans"])
        kri = "".join(f"<li>{e(k.id)} {e(k.fields['title'])}: {KRI_TEXT[st]}{f' ({num(last[1])} pada {date_long(last[0])})' if last else ''}</li>" for k, st, last in r["kris"])
        extra = "".join(f"<h4>{e(t)}</h4><p>{inline(c)}</p>" for t, c in _extra_sections(r["eva"].body))
        sect = lambda title, items: f"<h4>{title}</h4><ul>{items}</ul>" if items else ""
        out.append(f"<div class='card'><div class='head'><span class='t'>{e(risk.id)} {e(risk.fields['title'])}</span>"
                   f"{chip(r['zone'], r['zone']) if r['zone'] else ''}</div>"
                   f"<div class='sub'>{e(r['process'].fields['title'])} &middot; {e(r['indicator'].fields['title'])} &middot; {e(r['eva'].id)} &middot; "
                   f"{e(APPETITE_TEXT[r['appetite']])}{' &middot; tren ' + e(r['trend']) if r['trend'] else ''}</div>"
                   f"<p>{inline(risk.fields.get('description') or '')}</p><div class='vals'>{vals}</div>{''.join(trees)}"
                   f"{sect('Kontrol yang ada', ctl)}{sect('Rencana perlakuan', pln)}{sect('Indikator risiko kunci', kri)}"
                   f"{('<p><small>Insiden tahun ini: ' + str(len(r['incidents'])) + '</small></p>') if r['incidents'] else ''}{extra}</div>")
    return "".join(out)


def simulations(rows: list, mx) -> str:
    parts = []
    for r in rows:
        f = r["eva"].fields
        text = get_section(r["eva"].body, "Simulasi Monte Carlo")
        if not f.get("sim_suggestion") or not text:
            continue
        comma = lambda c: re.sub(r"(?<=\d)\.(?=\d)", ",", c)  # decimal comma, as in the rest of the report
        tab = [[e(comma(c)) for c in row.values()] for row in table_rows(text)]
        head = list(table_rows(text)[0].keys()) if tab else []
        lines = [l.strip() for l in text.split("\n") if l.strip() and not l.strip().startswith("|")]
        used = any(l.startswith("Saran ini dipakai") for l in lines)
        prose = ""
        for l in lines:
            if l.startswith("Saran sel:"):  # drop the how-to-use hint of the engine; say plainly whether it was used
                l = l.split(" Ini hanya SARAN")[0] + ("" if used else " Belum dipakai sebagai nilai risiko.")
            prose += f"<p>{inline(comma(l))}</p>"
        parts.append(f"<div class='keep'><h4>{e(r['risk'].id)} {e(r['risk'].fields['title'])}</h4>"
                     + (tbl([e(h.capitalize()) for h in head], tab) if tab else "") + prose + "</div>")
    if not parts:
        return ""
    return ("<h3>2.4 Analisis kuantitatif: simulasi Monte Carlo</h3><p class=lead>Model Poisson majemuk dari insiden tahun berjalan. Hasilnya saran sel, "
            "bukan nilai risiko, sampai seseorang memakainya.</p>" + "".join(parts))


def treatment(rows: list, mx) -> str:
    plans = sorted(((r, p) for r in rows for p in r["plans"]), key=lambda t: str(t[1].fields["target_date"]))
    out = ["<h2 class='pb'>3. Perlakuan risiko <small>(ISO 31000 butir 6.5)</small></h2>"]
    if not plans:
        return out[0] + "<p>Belum ada rencana perlakuan.</p>"
    body = [[e(p.id), e(r["risk"].id), e(p.fields["action"]), e(p.fields["pic"]), e(date_long(p.fields["target_date"])), f"<b>{e(p.fields['status'])}</b>",
             e(f"{p.fields.get('new_control_code') or ''} {p.fields.get('new_control_title') or ''}".strip() or "-"), inline(p.fields.get("notes") or "")] for r, p in plans]
    out.append(tbl(["Rencana", "Risiko", "Tindakan", "PIC", "Target", "Status", "Kontrol yang dihasilkan", "Catatan"], body))
    cmp_rows = [[e(r["risk"].id), e(r["risk"].fields["title"]), _val(mx, r["active_cell"]), _val(mx, r["eva"].fields.get("expected"))]
                for r in sorted(rows, key=lambda r: -(r["score"] or 0)) if r["plans"] and r["eva"].fields.get("expected")]
    if cmp_rows:
        out.append("<h3>Nilai aktif sekarang dan nilai yang diharapkan setelah rencana selesai</h3>"
                   + tbl(["Kode", "Risiko", "Aktif sekarang", "Ekspektasi"], cmp_rows))
    return "".join(out)


def monitoring(vault, year: int, rows: list) -> str:
    out = ["<h2>4. Pemantauan dan tinjauan <small>(ISO 31000 butir 6.6)</small></h2><h3>4.1 Indikator risiko kunci (KRI)</h3>"]
    kris = [(r, k, st, last) for r in rows for k, st, last in r["kris"]]
    if not kris:
        out.append("<p>Belum ada KRI aktif.</p>")
    else:
        body = [[e(k.id), e(r["risk"].id), e(k.fields["title"]), e(k.fields.get("unit") or "-"), f"{num(k.fields.get('amber'))} / {num(k.fields.get('red'))}",
                 f"{num(last[1])} ({e(date_long(last[0]))})" if last else "-", f"<b>{KRI_TEXT[st]}</b>"] for r, k, st, last in kris]
        out.append(tbl(["KRI", "Risiko", "Nama", "Satuan", "Ambang kuning / merah", "Pembacaan terakhir", "Status"], body))
        out.append("<p><small>Ambang hanya diubah seseorang dengan alasan tercatat; draf tidak pernah mengisinya.</small></p>")
        for r, k, st, last in kris:
            chart = kri_chart(k)
            hist = table_rows(get_section(k.body, "Riwayat ambang"))
            why = f"<p><small>Alasan ambang: {inline(hist[-1].get('alasan', ''))}</small></p>" if hist and hist[-1].get("alasan") else ""
            if chart:
                out.append(f"<h4>{e(k.id)} {e(k.fields['title'])}</h4>{chart}{why}")
    inc = sorted((i for r in rows for i in r["incidents"]), key=lambda i: str(i.fields["date"]))
    out.append("<h3>4.2 Insiden</h3>")
    out.append(tbl(["ID", "Tanggal", "Judul", "Pasangan", "Level dampak"], [[e(i.id), e(date_long(i.fields["date"])), e(i.fields["title"]), e(i.fields["pre"]),
                                                                               str(i.fields["impact"])] for i in inc]) if inc else f"<p>Tidak ada insiden tercatat pada {year}.</p>")
    pending = sum(n.fields["status"] == "PENDING" for n in vault.all("laporan"))
    out.append(f"<p>Laporan insiden masuk yang menunggu keputusan: <b>{pending}</b>.</p>")
    return "".join(out)


def recording(vault, rows: list, s: dict | None, findings: list, status_lines: str, drafts: list) -> str:
    errors = [f for f in findings if f[0] == "ERROR"]
    out = ["<h2>5. Pencatatan dan pelaporan <small>(ISO 31000 butir 6.7)</small></h2>",
           "<div class='note'>Laporan ini hanya memuat isi vault. Nilai aktif, tren, warna KRI, status appetite dan tutup buku dihitung mesin, bukan diketik. "
           "Usulan yang belum diterima seseorang tidak dihitung. Laporan ini bahan kerja bagi pemilik risiko, bukan penilaian akhir.</div>"]
    if status_lines:
        out.append(f"<h3>5.1 Catatan data</h3><pre>{e(status_lines)}</pre>")
    out.append(f"<h3>5.2 Pemeriksaan vault</h3><p>{len(errors)} error dan {len(findings) - len(errors)} peringatan.</p>")
    if findings:
        out.append(tbl(["Tingkat", "Catatan", "Temuan"], [[e(l), e(i), e(m)] for l, i, m in findings[:30]]))
    if drafts:
        out.append("<h3>5.3 Draf yang menunggu keputusan</h3>" + tbl(["Draf", "Jenis", "Target", "Status", "Butir belum diputuskan"], drafts))
    return "".join(out)
