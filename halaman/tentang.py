import plotly.express as px
import streamlit as st

import db
import ui

ui.judul("Tentang Data", "Dari mana data berasal, bagaimana disimpan, dan apa keterbatasannya")

c1, c2 = st.columns(2)
with c1:
    with ui.kartu("Sumber dan penyimpanan"):
        st.markdown("""
- **Berita:** judul dan tautan dari indeks **CNN Indonesia** (per kanal dan sub-kanal) dan
  **CNBC Indonesia** (indeks berita terbaru), 20 Oktober 2024 sampai 20 September 2026.
- **IHSG:** harga harian indeks `^JKSE` dari Yahoo Finance.
- **Penyimpanan:** tiap sumber disimpan di file DuckDB sendiri (`cnn.duckdb`, `cnbc.duckdb`,
  `ihsg.duckdb`), lalu digabung ke **DuckLake** dengan empat schema: `cnn`, `cnbc`, `pasar`,
  dan `analitik` (gabungan CNN + CNBC beserta kolom `tema`).
- **Dashboard** ini hanya membaca dari DuckLake.
""")
with c2:
    with ui.kartu("Kolom tema"):
        st.markdown("""
- CNN dan CNBC memakai kategori berbeda (rubrik `news` di CNBC berisi campuran politik, hukum,
  dan ekonomi), sehingga kategori asli tidak bisa dibandingkan langsung.
- Karena itu dibuat kolom `tema` yang seragam. Untuk rubrik yang jelas (misalnya `ekonomi` di
  CNN atau `market` di CNBC) tema diambil dari kategori; untuk rubrik umum tema ditebak dari
  kata kunci pada judul. **Tema hasil tebakan bersifat perkiraan.**
""")

with ui.kartu("Keterbatasan yang perlu diingat"):
    st.markdown("""
- CNN membatasi halaman indeks sampai 1000 halaman per kanal, sehingga jumlah berita CNN per
  hari lebih sedikit di awal periode dan makin banyak di akhir periode. CNBC tidak punya batas
  ini. Perbandingan jumlah CNN dan CNBC paling adil pada periode yang lebih baru.
- Berita akhir pekan dan hari libur tidak punya data IHSG; di halaman hubungan berita dan IHSG
  berita tersebut dapat dipindahkan ke hari bursa berikutnya.
- Analisis kata hanya memakai judul, bukan isi berita, dan sebagian kata umum disaring.
- Hubungan yang tampak bersifat korelasi, bukan bukti sebab-akibat.
""")

st.markdown("#### Isi DuckLake")
tabel = db.ringkasan_tabel()
tabel["awal"] = tabel["awal"].astype(str)
tabel["akhir"] = tabel["akhir"].astype(str)
st.dataframe(tabel, hide_index=True)

cak = db.cakupan_bulanan()
dasar = st.radio("Cakupan berita per bulan, dikelompokkan per", ["Sumber", "Tema"],
                 horizontal=True)
kolom = dasar.lower()
data = cak.groupby(["bulan", kolom])["jumlah"].sum().reset_index()
peta = ui.WARNA_SUMBER if kolom == "sumber" else None
fig = px.bar(data, x="bulan", y="jumlah", color=kolom, color_discrete_map=peta,
             color_discrete_sequence=ui.WARNA,
             labels={"bulan": "Bulan", "jumlah": "Jumlah berita", kolom: dasar})
with ui.kartu("Cakupan berita per bulan (tanpa filter)"):
    ui.tampil(fig, 420)