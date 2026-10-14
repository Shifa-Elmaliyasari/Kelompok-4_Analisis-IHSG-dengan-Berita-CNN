import os
from datetime import date, timedelta

import duckdb
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

START = date(2024, 10, 20)
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


# ==============================
# AKSES DUCKLAKE (hanya baca)
# ==============================

def _p(path):
    return path.replace("\\", "/")


   


@st.cache_resource(show_spinner=False)
def _koneksi():
    """Satu koneksi bersama yang meng-ATTACH DuckLake."""
    con = duckdb.connect()
    con.execute("INSTALL ducklake")
    con.execute("LOAD ducklake")

    catalog_path = os.path.abspath(LAKE_CATALOG).replace("\\", "/")
    data_path = os.path.abspath(LAKE_DATA).replace("\\", "/")
    data_path = data_path.rstrip("/") + "/"

    # Samakan huruf drive dengan path yang tercatat di katalog.
    if len(data_path) >= 2 and data_path[1] == ":":
        data_path = data_path[0].lower() + data_path[1:]

    sql = (
        f"ATTACH 'ducklake:{catalog_path}' AS lake "
        f"(DATA_PATH '{data_path}', READ_ONLY)"
    )

    con.execute(sql)
    return con



def _query(sql, params=None):
    if not os.path.exists(LAKE_CATALOG):
        st.error("DuckLake belum ditemukan. Jalankan buat_ducklake.py terlebih dahulu "
                 "(harus ada folder ducklake/ di samping app.py).")
        st.stop()
    cur = _koneksi().cursor()
    try:
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


@st.cache_data(show_spinner=False)
def berita_harian(f):
    where, params = _where_berita(f)
    df = _query(f"SELECT tanggal, sumber, tema, COUNT(*) AS jumlah FROM {T_BERITA} "
                f"WHERE {where} GROUP BY 1, 2, 3 ORDER BY 1", params)
    return _ke_waktu(df)


@st.cache_data(show_spinner=False)
def cari_berita(f, urut, limit):
    where, params = _where_berita(f)
    arah = "DESC" if urut == "Terbaru" else "ASC"
    return _query(f"SELECT published, sumber, tema, kategori, title, link FROM {T_BERITA} "
                  f"WHERE {where} ORDER BY published {arah} LIMIT {int(limit)}", params)


@st.cache_data(show_spinner=False)
def judul_berita(f):
    where, params = _where_berita(f)
    df = _query(f"SELECT tanggal, sumber, title FROM {T_BERITA} WHERE {where}", params)
    return _ke_waktu(df)


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


def sidebar_filter():
    """Gambar filter di sidebar dan kembalikan nilainya sebagai dict."""
    opsi = daftar_tema()
    st.session_state.setdefault("preset", "Semua")
    st.session_state.setdefault("rentang", (START, END))
    st.session_state.setdefault("sumber", list(SUMBER))
    st.session_state.setdefault("tema", _tema_default(opsi))
    st.session_state.setdefault("kata", "")
    st.session_state.setdefault("mode", "Salah satu kata")

    sb = st.sidebar
    sb.header("Filter")
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

    f = {
        "awal": rentang[0],
        "akhir": rentang[1],
        "sumber": tuple(st.session_state["sumber"]),
        "tema": tuple(st.session_state["tema"]),
        "kata": st.session_state["kata"],
        "mode": st.session_state["mode"],
    }

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