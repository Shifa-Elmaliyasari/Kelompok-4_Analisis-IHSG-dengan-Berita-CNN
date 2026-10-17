# tema.py
# Aturan kolom "tema". Tidak membuka database sendiri:
# dipakai oleh cek_tema.py dan buat_ducklake.py lewat sql_berita_semua().

# ------------------------------------------------------------
# DAFTAR KATA KUNCI (urutan = prioritas, yang cocok lebih dulu menang)
#   awalan : cocok di awal kata, boleh diikuti imbuhan (banjir -> banjirnya)
#   persis : harus kata utuh (as, ai, gol, mk)
# Cukup edit daftar ini lalu jalankan ulang cek_tema.py / buat_ducklake.py.
# Huruf kecil, tanpa tanda kutip di dalam kata.
# ------------------------------------------------------------
TEMA_KATA = [
    ("Bencana & Lingkungan",
     ["banjir", "gempa", "longsor", "tsunami", "erupsi", "bencana", "kebakaran", "karhutla",
      "kekeringan", "badai", "puting beliung", "cuaca", "bmkg", "evakuasi", "iklim", "polusi",
      "sampah", "lingkungan", "emisi", "hutan", "abrasi", "siklon", "basarnas", "gunung",
      "pengungsi", "kemarau", "hujan"],
     ["el nino", "la nina"]),
    ("Kesehatan",
     ["kesehatan", "penyakit", "rumah sakit", "obat", "vaksin", "virus", "kanker", "diabetes",
      "dokter", "covid", "wabah", "gizi", "stunting", "keracunan", "medis", "pasien", "jantung",
      "kolesterol"],
     ["bpjs", "rs", "fda"]),
    ("Hukum & Kriminal",
     ["korupsi", "kpk", "kejagung", "kejaksaan", "jaksa", "polisi", "polri", "tersangka",
      "tahanan", "vonis", "hakim", "sidang", "pengadilan", "mahkamah", "narkoba", "pembunuhan",
      "penipuan", "pencurian", "ditangkap", "penangkapan", "pidana", "hukum", "terdakwa",
      "bareskrim", "pencucian uang", "suap", "gratifikasi", "dugaan", "penjara"],
     ["mk", "ott"]),
    ("Ekonomi & Pasar",
     ["ihsg", "saham", "rupiah", "inflasi", "suku bunga", "bi rate", "apbn", "pajak", "ekspor",
      "impor", "emas", "bbm", "minyak", "obligasi", "bursa", "investasi", "investor", "ekonomi",
      "bank", "kredit", "utang", "subsidi", "tarif", "bumn", "laba", "dividen", "kripto",
      "bitcoin", "properti", "umkm", "pertamina", "harga", "pasar", "industri", "keuangan",
      "anggaran", "ojk", "danantara", "gaji", "upah", "phk", "bisnis", "perusahaan", "pabrik",
      "tambang", "batu bara", "nikel", "sawit", "listrik", "energi", "pangan", "beras", "cuan",
      "rekomendasi saham", "dolar", "kurs", "resesi", "devisa", "fiskal", "moneter",
      "pengusaha", "apindo", "logistik", "bea cukai", "cukai", "sritex", "kopdes", "koperasi",
      "peternakan", "ayam", "hilirisasi", "belanja", "diskon", "promo", "ritel", "deflasi", "plts",
      "pln", "fortune", "kelas menengah", "daya saing", "daya beli", "lapangan kerja",
      "pengangguran", "kemiskinan", "rokok", "produksi", "produk", "konsumen", "penjualan",
      "proyek", "infrastruktur", "swasta", "dirut", "direktur utama", "komisaris", "meikarta",
      "apartemen", "perumahan", "pengembang", "smelter", "ekspansi", "akuisisi", "merger",
      "airlangga", "zulhas", "amran", "mentan", "menkeu", "mendag", "menperin", "bahlil",
      "sri mulyani", "purbaya", "luhut", "menteri keuangan", "menteri perdagangan"],
     ["thr", "pdb", "ipo", "the fed", "fed", "bi", "mal", "ceo", "ihk"]),
    ("Olahraga",
     ["timnas", "liga", "pssi", "piala", "motogp", "formula", "bulu tangkis", "sepak bola",
      "atlet", "olimpiade", "juara", "pertandingan", "turnamen", "basket", "voli", "tenis",
      "persib", "persija", "ronaldo", "messi", "klasemen"],
     ["gol", "f1", "ufc"]),
    ("Internasional",
     ["amerika", "china", "tiongkok", "rusia", "ukraina", "israel", "gaza", "iran", "trump",
      "eropa", "jepang", "korea", "palestina", "pbb", "venezuela", "india", "inggris", "jerman",
      "prancis", "arab saudi", "timur tengah", "taiwan", "australia", "singapura", "malaysia",
      "thailand", "myanmar", "afrika", "turki", "kanada", "brasil", "meksiko", "vietnam"],
     ["as", "nato", "uni eropa"]),
    ("Politik & Pemerintahan",
     ["presiden", "prabowo", "gibran", "jokowi", "istana", "dpr", "dpd", "mpr", "menteri",
      "wamen", "partai", "pilkada", "pemilu", "gubernur", "bupati", "walikota", "wali kota",
      "pemerintah", "kabinet", "reshuffle", "undang-undang", "demo", "unjuk rasa", "kemendagri",
      "kementerian", "mbg", "megawati", "anies", "politik", "koalisi", "relawan"],
     ["ruu", "tni", "mbg", "pns", "asn", "ikn"]),
    ("Pendidikan",
     ["sekolah", "siswa", "mahasiswa", "universitas", "kampus", "kuliah", "guru", "kurikulum",
      "beasiswa", "ujian", "pendidikan", "kemendikbud", "jurusan", "dosen", "wisuda", "pelajar"],
     ["snbp", "snbt", "ui", "ugm", "itb"]),
    ("Teknologi",
     ["teknologi", "kecerdasan buatan", "chatgpt", "openai", "google", "apple", "iphone",
      "samsung", "android", "aplikasi", "startup", "internet", "siber", "hacker", "peretas",
      "data center", "semikonduktor", "nvidia", "tiktok", "robot", "satelit", "gadget",
      "digital", "software", "smartphone", "starlink", "microsoft", "elon musk", "gemini",
      "deepfake", "teknologi", "inovasi"],
     ["ai", "chip", "meta", "ponsel", "hp"]),
    ("Transportasi & Otomotif",
     ["mobil", "motor", "kereta", "pesawat", "bandara", "mudik", "kendaraan", "otomotif",
      "penerbangan", "pelabuhan", "transjakarta", "mrt", "lrt", "maskapai", "garuda"],
     ["ev", "tol", "bus"]),
    ("Agama",
     ["imsak", "puasa", "ramadan", "zakat", "haji", "umrah", "sholat", "salat", "doa", "masjid",
      "natal", "lebaran", "idul", "ustaz", "syariah", "khutbah", "paus", "gereja"],
     []),
    ("Hiburan & Gaya Hidup",
     ["artis", "film", "drama", "konser", "lagu", "musik", "selebriti", "seleb", "kuliner",
      "resep", "wisata", "liburan", "fashion", "travel", "gaya hidup", "kecantikan", "skincare",
      "kencan", "pernikahan", "cerai", "viral", "netizen", "influencer", "zodiak", "ramalan",
      "restoran", "kafe", "makanan", "minuman"],
     ["k-pop", "kpop"]),
]


def regex_tema(awalan, persis):
    bagian = []
    if awalan:
        bagian.append(r"\b(?:" + "|".join(awalan) + r")\w*")
    if persis:
        bagian.append(r"\b(?:" + "|".join(persis) + r")\b")
    return "|".join(bagian)


def kasus_judul(bawaan):
    """CASE SQL: tema dari kata kunci judul, kalau tidak ada yang cocok pakai `bawaan`."""
    baris = ["CASE"]
    for nama, awalan, persis in TEMA_KATA:
        baris.append(f"  WHEN regexp_matches(lower(title), '{regex_tema(awalan, persis)}') "
                     f"THEN '{nama}'")
    baris.append(f"  ELSE '{bawaan}' END")
    return "\n".join(baris)


def sql_berita_semua(tabel_cnn="cnn_db.berita", tabel_cnbc="cnbc_db.berita"):
    """SELECT gabungan CNN + CNBC dengan kolom tema.
    Kolom: sumber, tanggal, published, kategori, tema, title, link."""
    return f"""
WITH gabung AS (
    SELECT 'CNN' AS sumber, tanggal, published, kategori, title, link FROM {tabel_cnn}
    UNION ALL
    SELECT 'CNBC', tanggal, published, kategori, title, link FROM {tabel_cnbc}
)
SELECT sumber, tanggal, published, kategori,
CASE
  WHEN sumber = 'CNN' AND kategori = 'ekonomi'       THEN 'Ekonomi & Pasar'
  WHEN sumber = 'CNN' AND kategori = 'internasional' THEN 'Internasional'
  WHEN sumber = 'CNN' AND kategori = 'olahraga'      THEN 'Olahraga'
  WHEN sumber = 'CNN' AND kategori = 'teknologi'     THEN 'Teknologi'
  WHEN sumber = 'CNN' AND kategori = 'otomotif'      THEN 'Transportasi & Otomotif'
  WHEN sumber = 'CNN' AND kategori = 'hiburan'       THEN 'Hiburan & Gaya Hidup'
  WHEN sumber = 'CNN' AND kategori = 'gaya-hidup'    THEN
{kasus_judul('Hiburan & Gaya Hidup')}
  WHEN sumber = 'CNN' AND kategori = 'nasional'      THEN
{kasus_judul('Politik & Pemerintahan')}
  WHEN sumber = 'CNN'                                THEN 'Lainnya'
  WHEN kategori IN ('market','research','mymoney','entrepreneur','cuap-cuap-cuan','company-update')
                                                     THEN 'Ekonomi & Pasar'
  WHEN kategori = 'tech'                             THEN 'Teknologi'
  WHEN kategori = 'syariah'                          THEN 'Agama'
  WHEN kategori = 'lifestyle'                        THEN
{kasus_judul('Hiburan & Gaya Hidup')}
  ELSE
{kasus_judul('Lainnya')}
END AS tema,
title, link
FROM gabung
"""