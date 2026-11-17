---
org: Instansi Demo
fiscal_year: 2026
period_open: false
active_matrix: "[[MTX-001]]"
---

# GRIMIS: vault manajemen risiko

Vault ini dikelola oleh skill `grimis-payungan`. Siklusnya: mandat -> sasaran -> indikator -> proses
-> identifikasi risiko -> evaluasi (inheren, residual, ekspektasi, aktual) -> mitigasi -> insiden -> tutup buku tahunan.

- Satu catatan = satu objek. ID dan nama berkas sama (mis. `RSK-001.md`). Tautan memakai `[[ID]]`.
- Nilai dan status yang beraturan diubah lewat perintah `grimis.py` (rate, plan, kri, close), bukan diketik manual.
- Teks bebas (deskripsi, penyebab, dampak, catatan) boleh diedit langsung.
- `LOG.md` mencatat setiap perubahan dan hanya bertambah. `00-Dashboard.md` dan `99-Laporan/` dibuat otomatis.
- Kolom di atas (org, fiscal_year, period_open, active_matrix) adalah pengaturan akar: tahun kerja, apakah periode tutup buku
  dibuka (ACTUAL baru boleh diisi saat dibuka), dan matriks aktif untuk tahun depan.
