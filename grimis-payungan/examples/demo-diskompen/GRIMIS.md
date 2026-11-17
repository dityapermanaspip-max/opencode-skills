---
org: Dinas Komunikasi dan Penerangan Kabupaten Tirta Sembada (dokumen fiktif)
fiscal_year: 2025
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

## Catatan demo (baca dahulu)

Vault ini dibangun dari dokumen fiktif "Laporan Kinerja Instansi Pemerintah (LKjIP) 2025 Dinas Komunikasi dan Penerangan Kabupaten Tirta
Sembada". Dokumennya tidak disertakan di repositori. Yang berasal dari dokumen dan yang bukan:

- **Fakta dari dokumen**: sasaran, indikator, target, realisasi, kejadian, bulan, angka ketersediaan layanan per bulan, rencana perbaikan
  pada Bab IV. Nomor halaman ada pada deskripsi risiko.
- **Usulan penyusun demo (contoh, bukan penilaian Dinas)**: nilai inheren, residual dan ekspektasi, efektivitas kontrol, level dampak
  insiden menurut kriteria contoh, batas appetite 14 (batas atas zona MODERATE), ambang KRI (kuning 99,50 mengikuti target PK; merah 98,00 dipakai dokumen untuk
  menyebut bulan terburuk) dan alasan penilaian pada tiap evaluasi.
- **Tanggal**: rencana yang tanggalnya tidak disebut dokumen diberi 2026-12-31 sementara (tertulis pada catatan rencana). Insiden
  ketersediaan bertanggal akhir bulan karena dokumen hanya menyebut bulan.
- **Tidak dimasukkan**: 14 insiden keamanan informasi (5 phishing, 4 malware, 3 pengubahan tampilan, 2 akses tidak sah) karena dokumen
  hanya memberi jumlah, tanpa tanggal dan dampak per kejadian. Tambahkan dengan `new insiden` bila datanya ada.
- **Belum dikerjakan**: ACTUAL, periode tutup buku dan tren. Coba `open-period`, isi ACTUAL, lalu `close`.

Alur yang dipakai: konteks, risiko, bowtie dan KRI masuk sebagai draf (`_Draft/`) yang diterima atau ditolak seseorang; nilai dan
status dihitung mesin (`check` dan `status` bisa dijalankan kapan saja).
