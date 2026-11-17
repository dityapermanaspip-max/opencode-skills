# Laporan Manajemen Risiko Instansi Demo - 2025

Disusun 2026-11-17 dari vault GRIMIS (kerangka ISO 31000: konteks, identifikasi, analisis, evaluasi, perlakuan, pemantauan). Matriks MTX-001 (5x5), batas appetite 9.

## 1. Konteks

- Mandat 1, sasaran 2, indikator 2, proses 3.
- Kamus: 5 peristiwa risiko, 6 kontrol.

## 2. Peta risiko (jumlah risiko per sel, nilai aktif)

```
K\D     1     2     3     4     5
  5     5    10    15    20    25
  4     4     8    12    16    20
  3     3     6     3    12    15
  2     2     4     2     8    10
  1     1     2     3     4     5
```

## 3. Profil risiko

| Risiko | Proses | Aktif | Sel | Skor | Zona | Appetite | Kontrol | Rencana | Insiden | Tren |
|---|---|---|---|---|---|---|---|---|---|---|
| RSK-001 Berkas permohonan izin hilang saat berpindah antarbagian | Pelayanan perizinan | RESIDUAL | 3x3 | 9 | MODERATE_LOW | DI_BAWAH_APPETITE | 2 | 0 | 1 | IMPROVING |
| RSK-002 Izin terbit melewati batas waktu standar | Pelayanan perizinan | RESIDUAL | 3x3 | 9 | MODERATE_LOW | DI_BAWAH_APPETITE | 1 | 0 | 0 | STABLE |
| RSK-004 Bukti pertanggungjawaban belanja tidak lengkap saat diperiksa | Pembayaran dan pertanggungjawaban belanja | RESIDUAL | 3x3 | 9 | MODERATE_LOW | DI_BAWAH_APPETITE | 1 | 1 | 0 | STABLE |
| RSK-003 Tagihan penyedia dibayar dua kali | Pembayaran dan pertanggungjawaban belanja | EXPECTED | 2x3 | 6 | MODERATE_LOW | DI_BAWAH_APPETITE | 2 | 1 | 1 | WORSENING |
| RSK-005 Dokumen arsip rusak di ruang penyimpanan | Pengelolaan arsip dokumen | RESIDUAL | 2x3 | 6 | MODERATE_LOW | DI_BAWAH_APPETITE | 1 | 0 | 0 | STABLE |

## 4. Risiko di atas appetite

Tidak ada.

## 5. Efektivitas kontrol

Kontrol terpasang menurut penilaian: EFFECTIVE 7

## 6. Realisasi rencana perlakuan

Rencana: DONE 1, NOT_REALISED 1; anggaran Rp48,000,000.

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
| INS-003 | 2025-05-06 | Berkas hilang di loket | PRE-001 | 3 |
| INS-004 | 2025-09-17 | Tagihan terbayar ganda | PRE-003 | 4 |
