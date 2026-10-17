import os
import re
from datetime import date, timedelta

import duckdb
import numpy as np
import pandas as pd
import streamlit as st

# ==============================
# KONFIGURASI
# ==============================

BASE = os.path.dirname(os.path.abspath(__file__))
LAKE_FOLDER = os.path.join(BASE, "ducklake")
LAKE_CATALOG = os.path.join(LAKE_FOLDER, "berita_ihsg.ducklake")   # katalog DuckLake
LAKE_DATA = os.path.join(LAKE_FOLDER, "data")                      # file parquet

T_BERITA = "lake.analitik.berita_semua"   # gabungan CNN + CNBC (ada kolom sumber dan tema)
T_IHSG = "lake.pasar.ihsg"

START = date(2024, 10, 20)         # hari pelantikan Presiden Prabowo
END = date(2026, 9, 20)
BATAS_CAKUPAN = date(2025, 4, 1)   # sebelum tanggal ini cakupan berita CNN lebih tipis

SUMBER = ["CNN", "CNBC"]
TEMA_DEFAULT = "Ekonomi & Pasar"

PRESET = {
    "Semua": None,
    "1 bulan terakhir": 30,
    "3 bulan terakhir": 91,
    "6 bulan terakhir": 182,
    "1 tahun terakhir": 365,
}

# ------------------------------------------------------------
# KATA YANG TIDAK DIHITUNG pada analisis kata (stopword).
# Tambahkan kata baru di sini kalau masih ada kata "sampah" yang muncul.
# ------------------------------------------------------------
STOPWORD = set("""
yang dan di ke dari untuk dengan pada ini itu akan dalam atau juga tak tidak jadi ada oleh sebagai
bagi usai kini hari saat bisa agar telah masih karena lebih hingga per ungkap soal jelang sebut kata
ketika sudah bakal hanya segera para sebuah mereka kami kita dia nya bukan belum sempat setelah
antara sampai tapi namun serta lalu sejak sedang pernah harus mau bila jika kalau seperti yaitu
adalah ialah dua tiga empat lima satu tak
video foto fotos infografis galeri live update breaking terkini terbaru berita simak cek ternyata
catat langsung lihat baca klik wib begini begitu ramai viral hot
tegas buka bicara tanggapi respons respon minta beri beber ungkapkan jelaskan klaim akui
rp tahun baru orang kali bakal capai hingga
""".split())

# ------------------------------------------------------------
# TOPIK KEBIJAKAN untuk grafik tren. Kata diawali pencocokan awal kata
# (mbg cocok dengan "mbg" dan "mbgnya"); awali dengan "=" untuk kata utuh.
# ------------------------------------------------------------
TOPIK = {
    "MBG (makan bergizi)": ["mbg", "makan bergizi"],
    "Danantara": ["danantara"],
    "Efisiensi anggaran": ["efisiensi anggaran", "efisiensi"],
    "Tarif Trump": ["tarif trump", "tarif resiprokal", "tarif timbal balik"],
    "Koperasi Merah Putih": ["kopde", "koperasi desa", "=kdmp", "koperasi merah putih"],
    "PHK": ["=phk", "pemutusan hubungan kerja"],
    "Reshuffle": ["reshuffle", "perombakan kabinet"],
    "Demo / unjuk rasa": ["=demo", "unjuk rasa"],
    "Korupsi": ["korupsi"],
}

TOKOH = {
    "Prabowo": ["prabowo"],
    "Gibran": ["gibran"],
    "Jokowi": ["jokowi"],
    "Megawati": ["megawati"],
    "Sri Mulyani": ["sri mulyani"],
    "Purbaya": ["purbaya"],
    "Trump": ["trump"],
}

# ------------------------------------------------------------
# PERISTIWA PENTING (perkiraan, mohon dicek ulang dengan berita di data kamu).
# Format: (tanggal, nama singkat). Boleh diubah/ditambah.
# ------------------------------------------------------------
PERISTIWA = [
    (date(2024, 10, 20), "Pelantikan Presiden"),
    (date(2025, 1, 6), "Program MBG mulai"),
    (date(2025, 2, 24), "Peluncuran Danantara"),
    (date(2025, 3, 18), "Penghentian sementara perdagangan IHSG"),
    (date(2025, 4, 2), "Pengumuman tarif Trump"),
    (date(2025, 4, 8), "Bursa buka setelah libur Lebaran"),
    (date(2025, 8, 28), "Gelombang demonstrasi"),
    (date(2025, 9, 8), "Reshuffle kabinet"),
]


# ==============================
# AKSES DUCKLAKE (hanya baca)
# ==============================

def _p(path):
    return path.replace("\\", "/")


@st.cache_resource(show_spinner=False)
def _koneksi():
    """Satu koneksi bersama yang meng-ATTACH DuckLake (dibuat sekali)."""
    con = duckdb.connect()
    con.execute("INSTALL ducklake")
    con.execute("LOAD ducklake")
    sql = (f"ATTACH 'ducklake:{_p(LAKE_CATALOG)}' AS lake "
           f"(DATA_PATH '{_p(LAKE_DATA)}/', OVERRIDE_DATA_PATH true")
    try:
        con.execute(sql + ", READ_ONLY)")
    except Exception:
        con.execute(sql + ")")
    return con


def _query(sql, params=None, daftar=None):
    """Jalankan SQL. `daftar` = {nama: DataFrame} yang dipakai sebagai tabel sementara."""
    if not os.path.exists(LAKE_CATALOG):
        st.error("DuckLake belum ditemukan. Jalankan buat_ducklake.py terlebih dahulu "
                 "(harus ada folder ducklake/ di samping app.py).")
        st.stop()
    cur = _koneksi().cursor()
    try:
        for nama, df in (daftar or {}).items():
            cur.register(nama, df)
        return cur.execute(sql, params or []).df()
    finally:
        cur.close()


def _ke_waktu(df, kolom="tanggal"):
    df[kolom] = pd.to_datetime(df[kolom]).astype("datetime64[ns]")
    return df


@st.cache_data(show_spinner=False)
def muat_ihsg():
    df = _query(f"SELECT tanggal, open, high, low, close, volume, return_pct "
                f"FROM {T_IHSG} ORDER BY tanggal")
    return _ke_waktu(df)


@st.cache_data(show_spinner=False)
def daftar_tema():
    df = _query(f"SELECT tema, COUNT(*) AS n FROM {T_BERITA} GROUP BY 1 ORDER BY n DESC")
    return df["tema"].tolist()


@st.cache_data(show_spinner=False)
def cakupan_bulanan():
    return _query(f"""
        SELECT strftime(tanggal, '%Y-%m') AS bulan, sumber, tema, COUNT(*) AS jumlah
        FROM {T_BERITA} GROUP BY 1, 2, 3 ORDER BY 1
    """)


@st.cache_data(show_spinner=False)
def ringkasan_tabel():
    return _query("""
        SELECT 'cnn.berita' AS tabel, COUNT(*) AS baris, MIN(tanggal) AS awal, MAX(tanggal) AS akhir
          FROM lake.cnn.berita
        UNION ALL SELECT 'cnbc.berita', COUNT(*), MIN(tanggal), MAX(tanggal) FROM lake.cnbc.berita
        UNION ALL SELECT 'pasar.ihsg', COUNT(*), MIN(tanggal), MAX(tanggal) FROM lake.pasar.ihsg
        UNION ALL SELECT 'analitik.berita_semua', COUNT(*), MIN(tanggal), MAX(tanggal)
          FROM lake.analitik.berita_semua
    """)


def _where_berita(f):
    kond = ["tanggal BETWEEN ? AND ?"]
    params = [f["awal"], f["akhir"]]
    if f["sumber"]:
        kond.append("sumber IN (" + ",".join("?" * len(f["sumber"])) + ")")
        params += list(f["sumber"])
    if f["tema"]:
        kond.append("tema IN (" + ",".join("?" * len(f["tema"])) + ")")
        params += list(f["tema"])
    kata = [k.strip() for k in f["kata"].split(",") if k.strip()]
    if kata:
        op = " OR " if f["mode"] == "Salah satu kata" else " AND "
        kond.append("(" + op.join(["title ILIKE ?"] * len(kata)) + ")")
        params += [f"%{k}%" for k in kata]
    return " AND ".join(kond), params


def semua_tema(f):
    """Salinan filter tanpa batasan tema dan kata (untuk grafik proporsi/perbandingan)."""
    return {**f, "tema": (), "kata": ""}


@st.cache_data(show_spinner=False)
def berita_harian(f):
    where, params = _where_berita(f)
    df = _query(f"SELECT tanggal, sumber, tema, COUNT(*) AS jumlah FROM {T_BERITA} "
                f"WHERE {where} GROUP BY 1, 2, 3 ORDER BY 1", params)
    return _ke_waktu(df)


@st.cache_data(show_spinner=False)
def berita_per_jam(f):
    where, params = _where_berita(f)
    return _query(f"SELECT hour(published) AS jam, sumber, COUNT(*) AS jumlah FROM {T_BERITA} "
                  f"WHERE {where} GROUP BY 1, 2 ORDER BY 1", params)


@st.cache_data(show_spinner=False)
def cari_berita(f, urut, limit):
    where, params = _where_berita(f)
    arah = "DESC" if urut == "Terbaru" else "ASC"
    return _query(f"SELECT published, sumber, tema, kategori, title, link FROM {T_BERITA} "
                  f"WHERE {where} ORDER BY published {arah} LIMIT {int(limit)}", params)


# ==============================
# ANALISIS KATA (dihitung di DuckDB, bukan di Python)
# ==============================

def bersihkan_kata(df, kolom="kata"):
    """Buang stopword dan angka dari hasil hitung kata."""
    return df[~df[kolom].isin(STOPWORD)].copy()


@st.cache_data(show_spinner=False)
def kata_per_sumber(f):
    where, params = _where_berita(f)
    return _query(f"""
        WITH w AS (
            SELECT sumber, unnest(regexp_extract_all(lower(title), '[a-z]{{3,}}')) AS kata
            FROM {T_BERITA} WHERE {where}
        )
        SELECT sumber, kata, COUNT(*) AS jumlah FROM w GROUP BY 1, 2 HAVING COUNT(*) >= 3
    """, params)


def peta_arah(f, geser=True):
    """Tanggal kalender -> 'naik'/'turun' menurut hari bursa terkait."""
    ih = muat_ihsg()[["tanggal", "return_pct"]].rename(columns={"tanggal": "hari_bursa"})
    kal = pd.DataFrame({"tanggal": pd.date_range(f["awal"], f["akhir"]).astype("datetime64[ns]")})
    if geser:
        m = pd.merge_asof(kal, ih.sort_values("hari_bursa"), left_on="tanggal",
                          right_on="hari_bursa", direction="forward")
    else:
        m = kal.merge(ih, left_on="tanggal", right_on="hari_bursa", how="left")
    m = m.dropna(subset=["return_pct"])
    m = m[m["return_pct"] != 0].copy()
    m["arah"] = np.where(m["return_pct"] > 0, "naik", "turun")
    return pd.DataFrame({"tgl": m["tanggal"].dt.date, "arah": m["arah"]})


@st.cache_data(show_spinner=False)
def kata_naik_turun(f, geser=True):
    """Hitung kata pada judul untuk hari IHSG naik vs turun.
    Return: (DataFrame arah/kata/jumlah, {'naik': n_judul, 'turun': n_judul})."""
    peta = peta_arah(f, geser)
    where, params = _where_berita(f)
    kata = _query(f"""
        WITH j AS (
            SELECT p.arah AS arah, lower(title) AS t
            FROM {T_BERITA} b JOIN peta p ON p.tgl = b.tanggal WHERE {where}
        ), w AS (
            SELECT arah, unnest(regexp_extract_all(t, '[a-z]{{3,}}')) AS kata FROM j
        )
        SELECT arah, kata, COUNT(*) AS jumlah FROM w GROUP BY 1, 2 HAVING COUNT(*) >= 3
    """, params, {"peta": peta})
    n = _query(f"""
        SELECT p.arah AS arah, COUNT(*) AS n
        FROM {T_BERITA} b JOIN peta p ON p.tgl = b.tanggal WHERE {where} GROUP BY 1
    """, params, {"peta": peta})
    return kata, {r.arah: int(r.n) for r in n.itertuples()}


def kata_khas(df, kolom_grup, grup_a, grup_b, min_total=30, n=15):
    """Kata yang relatif lebih khas di grup_a dibanding grup_b (log-odds sederhana)."""
    p = df.pivot_table(index="kata", columns=kolom_grup, values="jumlah", aggfunc="sum",
                       fill_value=0)
    for g in (grup_a, grup_b):
        if g not in p.columns:
            p[g] = 0
    p = p[(p[grup_a] + p[grup_b]) >= min_total]
    if p.empty:
        return p
    na, nb = max(p[grup_a].sum(), 1), max(p[grup_b].sum(), 1)
    p["skor"] = np.log((p[grup_a] + 1) / na) - np.log((p[grup_b] + 1) / nb)
    return p.sort_values("skor", ascending=False).head(n)[[grup_a, grup_b, "skor"]]


# ==============================
# TREN TOPIK / TOKOH
# ==============================

def _pola(kata_list):
    bagian = []
    for k in kata_list:
        k = k.strip().lower()
        if not k:
            continue
        if k.startswith("="):
            bagian.append(re.escape(k[1:]) + r"\b")
        else:
            bagian.append(re.escape(k) + r"\w*")
    return r"\b(?:" + "|".join(bagian) + ")" if bagian else None


@st.cache_data(show_spinner=False)
def tren_kata(f, kelompok, per="hari"):
    """kelompok: tuple of (nama, tuple(kata)). Return DataFrame waktu/sumber/grup/jumlah."""
    sel, params, nama_kol = [], [], {}
    for i, (nama, kata) in enumerate(kelompok):
        pola = _pola(list(kata))
        if not pola:
            continue
        sel.append(f"COUNT(*) FILTER (WHERE regexp_matches(lower(title), ?)) AS g{i}")
        params.append(pola)
        nama_kol[f"g{i}"] = nama
    if not sel:
        return pd.DataFrame(columns=["waktu", "sumber", "grup", "jumlah"])
    where, wp = _where_berita(f)
    bucket = "tanggal" if per == "hari" else "date_trunc('month', tanggal)"
    df = _query(f"SELECT {bucket} AS waktu, sumber, {', '.join(sel)} FROM {T_BERITA} "
                f"WHERE {where} GROUP BY 1, 2 ORDER BY 1", params + wp)
    long = df.melt(id_vars=["waktu", "sumber"], var_name="grup", value_name="jumlah")
    long["grup"] = long["grup"].map(nama_kol)
    long["waktu"] = pd.to_datetime(long["waktu"]).astype("datetime64[ns]")
    return long


def kelompok_dari(kamus, pilihan):
    return tuple((n, tuple(kamus[n])) for n in pilihan)


# ==============================
# UTILITAS HARI BURSA
# ==============================

def ke_hari_bursa(df, ihsg, geser=True, kolom="tanggal"):
    """Petakan tanggal kalender ke hari bursa (berikutnya, atau hanya hari yang sama)."""
    bursa = ihsg[["tanggal"]].rename(columns={"tanggal": "hari_bursa"}).sort_values("hari_bursa")
    df = df.sort_values(kolom)
    if geser:
        m = pd.merge_asof(df, bursa, left_on=kolom, right_on="hari_bursa", direction="forward")
    else:
        m = df.merge(bursa, left_on=kolom, right_on="hari_bursa", how="left")
    return m.dropna(subset=["hari_bursa"])


def korelasi_lag(harian_total, ihsg, awal, akhir, target="Return (%)", geser=True, maks=5):
    """harian_total: DataFrame (tanggal, jumlah). Return (df pasangan harian, daftar korelasi)."""
    per_bursa = (ke_hari_bursa(harian_total, ihsg, geser)
                 .groupby("hari_bursa")["jumlah"].sum().reset_index())
    df = ihsg.merge(per_bursa, left_on="tanggal", right_on="hari_bursa", how="left")
    df["jumlah"] = df["jumlah"].fillna(0)
    df["y"] = df["return_pct"] if target == "Return (%)" else df["return_pct"].abs()
    df = df[(df["tanggal"] >= awal) & (df["tanggal"] <= akhir)].reset_index(drop=True)
    kor = [{"Lag": L, "Korelasi": df["jumlah"].corr(df["y"].shift(-L))} for L in range(maks + 1)]
    return df, pd.DataFrame(kor)


# ==============================
# INSIGHT (kartu temuan otomatis)
# ==============================

def _angka(n):
    return f"{int(round(n)):,}".replace(",", ".")


def _tgl(t):
    bulan = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    t = pd.Timestamp(t)
    return f"{t.day} {bulan[t.month - 1]} {t.year}"


def kekuatan(r):
    a = abs(r)
    kata = ("sangat lemah" if a < 0.1 else "lemah" if a < 0.3 else
            "sedang" if a < 0.5 else "kuat")
    arah = "positif" if r > 0 else "negatif"
    return f"{kata} ({arah})" if a >= 0.1 else kata


def _bulan(p):
    nama = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus",
            "September", "Oktober", "November", "Desember"]
    return f"{nama[p.month - 1]} {p.year}"


def insight_ihsg(ih):
    """ih: DataFrame IHSG pada rentang terpilih."""
    h = ih.dropna(subset=["return_pct"])
    if len(h) < 5:
        return []
    out = []
    naik, turun = h.loc[h["return_pct"].idxmax()], h.loc[h["return_pct"].idxmin()]
    out.append(("Kenaikan harian terbesar", f"+{naik['return_pct']:.2f}%",
                f"{_tgl(naik['tanggal'])}, ditutup di {_angka(naik['close'])}"))
    out.append(("Penurunan harian terbesar", f"{turun['return_pct']:.2f}%",
                f"{_tgl(turun['tanggal'])}, ditutup di {_angka(turun['close'])}"))
    bln = (ih.assign(b=ih["tanggal"].dt.to_period("M"))
             .groupby("b")["close"].agg(["first", "last"]))
    bln["ubah"] = (bln["last"] / bln["first"] - 1) * 100
    if len(bln) >= 2:
        b, w = bln["ubah"].idxmax(), bln["ubah"].idxmin()
        out.append(("Bulan terbaik", f"{bln.loc[b, 'ubah']:+.1f}%", _bulan(b)))
        out.append(("Bulan terburuk", f"{bln.loc[w, 'ubah']:+.1f}%", _bulan(w)))
    tinggi, rendah = ih.loc[ih["close"].idxmax()], ih.loc[ih["close"].idxmin()]
    out.append(("Penutupan tertinggi", _angka(tinggi["close"]), _tgl(tinggi["tanggal"])))
    out.append(("Penutupan terendah", _angka(rendah["close"]), _tgl(rendah["tanggal"])))
    n_naik, n_turun = int((h["return_pct"] > 0).sum()), int((h["return_pct"] < 0).sum())
    out.append(("Hari naik vs turun", f"{n_naik} : {n_turun}",
                f"{n_naik / max(n_naik + n_turun, 1) * 100:.0f}% hari bursa ditutup naik"))
    return out


def insight_berita(f):
    """Insight dari berita pada rentang/sumber terpilih (tema tidak dibatasi)."""
    fs = semua_tema(f)
    h = berita_harian(fs)
    if h.empty:
        return []
    out = []
    tot = h["jumlah"].sum()
    tema = h.groupby("tema")["jumlah"].sum().sort_values(ascending=False)
    out.append(("Tema paling dominan", tema.index[0],
                f"{tema.iloc[0] / tot * 100:.0f}% dari {_angka(tot)} berita"))
    per_hari = h.groupby("tanggal")["jumlah"].sum()
    hari = per_hari.idxmax()
    tema_hari = h[h["tanggal"] == hari].groupby("tema")["jumlah"].sum().idxmax()
    out.append(("Hari dengan berita terbanyak", _tgl(hari),
                f"{_angka(per_hari.max())} berita, paling banyak bertema {tema_hari}"))
    jam = berita_per_jam(fs)
    if not jam.empty:
        j = jam.groupby("jam")["jumlah"].sum()
        out.append(("Jam terbit paling ramai", f"{int(j.idxmax()):02d}.00",
                    f"{j.max() / j.sum() * 100:.1f}% berita terbit pada jam ini (WIB)"))
    if h["sumber"].nunique() >= 2:
        s = h.groupby(["sumber", "tema"])["jumlah"].sum().reset_index()
        s["p"] = s["jumlah"] / s.groupby("sumber")["jumlah"].transform("sum") * 100
        bagian = []
        for nama, g in s.groupby("sumber"):
            t = g.sort_values("p", ascending=False).iloc[0]
            bagian.append(f"{nama}: {t['tema']} ({t['p']:.0f}%)")
        out.append(("Fokus tiap media", " | ".join(bagian), "tema terbesar di masing-masing media"))
    return out


def insight_hubungan(f, geser=True):
    """Insight yang menghubungkan berita dan IHSG pada rentang terpilih."""
    ihsg = muat_ihsg()
    awal, akhir = pd.Timestamp(f["awal"]), pd.Timestamp(f["akhir"])
    fs = semua_tema(f)
    h = berita_harian(fs)
    if h.empty:
        return []
    out = []
    total = h.groupby("tanggal")["jumlah"].sum().reset_index()
    df, kor = korelasi_lag(total, ihsg, awal, akhir, "Return (%)", geser)
    df2, kor2 = korelasi_lag(total, ihsg, awal, akhir, "|Return| (volatilitas)", geser)
    if df["y"].notna().sum() >= 10:
        r0, rv = kor["Korelasi"].iloc[0], kor2["Korelasi"].iloc[0]
        out.append(("Berita ramai vs arah IHSG", f"r = {r0:.2f}",
                    f"hubungan {kekuatan(r0)}; ramainya berita tidak memprediksi naik/turun"))
        out.append(("Berita ramai vs gejolak IHSG", f"r = {rv:.2f}",
                    f"hubungan {kekuatan(rv)} dengan besarnya perubahan harian"))
    # hari ekstrem
    d = df.dropna(subset=["return_pct"])
    if len(d) >= 5:
        rata = d["jumlah"].mean()
        t = d.loc[d["return_pct"].idxmin()]
        out.append(("Hari IHSG turun terbesar", f"{t['return_pct']:.2f}%",
                    f"{_tgl(t['tanggal'])}: {_angka(t['jumlah'])} berita "
                    f"({t['jumlah'] / max(rata, 1):.1f}x rata-rata hari bursa)"))
        n = d.loc[d["return_pct"].idxmax()]
        out.append(("Hari IHSG naik terbesar", f"+{n['return_pct']:.2f}%",
                    f"{_tgl(n['tanggal'])}: {_angka(n['jumlah'])} berita "
                    f"({n['jumlah'] / max(rata, 1):.1f}x rata-rata hari bursa)"))
    # tema naik vs turun
    arah = peta_arah(f, geser)
    if not arah.empty:
        hh = h.copy()
        hh["tgl"] = hh["tanggal"].dt.date
        m = hh.merge(arah, on="tgl")
        hari = arah.groupby("arah").size()
        if {"naik", "turun"} <= set(hari.index):
            t = m.groupby(["tema", "arah"])["jumlah"].sum().unstack(fill_value=0)
            for c in ("naik", "turun"):
                if c not in t.columns:
                    t[c] = 0
            t["naik_hr"] = t["naik"] / hari["naik"]
            t["turun_hr"] = t["turun"] / hari["turun"]
            t = t[(t["naik"] + t["turun"]) >= 200]
            if not t.empty:
                t["rasio"] = t["turun_hr"] / t["naik_hr"].replace(0, np.nan)
                tm = t["rasio"].idxmax()
                selisih = (t.loc[tm, "rasio"] - 1) * 100
                if selisih >= 10:
                    out.append(("Tema yang lebih ramai saat IHSG turun", tm,
                                f"rata-rata {selisih:.0f}% lebih banyak per hari dibanding "
                                f"hari IHSG naik"))
                else:
                    out.append(("Tema saat IHSG turun vs naik", "Tidak ada yang mencolok",
                                f"selisih terbesar hanya {selisih:.0f}% (tema {tm})"))
    return out


# ==============================
# STUDI PERISTIWA & RAPOR PERIODE
# ==============================

def studi_peristiwa(ihsg, tgl, jendela=5):
    """Perubahan IHSG di sekitar tanggal peristiwa. Hari 0 = hari bursa pertama pada/after tgl.
    Return DataFrame: hari, tanggal, close, indeks (hari -1 = 100), return_pct."""
    d = ihsg.sort_values("tanggal").reset_index(drop=True)
    idx = d.index[d["tanggal"] >= pd.Timestamp(tgl)]
    if len(idx) == 0:
        return pd.DataFrame()
    i0 = int(idx[0])
    lo, hi = max(i0 - jendela, 0), min(i0 + jendela, len(d) - 1)
    w = d.iloc[lo:hi + 1].copy()
    w["hari"] = range(lo - i0, hi - i0 + 1)
    base = d["close"].iloc[i0 - 1] if i0 >= 1 else d["close"].iloc[i0]
    w["indeks"] = w["close"] / base * 100
    return w[["hari", "tanggal", "close", "indeks", "return_pct"]]


def rapor_periode(ihsg, harian, panjang=100):
    """Ringkasan per `panjang` hari kalender sejak START. harian: berita_harian tanpa filter."""
    baris = []
    awal = pd.Timestamp(START)
    akhir_data = pd.Timestamp(END)
    k = 0
    while awal <= akhir_data:
        akhir = min(awal + pd.Timedelta(days=panjang - 1), akhir_data)
        ih = ihsg[(ihsg["tanggal"] >= awal) & (ihsg["tanggal"] <= akhir)]
        hb = harian[(harian["tanggal"] >= awal) & (harian["tanggal"] <= akhir)]
        if not ih.empty:
            tema = hb.groupby("tema")["jumlah"].sum().sort_values(ascending=False)
            baris.append({
                "Periode": f"Hari {k * panjang + 1}-{k * panjang + (akhir - awal).days + 1}",
                "Tanggal": f"{_tgl(awal)} - {_tgl(akhir)}",
                "Hari bursa": len(ih),
                "Perubahan IHSG (%)": round((ih["close"].iloc[-1] / ih["close"].iloc[0] - 1) * 100, 2),
                "Volatilitas harian (%)": round(ih["return_pct"].std(), 3),
                "Total berita": int(hb["jumlah"].sum()),
                "Tema dominan": tema.index[0] if len(tema) else "-",
            })
        awal = akhir + pd.Timedelta(days=1)
        k += 1
    return pd.DataFrame(baris)


# ==============================
# FILTER GLOBAL (SIDEBAR)
# ==============================

def _terapkan_preset():
    hari = PRESET[st.session_state["preset"]]
    awal = START if hari is None else max(START, END - timedelta(days=hari))
    st.session_state["rentang"] = (awal, END)


def _tema_default(opsi):
    return [TEMA_DEFAULT] if TEMA_DEFAULT in opsi else opsi[:1]


def _reset():
    st.session_state["preset"] = "Semua"
    st.session_state["rentang"] = (START, END)
    st.session_state["sumber"] = list(SUMBER)
    st.session_state["tema"] = _tema_default(daftar_tema())
    st.session_state["kata"] = ""
    st.session_state["mode"] = "Salah satu kata"


def _filter_dari_state():
    rentang = st.session_state["rentang"]
    return {
        "awal": rentang[0],
        "akhir": rentang[1],
        "sumber": tuple(st.session_state["sumber"]),
        "tema": tuple(st.session_state["tema"]),
        "kata": st.session_state["kata"],
        "mode": st.session_state["mode"],
    }


def filter_aktif():
    """Nilai filter sidebar saat ini (dipakai oleh halaman)."""
    return _filter_dari_state()


def sidebar_filter():
    """Gambar filter di sidebar (sekali, dari app.py)."""
    opsi = daftar_tema()
    st.session_state.setdefault("preset", "Semua")
    st.session_state.setdefault("rentang", (START, END))
    st.session_state.setdefault("sumber", list(SUMBER))
    st.session_state.setdefault("tema", _tema_default(opsi))
    st.session_state.setdefault("kata", "")
    st.session_state.setdefault("mode", "Salah satu kata")

    sb = st.sidebar
    sb.markdown("##### Filter")
    sb.selectbox("Rentang cepat", list(PRESET), key="preset", on_change=_terapkan_preset,
                 help="Dihitung mundur dari 20 September 2026 (akhir data).")
    sb.date_input("Rentang tanggal", min_value=START, max_value=END, key="rentang")
    sb.multiselect("Sumber berita", SUMBER, key="sumber", help="Kosong = semua sumber.")
    sb.multiselect("Tema berita", opsi, key="tema",
                   help="Tema dibuat seragam untuk CNN dan CNBC. Kosong = semua tema.")
    sb.text_input("Kata kunci judul", key="kata",
                  help="Pisahkan dengan koma, contoh: ihsg, rupiah")
    sb.radio("Kecocokan kata", ["Salah satu kata", "Semua kata"], key="mode", horizontal=True)
    sb.button("Reset filter", on_click=_reset)

    rentang = st.session_state["rentang"]
    if not isinstance(rentang, (tuple, list)) or len(rentang) != 2:
        sb.info("Pilih tanggal akhir pada kalender.")
        st.stop()

    f = _filter_dari_state()
    jml = int(berita_harian(f)["jumlah"].sum())
    ihsg = muat_ihsg()
    n_hari = int(((ihsg["tanggal"] >= pd.Timestamp(f["awal"])) &
                  (ihsg["tanggal"] <= pd.Timestamp(f["akhir"]))).sum())
    sb.caption(f"{jml:,} berita, {n_hari} hari bursa".replace(",", "."))
    return f


def peringatan_cakupan(f):
    """Peringatan jika rentang mencakup periode saat cakupan berita CNN lebih tipis."""
    cnn_dipilih = (not f["sumber"]) or ("CNN" in f["sumber"])
    if f["awal"] < BATAS_CAKUPAN and cnn_dipilih:
        st.warning("Rentang ini mencakup periode sebelum April 2025, saat cakupan berita CNN "
                   "lebih tipis (batas 1000 halaman per kanal). Jumlah berita CNN di periode "
                   "ini tidak setara dengan bulan-bulan sesudahnya, sedangkan CNBC relatif "
                   "stabil.")