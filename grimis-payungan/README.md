# grimis-payungan

An agent skill that runs the enterprise risk-management cycle (ISO 31000) for one organisation on an **Obsidian vault** of Markdown
notes, with no web app or database. The agent drafts and explains, a small Python engine enforces the rules, a person decides.
Works with **Claude Code** and **OpenCode** (same `SKILL.md` format). Working language of the output: Indonesian.

## What it does

Context (mandate, objectives, indicators, processes) -> risk matrix and appetite -> risk identification and bowtie (as AI drafts a person
accepts) -> evaluation with the four values (inherent, residual, expected, actual) and the active-value rule -> controls and mitigation
plans -> KRI with traffic lights -> incident register and report inbox -> Monte Carlo suggestion -> ISO 31000 report (Markdown + CSV) ->
annual close with carry-over and trend.

Rules the skill keeps: no invented scores or thresholds, AI output is a draft until a person accepts it, the engine (not the agent)
decides the active value, trend, KRI colour and the close, and a refusal is reported, never worked around.

## Install

Needs Python 3.11+ (standard library only; use `python3` on macOS/Linux).

| Agent | Where the folder goes |
|---|---|
| Claude Code | `~/.claude/skills/grimis-payungan/` (Windows: `%USERPROFILE%\.claude\skills\grimis-payungan\`) |
| OpenCode, all projects | `~/.config/opencode/skills/grimis-payungan/` |
| OpenCode, one project | `<project>/.opencode/skills/grimis-payungan/` |

```
git clone <this repo> <one of the folders above>
python -P <folder>/scripts/selftest.py        # 13 tests, expect OK
```

The skill is picked up when the agent starts. Then open the agent in the folder that should hold the vault and say, for example:

- "Buat vault manajemen risiko untuk Instansi X, tahun 2026"
- "Buat matriks risiko 5x5 dan atur appetite 9"
- "Baca dokumen renstra / LKjIP ini dan susun draft konteksnya" (sasaran, indikator, proses)
- "Usulkan risiko untuk proses Pelayanan perizinan, cocokkan dengan kamus yang ada"
- "Nilai risiko RSK-001: inheren 4x4 ..." / "Bagaimana status risiko tahun ini?" / "Buat laporan 2026" / "Tutup buku 2026"

The engine also works by hand: `python -P scripts/grimis.py --help`.

## Try it first

Two complete vaults to open in Obsidian (File > Open folder as vault) or to query from the command line:

- `examples/demo-diskompen/`: built from a fictional performance report (LKjIP 2025) of a district communications office: context drafted from
  the document, 14 risks with the document's facts as the basis, real monthly availability data as KRI readings and as incidents, and a Monte Carlo
  suggestion. The ratings are the demo author's illustrative proposals.
- `examples/demo-vault/`: a fictional organisation over three fiscal years with two annual closes (trend, carry-over, plans NOT_REALISED).

```
python -P scripts/grimis.py --vault examples/demo-diskompen status
python -P scripts/grimis.py --vault examples/demo-diskompen check
python -P scripts/make_demo.py <new folder>            # rebuild the second demo
python -P scripts/make_demo_diskompen.py <new folder>  # rebuild the first demo
```

## Layout

```
SKILL.md              instructions for the agent (English); user-facing output is Indonesian
scripts/grimis.py     command line; gv_*.py are the engine modules; selftest.py; make_demo*.py
references/           vault model, risk cycle, drafting rules, matrix, KRI and simulation, report and close, limits
examples/             the two demo vaults
```

## Status

Written 2026-11-17. The engine self-test passes, and the Monte Carlo, percentile, KRI status and zone functions were compared with an
independent reference implementation (385 identical comparisons). The active-value, trend and close logic are covered by the self-test only;
nobody has used the skill on a real register yet. Treat its output as a working draft for the risk owner.
