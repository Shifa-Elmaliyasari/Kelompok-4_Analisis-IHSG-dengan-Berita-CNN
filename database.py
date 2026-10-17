import os

import duckdb

BASE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.join(BASE, "data_duckdb")
os.makedirs(FOLDER, exist_ok=True)

TABEL_BERITA = """
CREATE TABLE IF NOT EXISTS berita (
    tanggal DATE,
    published TIMESTAMP,
    kategori VARCHAR,
    topic VARCHAR,
    title VARCHAR,
    link VARCHAR PRIMARY KEY
);
"""

TABEL_IHSG = """
CREATE TABLE IF NOT EXISTS ihsg (
    tanggal DATE PRIMARY KEY,
    open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE,
    volume BIGINT, return_pct DOUBLE
);
"""

for nama_file, ddl in [("cnn.duckdb", TABEL_BERITA),
                       ("cnbc.duckdb", TABEL_BERITA),
                       ("ihsg.duckdb", TABEL_IHSG)]:
    con = duckdb.connect(os.path.join(FOLDER, nama_file))
    con.execute(ddl)
    con.close()
    print(f"{nama_file}: siap")