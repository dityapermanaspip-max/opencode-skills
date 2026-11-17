# Laporan Manajemen Risiko Instansi Demo - 2026

Disusun 2026-11-17 dari vault GRIMIS (kerangka ISO 31000: konteks, identifikasi, analisis, evaluasi, perlakuan, pemantauan). Matriks MTX-001 (5x5), batas appetite 9.

## 1. Konteks

- Mandat 1, sasaran 2, indikator 2, proses 3.
- Kamus: 5 peristiwa risiko, 6 kontrol.

## 2. Peta risiko (jumlah risiko per sel, nilai aktif)

```
K\D     1     2     3     4     5
  5     5    10    15    20    25
  4     4     8    12    16    20
  3     3     6     1    12     1
  2     2     4     1     1    10
  1     1     2     1     4     5
```

## 3. Profil risiko

| Risiko | Proses | Aktif | Sel | Skor | Zona | Appetite | Kontrol | Rencana | Insiden | Tren |
|---|---|---|---|---|---|---|---|---|---|---|
| RSK-003 Tagihan penyedia dibayar dua kali | Pembayaran dan pertanggungjawaban belanja | RESIDUAL | 3x5 | 15 | HIGH | DI_ATAS_APPETITE | 2 | 1 | 2 | WORSENING |
| RSK-002 Izin terbit melewati batas waktu standar | Pelayanan perizinan | RESIDUAL | 3x3 | 9 | MODERATE_LOW | DI_BAWAH_APPETITE | 1 | 0 | 1 | STABLE |
| RSK-001 Berkas permohonan izin hilang saat berpindah antarbagian | Pelayanan perizinan | RESIDUAL | 2x4 | 8 | MODERATE_LOW | DI_BAWAH_APPETITE | 2 | 1 | 3 | IMPROVING |
| RSK-004 Bukti pertanggungjawaban belanja tidak lengkap saat diperiksa | Pembayaran dan pertanggungjawaban belanja | RESIDUAL | 2x3 | 6 | MODERATE_LOW | DI_BAWAH_APPETITE | 1 | 0 | 0 | STABLE |
| RSK-005 Dokumen arsip rusak di ruang penyimpanan | Pengelolaan arsip dokumen | EXPECTED | 1x3 | 3 | LOW | DI_BAWAH_APPETITE | 2 | 1 | 0 | STABLE |

## 4. Risiko di atas appetite

- RSK-003 Tagihan penyedia dibayar dua kali (skor 15)

## 5. Efektivitas kontrol

Kontrol terpasang menurut penilaian: EFFECTIVE 8

## 6. Realisasi rencana perlakuan

Rencana: DONE 1, IN_PROGRESS 1, PLANNED 1; anggaran Rp57,000,000.

## 7. Indikator risiko kunci (KRI)

| KRI | Nama | Risiko | Status | Pembacaan terakhir |
|---|---|---|---|---|
| KRI-001 | Berkas hilang per bulan | RSK-001 | amber | 3.0 |
| KRI-002 | Izin melewati batas waktu | RSK-002 | red | 22.0 |
| KRI-003 | Tagihan dibayar tanpa verifikasi ganda | RSK-003 | green | 0.0 |
| KRI-004 | Arsip tersimpan sesuai standar | RSK-005 | amber | 82.0 |

## 8. Insiden tahun ini

| ID | Tanggal | Judul | Pasangan | Level dampak |
|---|---|---|---|---|
| INS-005 | 2026-02-12 | Berkas hilang di loket 2 | PRE-001 | 3 |
| INS-006 | 2026-05-20 | Berkas tertukar antarbagian | PRE-001 | 2 |
| INS-007 | 2026-09-03 | Berkas hilang saat dipindah | PRE-001 | 3 |
| INS-010 | 2026-06-01 | Izin terlambat 9 hari | PRE-002 | 2 |
| INS-008 | 2026-04-14 | Tagihan terbayar ganda | PRE-003 | 4 |
| INS-009 | 2026-08-30 | Tagihan terbayar ganda lagi | PRE-003 | 5 |

## 9. Catatan data

```
Tahun fiskal 2026 | periode tutup buku belum dibuka
Risiko dievaluasi: 5 dari 5 (belum dinilai 0)
Appetite: di bawah 4, DI ATAS 1, belum ada batas 0
ACTUAL belum diisi: 0 | rencana jatuh tempo <= 14 hari: 0
KRI merah 1, kuning 2, hijau 1, abu-abu 0
Laporan insiden menunggu: 1
Cek konsistensi: plan_no_expected=1
```
