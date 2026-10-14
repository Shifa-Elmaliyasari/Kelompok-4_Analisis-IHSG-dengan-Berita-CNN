# 📈 Analisis Hubungan Pemberitaan Media Online dengan Pergerakan Indeks Harga Saham Gabungan (IHSG)

**Integrasi Data CNN Indonesia, CNBC Indonesia, dan Indeks Harga Saham Gabungan Menggunakan DuckDB**

Project ini merupakan proyek Data Warehousing yang berfokus pada pengumpulan, penyimpanan, pengolahan, dan integrasi data pemberitaan media online dengan data historis Indeks Harga Saham Gabungan (IHSG).

Project ini dikembangkan untuk mendukung penelitian berjudul **“Analisis Hubungan Pemberitaan Media Online dengan Pergerakan Indeks Harga Saham Gabungan (IHSG)”**. Data pemberitaan diperoleh dari CNN Indonesia dan CNBC Indonesia, sedangkan data historis IHSG diperoleh dari Yahoo Finance.

**DuckDB** digunakan sebagai basis data analitik untuk menyimpan dan mengelola data dari berbagai sumber. Data yang terkumpul dapat dibersihkan, ditransformasikan, dan diintegrasikan berdasarkan tanggal untuk mendukung analisis hubungan statistik antara intensitas pemberitaan media online dan pergerakan pasar saham Indonesia.

Secara umum, project ini menggabungkan dua kelompok data utama:

- 📰 **Data Pemberitaan Media Online** — metadata artikel CNN Indonesia dan CNBC Indonesia, meliputi tanggal publikasi, kategori, topik, judul, dan tautan artikel.
- 📊 **Data Historis IHSG** — data pasar saham yang meliputi harga pembukaan, harga tertinggi, harga terendah, harga penutupan, volume, dan persentase perubahan jika tersedia.

Kedua kelompok data memiliki unit pencatatan dan karakteristik waktu yang berbeda. Oleh karena itu, diperlukan proses transformasi, agregasi, dan penyelarasan waktu sebelum keduanya digunakan dalam analisis bersama.

---

## 🔍 Tujuan Project

Project ini bertujuan membangun alur Data Warehousing yang mengintegrasikan pemberitaan media online dan data historis IHSG untuk mendukung analisis hubungan antara informasi yang dipublikasikan media dan pergerakan pasar saham Indonesia.

Tujuan tersebut dijabarkan menjadi beberapa fokus berikut:

- Mengumpulkan metadata pemberitaan dari CNN Indonesia dan CNBC Indonesia.
- Mengumpulkan data historis IHSG dari Yahoo Finance.
- Menyimpan data dari berbagai sumber dalam database DuckDB.
- Melakukan pembersihan dan transformasi agar struktur data konsisten.
- Mengagregasi jumlah berita berdasarkan tanggal publikasi.
- Mengintegrasikan data pemberitaan dengan data IHSG berdasarkan aturan pencocokan waktu.
- Mengeksplorasi pola intensitas pemberitaan dan perubahan IHSG.
- Menguji hubungan statistik antara jumlah berita dan return IHSG apabila data telah siap dianalisis.

### Pertanyaan Analisis

Beberapa pertanyaan yang ingin dieksplorasi dalam project ini meliputi:

1. Bagaimana perkembangan jumlah berita dari masing-masing media selama periode pengamatan?
2. Bagaimana pergerakan IHSG pada periode yang sama?
3. Apakah terdapat hubungan statistik antara jumlah pemberitaan harian dan return IHSG?
4. Apakah pola hubungan berbeda antara CNN Indonesia dan CNBC Indonesia?
5. Apakah terdapat pola hubungan ketika pemberitaan dibandingkan dengan pergerakan IHSG pada sesi perdagangan berikutnya?

Analisis ini bersifat eksploratif. Hubungan statistik yang ditemukan tidak secara otomatis menunjukkan bahwa pemberitaan menyebabkan perubahan IHSG.

---

## 🗂️ Dataset dan Sumber Data

Project ini menggunakan tiga sumber data utama, yaitu CNN Indonesia, CNBC Indonesia, dan Yahoo Finance.

### 1. 📰 CNN Indonesia — Data Pemberitaan Media Online

- **Sumber:** CNN Indonesia
- **Website:** https://www.cnnindonesia.com/
- **Script:** `scraping_berita.py`
- **Database:** `berita_ihsg.duckdb`
- **Tabel:** `berita`

Dataset ini berisi metadata pemberitaan CNN Indonesia yang dikumpulkan melalui proses *web scraping* dari berbagai kanal berita.

Variabel yang digunakan meliputi:

| Variabel | Deskripsi |
|---|---|
| `tanggal` | Tanggal publikasi berita |
| `published` | Informasi waktu publikasi berita |
| `kategori` | Kategori atau kanal berita |
| `topic` | Topik atau kanal yang digunakan dalam proses pengumpulan |
| `title` | Judul artikel berita |
| `link` | Tautan artikel untuk identifikasi dan penelusuran |

Kanal berita yang dikonfigurasi dalam script mencakup kategori seperti keuangan, bisnis, ekonomi, nasional, internasional, teknologi, politik, energi, serta kanal lainnya sesuai konfigurasi pengambilan data.

**Periode yang dikonfigurasi dalam script:** 20 Oktober 2024–20 September 2026.

Rentang tersebut merupakan periode yang dikonfigurasi dan perlu dibedakan dari periode data aktual yang berhasil dikumpulkan.

**Unit pencatatan data:**

```text
Satu baris
    ↓
Satu artikel berita
    ↓
Tanggal dan waktu publikasi
    ↓
Kategori, topik, judul, dan tautan
```

Setiap observasi merepresentasikan satu artikel berita. Tautan artikel dapat digunakan sebagai salah satu dasar identifikasi untuk membantu mendeteksi artikel yang tersimpan secara berulang.

Data ini dapat diagregasi berdasarkan tanggal untuk menghasilkan indikator jumlah berita harian.

### 2. 📰 CNBC Indonesia — Data Pemberitaan Media Online

- **Sumber:** CNBC Indonesia
- **Website:** https://www.cnbcindonesia.com/
- **Script:** `scraping_cnbc.py`
- **Database:** `berita_ihsg.duckdb`
- **Tabel:** `berita_cnbc`

Dataset ini berisi metadata pemberitaan CNBC Indonesia yang dikumpulkan melalui proses *web scraping*.

Variabel yang digunakan meliputi:

| Variabel | Deskripsi |
|---|---|
| `tanggal` | Tanggal publikasi berita |
| `published` | Informasi waktu publikasi berita |
| `kategori` | Kategori berita |
| `topic` | Topik atau kanal pengumpulan |
| `title` | Judul artikel berita |
| `link` | Tautan artikel untuk identifikasi dan penelusuran |

**Periode yang dikonfigurasi dalam script:** 20 Oktober 2024–20 September 2026.

Periode aktual tetap perlu diperiksa berdasarkan hasil pengambilan data.

**Unit pencatatan data:**

```text
Satu baris
    ↓
Satu artikel berita
    ↓
Tanggal dan waktu publikasi
    ↓
Kategori, topik, judul, dan tautan
```

Data CNBC Indonesia melengkapi data CNN Indonesia sehingga analisis dapat membandingkan intensitas pemberitaan dari dua sumber media online.

Penggunaan dua sumber memungkinkan jumlah berita dianalisis secara terpisah berdasarkan media maupun digabungkan menjadi indikator total pemberitaan.

### 3. 📊 Yahoo Finance — Data Historis IHSG

- **Sumber:** Yahoo Finance
- **Instrumen:** `^JKSE`
- **Website:** https://finance.yahoo.com/quote/%5EJKSE/
- **Script:** `scraping_ihsg.py`
- **Database:** `berita_ihsg.duckdb`
- **Tabel:** `ihsg`

Dataset ini berisi data historis Indeks Harga Saham Gabungan dengan kode indeks `^JKSE`. Pengambilan data menggunakan library `yfinance`, kemudian data disimpan ke DuckDB untuk pengolahan lebih lanjut.

Variabel yang digunakan meliputi:

| Variabel | Deskripsi |
|---|---|
| `tanggal` | Tanggal perdagangan |
| `open` | Nilai indeks saat pembukaan |
| `high` | Nilai indeks tertinggi |
| `low` | Nilai indeks terendah |
| `close` | Nilai indeks saat penutupan |
| `volume` | Informasi volume yang disediakan sumber |
| `return_pct` | Persentase perubahan harga penutupan terhadap sesi perdagangan sebelumnya, jika dihitung dan tersedia |

**Periode yang dikonfigurasi dalam script:** 20 Oktober 2024–20 September 2026.

Data IHSG mengikuti kalender perdagangan bursa. Oleh karena itu, tanggal observasi tidak selalu mencakup setiap hari kalender.

Persentase perubahan harga penutupan dapat dihitung menggunakan rumus berikut:

\[
Return_t=\frac{Close_t-Close_{t-1}}{Close_{t-1}}\times100\%
\]

Keterangan:

- \(Close_t\): nilai penutupan IHSG pada sesi perdagangan saat ini.
- \(Close_{t-1}\): nilai penutupan IHSG pada sesi perdagangan sebelumnya.
- \(Return_t\): persentase perubahan nilai penutupan IHSG.

**Unit pencatatan data:**

```text
Satu baris
    ↓
Satu sesi perdagangan
    ↓
Open, High, Low, Close
    ↓
Volume dan return, jika tersedia
```

Data IHSG digunakan untuk mengamati perubahan indeks dan membandingkannya dengan intensitas pemberitaan selama periode pengamatan.

---

## 🧩 Struktur Tabel Database

Data dari ketiga sumber disimpan dalam satu database DuckDB dengan tabel yang memiliki fungsi berbeda.

| Sumber | Nama Tabel | Unit Pencatatan | Informasi Utama |
|---|---|---|---|
| CNN Indonesia | `berita` | Artikel berita | Judul, tanggal, kategori, tautan |
| CNBC Indonesia | `berita_cnbc` | Artikel berita | Judul, tanggal, kategori, tautan |
| Yahoo Finance | `ihsg` | Sesi perdagangan | OHLC, volume, return |

Secara konseptual, struktur database dapat digambarkan sebagai berikut:

```text
berita_ihsg.duckdb
│
├── berita
│   └── Metadata pemberitaan CNN Indonesia
│
├── berita_cnbc
│   └── Metadata pemberitaan CNBC Indonesia
│
└── ihsg
    └── Data historis IHSG
```

Data berita memiliki unit pencatatan berupa artikel, sedangkan data IHSG memiliki unit pencatatan berupa sesi perdagangan. Perbedaan tersebut menjadi dasar perlunya proses agregasi dan penyelarasan tanggal sebelum analisis dilakukan.

---

## 🏗️ Tahapan Project

Project dirancang mengikuti alur pengumpulan data, penyimpanan, transformasi, integrasi, dan analisis.

```text
                     DATA SOURCES
                          │
              ┌───────────┼───────────┐
              │           │           │
              ▼           ▼           ▼
        CNN Indonesia  CNBC Indonesia  Yahoo Finance
              │           │           │
              ▼           ▼           ▼
          Scraping     Scraping     Pengambilan
          Berita CNN   Berita CNBC  Data Historis
              │           │           │
              └───────────┼───────────┘
                          │
                          ▼
                    DUCKDB DATABASE
                   berita_ihsg.duckdb
                          │
              ┌───────────┼───────────┐
              │           │           │
              ▼           ▼           ▼
           berita    berita_cnbc     ihsg
              │           │           │
              └───────────┼───────────┘
                          │
                          ▼
                  DATA CLEANING & ETL
                          │
                          ▼
                AGREGASI BERITA HARIAN
                          │
                          ▼
                 INTEGRASI BERDASARKAN
                       ATURAN WAKTU
                          │
                          ▼
                    TABEL ANALITIK
                          │
                          ▼
                     ANALISIS DATA
                          │
                          ▼
                   VISUALISASI HASIL
```

Arsitektur tersebut menggambarkan alur yang dituju. Tahapan integrasi, pembentukan tabel analitik, analisis, dan visualisasi perlu disesuaikan dengan implementasi aktual.

---

## 🗃️ DuckDB sebagai Basis Data Analitik

DuckDB digunakan sebagai basis data analitik untuk menyimpan dan mengolah data pemberitaan serta data historis IHSG.

**Nama database utama:**

```text
berita_ihsg.duckdb
```

DuckDB mendukung pemrosesan data menggunakan SQL dan dapat diintegrasikan dengan Python serta Pandas. Dalam project ini, DuckDB berfungsi sebagai pusat penyimpanan data yang memungkinkan proses query, agregasi, transformasi, dan pengolahan data dilakukan dalam satu lingkungan database.

Contoh alur penyimpanan:

```text
Data CNN Indonesia ──┐
                     │
Data CNBC Indonesia ─┼──> DuckDB
                     │
Data IHSG ───────────┘
```

Penyimpanan dalam satu database mempermudah pengelolaan data dari berbagai sumber dan memungkinkan setiap tabel diolah secara terstruktur sebelum dilakukan integrasi untuk analisis.

### 🦆 Jumlah Tabel yang Digunakan

Dalam struktur database yang dirancang untuk project ini, terdapat **3 tabel utama** yang merepresentasikan tiga sumber data berbeda.

| No. | Nama Tabel | Sumber Data | Fungsi |
|---:|---|---|---|
| 1 | `berita` | CNN Indonesia | Menyimpan metadata artikel berita CNN Indonesia |
| 2 | `berita_cnbc` | CNBC Indonesia | Menyimpan metadata artikel berita CNBC Indonesia |
| 3 | `ihsg` | Yahoo Finance | Menyimpan data historis pergerakan IHSG |

Dengan demikian, database `berita_ihsg.duckdb` dirancang menggunakan **3 tabel utama**. Setiap tabel memiliki struktur dan unit pencatatan yang disesuaikan dengan karakteristik sumber datanya.

Jumlah tersebut mengacu pada struktur yang dijelaskan dalam dokumentasi ini. Untuk memastikan jumlah tabel yang benar-benar telah dibuat, struktur database dapat diperiksa setelah script dijalankan.

---

## 🔄 Proses ETL

ETL (*Extract, Transform, Load*) merupakan proses pengumpulan, transformasi, dan pemuatan data ke dalam database analitik.

### 1. Extract

Tahap ini dilakukan melalui tiga script utama:

- `scraping_berita.py` untuk mengambil metadata berita CNN Indonesia.
- `scraping_cnbc.py` untuk mengambil metadata berita CNBC Indonesia.
- `scraping_ihsg.py` untuk mengambil data historis IHSG dari Yahoo Finance.

Data berita dikumpulkan dari kanal media yang dikonfigurasi dalam script. Sementara itu, data IHSG diambil menggunakan kode instrumen `^JKSE`.

Rentang tanggal dan hasil aktual pengambilan data perlu diperiksa setelah setiap script dijalankan.

### 2. Transform

Tahap transformasi bertujuan menyiapkan data agar konsisten dan dapat digunakan dalam analisis.

Proses yang diperlukan meliputi:

- Memastikan kolom tanggal memiliki tipe data yang sesuai.
- Memeriksa kelengkapan tanggal publikasi dan judul berita.
- Memeriksa duplikasi artikel berdasarkan tautan atau identitas lain yang tersedia.
- Memeriksa duplikasi tanggal perdagangan.
- Memvalidasi nilai numerik pada kolom OHLC dan volume.
- Menyeragamkan format waktu dan zona waktu jika diperlukan.
- Mengagregasi jumlah berita berdasarkan tanggal.
- Menghitung perubahan dan return IHSG berdasarkan urutan sesi perdagangan.
- Menentukan aturan pencocokan tanggal berita dengan tanggal perdagangan.
- Memeriksa hasil integrasi agar tidak terjadi penggandaan baris yang tidak diinginkan.

Contoh data artikel sebelum agregasi:

```text
Tanggal     | Sumber | Judul
2025-01-02  | CNN    | Berita A
2025-01-02  | CNN    | Berita B
2025-01-02  | CNBC   | Berita C
2025-01-03  | CNN    | Berita D
```

Setelah agregasi jumlah berita:

```text
Tanggal     | Berita CNN | Berita CNBC
2025-01-02  | 2          | 1
2025-01-03  | 1          | 0
```

Angka tersebut hanya ilustrasi untuk menjelaskan proses agregasi, bukan hasil aktual pengumpulan data.

### 3. Load

Data yang telah dikumpulkan disimpan dalam database DuckDB sesuai tabel sumbernya.

```text
CNN Indonesia  → berita
CNBC Indonesia → berita_cnbc
Yahoo Finance  → ihsg
```

Setelah proses transformasi dan integrasi dilakukan, hasilnya dapat disimpan sebagai tabel analitik tambahan. Tabel tersebut akan mempermudah analisis statistik dan pembuatan visualisasi.

---

## 🔗 Integrasi dan Agregasi Data

Integrasi dilakukan untuk menghubungkan jumlah pemberitaan dengan indikator pergerakan IHSG berdasarkan waktu pengamatan.

Data berita perlu diagregasi karena satu tanggal dapat memiliki banyak artikel. Sebaliknya, data IHSG umumnya memiliki satu observasi untuk setiap sesi perdagangan.

Contoh rancangan tabel hasil integrasi:

| Tanggal | Berita CNN | Berita CNBC | Total Berita | Close IHSG | Return IHSG |
|---|---:|---:|---:|---:|---:|
| 2025-01-02 | ... | ... | ... | ... | ... |
| 2025-01-03 | ... | ... | ... | ... | ... |
| 2025-01-06 | ... | ... | ... | ... | ... |

Tabel tersebut merupakan contoh struktur data yang direncanakan. Nilai aktual diisi setelah proses pengolahan dijalankan.

### Aturan Penyelarasan Tanggal

Penyelarasan waktu menjadi bagian penting karena:

- Berita dapat diterbitkan pada akhir pekan atau hari libur bursa.
- Berita dapat terbit sebelum, selama, atau setelah jam perdagangan.
- Tanggal publikasi dan tanggal perdagangan tidak selalu identik.
- Penggunaan tanggal yang sama tidak selalu sesuai untuk menguji kemungkinan hubungan waktu.

Karena itu, analisis dapat membedakan hubungan pada tanggal yang sama dan hubungan terhadap sesi perdagangan berikutnya.

Tanggal yang tidak memiliki observasi berita juga perlu ditangani secara hati-hati. Nilai nol hanya digunakan jika dapat dipastikan bahwa tidak ada berita yang tercatat untuk tanggal tersebut, bukan karena proses pengambilan data gagal.

---

## 🔍 Ruang Lingkup Analisis

### 1. Analisis Perkembangan Pemberitaan

Analisis ini digunakan untuk mengamati perkembangan jumlah artikel yang dikumpulkan dari kedua media.

Indikator yang dapat dihitung:

- Jumlah berita harian.
- Jumlah berita bulanan.
- Perbandingan jumlah berita CNN Indonesia dan CNBC Indonesia.
- Distribusi berita berdasarkan kategori, jika datanya memadai.
- Periode dengan intensitas pemberitaan tertinggi dan terendah.

Hasil analisis dapat membantu menggambarkan pola aktivitas pemberitaan selama periode pengamatan.

### 2. Analisis Pergerakan IHSG

Analisis ini digunakan untuk memahami karakteristik pergerakan indeks selama periode penelitian.

Indikator yang dapat dihitung:

- Nilai penutupan IHSG.
- Perubahan poin harian.
- Persentase return harian.
- Jumlah sesi perdagangan dengan return positif dan negatif.
- Periode dengan perubahan indeks terbesar.
- Distribusi return selama periode pengamatan.

Analisis dilakukan berdasarkan urutan sesi perdagangan, bukan dengan menganggap setiap hari kalender sebagai hari perdagangan.

### 3. Analisis Hubungan Pemberitaan dengan IHSG

Analisis utama berfokus pada pengujian hubungan statistik antara intensitas pemberitaan media online dan pergerakan IHSG.

Variabel yang dapat digunakan:

| Variabel | Fungsi Analisis |
|---|---|
| Jumlah berita CNN per hari | Indikator intensitas pemberitaan CNN |
| Jumlah berita CNBC per hari | Indikator intensitas pemberitaan CNBC |
| Total berita harian | Ringkasan intensitas pemberitaan dua media |
| `close` IHSG | Nilai penutupan indeks |
| `return_pct` IHSG | Ukuran perubahan persentase indeks |

Metode yang dapat dipertimbangkan:

- **Korelasi Pearson** untuk mengevaluasi hubungan linear apabila persyaratan penggunaannya memadai.
- **Korelasi Spearman** untuk mengevaluasi hubungan monoton berdasarkan peringkat.
- **Analisis lag** untuk mengeksplorasi hubungan intensitas pemberitaan dengan return pada sesi perdagangan berikutnya.

Pemilihan metode perlu mempertimbangkan distribusi data, pencilan, karakteristik deret waktu, dan kesesuaian tanggal pengamatan.

### 4. Perbandingan Antar-Sumber Media

Analisis dapat dilakukan secara terpisah untuk CNN Indonesia dan CNBC Indonesia.

Tujuannya adalah mengevaluasi apakah pola hubungan statistik dengan pergerakan IHSG berbeda berdasarkan sumber pemberitaan.

Perbandingan ini tidak otomatis menunjukkan bahwa salah satu media lebih berpengaruh. Jumlah artikel, karakteristik topik, dan waktu publikasi kedua sumber dapat berbeda.

### 5. Analisis Berdasarkan Waktu Publikasi

Jika waktu publikasi tersedia dan cukup lengkap, analisis dapat diperluas dengan mempertimbangkan waktu berita diterbitkan.

Contoh pengelompokan:

```text
Berita sebelum perdagangan
          │
          ▼
Return pada sesi perdagangan terkait

Berita selama perdagangan
          │
          ▼
Pergerakan indeks selama periode terkait

Berita setelah perdagangan
          │
          ▼
Return pada sesi perdagangan berikutnya
```

Pengelompokan tersebut perlu disesuaikan dengan kelengkapan *timestamp*, zona waktu, serta definisi jam perdagangan yang digunakan.

### 6. Interpretasi Hasil

Hasil analisis digunakan untuk memahami pola yang muncul dalam data, bukan untuk menyimpulkan bahwa jumlah berita merupakan penyebab tunggal perubahan IHSG.

Interpretasi juga perlu mempertimbangkan faktor lain, seperti kondisi ekonomi, kebijakan pemerintah, perkembangan pasar global, suku bunga, dan sentimen investor.

---

## 🗂️ Struktur Repository

Struktur repository saat ini berfokus pada script pengambilan data.

```text
Kelompok-4_Analisis-IHSG-dengan-Berita-CNN/
│
├── README.md
├── scraping_berita.py
├── scraping_cnbc.py
└── scraping_ihsg.py
```

Database `berita_ihsg.duckdb` dibuat atau diperbarui oleh script sesuai implementasinya dan dapat tersimpan pada direktori kerja yang digunakan.

---

## 🧪 Validasi dan Kualitas Data

Validasi data diperlukan untuk memastikan hasil pengolahan dapat digunakan dalam analisis secara konsisten.

Pemeriksaan yang perlu dilakukan meliputi:

- **Kelengkapan:** memeriksa ketersediaan tanggal, judul berita, tautan, dan indikator IHSG.
- **Duplikasi:** memeriksa artikel berulang dan tanggal perdagangan yang tercatat lebih dari satu kali.
- **Konsistensi waktu:** menyeragamkan format tanggal dan zona waktu publikasi.
- **Validasi numerik:** memeriksa nilai Open, High, Low, Close, volume, dan return.
- **Validasi integrasi:** memastikan pencocokan tanggal tidak menggandakan observasi secara tidak sengaja.
- **Pemeriksaan rentang:** membandingkan tanggal aktual hasil pengambilan data dengan periode yang dikonfigurasi.
- **Dokumentasi perubahan:** mencatat jumlah observasi sebelum dan sesudah pembersihan serta alasan penghapusan data jika dilakukan.

Hasil pemeriksaan ini menjadi dasar untuk menentukan data yang layak digunakan dalam analisis selanjutnya.

---

## ⚠️ Batasan Project

Beberapa hal perlu diperhatikan ketika menafsirkan hasil project:

1. Data pemberitaan hanya berasal dari CNN Indonesia dan CNBC Indonesia, sehingga belum mewakili keseluruhan media online di Indonesia.
2. Jumlah berita menggambarkan intensitas pemberitaan, bukan sentimen berita secara langsung.
3. Judul berita saja belum cukup untuk menentukan sentimen positif, negatif, atau netral tanpa metode analisis tambahan.
4. Artikel dari dua media dapat membahas peristiwa yang sama.
5. Tanggal publikasi berita tidak selalu sama dengan tanggal perdagangan IHSG.
6. Hari libur bursa tidak boleh otomatis dianggap sebagai hari dengan data IHSG yang hilang.
7. Nilai kosong tidak boleh otomatis diubah menjadi nol tanpa mengetahui penyebabnya.
8. Volume yang kosong atau nol perlu diperiksa sesuai karakteristik data dari sumber.
9. Korelasi tidak membuktikan hubungan sebab-akibat.
10. Pergerakan IHSG juga dipengaruhi faktor ekonomi, politik, global, dan kondisi pasar lainnya.
11. Kesimpulan analisis dibatasi oleh sumber, periode, dan kualitas data yang berhasil dikumpulkan.

---

## 💡 Kesimpulan Project

Project **Analisis Hubungan Pemberitaan Media Online dengan Pergerakan Indeks Harga Saham Gabungan (IHSG)** memanfaatkan DuckDB untuk membangun fondasi penyimpanan dan pengolahan data yang terstruktur dari dua sumber pemberitaan media online dan data historis IHSG.

Database dirancang dengan tiga tabel utama, yaitu `berita`, `berita_cnbc`, dan `ihsg`. Ketiga tabel tersebut menyimpan data sesuai karakteristik masing-masing sumber sebelum dilakukan proses pembersihan, agregasi, dan integrasi berdasarkan waktu.

Melalui alur Data Warehousing tersebut, project ini diharapkan dapat mendukung eksplorasi hubungan statistik antara intensitas pemberitaan media online dan pergerakan IHSG secara terukur, dengan tetap mempertimbangkan perbedaan waktu publikasi, karakteristik pasar saham, dan keterbatasan sumber data.

**Repository:** [Kelompok-4_Analisis-IHSG-dengan-Berita-CNN](https://github.com/Shifa-Elmaliyasari/Kelompok-4_Analisis-IHSG-dengan-Berita-CNN)

**PPT:** https://canva.link/pxtttml94lpa2p3

**Keywords:** Data Warehousing, DuckDB, Online News, IHSG, Data Integration, SQL, Stock Market Analytics
