# buat_ducklake.py
# Menggabungkan 3 file DuckDB (cnn, cnbc, ihsg) menjadi satu DuckLake.
# Jalankan: python buat_ducklake.py
import os
import shutil

import duckdb

import tema

BASE = os.path.dirname(os.path.abspath(__file__))
FOLDER_SUMBER = os.path.join(BASE, "data_duckdb")
FOLDER_LAKE = os.path.join(BASE, "ducklake")
CATALOG = os.path.join(FOLDER_LAKE, "berita_ihsg.ducklake")
DATA_PATH = os.path.join(FOLDER_LAKE, "data")


def setup_environment():
    """Hapus DuckLake lama supaya selalu dibuat bersih (data sumber tidak disentuh)."""
    if os.path.exists(FOLDER_LAKE):
        shutil.rmtree(FOLDER_LAKE)
    os.makedirs(DATA_PATH)
    for nama in ("cnn", "cnbc", "ihsg"):
        if not os.path.exists(os.path.join(FOLDER_SUMBER, f"{nama}.duckdb")):
            raise SystemExit(f"File data_duckdb/{nama}.duckdb tidak ditemukan. "
                             f"Jalankan scraping dulu.")


def init_ducklake_connection():
    con = duckdb.connect()
    con.execute("INSTALL ducklake")
    con.execute("LOAD ducklake")

    # tiga sumber, hanya dibaca
    for nama in ("cnn", "cnbc", "ihsg"):
        path = os.path.join(FOLDER_SUMBER, f"{nama}.duckdb").replace("\\", "/")
        con.execute(f"ATTACH '{path}' AS {nama}_db (READ_ONLY)")

    # DuckLake: catalog + folder Parquet
    cat = CATALOG.replace("\\", "/")
    dat = DATA_PATH.replace("\\", "/") + "/"
    con.execute(f"ATTACH 'ducklake:{cat}' AS lake "
                f"(DATA_PATH '{dat}', OVERRIDE_DATA_PATH true)")

    for schema in ("cnn", "cnbc", "pasar", "analitik"):
        con.execute(f"CREATE SCHEMA lake.{schema}")
    return con


def muat_cnn(con):
    con.execute("CREATE TABLE lake.cnn.berita AS SELECT * FROM cnn_db.berita ORDER BY tanggal")
    print("  lake.cnn.berita      dimuat")


def muat_cnbc(con):
    con.execute("CREATE TABLE lake.cnbc.berita AS SELECT * FROM cnbc_db.berita ORDER BY tanggal")
    print("  lake.cnbc.berita     dimuat")


def muat_pasar(con):
    con.execute("CREATE TABLE lake.pasar.ihsg AS SELECT * FROM ihsg_db.ihsg ORDER BY tanggal")
    print("  lake.pasar.ihsg      dimuat")


def muat_analitik(con):
    # gabungan CNN + CNBC beserta kolom tema (aturan dari tema.py)
    con.execute(f"""
        CREATE TABLE lake.analitik.berita_semua AS
        SELECT * FROM ({tema.sql_berita_semua()}) ORDER BY tanggal
    """)
    print("  lake.analitik.berita_semua dimuat")


def verifikasi(con):
    print("\nVerifikasi jumlah baris (sumber vs DuckLake):")
    cek = [
        ("cnn.berita",  "cnn_db.berita",  "lake.cnn.berita"),
        ("cnbc.berita", "cnbc_db.berita", "lake.cnbc.berita"),
        ("ihsg",        "ihsg_db.ihsg",   "lake.pasar.ihsg"),
    ]
    for nama, src, dst in cek:
        a = con.execute(f"SELECT COUNT(*) FROM {src}").fetchone()[0]
        b = con.execute(f"SELECT COUNT(*) FROM {dst}").fetchone()[0]
        print(f"  {nama:<12} sumber {a:>8,}  lake {b:>8,}  {'OK' if a == b else 'BEDA!'}")

    gab = con.execute("SELECT COUNT(*) FROM lake.analitik.berita_semua").fetchone()[0]
    cnn = con.execute("SELECT COUNT(*) FROM lake.cnn.berita").fetchone()[0]
    cnbc = con.execute("SELECT COUNT(*) FROM lake.cnbc.berita").fetchone()[0]
    print(f"  berita_semua {gab:>8,}  (cnn + cnbc = {cnn + cnbc:,})  "
          f"{'OK' if gab == cnn + cnbc else 'BEDA!'}")


def run_analytics(con):
    print("\nContoh analitik: berita per hari bursa dan return IHSG (10 hari terakhir):")
    print(con.execute("""
        SELECT i.tanggal, i.close, i.return_pct,
               COUNT(*) FILTER (WHERE b.sumber = 'CNN')  AS berita_cnn,
               COUNT(*) FILTER (WHERE b.sumber = 'CNBC') AS berita_cnbc
        FROM lake.pasar.ihsg i
        LEFT JOIN lake.analitik.berita_semua b ON b.tanggal = i.tanggal
        GROUP BY i.tanggal, i.close, i.return_pct
        ORDER BY i.tanggal DESC LIMIT 10
    """).df().to_string(index=False))

    print("\nRiwayat snapshot DuckLake:")
    print(con.execute("FROM lake.snapshots()").df().to_string(index=False))


def main():
    setup_environment()
    con = init_ducklake_connection()
    print("Memuat data ke DuckLake:")
    muat_cnn(con)
    muat_cnbc(con)
    muat_pasar(con)
    muat_analitik(con)
    verifikasi(con)
    run_analytics(con)
    con.close()
    print(f"\nSelesai. DuckLake ada di folder: {FOLDER_LAKE}")


if __name__ == "__main__":
    main()