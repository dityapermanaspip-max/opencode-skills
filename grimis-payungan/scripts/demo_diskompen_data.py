"""Data for examples/demo-diskompen: facts taken from the fictional report 'LKjIP 2025 Dinas Komunikasi dan Penerangan Kabupaten Tirta Sembada'
(page numbers are those of the report). Ratings (inherent/residual/expected) are the demo author's ILLUSTRATIVE proposals."""

ORG = "Dinas Komunikasi dan Penerangan Kabupaten Tirta Sembada (dokumen fiktif)"
YEAR = 2025

MANDATES = [("m1", "Peraturan Bupati Nomor 45 Tahun 2021 tentang tugas, fungsi, dan tata kerja Dinas", "LKjIP 2025 Bab I.B dan I.D"),
            ("m2", "Rencana Strategis Dinas 2021-2026 dan Perjanjian Kinerja 2025", "LKjIP 2025 Bab II")]
OBJECTIVES = ["Meningkatnya keterbukaan dan kualitas informasi publik", "Meningkatnya kualitas penyelenggaraan sistem pemerintahan berbasis elektronik",
              "Meningkatnya keamanan informasi dan ketersediaan data statistik sektoral", "Meningkatnya akuntabilitas kinerja dan tata kelola Dinas"]
# code, objective index, title, unit, target PK 2025
INDICATORS = [("1.1", 0, "Skor Monev Keterbukaan Informasi Publik Badan Publik (skala 0 s.d. 100)", "skor", "82,00"),
              ("1.2", 0, "Persentase permohonan informasi publik yang dilayani dalam 10 hari kerja", "%", "95,00"),
              ("1.3", 0, "Jumlah konten diseminasi informasi program pemerintah daerah", "konten", "1.200"),
              ("2.1", 1, "Indeks SPBE (skala 0 s.d. 5)", "indeks", "3,20"),
              ("2.2", 1, "Persentase PD yang terintegrasi dengan aplikasi layanan terpadu", "%", "80,00"),
              ("2.3", 1, "Persentase ketersediaan layanan jaringan dan pusat data", "%", "99,50"),
              ("3.1", 2, "Persentase insiden keamanan informasi yang ditangani sesuai SOP", "%", "100,00"),
              ("3.2", 2, "Persentase PD yang menggunakan sertifikat elektronik", "%", "60,00"),
              ("3.3", 2, "Jumlah dataset statistik sektoral pada portal Satu Data", "dataset", "120"),
              ("4.1", 3, "Nilai evaluasi akuntabilitas kinerja Perangkat Daerah (skala 0 s.d. 100)", "nilai", "72,00"),
              ("4.2", 3, "Persentase penyerapan anggaran", "%", "95,00"),
              ("4.3", 3, "Persentase tindak lanjut rekomendasi hasil evaluasi", "%", "100,00")]
# key, title, owner, indicator codes
PROCESSES = [("ppid", "Layanan informasi publik (PPID)", "Bidang Informasi dan Komunikasi Publik, Seksi Layanan Informasi Publik", ["1.1", "1.2"]),
             ("konten", "Diseminasi informasi dan pengelolaan konten", "Seksi Pengelolaan Media dan Konten", ["1.3"]),
             ("spbe", "Pengelolaan SPBE dan layanan terpadu (Sembada One)", "Bidang Aplikasi Informatika dan E-Government", ["2.1", "2.2"]),
             ("jaringan", "Pengelolaan jaringan dan pusat data", "Seksi Infrastruktur TIK dan Persandian", ["2.3"]),
             ("keamanan", "Persandian dan penanganan insiden keamanan informasi", "Seksi Infrastruktur TIK dan Persandian", ["3.1", "3.2"]),
             ("statistik", "Penyelenggaraan statistik sektoral (Satu Data)", "Seksi Statistik Sektoral", ["3.3"]),
             ("kinerja", "Perencanaan, pengukuran, dan pelaporan kinerja", "Subbagian Perencanaan dan Keuangan", ["4.1", "4.3"]),
             ("anggaran", "Pengelolaan anggaran dan pengadaan", "Subbagian Perencanaan dan Keuangan", ["4.2", "3.2"])]
CONTROLS = {"bimtek": ("Bimbingan teknis bagi PPID Pelaksana (dua kali pada 2025)", "preventif"),
            "sop": ("SOP penanganan insiden keamanan informasi", "korektif"),
            "triwulan": ("Pemantauan kinerja triwulanan (empat kali pada 2025)", "detektif"),
            "manual": ("Manual indikator kinerja dan penjenjangan kinerja (berlaku Februari 2025)", "preventif"),
            "lognet": ("Log pemantauan jaringan dan pusat data", "detektif"),
            "spbe": ("Evaluasi mandiri SPBE oleh Tim Koordinasi SPBE", "detektif"),
            "kabid": ("Reviu data kinerja oleh masing-masing kepala bidang", "detektif"),
            "sepuluh": ("Layanan permohonan informasi dengan batas sepuluh hari kerja", "preventif")}
ASSUMED = "Tanggal target tidak disebut dokumen; akhir tahun 2026 dipakai sebagai batas sementara."
# key, process key, indicator, title, description, inherent, residual, expected, [(control key, effectiveness)], why, plan
# plan = (action, target date, code, title, type, note) or None
RISKS = [
 ("ppid", "ppid", "1.1", "Daftar Informasi Publik dan informasi berkala pada portal PPID tidak diperbarui",
  "Daftar Informasi Publik terakhir diperbarui Maret 2024 dan sebagian PD belum menyampaikan pembaruan berkala (hal. 11).", "5x3", "5x3", "2x3",
  [("bimtek", "PARTIAL")], "Kejadiannya sudah berlangsung (kemungkinan 5); skor Monev 78,40 (Cukup Informatif) di bawah target 82,00 (dampak 3). Dua bimtek belum menyelesaikan masalah.",
  ("Memperbarui Daftar Informasi Publik dan melengkapi informasi berkala pada portal PPID", "2026-03-31", "DIP-01", "Daftar Informasi Publik dan informasi berkala mutakhir", "preventif", "LKjIP Bab IV.B butir 1: paling lambat Maret 2026.")),
 ("permohonan", "ppid", "1.2", "Permohonan informasi publik dilayani melewati sepuluh hari kerja",
  "Permohonan naik dari 64 (2024) menjadi 87 (2025); seluruhnya dilayani dalam sepuluh hari kerja (hal. 11).", "3x3", "1x3", None,
  [("sepuluh", "EFFECTIVE")], "Seluruh 87 permohonan tepat waktu: kemungkinan residual 1.", None),
 ("konten", "konten", "1.3", "Konten diseminasi tidak menjangkau khalayak yang dituju",
  "Indikator hanya menghitung jumlah konten (1.536); jangkauan dan pemahaman khalayak belum diukur dan hasil survei kepuasan masyarakat Desember 2025 masih diolah (hal. 11-12).",
  "3x3", None, "2x3", [], "Belum ada pengendalian pengukuran jangkauan.",
  ("Melaksanakan survei kepuasan masyarakat atas layanan informasi dan memakai hasilnya", "2026-12-31", "IKM-02", "Survei kepuasan masyarakat berkala", "detektif", ASSUMED + " LKjIP Bab IV.B butir 6.")),
 ("spbe", "spbe", "2.1", "Hasil evaluasi SPBE eksternal lebih rendah daripada evaluasi mandiri",
  "Indeks SPBE 2,95 berasal dari evaluasi mandiri dan belum divalidasi eksternal; audit TIK belum pernah dilaksanakan; domain Manajemen (2,60) dan Tata Kelola (2,80) terendah (hal. 12).",
  "4x3", "4x3", "3x3", [("spbe", "PARTIAL")], "Nilai belum tervalidasi dan capaian 92,19% di bawah target.",
  ("Melaksanakan audit teknologi informasi dan komunikasi", "2026-12-31", "AUD-03", "Audit teknologi informasi dan komunikasi", "detektif", ASSUMED + " LKjIP Bab IV.B butir 6.")),
 ("avail", "jaringan", "2.3", "Layanan jaringan dan pusat data terhenti melebihi batas ketersediaan yang ditargetkan",
  "Ketersediaan rata-rata 98,40% dari target 99,50%; hanya 2 dari 12 bulan memenuhi target dan 140,9 jam henti sepanjang 2025 (Lampiran 2).", "5x4", "sim", "3x3",
  [("lognet", "PARTIAL")], "Residual diambil dari saran simulasi Monte Carlo atas 10 bulan di bawah target (lihat bagian Simulasi): log pemantauan hanya mendeteksi gangguan, tidak mencegahnya.",
  ("Menyusun rencana pemeliharaan catu daya dan pendingin ruang server", "2026-03-31", "PEL-04", "Rencana pemeliharaan catu daya dan pendingin ruang server", "preventif", "LKjIP Bab IV.B butir 2; tanggal mengikuti butir itu (Maret 2026).")),
 ("server", "jaringan", "2.3", "Server utama berusia delapan tahun gagal beroperasi sebelum server pengganti aktif",
  "Dua server dan satu perangkat penyimpanan pengganti diterima 29 Desember 2025 dan dijadwalkan beroperasi Maret 2026 setelah migrasi (hal. 12).", "4x5", None, "1x4", [],
  "Server lama masih melayani sampai migrasi selesai.",
  ("Memasang dan memigrasikan sistem ke server baru", "2026-03-31", "MIG-05", "Server baru beroperasi", "korektif", "LKjIP Bab IV.B butir 2: paling lambat Maret 2026.")),
 ("kabel", "jaringan", "2.3", "Kabel serat optik putus sehingga layanan jaringan terhenti",
  "Putus pada Juni dan Oktober 2025; kedua bulan itu mencatat ketersediaan terendah, 96,80% dan 96,20% (hal. 12).", "4x4", None, None, [], "Terjadi dua kali pada 2025 (kemungkinan 4).", None),
 ("insiden", "keamanan", "3.1", "Insiden keamanan informasi menyebabkan pengubahan tampilan atau akses tidak sah pada laman pemerintah daerah",
  "Tercatat 14 insiden pada 2025: 5 phishing, 4 malware, 3 pengubahan tampilan laman, 2 akses tidak sah; seluruhnya ditangani sesuai SOP (hal. 12).", "5x4", "4x4", "3x4",
  [("sop", "EFFECTIVE")], "SOP efektif menangani, tetapi insiden tetap terjadi dan uji penetrasi belum terlaksana.",
  ("Melaksanakan uji penetrasi setelah penyedia diperoleh", "2026-03-31", "PEN-06", "Uji penetrasi sistem pemerintah daerah", "detektif", "LKjIP Bab IV.B butir 5: triwulan I 2026.")),
 ("dataset", "statistik", "3.3", "Dataset statistik sektoral tidak tersedia pada portal Satu Data sesuai jadwal",
  "74 dari 120 dataset (61,67%); sebagian PD produsen data belum menyampaikan data dan keputusan pembaruan Forum Satu Data belum ditetapkan (hal. 12-13).", "5x2", None, "3x2", [],
  "Capaian jauh di bawah target (kemungkinan 5); dampak pada perencanaan daerah dinilai kecil sampai sedang.",
  ("Memperbarui keputusan Forum Satu Data dan menetapkan jadwal penyampaian data oleh PD produsen data", "2026-12-31", "FSD-07", "Keputusan dan jadwal Forum Satu Data", "preventif", ASSUMED + " LKjIP Bab IV.B butir 4.")),
 ("datakinerja", "kinerja", "4.1", "Data capaian kinerja dilaporkan tanpa verifikasi independen",
  "Data direviu oleh masing-masing kepala bidang dan belum diverifikasi terpisah oleh unit lain; Indeks SPBE bersumber dari evaluasi mandiri (hal. 9, 12).", "3x3", "3x3", None,
  [("kabid", "PARTIAL"), ("triwulan", "EFFECTIVE")], "Ada reviu berjenjang, tetapi tidak independen.", None),
 ("targetpk", "kinerja", "4.1", "Target Perjanjian Kinerja ditetapkan berbeda dari target Renstra",
  "Target PK 2025 lebih rendah daripada Renstra pada beberapa indikator (13 indikator Renstra, 12 pada PK) tanpa perubahan Renstra (hal. 5, 15).", "5x2", None, "2x2", [],
  "Sudah terjadi pada 2025 (kemungkinan 5); dampaknya pada penilaian akuntabilitas kecil.",
  ("Menyelaraskan target Perjanjian Kinerja 2026 dengan Renstra", "2026-12-31", "TGT-08", "Target PK selaras dengan Renstra", "preventif", ASSUMED + " LKjIP Bab IV.B butir 3.")),
 ("tindaklanjut", "kinerja", "4.3", "Rekomendasi hasil evaluasi akuntabilitas kinerja tidak ditindaklanjuti sesuai batas waktu",
  "Dari 7 rekomendasi, 4 selesai (57,14%); reviu IKU dan penyelarasan target belum, pemanfaatan hasil evaluasi masih proses (hal. 15).", "4x3", "4x3", "3x3",
  [("triwulan", "EFFECTIVE"), ("manual", "EFFECTIVE")], "Capaian 57,14% terhadap target 100%.",
  ("Mereviu IKU agar memuat indikator hasil (outcome)", "2026-12-31", "IKU-09", "IKU berorientasi hasil", "korektif", ASSUMED + " LKjIP Bab IV.B butir 3.")),
 ("pengadaan", "anggaran", "3.2", "Pengadaan uji penetrasi dan token sertifikat elektronik tidak menghasilkan penyedia",
  "Pada 2025 proses pengadaan tidak menghasilkan penyedia hingga akhir tahun sehingga kegiatan tidak terlaksana; Program Persandian terserap 75,00% (hal. 12, 13).", "5x3", None, "2x3", [],
  "Sudah terjadi pada 2025 (kemungkinan 5).",
  ("Menjadwalkan ulang pengadaan uji penetrasi dan token pada triwulan I 2026", "2026-03-31", "PGD-10", "Penyedia uji penetrasi dan token diperoleh", "korektif", "LKjIP Bab IV.B butir 5: triwulan I 2026.")),
 ("anggaran", "anggaran", "4.2", "Anggaran kegiatan tidak terserap sesuai rencana",
  "Serapan 93,56% dari target 95,00%; Layanan PPID hanya 61,50% dan Program Persandian 75,00%; sisa anggaran Rp963.569.000 (hal. 12-14).", "4x3", None, None, [],
  "Sudah terjadi pada dua kegiatan (kemungkinan 4).", None),
]
BOWTIE = {
 "ppid": [("cause", "Bimbingan teknis belum membuat seluruh PD menyampaikan pembaruan berkala", "Stakeholders"), ("cause", "Daftar Informasi Publik tidak ditinjau sejak Maret 2024", "Kelalaian Manusia"),
          ("impact", "Skor Monev keterbukaan informasi publik tidak mencapai target", "Reputasi")],
 "avail": [("cause", "Catu daya dan pendingin ruang server bermasalah", "Kelalaian Manusia"), ("cause", "Kabel serat optik putus", "Stakeholders"), ("cause", "Server utama berusia delapan tahun", "Kebijakan"),
           ("impact", "Aplikasi layanan terpadu tidak dapat diakses pengguna", "Gangguan Layanan")],
 "server": [("cause", "Perangkat pengganti baru diterima 29 Desember 2025", "Kebijakan"), ("impact", "Seluruh layanan berbasis server utama terhenti", "Gangguan Layanan"), ("impact", "Data tersimpan di server lama hilang", "Finansial")],
 "insiden": [("cause", "Uji penetrasi belum terlaksana", "Kebijakan"), ("cause", "Pengguna membuka surel phishing", "Kelalaian Manusia"), ("impact", "Tampilan laman pemerintah daerah diubah pihak lain", "Reputasi"), ("impact", "Data akses tidak sah bocor", "Hukum")],
 "dataset": [("cause", "PD produsen data tidak menyampaikan data sesuai jadwal", "Stakeholders"), ("cause", "Keputusan pembaruan Forum Satu Data belum ditetapkan", "Kebijakan"),
             ("impact", "Data sektoral tidak tersedia bagi perencanaan daerah", "Gangguan Layanan")]}
AVAIL = [("Januari", 31, "99,10", 6.7), ("Februari", 28, "98,90", 7.4), ("Mei", 31, "98,60", 10.4), ("Juni", 30, "96,80", 23.0), ("Juli", 31, "97,80", 16.4),
         ("Agustus", 31, "98,50", 11.2), ("September", 30, "98,70", 9.4), ("Oktober", 31, "96,20", 28.3), ("November", 30, "98,40", 11.5), ("Desember", 31, "98,60", 10.4)]
AVAIL_ALL = [("01", 99.10), ("02", 98.90), ("03", 99.60), ("04", 99.55), ("05", 98.60), ("06", 96.80), ("07", 97.80), ("08", 98.50), ("09", 98.70), ("10", 96.20), ("11", 98.40), ("12", 98.60)]
MONTH_NO = {"Januari": "01", "Februari": "02", "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08", "September": "09", "Oktober": "10", "November": "11", "Desember": "12"}
DOWNTIME_CRITERIA = [(1, "Jam henti sampai 4 jam dalam sebulan"), (2, "Lebih dari 4 sampai 8 jam"), (3, "Lebih dari 8 sampai 16 jam"), (4, "Lebih dari 16 sampai 24 jam"), (5, "Lebih dari 24 jam")]


def downtime_level(hours: float) -> int:
    return 1 if hours <= 4 else 2 if hours <= 8 else 3 if hours <= 16 else 4 if hours <= 24 else 5
