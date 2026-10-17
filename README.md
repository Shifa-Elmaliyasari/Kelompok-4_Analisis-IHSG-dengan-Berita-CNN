# 📈 Berita & IHSG — Data Warehouse Berita Ekonomi dan Pasar Saham Indonesia

Project ini adalah tugas Data Mining 2 / Data Warehousing yang mengintegrasikan tiga sumber data (berita CNN Indonesia, berita CNBC Indonesia, dan harga IHSG) ke dalam sebuah data warehouse berbasis **DuckDB** dan **DuckLake**, lalu menyajikannya lewat dashboard **Streamlit**.

Periode data: **20 Oktober 2024 – 20 September 2026** (masa pemerintahan Prabowo).

## 🎯 Tujuan Project

Membangun data warehouse yang memungkinkan kita melihat hubungan antara pemberitaan media dan pergerakan pasar saham. Pertanyaan yang ingin dijawab:

- Seberapa banyak berita yang terbit per hari, per tema, dan per sumber?
- Tema apa yang paling banyak diberitakan di masa pemerintahan ini?
- Apakah jumlah berita berkaitan dengan return harian IHSG?
- Kata apa yang sering muncul saat IHSG naik dibanding saat turun?
- Bagaimana tren topik tertentu (misalnya MBG, Danantara, tarif) dari waktu ke waktu?
- Bagaimana IHSG bergerak di sekitar peristiwa penting?
- Apa perbedaan fokus pemberitaan CNN Indonesia dan CNBC Indonesia?

## 📦 Dataset

| Sumber | Isi | Granularitas | Jumlah data |
|---|---|---|---|
| CNN Indonesia | Judul berita dari halaman indeks per kanal | 1 baris = 1 artikel | 105.469 berita |
| CNBC Indonesia | Judul berita dari halaman indeks | 1 baris = 1 artikel | 146.178 berita |
| Yahoo Finance (`^JKSE`) | Harga open, high, low, close, volume IHSG | 1 baris = 1 hari bursa | 452 hari bursa |

Ketiganya punya granularitas berbeda: berita bersifat per artikel (termasuk akhir pekan), sedangkan IHSG hanya ada pada hari bursa. Penyelarasan keduanya dilakukan pada level **tanggal**.

## 🏗️ Arsitektur Data Warehouse

```
        SUMBER DATA
            │
  ┌─────────┼─────────┐
  ▼         ▼         ▼
 CNN      CNBC     Yahoo Finance
  │         │         │
  ▼         ▼         ▼
scraping  scraping  scraping
_cnn.py   _cnbc.py  _ihsg.py
  │         │         │
  ▼         ▼         ▼
cnn.duckdb cnbc.duckdb ihsg.duckdb      ← STAGING (satu file per sumber)
  │         │         │
  └─────────┼─────────┘
            ▼
     buat_ducklake.py  (+ tema.py)      ← ETL / ELT
            ▼
        DUCKLAKE
 berita_ihsg.ducklake + data/
 ├── cnn.berita
 ├── cnbc.berita
 ├── pasar.ihsg
 └── analitik.berita_semua
            ▼
   STREAMLIT DASHBOARD
```

### 🗄️ Layer 1 — DuckDB per sumber (staging)

Setiap sumber disimpan di file DuckDB sendiri di folder `data_duckdb/`:

| File | Tabel | Keterangan |
|---|---|---|
| `cnn.duckdb` | `berita` | Berita CNN Indonesia |
| `cnbc.duckdb` | `berita` | Berita CNBC Indonesia |
| `ihsg.duckdb` | `ihsg` | Harga harian IHSG |

Layer ini berfungsi sebagai data mentah yang masih bisa ditelusuri ke sumbernya. Pemisahan per file membuat tiap scraper berjalan mandiri dan bisa dilanjutkan (resumable) lewat file progress (`cnn_progress.json`, `cnbc_progress.json`). Duplikasi dicegah dengan `INSERT OR IGNORE` (berita, kunci berupa tautan/ID artikel) dan `INSERT OR REPLACE` (IHSG, kunci berupa tanggal).

### 🦆 Layer 2 — DuckLake (integrasi)

Data dari tiga file DuckDB digabung ke satu DuckLake oleh `buat_ducklake.py`:

- **Catalog/metadata:** `ducklake/berita_ihsg.ducklake`
- **Penyimpanan data fisik:** `ducklake/data/`

Struktur schema:

| Schema | Tabel | Asal | Isi |
|---|---|---|---|
| `cnn` | `berita` | `cnn.duckdb` | Berita CNN apa adanya |
| `cnbc` | `berita` | `cnbc.duckdb` | Berita CNBC apa adanya |
| `pasar` | `ihsg` | `ihsg.duckdb` | Harga dan return harian IHSG |
| `analitik` | `berita_semua` | gabungan CNN + CNBC | Satu tabel berita dengan kolom `sumber` dan `tema` |

Tabel `analitik.berita_semua` adalah **tabel analitik (data mart)** yang dipakai dashboard. Kolom `tema` dibuat oleh `tema.py` (13 tema) dari kombinasi kategori berita dan kata kunci pada judul.

### 🔄 Proses ETL / ELT

1. **Extract:** scraper mengambil judul berita dari halaman indeks CNN dan CNBC serta harga IHSG dari Yahoo Finance (`yfinance`).
2. **Transform:**
   - standardisasi tanggal dan waktu terbit,
   - pembuatan kolom `sumber`,
   - klasifikasi tema berdasarkan kategori dan kata kunci judul,
   - perhitungan return harian IHSG,
   - penyelarasan berita akhir pekan ke hari bursa berikutnya,
   - pengecekan duplikasi dan hari kosong.
3. **Load:** tabel hasil olahan dimuat ke schema DuckLake menggunakan `CREATE TABLE AS SELECT`, lalu diverifikasi (jumlah baris per tabel).

## 🧪 Validasi Data

Skrip pemeriksaan dipisah dari pipeline utama:

- `cek_database.py` — total baris, hari tanpa data, jumlah per bulan dan kategori, berita terbaru, ringkasan IHSG.
- `cek_tema.py` — jumlah berita per tema dan contoh judul yang jatuh ke tema "Lainnya", untuk menyempurnakan kata kunci.

Hasil pemeriksaan terakhir: tidak ada hari kosong dan tidak ada duplikasi pada ketiga database.

## 📈 Analisis

- **Hubungan berita–IHSG:** korelasi jumlah berita dengan return harian, plus korelasi dengan jeda waktu (lag) pada hari bursa.
- **Tema:** proporsi tema, tema yang lebih ramai saat IHSG naik atau turun.
- **Kata pada judul:** kata terbanyak per sumber, kata khas saat IHSG naik atau turun (dengan *stopword* dan kata umum seperti "video" disaring).
- **Tren topik:** MBG, Danantara, tarif, dan topik lain dari waktu ke waktu.
- **Studi peristiwa:** pergerakan IHSG di sekitar peristiwa penting.
- **Tokoh:** frekuensi tokoh yang disebut dalam judul.
- **Rapor per 100 hari:** ringkasan IHSG dan pemberitaan per periode 100 hari pemerintahan.
- **CNN vs CNBC:** perbandingan fokus pemberitaan kedua media.

## 🖥️ Dashboard Streamlit

Dashboard membaca langsung dari DuckLake (mode `READ_ONLY`) dan memiliki 4 menu:

1. **Hubungan IHSG & Berita** — ringkasan dan insight, korelasi, topik dan peristiwa, kata pada judul.
2. **Berita** — ringkasan, CNN vs CNBC, tokoh, daftar berita.
3. **IHSG** — grafik harga, return harian, rapor per 100 hari.
4. **Tentang Data** — sumber, penjelasan tema, keterbatasan, ringkasan tabel DuckLake, cakupan bulanan.

## 📁 Struktur Repository

```
projek/
├── database.py              # membuat folder & tabel di 3 file DuckDB
├── scraping_cnn.py
├── scraping_cnbc.py
├── scraping_ihsg.py
├── tema.py                  # aturan klasifikasi 13 tema
├── cek_tema.py
├── cek_database.py
├── buat_ducklake.py         # menggabungkan 3 DuckDB → DuckLake
├── data_duckdb/
│   ├── cnn.duckdb
│   ├── cnbc.duckdb
│   └── ihsg.duckdb
├── ducklake/
│   ├── berita_ihsg.ducklake
│   └── data/
├── app.py                   # entry point Streamlit
├── db.py                    # query ke DuckLake
├── ui.py                    # tema, CSS, komponen tampilan
├── halaman/
│   ├── hubungan.py
│   ├── berita.py
│   ├── ihsg.py
│   └── tentang.py
├── .streamlit/config.toml
├── requirements.txt
└── README.md
```

## ⚙️ Cara Menjalankan

```bash
pip install -r requirements.txt

# 1. buat database
python database.py

# 2. scraping (masing-masing bisa dilanjutkan jika terhenti)
python scraping_ihsg.py
python scraping_cnn.py
python scraping_cnbc.py

# 3. pemeriksaan (opsional)
python cek_database.py
python cek_tema.py

# 4. bangun DuckLake
python buat_ducklake.py

# 5. jalankan dashboard
streamlit run app.py
```

## 🛠️ Tools dan Teknologi

- Python
- DuckDB — staging dan pemrosesan SQL
- DuckLake — integrasi data (catalog + penyimpanan)
- Pandas — pengolahan data
- Requests & BeautifulSoup — scraping berita
- yfinance — data IHSG
- Streamlit — dashboard
- Plotly — visualisasi interaktif

## ⚠️ Catatan Data

- Data berita hanya berupa **judul**, bukan isi artikel.
- CNN Indonesia membatasi halaman indeks hingga 1000 halaman per kanal, sehingga jumlah berita CNN lebih sedikit di periode awal. Perbandingan CNN vs CNBC paling adil pada periode yang lebih baru.
- Klasifikasi tema berbasis kata kunci, jadi tidak sempurna dan sebagian berita masuk tema Lainnya.
- Korelasi antara jumlah berita dan return IHSG sangat lemah. Hubungan ini tidak boleh dibaca sebagai sebab-akibat.
- IHSG hanya ada pada hari bursa, sedangkan berita terbit setiap hari.
- Hasil scraping bergantung pada struktur situs saat pengambilan data, yang bisa berubah sewaktu-waktu.

## 🚧 Status Project

- [x] Scraping CNN, CNBC, dan IHSG
- [x] DuckDB per sumber
- [x] Klasifikasi tema
- [x] Validasi data
- [x] DuckLake (4 schema)
- [x] Tabel analitik
- [x] Dashboard Streamlit (4 menu)
