# The risk value cycle, plans, trend and the close

The rules below are implemented by the engine exactly as written.
The engine implements all of it; this file is for explaining it to a user and for deciding what to ask.

## Four values per evaluation

Each is a matrix cell written `LxI` (likelihood x impact), always inside the evaluation's matrix.

| Value | Filled | Meaning |
|---|---|---|
| inherent | any time | the risk with no controls at all |
| residual | any time | the risk today, with the existing controls |
| expected | any time | projection if every mitigation plan succeeds |
| actual | only while the close period is open | the real value at year end; input of the close only |

ACTUAL is never the active value.

## Which value is active (computed, never typed)

1. No existing control on the evaluation -> **INHERENT**.
2. At least one control, and there is no plan or not every plan is DONE -> **RESIDUAL**.
3. At least one control and there are plans and every plan is DONE -> **EXPECTED**.

It is recomputed after `rate`, `control add|remove`, `new rencana` and `plan done`. A new plan on an evaluation whose plans were
all DONE moves it back to RESIDUAL. The score of the active cell (likelihood x impact, unless the matrix overrides the cell) is
what appetite, the map and the report use. Always show the user `active_type`, never assume "residual".

Consistency flags (in `status`): RESIDUAL filled but no control; a control but no RESIDUAL; EXPECTED filled but no plan; a plan but no EXPECTED.
They are prompts to ask the user, not errors.

## Controls and plans

- A control in the dictionary (`CTL`) is attached to an evaluation as an *existing control* with an effectiveness, **and only
  when a person has put evidence for it in the evidence folder** (next section).
- A plan has an action, a person in charge, a target date, a budget and the control it will produce (`new_control_code`,
  optionally title and type). `plan done` marks it DONE, creates (or reuses by `code`) that control and attaches it to the
  evaluation with the plan as its source. A plan cannot be edited after its evaluation is closed.
- Plan statuses: PLANNED -> IN_PROGRESS -> DONE; NOT_REALISED is set only by the close.
- A control that came from a plan cannot be removed from its evaluation by hand.

### Bukti kontrol eksisting (evidence)

Kontrol eksisting diakui **hanya bila ada berkas buktinya**: SOP, tangkapan layar aplikasi, foto atau CCTV, dan sejenisnya,
yang **diletakkan oleh orang** di `08-Bukti/<EVA>/<CTL>/` (mis. `08-Bukti/EVA-2025-050/CTL-005/`). Engine hanya memeriksa bahwa
ada berkas di folder itu (berkas tersembunyi dan sementara tidak dihitung); engine dan agen tidak membaca, menilai, atau membuat bukti.

- `control add EVA CTL` ditolak bila foldernya belum berisi berkas. Engine menyiapkan foldernya dan menyebut lokasinya.
- Berkas yang salah folder dipindahkan ke folder yang benar bila ID `EVA-...` atau `CTL-...` ada pada nama berkas atau foldernya:
  otomatis oleh `control add` (untuk kontrol itu saja) dan oleh `evidence sort [--dry-run]` (semua berkas). Tidak pernah menimpa
  (bentrok nama diberi ` (2)`), dicatat di `LOG.md`, dan hanya berkas non-catatan yang disentuh. Yang tidak bisa dipastikan tujuannya
  dibiarkan dan dilaporkan beserta alasannya.
- `evidence show [EVA]` menunjukkan kontrol yang belum punya bukti dan folder tujuannya. `check` memberi WARN per evaluasi tahun kerja.
- Kontrol yang sudah terpasang sebelum aturan ini tetap terpasang dan tetap dihitung pada nilai aktif, tetapi ditandai **tanpa bukti**
  di `status`, `check`, laporan (Markdown, CSV, PDF) dan bowtie sampai berkasnya diletakkan. Itu bukan error.
- Kontrol yang berasal dari rencana DONE dibuktikan oleh rencananya (`plan done --evidence`), bukan oleh folder ini.
- Agen tidak boleh membuat, menyalin, atau mengganti nama berkas agar engine puas. Bila bukti belum ada, katakan apa yang perlu
  diletakkan dan di folder mana, lalu tunggu orangnya.

### SOP yang sudah berlaku versus SOP yang baru (aturan klasifikasi)

Klasifikasi ditentukan oleh **waktu mulai berlaku**, bukan oleh nama "SOP" atau "prosedur".

| Keadaan SOP | Masuk ke | Perintah | Akibat pada nilai |
|---|---|---|---|
| Sudah berlaku sebelum tahun kerja berjalan (misalnya sejak 2020) | **existing control** (`CTL-nnn`) | `new kontrol ...`, orang meletakkan berkas SOP-nya di `08-Bukti/<EVA>/<CTL>/`, lalu `control add EVA CTL --notes "berlaku sejak ..."` | Menjadi bagian RESIDUAL. Tidak membuat EXPECTED. |
| Baru dirancang atau baru ditetapkan pada tahun kerja berjalan | **rencana** (`PLN-nnn`) | `new rencana ... new_control_code=CTL-nnn`, lalu `plan start` / `plan done` | Sebelum DONE bukan kontrol eksisting. Setelah DONE kontrolnya dipasang engine dengan sumber rencana itu. |

- Jangan mengubah SOP lama menjadi rencana hanya agar kontrolnya terbawa saat tutup buku. Jangan pula mencatat SOP tahun ini sebagai existing control sebelum `plan done`.
- Bukti utama adalah berkas di folder bukti. Cantumkan juga mulai berlakunya SOP lama di kolom `notes` pada `control add` (sumber dokumen dan tahun berlaku, sesuai isi dokumen; jangan mengarang tahun).
- Simpan dua kategori ini terpisah di laporan dan saat tutup buku. `close` hanya membawa kontrol yang bersumber dari rencana **DONE**; kontrol eksisting tidak dibawa dan dicantumkan dalam `needs_controls` untuk dipasang ulang dengan `control add` dari CTL yang sama. Lihat langkah 4 di bawah.

## The fiscal period and the close

`open-period` opens the close period of the working year (`period_open: true`). While it is open ACTUAL may be entered. `close` then:

1. Refuses unless the period is open, an active matrix is set, every open evaluation of the year has ACTUAL, and next year's
   evaluations do not exist yet. The refusal names what is missing.
2. Creates next year's evaluation for each anchor on the **active matrix**.
   - Same matrix as this year: this year's ACTUAL becomes next year's RESIDUAL, and INHERENT is copied.
   - Different matrix: the new evaluation is empty and must be rated again. A matrix change is announced to the people involved.
3. Plans still open become NOT_REALISED (history only; they do not carry over). Plans that are DONE bring their control into next
   year's evaluation (effectiveness EFFECTIVE, source = the plan), whether or not the matrix changed.
4. **Controls that did not come from a DONE plan are not carried** (a deliberate rule of this workflow). The new evaluation may therefore
   hold a RESIDUAL with no control: the engine lists these ("perlu dipasang ulang kontrolnya") and the user installs the controls
   that still apply with `control add`; each needs its evidence in the new evaluation's folder (`08-Bukti/<new EVA>/<CTL>/`) again.
5. Trend of the closed evaluation: this year's RESIDUAL score against last year's RESIDUAL of the same anchor **on the same matrix**:
   lower = IMPROVING, higher = WORSENING, equal, or no comparable year, or no RESIDUAL = STABLE. Meaningful after a few years.
6. Closed evaluations are history: they accept no rating, control or plan changes. The working year moves to year + 1 and the
   period is closed; open it again when that year ends.

Before running `close` tell the user, in Indonesian: how many evaluations will close, whether the matrix changes, which plans
will become NOT_REALISED, and that old controls need to be installed again. Run it only after they agree.
