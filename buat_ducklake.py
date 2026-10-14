import os
import shutil

import duckdb

BASE = os.path.dirname(os.path.abspath(__file__))
SUMBER = os.path.join(BASE, "berita_ihsg.duckdb")
FOLDER = os.path.join(BASE, "ducklake")
CATALOG = os.path.join(FOLDER, "berita_ihsg.ducklake")   # katalog/metadata
STORAGE = os.path.join(FOLDER, "data")                   # file parquet


def p(path):
    return path.replace("\\", "/")


def setup_environment():
    """Hapus lake lama (kalau ada) dan siapkan folder penyimpanan."""
    if os.path.exists(FOLDER):
        shutil.rmtree(FOLDER)
    os.makedirs(STORAGE, exist_ok=True)


def init_ducklake_connection():
    """Satu koneksi: database lama (read-only) + DuckLake."""
    conn = duckdb.connect()
    conn.execute("INSTALL ducklake;")
    conn.execute("LOAD ducklake;")
    conn.execute(f"ATTACH '{p(SUMBER)}' AS lama (READ_ONLY);")
    conn.execute(f"ATTACH 'ducklake:{p(CATALOG)}' AS lake (DATA_PATH '{p(STORAGE)}/');")
    conn.execute("USE lake;")
    return conn


def muat_cnn():
    print("[CNN] memuat...")
    conn = init_ducklake_connection()
    conn.execute("CREATE SCHEMA IF NOT EXISTS cnn;")
    conn.execute("CREATE TABLE cnn.berita AS SELECT * FROM lama.berita ORDER BY tanggal;")
    conn.close()


def muat_cnbc():
    print("[CNBC] memuat...")
    conn = init_ducklake_connection()
    conn.execute("CREATE SCHEMA IF NOT EXISTS cnbc;")
    conn.execute("CREATE TABLE cnbc.berita AS SELECT * FROM lama.berita_cnbc ORDER BY tanggal;")
    conn.close()


def muat_pasar():
    print("[Pasar] memuat IHSG...")
    conn = init_ducklake_connection()
    conn.execute("CREATE SCHEMA IF NOT EXISTS pasar;")
    conn.execute("CREATE TABLE pasar.ihsg AS SELECT * FROM lama.ihsg ORDER BY tanggal;")
    conn.close()


def muat_analitik():
    print("[Analitik] memuat gabungan CNN + CNBC (dengan kolom tema)...")
    conn = init_ducklake_connection()
    conn.execute("CREATE SCHEMA IF NOT EXISTS analitik;")
    conn.execute("CREATE TABLE analitik.berita_semua AS "
                 "SELECT * FROM lama.v_berita_semua ORDER BY tanggal;")
    conn.close()


def verifikasi():
    print("\n--- Verifikasi jumlah baris (lama vs lake) ---")
    conn = init_ducklake_connection()
    pasangan = [
        ("cnn.berita", "lama.berita"),
        ("cnbc.berita", "lama.berita_cnbc"),
        ("pasar.ihsg", "lama.ihsg"),
        ("analitik.berita_semua", "lama.v_berita_semua"),
    ]
    for baru, lama in pasangan:
        a = conn.execute(f"SELECT COUNT(*) FROM {lama}").fetchone()[0]
        b = conn.execute(f"SELECT COUNT(*) FROM {baru}").fetchone()[0]
        print(f"{baru:<24} lama={a:>8}  lake={b:>8}  {'OK' if a == b else 'BEDA!'}")
    conn.close()


def run_analytics():
    print("\n--- Query lintas schema: jumlah berita vs IHSG (10 hari bursa terakhir) ---")
    conn = init_ducklake_connection()
    hasil = conn.execute("""
        SELECT i.tanggal, i.close, ROUND(i.return_pct, 2) AS return_pct,
               COALESCE(c.jumlah, 0) AS berita_cnn,
               COALESCE(n.jumlah, 0) AS berita_cnbc
        FROM pasar.ihsg i
        LEFT JOIN (SELECT tanggal, COUNT(*) AS jumlah FROM cnn.berita  GROUP BY 1) c
               ON c.tanggal = i.tanggal
        LEFT JOIN (SELECT tanggal, COUNT(*) AS jumlah FROM cnbc.berita GROUP BY 1) n
               ON n.tanggal = i.tanggal
        ORDER BY i.tanggal DESC
        LIMIT 10
    """).fetchall()

    print(f"{'Tanggal':<12} | {'IHSG':>9} | {'Return %':>8} | {'CNN':>5} | {'CNBC':>5}")
    print("-" * 52)
    for tgl, close, ret, cnn, cnbc in hasil:
        ret = "-" if ret is None else f"{ret:.2f}"
        print(f"{str(tgl):<12} | {close:>9.2f} | {ret:>8} | {cnn:>5} | {cnbc:>5}")

    print("\n--- Snapshot DuckLake (riwayat versi) ---")
    print(conn.execute("FROM lake.snapshots();").df().to_string(index=False))
    conn.close()


if __name__ == "__main__":
    setup_environment()
    print("=== Memuat data ke DuckLake ===")
    muat_cnn()
    muat_cnbc()
    muat_pasar()
    muat_analitik()
    verifikasi()
    run_analytics()