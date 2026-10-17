import argparse
import json
import os
import random
import re
import time
from collections import defaultdict
from datetime import date, datetime

import duckdb
import requests
from bs4 import BeautifulSoup

# ==============================
# KONFIGURASI
# ==============================

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "data_duckdb", "cnbc.duckdb")
PROGRESS = os.path.join(BASE, "cnbc_progress.json")

START = date(2024, 10, 20)
END = date(2026, 9, 20)

TOPIC = "cnbc"
INDEKS = "https://www.cnbcindonesia.com/indeks"
DELAY = 2.0
BATAS_CARI = 30000        # halaman yang pasti lebih lama dari START (halaman 20000 = Feb 2024)
OLD_PAGES_TO_STOP = 2     # berhenti jika median tanggal < START selama N halaman berturut-turut
MUNDUR_AMAN = 3           # mulai sedikit sebelum titik yang ditemukan, biar tidak ada yang terlewat

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "id-ID,id;q=0.9",
}
ARTICLE_RE = re.compile(
    r"https?://www\.cnbcindonesia\.com/([a-z\-]+(?:/[a-z\-]+)?)/(\d{14})-\d+-\d+/([^/?#]+)"
)

ID_RE = re.compile(r"/\d{14}-\d+-(\d+)/")

s = requests.Session()
s.headers.update(HEADERS)


def id_artikel(link):
    """ID artikel (angka terakhir di URL), dipakai untuk mencegah berita ganda."""
    m = ID_RE.search(link)
    return m.group(1) if m else link


# ==============================
# DATABASE
# ==============================

def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
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
    return con.execute(
        "SELECT COUNT(*) FROM berita WHERE tanggal = ?", [tgl]).fetchone()[0]


# ==============================
# SCRAPING
# ==============================

def url_halaman(page):
    return INDEKS if page <= 1 else f"{INDEKS}?page={page}"


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


def bersihkan_judul(teks, slug):
    teks = re.sub(r"\s+", " ", teks or "").strip()
    return teks if len(teks) >= 8 else slug.replace("-", " ")


def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    out = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].split("?")[0]
        m = ARTICLE_RE.match(href)
        if not m:
            continue
        kategori, ts, slug = m.groups()
        h = a.find(["h1", "h2", "h3", "h4"])
        judul = bersihkan_judul(h.get_text(" ", strip=True) if h else a.get_text(" ", strip=True), slug)
        if href not in out or len(judul) > len(out[href][3]):
            out[href] = (kategori, datetime.strptime(ts, "%Y%m%d%H%M%S"), href, judul)
    return list(out.values())


def median_waktu(items):
    ds = sorted(x[1] for x in items)
    return ds[len(ds) // 2]


def median_halaman(page):
    html = fetch(url_halaman(page))
    time.sleep(DELAY + random.uniform(0, 1.0))
    items = parse(html) if html else []
    return median_waktu(items) if items else None


def cari_halaman(target):
    """Cari halaman terkecil yang median waktunya sudah <= target (pencarian biner)."""
    m_hi = median_halaman(BATAS_CARI)
    if m_hi is not None and m_hi > target:
        raise SystemExit(f"Halaman {BATAS_CARI} masih lebih baru dari {target}. "
                         f"Naikkan BATAS_CARI.")
    lo, hi = 1, BATAS_CARI
    while lo < hi:
        mid = (lo + hi) // 2
        m = median_halaman(mid)
        print(f"   cari halaman: {mid} -> {m}")
        if m is None or m <= target:
            hi = mid
        else:
            lo = mid + 1
    return lo


def load_progress():
    if os.path.exists(PROGRESS):
        with open(PROGRESS, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_progress(p):
    with open(PROGRESS, "w", encoding="utf-8") as f:
        json.dump(p, f, indent=2)


def simpan_halaman(con, items, seen):
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
        kid = id_artikel(href)
        if kid in seen:
            continue
        seen.add(kid)
        per_tgl[d][1] += 1
        baris.append((d, waktu, kategori, TOPIC, judul, href))
    if baris:
        con.executemany("INSERT OR IGNORE INTO berita VALUES (?,?,?,?,?,?)", baris)
    return per_tgl, luar


# ==============================
# PROGRAM UTAMA
# ==============================

def tes():
    """Ambil 2 halaman pertama dan tampilkan hasil parse, TANPA menulis ke DB."""
    for page in (1, 2):
        html = fetch(url_halaman(page))
        items = parse(html) if html else []
        print(f"\n=== Halaman {page}: {len(items)} artikel ===")
        for kategori, waktu, href, judul in items:
            print(f"{waktu} | {kategori:<12} | {judul[:90]}\n    {href}")
        time.sleep(DELAY)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tes", action="store_true",
                    help="hanya tampilkan hasil parse 2 halaman pertama, tanpa menyimpan")
    args = ap.parse_args()
    if args.tes:
        tes()
        return

    progress = load_progress()
    if progress.get("done"):
        print("CNBC sudah selesai. Hapus cnbc_progress.json jika ingin mengulang.")
        return

    con = connect()
    seen = {id_artikel(r[0]) for r in con.execute(
        "SELECT link FROM berita").fetchall()}
    print(f"DB: {len(seen)} berita CNBC sudah tersimpan. Rentang {START} s/d {END}")

    if progress.get("terakhir"):
        target = datetime.fromisoformat(progress["terakhir"])
        print(f"Melanjutkan dari sekitar {target}")
    else:
        target = datetime.combine(END, datetime.max.time()).replace(microsecond=0)
        print(f"Mencari halaman untuk {target} ...")
    page = max(1, cari_halaman(target) - MUNDUR_AMAN)
    print(f"Mulai dari halaman {page}\n")

    saved = 0
    old_streak = 0
    while True:
        html = fetch(url_halaman(page))
        time.sleep(DELAY + random.uniform(0, 1.0))
        if not html:
            print(f"   halaman {page} gagal total. Jalankan ulang nanti untuk lanjut.")
            con.close()
            return
        items = parse(html)
        if not items:
            print(f"   halaman {page} kosong, selesai")
            break

        per_tgl, luar = simpan_halaman(con, items, seen)
        saved += sum(v[1] for v in per_tgl.values())

        med = median_waktu(items)
        progress["terakhir"] = med.isoformat()
        save_progress(progress)

        bagian = [f"{tgl.isoformat()} ambil {v[0]} baru {v[1]} db {total_db(con, tgl)}"
                  for tgl, v in sorted(per_tgl.items(), reverse=True)]
        if luar:
            bagian.append(f"luar rentang {luar}")
        print(f"   hal {page}: " + " | ".join(bagian) if bagian else f"   hal {page}: -")

        old_streak = old_streak + 1 if med.date() < START else 0
        if old_streak >= OLD_PAGES_TO_STOP:
            print(f"   sudah menjangkau {START}.")
            break
        page += 1

    progress["done"] = True
    save_progress(progress)
    print(f"\nSelesai: {saved} berita CNBC baru masuk DB.")
    con.close()


if __name__ == "__main__":
    main()