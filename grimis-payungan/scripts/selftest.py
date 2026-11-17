"""Self-test of the engine: `python -P scripts/selftest.py`. Builds throw-away vaults; touches nothing else."""

from __future__ import annotations

import csv
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gv_check  # noqa: E402
import gv_close  # noqa: E402
import gv_cmds as C  # noqa: E402
import gv_cycle  # noqa: E402
import gv_draft  # noqa: E402
import gv_kri  # noqa: E402
import gv_notes  # noqa: E402
import gv_pdf  # noqa: E402
import gv_report  # noqa: E402
import gv_sim  # noqa: E402
from gv_rules import VaultError  # noqa: E402
from gv_vault import Vault  # noqa: E402


def base(tmp: Path) -> Vault:
    C.init(str(tmp / "v"), "Instansi Uji", 2026)
    v = Vault(tmp / "v")
    steps = [("matriks", ["title=M5", "max_likelihood=5", "max_impact=5"]), ("mandat", ["title=Pelayanan"]),
             ("sasaran", ["title=Cepat", "mandate=MND-001"]), ("indikator", ["title=Waktu", "objective=SAS-001"]),
             ("proses", ["title=Perizinan", "indicators=IND-001"]), ("risiko", ["title=Berkas hilang"]),
             ("pasang", ["risk=RSK-001", "process=PRS-001", "indicator=IND-001"]), ("kontrol", ["title=Pemindaian", "control_type=preventif"]),
             ("evaluasi", ["pre=PRE-001"])]
    for ent, pairs in steps:
        C.new(v, ent, pairs)
        if ent == "matriks":
            C.matrix(v, "activate", "MTX-001")
            C.appetite(v, "MTX-001", 2026, 9)
    return v


class T(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.v = base(self.tmp)

    def tearDown(self):
        self._tmp.cleanup()

    def active(self, eva="EVA-2026-001"):
        f = self.v.get(eva).fields
        return f["active_type"], f["active_cell"]

    # ---- notes -------------------------------------------------------------------------------------------
    def test_frontmatter_roundtrip_of_awkward_text(self):
        f = {"a": "kunci: nilai # x", "b": "[[X-1]]", "c": "2026", "d": True, "e": None, "f": ["[[A-1]]", "b, c"], "g": 3.5, "h": "- dash"}
        out, _ = gv_notes.parse(gv_notes.dump(f, "isi"))
        self.assertEqual(out, f)

    def test_tables_and_bullet_trees(self):
        rows = gv_notes.table_rows(gv_notes.make_table(["A", "B"], [["1", "x|y"], ["2", ""]]))
        self.assertEqual(rows[0], {"a": "1", "b": "x/y"})
        tree = gv_notes.bullet_tree("- a [Fraud]\n  - b\n    - c [Hukum]\n- d")
        self.assertEqual([n["text"] for n in tree], ["a", "d"])
        self.assertEqual(tree[0]["children"][0]["children"][0]["category"], "Hukum")
        self.assertEqual(gv_notes.bullet_tree(gv_notes.make_bullet_tree(tree)), tree)

    # ---- the value cycle ---------------------------------------------------------------------------------
    def test_active_value_follows_controls_and_plans(self):
        C.rate(self.v, "EVA-2026-001", inherent="4x4", residual="3x3", expected="2x2")
        self.assertEqual(self.active(), ("INHERENT", "4x4"))
        C.control(self.v, "add", "EVA-2026-001", "CTL-001")
        self.assertEqual(self.active(), ("RESIDUAL", "3x3"))
        C.new(self.v, "rencana", ["evaluation=EVA-2026-001", "action=A", "pic=P", "target_date=2026-12-01", "new_control_code=NEW-1"])
        C.new(self.v, "rencana", ["evaluation=EVA-2026-001", "action=B", "pic=P", "target_date=2026-12-01", "new_control_code=NEW-2"])
        C.plan(self.v, "done", "PLN-001")
        self.assertEqual(self.active(), ("RESIDUAL", "3x3"), "one plan still open")
        C.plan(self.v, "start", "PLN-002")
        C.plan(self.v, "done", "PLN-002")
        self.assertEqual(self.active(), ("EXPECTED", "2x2"))
        C.new(self.v, "rencana", ["evaluation=EVA-2026-001", "action=C", "pic=P", "target_date=2026-12-01"])
        self.assertEqual(self.active(), ("RESIDUAL", "3x3"), "a new plan reopens the cycle")
        self.assertEqual(len(gv_cycle.ecm_rows(self.v.get("EVA-2026-001"))), 3)

    def test_rules_are_enforced(self):
        v = self.v
        with self.assertRaises(VaultError):
            C.rate(v, "EVA-2026-001", inherent="6x1")                    # outside the 5x5 matrix
        with self.assertRaises(VaultError):
            C.rate(v, "EVA-2026-001", actual="3x3")                      # period is not open
        with self.assertRaises(VaultError):
            C.new(v, "pasang", ["risk=RSK-001", "process=PRS-001", "indicator=IND-001"])  # duplicate anchor
        C.new(v, "indikator", ["title=Lain", "objective=SAS-001"])
        with self.assertRaises(VaultError):
            C.new(v, "pasang", ["risk=RSK-001", "process=PRS-001", "indicator=IND-002"])  # indicator not mapped to the process
        with self.assertRaises(VaultError):
            C.set_fields(v, "EVA-2026-001", ["residual=2x2"])           # values go through 'rate'
        for n in range(3):
            C.new(v, "kri", ["risk=RSK-001", f"title=K{n}", "kri_type=LEADING", "direction=higher_is_worse", "frequency=monthly"])
        with self.assertRaises(VaultError):
            C.new(v, "kri", ["risk=RSK-001", "title=K4", "kri_type=LEADING", "direction=higher_is_worse", "frequency=monthly"])
        with self.assertRaises(VaultError):
            gv_kri.change_threshold(v, "KRI-001", 2, 5, "")                # a reason is mandatory
        with self.assertRaises(VaultError):
            gv_kri.change_threshold(v, "KRI-001", 9, 5, "salah urut")      # amber above red, higher_is_worse
        with self.assertRaises(VaultError):
            C.new(v, "insiden", ["pre=PRE-001", "date=2026-01-01", "title=x", "impact=9"])

    def test_kri_status_both_directions(self):
        self.assertEqual([gv_kri.status_of(x, 2, 5, "higher_is_worse") for x in (1, 2, 5)], ["green", "amber", "red"])
        self.assertEqual([gv_kri.status_of(x, 80, 50, "lower_is_worse") for x in (90, 80, 50)], ["green", "amber", "red"])
        self.assertEqual(gv_kri.status_of(None, 2, 5, "higher_is_worse"), "grey")

    def test_kri_reading_threshold_log_and_retire(self):
        v = self.v
        C.new(v, "kri", ["risk=RSK-001", "title=K", "kri_type=LEADING", "direction=higher_is_worse", "frequency=monthly", "amber=2", "red=5"])
        self.assertEqual(gv_kri.add_reading(v, "KRI-001", 6, "2026-03-01"), "red")
        self.assertEqual(gv_kri.add_reading(v, "KRI-001", 1, "2026-04-01"), "green")
        gv_kri.change_threshold(v, "KRI-001", 1, 3, "ambang diperketat")
        self.assertIn("ambang diperketat", v.get("KRI-001").body)
        gv_kri.retire(v, "KRI-001")
        with self.assertRaises(VaultError):
            gv_kri.add_reading(v, "KRI-001", 1)

    # ---- Monte Carlo -------------------------------------------------------------------------------------
    def test_simulation(self):
        v = self.v
        with self.assertRaises(VaultError):
            gv_sim.simulate(v, "EVA-2026-001", iterations=10)
        none = gv_sim.simulate(v, "EVA-2026-001", 2000, seed=1)
        self.assertEqual((none["no_incident_data"], none["suggested_cell"]), (True, "1x1"))
        for d, i in (("2026-01-10", 3), ("2026-02-10", 4), ("2026-09-10", 2), ("2025-05-05", 5)):  # 2025 does not count
            C.new(v, "insiden", ["pre=PRE-001", f"date={d}", "title=i", f"impact={i}"])
        C.set_fields(v, "INS-003", ["use_in_simulation=false"])
        a, b = (gv_sim.simulate(v, "EVA-2026-001", 3000, seed=5) for _ in range(2))
        self.assertEqual((a["incident_count"], a["lambda"]), (2, 2.0))
        self.assertEqual(a["suggested_cell"], b["suggested_cell"])
        self.assertEqual(a["aggregate"]["mean"], b["aggregate"]["mean"], "same seed, same numbers")
        self.assertEqual(v.get("EVA-2026-001").fields["sim_suggestion"], a["suggested_cell"])
        C.rate(v, "EVA-2026-001", residual="sim")
        self.assertEqual(v.get("EVA-2026-001").fields["residual"], a["suggested_cell"])
        rng = random.Random(3)
        self.assertAlmostEqual(sum(gv_sim.poisson_draw(rng, 4.0) for _ in range(20000)) / 20000, 4.0, delta=0.1)

    # ---- close the year ----------------------------------------------------------------------------------
    def test_annual_close_two_years(self):
        v = self.v
        C.rate(v, "EVA-2026-001", inherent="4x4", residual="3x3", expected="2x2")
        C.control(v, "add", "EVA-2026-001", "CTL-001")
        C.new(v, "rencana", ["evaluation=EVA-2026-001", "action=A", "pic=P", "target_date=2026-12-01", "new_control_code=NEW-1", "new_control_title=Baru"])
        C.new(v, "rencana", ["evaluation=EVA-2026-001", "action=B", "pic=P", "target_date=2026-12-01"])
        C.plan(v, "done", "PLN-001")
        with self.assertRaises(VaultError):
            gv_close.close_year(v, 2026)                                 # period not open
        gv_close.open_period(v)
        with self.assertRaises(VaultError):
            gv_close.close_year(v, 2026)                                 # ACTUAL missing
        C.rate(v, "EVA-2026-001", actual="2x3")
        s = gv_close.close_year(Vault(v.root), 2026)
        self.assertEqual((s["closed"], s["carried"], s["not_realised"], s["blank_new"]), (1, 1, 1, 0))
        v = Vault(v.root)
        self.assertEqual((v.cfg["fiscal_year"], v.cfg["period_open"]), (2027, False))
        old, new = v.get("EVA-2026-001").fields, v.get("EVA-2027-001").fields
        self.assertTrue(old["closed"])
        self.assertEqual((new["residual"], new["inherent"], new["active_type"]), ("2x3", "4x4", "RESIDUAL"))
        self.assertEqual(v.get("PLN-002").fields["status"], "NOT_REALISED")
        self.assertEqual([r["plan"] for r in gv_cycle.ecm_rows(v.get("EVA-2027-001"))], ["PLN-001"], "only a DONE plan's control is carried")
        self.assertEqual(s["needs_controls"], [])
        with self.assertRaises(VaultError):
            C.rate(v, "EVA-2026-001", residual="1x1")                    # closed years are history
        C.rate(v, "EVA-2027-001", residual="1x2")
        gv_close.open_period(v)
        C.rate(v, "EVA-2027-001", actual="1x2")
        gv_close.close_year(v, 2027)
        self.assertEqual(Vault(v.root).get("EVA-2027-001").fields["trend"], "IMPROVING")   # 2 < 9 on the same matrix

    def test_matrix_change_blanks_next_year(self):
        v = self.v
        C.rate(v, "EVA-2026-001", inherent="4x4", residual="3x3")
        C.new(v, "matriks", ["title=M4", "max_likelihood=4", "max_impact=4"])
        C.matrix(v, "activate", "MTX-002")
        gv_close.open_period(v)
        C.rate(v, "EVA-2026-001", actual="2x2")
        self.assertEqual(gv_close.close_year(v, 2026)["blank_new"], 1)
        new = Vault(v.root).get("EVA-2027-001").fields
        self.assertEqual((new["matrix"], new["residual"], new["inherent"], new["trend"]), ("MTX-002", None, None, "STABLE"))

    # ---- drafts ------------------------------------------------------------------------------------------
    def test_drafts_need_a_human(self):
        v = self.v
        items = [{"type": "cause", "description": "Arsip tidak dikunci", "category": "Kebijakan",
                  "children": [{"description": "Kunci tidak dipegang petugas", "category": "Karangan"}]},
                 {"type": "impact", "description": "Izin tertunda", "category": "Gangguan Layanan"},
                 {"type": "cause", "description": "arsip TIDAK dikunci!", "category": "Fraud"}]
        d = gv_draft.create(v, "bowtie", "RSK-001", items)
        self.assertNotIn("Arsip tidak dikunci", v.get("RSK-001").body)   # a draft changes nothing by itself
        out = gv_draft.accept(v, d.id, [1, 2, 3])
        self.assertTrue(any("GAGAL" in m for m in out), "the paraphrase of item 1 is refused")
        tree = gv_notes.bullet_tree(gv_notes.get_section(v.get("RSK-001").body, "Penyebab"))
        self.assertEqual((tree[0]["text"], tree[0]["children"][0]["category"]), ("Arsip tidak dikunci", None))  # unknown category dropped
        self.assertEqual(v.get(d.id).fields["status"], "PARTIAL")
        gv_draft.reject(v, d.id, [3], "parafrasa")
        self.assertIn("arsip TIDAK dikunci!", v.get("RSK-001").body)
        k = gv_draft.create(v, "kri", "RSK-001", [{"title": "Berkas hilang", "kri_type": "LEADING", "direction": "higher_is_worse",
                                                   "frequency": "monthly", "amber": 2, "red": 5}])
        self.assertIn("diabaikan", gv_draft.accept(v, k.id)[0])
        self.assertIsNone(v.get("KRI-001").fields.get("amber"), "a draft never sets a threshold")
        r = gv_draft.create(v, "risiko", "PRS-001", [{"title": "Berkas hilang", "indicator": "IND-001", "match": "RSK-001"}])
        self.assertIn("sudah ada", " ".join(gv_draft.accept(v, r.id)))     # same anchor already exists

    def test_context_draft_resolves_refs(self):
        v = self.v
        items = [{"ref": "m", "level": "mandat", "title": "Mandat baru"}, {"ref": "s", "level": "sasaran", "title": "Sasaran baru", "parent": "m"},
                 {"ref": "i", "level": "indikator", "title": "Indikator baru", "parent": "s"},
                 {"level": "proses", "title": "Proses baru", "indicators": ["i"]}]
        gv_draft.accept(v, gv_draft.create(v, "konteks", None, items).id)
        self.assertEqual(v.get("PRS-002").fields["indicators"], ["IND-002"])
        self.assertEqual(v.get("SAS-002").fields["mandate"], "MND-002")

    # ---- views and checks --------------------------------------------------------------------------------
    def test_report_status_and_check(self):
        v = self.v
        C.rate(v, "EVA-2026-001", inherent="5x4", residual="4x4")
        C.control(v, "add", "EVA-2026-001", "CTL-001")
        s = gv_report.status(v)
        self.assertEqual((s["total"], s["above_appetite"], s["below_appetite"]), (1, 1, 0))     # 16 > 9
        md, cs = gv_report.report(v, 2026)
        self.assertIn("DI_ATAS_APPETITE", md.read_text(encoding="utf-8"))
        with cs.open(encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.reader(fh, delimiter=";"))
        self.assertEqual((len(rows), rows[1][gv_report.CSV_HEAD.index("Skor")]), (2, "16"))
        self.assertEqual([f for f in gv_check.check(v) if f[0] == "ERROR"], [])
        p = v.get("EVA-2026-001").path
        p.write_text(p.read_text(encoding="utf-8").replace("active_type: RESIDUAL", "active_type: INHERENT"), encoding="utf-8")
        self.assertTrue(any("tidak sama dengan hitungan" in m for _l, _i, m in gv_check.check(Vault(v.root))))

    def test_pdf_report_html_and_fallback(self):
        import os
        v = self.v
        C.set_fields(v, "RSK-001", ["title=Berkas <b>hilang</b> & rusak"])
        C.rate(v, "EVA-2026-001", inherent="5x4", residual="4x4")
        C.control(v, "add", "EVA-2026-001", "CTL-001")
        html = gv_pdf.build_html(v, 2026)
        self.assertIn("ISO 31000:2018", html)
        self.assertIn("Berkas &lt;b&gt;hilang&lt;/b&gt; &amp; rusak", html)      # note text is escaped, never injected
        self.assertNotIn("<b>hilang</b>", html)
        self.assertNotIn("<script", html)                                       # one self-contained file
        self.assertNotIn("http://", html.replace("http://www.w3.org/2000/svg", ""))
        with self.assertRaises(ValueError):
            gv_pdf.build_html(v, 2031)
        old = os.environ.get("GRIMIS_BROWSER")
        os.environ["GRIMIS_BROWSER"] = str(self.tmp / "no-such-browser.exe")
        try:
            page, pdf, msg = gv_pdf.write_pdf(v, 2026)
        finally:
            os.environ.pop("GRIMIS_BROWSER") if old is None else os.environ.update(GRIMIS_BROWSER=old)
        self.assertTrue(page.is_file())
        self.assertIsNone(pdf)
        self.assertIn("PDF tidak dibuat", msg)

    def test_edit_in_obsidian_style_is_read_back(self):
        v = self.v
        p = v.get("RSK-001").path
        text = p.read_text(encoding="utf-8").replace("title: Berkas hilang", 'title: "Berkas: hilang saat pindah"\ntags:\n  - kritis')
        p.write_text(text.replace("\n", "\r\n"), encoding="utf-8", newline="")   # CRLF, as Obsidian on Windows may save it
        again = Vault(v.root)
        self.assertEqual(again.get("RSK-001").fields["title"], "Berkas: hilang saat pindah")
        self.assertEqual(again.get("RSK-001").fields["tags"], ["kritis"])
        self.assertEqual(json.dumps(again.problems), "[]")


if __name__ == "__main__":
    unittest.main(verbosity=1)
