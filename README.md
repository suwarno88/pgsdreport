# 🎓 PGSD Performance Indicator Dashboard 2026

Dashboard interaktif untuk memvisualisasikan dan membandingkan **Performance Indicator** jurusan **Pendidikan Guru Sekolah Dasar (PGSD)** tahun 2026. Dibangun menggunakan **Streamlit** dan **Plotly** untuk analisis data yang responsif dan *user-friendly*.

---

## ✨ Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| **Perbandingan Target vs Realisasi** | Pilih kuartal (Q1–Q4) dan lihat perbandingan horizontal bar chart |
| **Persentase Capaian** | Bar chart dengan warna otomatis: hijau (≥100%), kuning (≥75%), merah (<75%) |
| **Analisis Tren Kuartal** | Line chart tren target dari Q1 hingga Q4 per indikator terpilih |
| **Radar Chart** | Perbandingan normalized Target Q4 vs Realisasi dalam bentuk radar |
| **PI Focus Cards** | Detail card khusus untuk indikator prioritas tinggi |
| **Donut Chart Status** | Ringkasan visual status pencapaian PI Focus |
| **Distribusi Skor** | Histogram distribusi skor seluruh indikator |
| **Tabel Interaktif** | Pencarian, sortir, dan download data CSV |
| **Filter Dinamis** | Filter berdasarkan kuartal, PI Focus, dan kategori indikator |

---

## 🚀 Cara Menjalankan

### Prasyarat
- Python 3.9 atau lebih baru
- pip (Python package manager)

### Instalasi Lokal

```bash
# 1. Clone repository
git clone https://github.com/<username>/pgsd-performance-dashboard.git
cd pgsd-performance-dashboard

# 2. (Opsional) Buat virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 3. Install dependensi
pip install -r requirements.txt

# 4. Jalankan aplikasi
streamlit run app.py
```

Aplikasi akan terbuka di browser pada `http://localhost:8501`.

---

## 🌐 Deploy ke Streamlit Cloud

1. Push seluruh kode ke repository GitHub (pastikan folder `data/` ikut ter-push).
2. Buka [share.streamlit.io](https://share.streamlit.io).
3. Klik **New app** → pilih repository, branch `main`, dan file `app.py`.
4. Klik **Deploy** — aplikasi akan live dalam beberapa menit.

---

## 📁 Struktur Proyek

```
pgsd-performance-dashboard/
├── app.py                  # Aplikasi utama Streamlit
├── requirements.txt        # Daftar dependensi Python
├── README.md               # Dokumentasi proyek
└── data/
    └── ReportRealization_Pendidikan_Guru_Sekolah_Dasar__PGSD_.xlsx
```

---

## 📊 Tentang Data

Data bersumber dari **Report Realization** jurusan PGSD tahun 2026, berisi 65 Performance Indicator dengan kolom:

- **No** — Nomor urut indikator
- **Year** — Tahun pelaporan (2026)
- **Performance Indicator** — Nama indikator kinerja
- **Unit Name** — Pendidikan Guru Sekolah Dasar (PGSD)
- **Target Q1–Q4** — Target per kuartal
- **Realization** — Nilai realisasi aktual
- **Score** — Skor penilaian
- **PI Focus** — YES/NO, menandai indikator prioritas tinggi

### Asumsi & Catatan

- Beberapa indikator memiliki target non-numerik (teks) di Q4 yang tidak disertakan dalam perhitungan perbandingan.
- Nilai `NaN` pada target atau realisasi berarti data belum tersedia untuk periode tersebut.
- Perhitungan **Achievement %** = (Realisasi / Target Kuartal) × 100.
- Indikator dikategorikan otomatis berdasarkan kata kunci pada nama indikator.

---

## 🛠 Teknologi

- **[Streamlit](https://streamlit.io/)** — Framework dashboard Python
- **[Plotly](https://plotly.com/python/)** — Library visualisasi interaktif
- **[Pandas](https://pandas.pydata.org/)** — Manipulasi & analisis data
- **[OpenPyXL](https://openpyxl.readthedocs.io/)** — Pembacaan file Excel

---

## 📝 Lisensi

Proyek ini dibuat untuk kebutuhan internal monitoring kinerja jurusan PGSD.
