import argparse
import json
import os
import random
import re
import time
from collections import defaultdict
from datetime import date, datetime, timedelta

import duckdb
import requests
from bs4 import BeautifulSoup

# ==============================
# KONFIGURASI
# ==============================

# File dicari di folder yang sama dengan script ini.
BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "berita_ihsg.duckdb")
PROGRESS = os.path.join(BASE, "cnn_progress.json")

START = date(2024, 10, 20)
END = date(2026, 9, 20)

DELAY = 2.0
MAX_PAGE = 1000
OLD_PAGES_TO_STOP = 2   # berhenti jika median tanggal < START selama N halaman berturut-turut

CHANNELS = [
    ("keuangan",      "keuangan",      38),
    ("bisnis",        "bisnis",        40),
    ("ekonomi",       "ekonomi",        5),
    ("nasional",      "nasional",       3),
    ("internasional", "internasional",  6),
    ("asean",         "asean",         42),
    ("asia-pasifik",  "asia-pasifik",  43),
    ("timur-tengah",  "timur-tengah",  44),
    ("olahraga",      "olahraga",       7),
    ("teknologi",     "teknologi",      8),
    ("hiburan",       "hiburan",        9),
    ("gaya-hidup",    "gaya-hidup",    10),
    ("otomotif",      "otomotif",     577),
        # sub-kanal, untuk menembus batas 1000 halaman kanal induk
    ("politik",         "politik",         4),
    ("hukum-kriminal",  "hukum-kriminal", 11),
    ("peristiwa",       "peristiwa",      18),
    ("pemilu",          "pemilu",        616),
    ("energi",          "energi",         39),
    ("makro",           "makro",         531),
    ("sepakbola",       "sepakbola",      47),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "id-ID,id;q=0.9",
}
ARTICLE_RE = re.compile(
    r"https?://www\.cnnindonesia\.com/([a-z\-]+(?:/[a-z\-]+)?)/(\d{14})-\d+-\d+/([^/?#]+)"
)

s = requests.Session()
s.headers.update(HEADERS)


# ==============================
# DATABASE
# ==============================

def connect():
    con = duckdb.connect(DB_PATH)
    con.execute("""
    CREATE TABLE IF NOT EXISTS berita (
        tanggal DATE,
        published TIMESTAMP,
        kategori VARCHAR,
        topic VARCHAR,
        title VARCHAR,
        link VARCHAR PRIMARY KEY
    );
    """)
    return con


def total_db(con, tgl):
    return con.execute("SELECT COUNT(*) FROM berita WHERE tanggal = ?", [tgl]).fetchone()[0]



# ==============================
# SCRAPING
# ==============================

def fetch(url):
    global s
    for i in range(6):
        try:
            r = s.get(url, timeout=25)
            if r.status_code == 200:
                return r.text
            print(f"   ! HTTP {r.status_code} untuk {url}")
            if r.status_code == 404:
                return None
        except requests.RequestException as e:
            print(f"   ! error: {e}")
        s.close()
        s = requests.Session()
        s.headers.update(HEADERS)
        wait = 15 * (i + 1)
        print(f"   ... tunggu {wait} detik lalu coba lagi ({i + 1}/6)")
        time.sleep(wait)
    return None


def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    out = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].split("?")[0]
        m = ARTICLE_RE.match(href)
        if not m:
            continue
        kategori, ts, slug = m.groups()
        judul = a.get_text(" ", strip=True)
        judul = re.sub(r"\s+\S+\s+•\s+.*$", "", judul).strip() or slug.replace("-", " ")
        if href not in out or len(judul) > len(out[href][3]):
            out[href] = (kategori, datetime.strptime(ts, "%Y%m%d%H%M%S"), href, judul)
    return list(out.values())


def load_progress():
    if os.path.exists(PROGRESS):
        with open(PROGRESS, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_progress(p):
    with open(PROGRESS, "w", encoding="utf-8") as f:
        json.dump(p, f, indent=2)


def median_date(items):
    ds = sorted(x[1].date() for x in items)
    return ds[len(ds) // 2]


def simpan_halaman(con, items, seen, nama):
    """Simpan artikel satu halaman ke DB.
    Return: (per_tanggal {tgl: [diambil, baru]}, jumlah_di_luar_rentang)."""
    per_tgl = defaultdict(lambda: [0, 0])
    baris = []
    luar = 0
    for kategori, waktu, href, judul in items:
        d = waktu.date()
        if not (START <= d <= END):
            luar += 1
            continue
        per_tgl[d][0] += 1
        if href in seen:
            continue
        seen.add(href)
        per_tgl[d][1] += 1
        baris.append((d, waktu, kategori, nama, judul, href))
    if baris:
        con.executemany("INSERT OR IGNORE INTO berita VALUES (?,?,?,?,?,?)", baris)
    return per_tgl, luar


# ==============================
# LAPORAN PER TANGGAL
# ==============================

def laporan(con):
    """Tabel per tanggal dari isi DB, termasuk tanggal yang kosong."""
    rows = con.execute("""
        SELECT CAST(d AS DATE) AS tanggal, COALESCE(b.n, 0) AS tersimpan
        FROM generate_series(CAST(? AS DATE), CAST(? AS DATE), INTERVAL 1 DAY) AS g(d)
        LEFT JOIN (SELECT tanggal, COUNT(*) AS n FROM berita GROUP BY 1) b
               ON b.tanggal = CAST(g.d AS DATE)
        ORDER BY 1
    """, [START, END]).fetchall()

    print(f"\nLaporan berita di DB, {START} s/d {END}")
    print(f"{'tanggal':<12}{'tersimpan':>10}")
    for tgl, n in rows:
        print(f"{tgl.isoformat():<12}{n:>10}")

    total = sum(n for _, n in rows)
    kosong = [t.isoformat() for t, n in rows if n == 0]
    print(f"\nTotal tersimpan : {total}")
    print(f"Jumlah hari     : {len(rows)}")
    print(f"Hari tanpa berita: {len(kosong)}")
    if kosong:
        print("   " + ", ".join(kosong[:30]) + (" ..." if len(kosong) > 30 else ""))


# ==============================
# PROGRAM UTAMA
# ==============================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--laporan", action="store_true",
                    help="hanya tampilkan jumlah berita per tanggal di DB, tanpa scraping")
    args = ap.parse_args()

    con = connect()
    if args.laporan:
        laporan(con)
        con.close()
        return

    progress = load_progress()
    seen = {r[0] for r in con.execute("SELECT link FROM berita").fetchall()}
    print(f"DB: {len(seen)} berita sudah tersimpan. Rentang {START} s/d {END}")

    for nama, path, cid in CHANNELS:
        st = progress.get(nama) or {"next_page": 1, "done": False}
        if st["done"]:
            print(f"=== Kanal {nama}: sudah selesai, dilewati ===")
            continue

        print(f"\n=== Kanal: {nama} (mulai dari halaman {st['next_page']}) ===")
        reached_start = False
        saved = 0
        old_streak = 0
        failed = False

        for page in range(st["next_page"], MAX_PAGE + 1):
            url = f"https://www.cnnindonesia.com/{path}/indeks/{cid}"
            if page > 1:
                url += f"?page={page}"
            html = fetch(url)
            time.sleep(DELAY + random.uniform(0, 1.0))

            if not html:
                print(f"   halaman {page} gagal total. Jalankan ulang nanti untuk lanjut.")
                failed = True
                break

            items = parse(html)
            if not items:
                print(f"   halaman {page} kosong, kanal dianggap selesai")
                break

            per_tgl, luar = simpan_halaman(con, items, seen, nama)
            saved += sum(v[1] for v in per_tgl.values())

            progress[nama] = {"next_page": page + 1, "done": False}
            save_progress(progress)

            # laporan per tanggal: diambil di halaman ini, baru masuk DB, total di DB
            bagian = [f"{tgl.isoformat()} ambil {v[0]} baru {v[1]} db {total_db(con, tgl)}"
                      for tgl, v in sorted(per_tgl.items(), reverse=True)]
            if luar:
                bagian.append(f"luar rentang {luar}")
            print(f"   hal {page}: " + " | ".join(bagian) if bagian else f"   hal {page}: -")

            med = median_date(items)
            old_streak = old_streak + 1 if med < START else 0
            if old_streak >= OLD_PAGES_TO_STOP:
                reached_start = True
                break

        if failed:
            print("\nScript dihentikan karena koneksi terus gagal. "
                  "Tunggu 10-30 menit lalu jalankan lagi.")
            con.close()
            return

        progress[nama] = {"next_page": MAX_PAGE + 1, "done": True}
        save_progress(progress)
        if reached_start:
            print(f"   kanal '{nama}' sudah menjangkau {START}.")
        else:
            print(f"   PERINGATAN: kanal '{nama}' BELUM menjangkau {START} "
                  f"(batas 1000 halaman / halaman habis).")
        print(f"   selesai {nama}: {saved} berita baru masuk DB")

    print("\nSemua kanal selesai.")
    laporan(con)
    con.close()


if __name__ == "__main__":
    main()