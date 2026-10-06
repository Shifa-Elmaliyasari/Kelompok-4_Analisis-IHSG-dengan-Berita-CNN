import os
from datetime import date, timedelta

import duckdb
import pandas as pd
import yfinance as yf

# ==============================
# KONFIGURASI
# ==============================

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "berita_ihsg.duckdb")
DB_SEMENTARA = os.path.join(BASE, "ihsg_sementara.duckdb")   # dipakai jika DB utama sedang terkunci

START = date(2024, 10, 20)
END = date(2026, 9, 20)
TICKER = "^JKSE"


# ==============================
# AMBIL DATA
# ==============================

def ambil_data():
    # Mundur 10 hari dari START supaya return hari bursa pertama (21 Okt 2024)
    # bisa dihitung dari penutupan hari sebelumnya, bukan NaN.
    awal = START - timedelta(days=10)
    akhir = END + timedelta(days=1)   # parameter end di yfinance bersifat eksklusif

    print(f"Mengambil {TICKER} dari Yahoo Finance...")
    df = yf.Ticker(TICKER).history(start=awal.isoformat(), end=akhir.isoformat())
    if df.empty:
        raise SystemExit("Data kosong dari Yahoo Finance. Coba lagi nanti.")

    df = df.reset_index()
    df["tanggal"] = pd.to_datetime(df["Date"]).dt.date
    df = df.rename(columns={"Open": "open", "High": "high", "Low": "low",
                            "Close": "close", "Volume": "volume"})
    df = df[["tanggal", "open", "high", "low", "close", "volume"]]
    df = df.dropna(subset=["close"]).drop_duplicates("tanggal").sort_values("tanggal")

    df["return_pct"] = (df["close"].pct_change() * 100).round(4)

    # potong ke rentang yang diinginkan SETELAH return dihitung
    df = df[(df["tanggal"] >= START) & (df["tanggal"] <= END)].copy()
    df["volume"] = df["volume"].fillna(0).astype("int64")
    return df.reset_index(drop=True)


# ==============================
# SIMPAN KE DUCKDB
# ==============================

def simpan(df, path):
    con = duckdb.connect(path)
    con.execute("""
    CREATE TABLE IF NOT EXISTS ihsg (
        tanggal DATE PRIMARY KEY,
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        volume BIGINT,
        return_pct DOUBLE
    );
    """)
    # REPLACE: kalau dijalankan ulang, baris tanggal yang sama diperbarui
    con.execute("""
        INSERT OR REPLACE INTO ihsg (tanggal, open, high, low, close, volume, return_pct)
        SELECT tanggal, open, high, low, close, volume, return_pct FROM df
    """)
    total = con.execute("SELECT COUNT(*) FROM ihsg").fetchone()[0]
    print(f"Tersimpan di '{os.path.basename(path)}', tabel ihsg sekarang {total} baris.")
    print(con.execute("SELECT * FROM ihsg ORDER BY tanggal DESC LIMIT 5").fetchdf())
    con.close()


# ==============================
# PROGRAM UTAMA
# ==============================

def main():
    df = ambil_data()
    print(f"{len(df)} hari bursa, {df['tanggal'].min()} s/d {df['tanggal'].max()}")

    nol = df[df["volume"] == 0]
    if len(nol):
        print(f"PERINGATAN: {len(nol)} hari volume 0 (data Yahoo mungkin belum lengkap): "
              + ", ".join(str(t) for t in nol["tanggal"]))

    try:
        simpan(df, DB_PATH)
    except duckdb.IOException:
        print("\nDB utama sedang dipakai proses lain (mungkin scraping_berita.py masih jalan).")
        print("Data disimpan dulu ke file sementara.")
        simpan(df, DB_SEMENTARA)


if __name__ == "__main__":
    main()