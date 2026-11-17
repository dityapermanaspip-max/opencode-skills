# Laporan Manajemen Risiko Dinas Komunikasi dan Penerangan Kabupaten Tirta Sembada (dokumen fiktif) - 2025

Disusun 2026-11-17 dari vault manajemen risiko (kerangka ISO 31000: konteks, identifikasi, analisis, evaluasi, perlakuan, pemantauan). Matriks MTX-001 (5x5), batas appetite 14.

## 1. Konteks

- Mandat 2, sasaran 4, indikator 12, proses 8.
- Kamus: 14 peristiwa risiko, 8 kontrol.

## 2. Peta risiko (jumlah risiko per sel, nilai aktif)

```
K\D     1     2     3     4     5
  5     5     2     2     1    25
  4     4     8     3     2     1
  3     3     6     2    12    15
  2     2     4     6     8    10
  1     1     2     1     4     5
```

## 3. Profil risiko

| Risiko | Proses | Aktif | Sel | Skor | Zona | Appetite | Kontrol | Rencana | Insiden | Tren |
|---|---|---|---|---|---|---|---|---|---|---|
| RSK-005 Layanan jaringan dan pusat data terhenti melebihi batas ketersediaan yang ditargetkan | Pengelolaan jaringan dan pusat data | RESIDUAL | 5x4 | 20 | EXTREME | DI_ATAS_APPETITE | 1 | 1 | 10 |  |
| RSK-006 Server utama berusia delapan tahun gagal beroperasi sebelum server pengganti aktif | Pengelolaan jaringan dan pusat data | INHERENT | 4x5 | 20 | EXTREME | DI_ATAS_APPETITE | 0 | 1 | 0 |  |
| RSK-007 Kabel serat optik putus sehingga layanan jaringan terhenti | Pengelolaan jaringan dan pusat data | INHERENT | 4x4 | 16 | HIGH | DI_ATAS_APPETITE | 0 | 0 | 0 |  |
| RSK-008 Insiden keamanan informasi menyebabkan pengubahan tampilan atau akses tidak sah pada laman pemerintah daerah | Persandian dan penanganan insiden keamanan informasi | RESIDUAL | 4x4 | 16 | HIGH | DI_ATAS_APPETITE | 1 | 1 | 0 |  |
| RSK-001 Daftar Informasi Publik dan informasi berkala pada portal PPID tidak diperbarui | Layanan informasi publik (PPID) | RESIDUAL | 5x3 | 15 | HIGH | DI_ATAS_APPETITE | 1 | 1 | 0 |  |
| RSK-013 Pengadaan uji penetrasi dan token sertifikat elektronik tidak menghasilkan penyedia | Pengelolaan anggaran dan pengadaan | INHERENT | 5x3 | 15 | HIGH | DI_ATAS_APPETITE | 0 | 1 | 0 |  |
| RSK-004 Hasil evaluasi SPBE eksternal lebih rendah daripada evaluasi mandiri | Pengelolaan SPBE dan layanan terpadu (Sembada One) | RESIDUAL | 4x3 | 12 | MODERATE | DI_BAWAH_APPETITE | 1 | 1 | 0 |  |
| RSK-012 Rekomendasi hasil evaluasi akuntabilitas kinerja tidak ditindaklanjuti sesuai batas waktu | Perencanaan, pengukuran, dan pelaporan kinerja | RESIDUAL | 4x3 | 12 | MODERATE | DI_BAWAH_APPETITE | 2 | 1 | 0 |  |
| RSK-014 Anggaran kegiatan tidak terserap sesuai rencana | Pengelolaan anggaran dan pengadaan | INHERENT | 4x3 | 12 | MODERATE | DI_BAWAH_APPETITE | 0 | 0 | 0 |  |
| RSK-009 Dataset statistik sektoral tidak tersedia pada portal Satu Data sesuai jadwal | Penyelenggaraan statistik sektoral (Satu Data) | INHERENT | 5x2 | 10 | MODERATE | DI_BAWAH_APPETITE | 0 | 1 | 0 |  |
| RSK-011 Target Perjanjian Kinerja ditetapkan berbeda dari target Renstra | Perencanaan, pengukuran, dan pelaporan kinerja | INHERENT | 5x2 | 10 | MODERATE | DI_BAWAH_APPETITE | 0 | 1 | 0 |  |
| RSK-003 Konten diseminasi tidak menjangkau khalayak yang dituju | Diseminasi informasi dan pengelolaan konten | INHERENT | 3x3 | 9 | MODERATE_LOW | DI_BAWAH_APPETITE | 0 | 1 | 0 |  |
| RSK-010 Data capaian kinerja dilaporkan tanpa verifikasi independen | Perencanaan, pengukuran, dan pelaporan kinerja | RESIDUAL | 3x3 | 9 | MODERATE_LOW | DI_BAWAH_APPETITE | 2 | 0 | 0 |  |
| RSK-002 Permohonan informasi publik dilayani melewati sepuluh hari kerja | Layanan informasi publik (PPID) | RESIDUAL | 1x3 | 3 | LOW | DI_BAWAH_APPETITE | 1 | 0 | 0 |  |

## 4. Risiko di atas appetite

- RSK-001 Daftar Informasi Publik dan informasi berkala pada portal PPID tidak diperbarui (skor 15)
- RSK-005 Layanan jaringan dan pusat data terhenti melebihi batas ketersediaan yang ditargetkan (skor 20)
- RSK-006 Server utama berusia delapan tahun gagal beroperasi sebelum server pengganti aktif (skor 20)
- RSK-007 Kabel serat optik putus sehingga layanan jaringan terhenti (skor 16)
- RSK-008 Insiden keamanan informasi menyebabkan pengubahan tampilan atau akses tidak sah pada laman pemerintah daerah (skor 16)
- RSK-013 Pengadaan uji penetrasi dan token sertifikat elektronik tidak menghasilkan penyedia (skor 15)

## 5. Efektivitas kontrol

Kontrol terpasang menurut penilaian: EFFECTIVE 5, PARTIAL 4

## 6. Realisasi rencana perlakuan

Rencana: PLANNED 10; anggaran belum diisi.

## 7. Indikator risiko kunci (KRI)

| KRI | Nama | Risiko | Status | Pembacaan terakhir |
|---|---|---|---|---|
| KRI-002 | Informasi berkala pada portal PPID yang mutakhir | RSK-001 | grey | - |
| KRI-001 | Ketersediaan layanan jaringan dan pusat data | RSK-005 | amber | 98.6 |
| KRI-003 | Dataset statistik sektoral pada portal Satu Data | RSK-009 | grey | 74.0 |

## 8. Insiden tahun ini

| ID | Tanggal | Judul | Pasangan | Level dampak |
|---|---|---|---|---|
| INS-001 | 2025-01-31 | Ketersediaan Januari 99,10% (6,7 jam henti) | PRE-005 | 2 |
| INS-002 | 2025-02-28 | Ketersediaan Februari 98,90% (7,4 jam henti) | PRE-005 | 2 |
| INS-003 | 2025-05-31 | Ketersediaan Mei 98,60% (10,4 jam henti) | PRE-005 | 3 |
| INS-004 | 2025-06-30 | Ketersediaan Juni 96,80% (23,0 jam henti) | PRE-005 | 4 |
| INS-005 | 2025-07-31 | Ketersediaan Juli 97,80% (16,4 jam henti) | PRE-005 | 4 |
| INS-006 | 2025-08-31 | Ketersediaan Agustus 98,50% (11,2 jam henti) | PRE-005 | 3 |
| INS-007 | 2025-09-30 | Ketersediaan September 98,70% (9,4 jam henti) | PRE-005 | 3 |
| INS-008 | 2025-10-31 | Ketersediaan Oktober 96,20% (28,3 jam henti) | PRE-005 | 5 |
| INS-009 | 2025-11-30 | Ketersediaan November 98,40% (11,5 jam henti) | PRE-005 | 3 |
| INS-010 | 2025-12-31 | Ketersediaan Desember 98,60% (10,4 jam henti) | PRE-005 | 3 |

## 9. Catatan data

```
Tahun fiskal 2025 | periode tutup buku belum dibuka
Risiko dievaluasi: 14 dari 14 (belum dinilai 0)
Appetite: di bawah 8, DI ATAS 6, belum ada batas 0
ACTUAL belum diisi: 0 | rencana jatuh tempo <= 14 hari: 5
KRI merah 0, kuning 1, hijau 0, abu-abu 2
Laporan insiden menunggu: 0
```
