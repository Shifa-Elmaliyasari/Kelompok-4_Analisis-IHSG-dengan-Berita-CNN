import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import db
import ui

ui.judul("Berita", "Pemberitaan CNN Indonesia dan CNBC Indonesia selama pemerintahan Prabowo")

f = db.filter_aktif()
db.peringatan_cakupan(f)
awal, akhir = pd.Timestamp(f["awal"]), pd.Timestamp(f["akhir"])

harian = db.berita_harian(f)
if harian.empty:
    st.info("Tidak ada berita yang cocok dengan filter ini.")
    st.stop()

fs = db.semua_tema(f)                 # untuk grafik proporsi/perbandingan (semua tema)
semua = db.berita_harian(fs)
per_hari = harian.groupby("tanggal")["jumlah"].sum()

# ---- kartu angka ----
k = st.columns(4)
ui.kartu_angka(k[0], "Berita (sesuai filter)", ui.angka(per_hari.sum()), gaya="lime")
ui.kartu_angka(k[1], "Rata-rata per hari", ui.angka(per_hari.sum() / max(len(per_hari), 1)))
tema_top = semua.groupby("tema")["jumlah"].sum().sort_values(ascending=False)
ui.kartu_angka(k[2], "Tema terbanyak (semua tema)", tema_top.index[0],
               f"{tema_top.iloc[0] / tema_top.sum() * 100:.0f}%", "net")
sumber_top = harian.groupby("sumber")["jumlah"].sum().sort_values(ascending=False)
ui.kartu_angka(k[3], "Sumber terbanyak", sumber_top.index[0],
               f"{sumber_top.iloc[0] / sumber_top.sum() * 100:.0f}%", "net", gaya="lav")
st.write("")

tab1, tab2, tab3, tab4 = st.tabs(["Ringkasan", "CNN vs CNBC", "Tokoh", "Daftar berita"])

# ======================================
# TAB 1: ringkasan
# ======================================
with tab1:
    c1, c2, c3 = st.columns(3)
    gran = c1.radio("Agregasi", ["Harian", "Mingguan", "Bulanan"], horizontal=True)
    hari = c2.radio("Cakupan hari", ["Hari kalender", "Hanya hari bursa"], horizontal=True)
    warna = c3.radio("Dikelompokkan per", ["Sumber", "Tema"], horizontal=True)
    kolom = warna.lower()

    d = harian.copy()
    if hari == "Hanya hari bursa":
        d = d.merge(db.muat_ihsg()[["tanggal"]], on="tanggal", how="inner")
    aturan = {"Harian": "D", "Mingguan": "W", "Bulanan": "MS"}[gran]
    agg = (d.set_index("tanggal").groupby(kolom)["jumlah"].resample(aturan).sum().reset_index())
    peta = ui.WARNA_SUMBER if kolom == "sumber" else None
    fig = px.bar(agg, x="tanggal", y="jumlah", color=kolom, color_discrete_map=peta,
                 color_discrete_sequence=ui.WARNA,
                 labels={"tanggal": "", "jumlah": "Jumlah berita", kolom: warna})
    with ui.kartu("Jumlah berita"):
        ui.tampil(fig, 380)

    a, b = st.columns(2)
    komp_tema = semua.groupby("tema")["jumlah"].sum().sort_values(ascending=False)
    with a:
        with ui.kartu("Proporsi tema", "Semua tema (filter Tema diabaikan)."):
            dn = go.Figure(go.Pie(labels=komp_tema.index, values=komp_tema.values, hole=0.58,
                                  marker_colors=ui.WARNA, sort=False, textinfo="percent",
                                  textposition="inside"))
            dn.update_layout(legend=dict(orientation="v", y=0.5, x=1.0))
            ui.tampil(dn, 400)
    komp_sumber = semua.groupby("sumber")["jumlah"].sum()
    with b:
        with ui.kartu("Proporsi sumber", "Sesuai rentang dan sumber di sidebar."):
            ds = go.Figure(go.Pie(labels=komp_sumber.index, values=komp_sumber.values, hole=0.58,
                                  marker_colors=[ui.WARNA_SUMBER.get(s, ui.REDUP)
                                                 for s in komp_sumber.index],
                                  textinfo="label+percent"))
            ds.add_annotation(text=f"<b>{ui.angka(komp_sumber.sum())}</b><br>berita",
                              showarrow=False, font=dict(size=15))
            ds.update_layout(showlegend=False)
            ui.tampil(ds, 400)

    st.markdown("#### Insight")
    daftar = db.insight_berita(f)
    if daftar:
        ui.kartu_insight(daftar, per_baris=4)

# ======================================
# TAB 2: CNN vs CNBC
# ======================================
with tab2:
    stabil = st.toggle("Pakai periode cakupan CNN yang stabil (mulai April 2025)", value=True,
                       help="Sebelum April 2025 cakupan CNN lebih tipis karena batas 1000 "
                            "halaman per kanal, sehingga perbandingan jumlah tidak adil.")
    f2 = {**fs, "sumber": ()}
    if stabil and f2["awal"] < db.BATAS_CAKUPAN:
        f2["awal"] = db.BATAS_CAKUPAN
    if f2["awal"] > f2["akhir"]:
        st.info("Rentang tanggal di sidebar berakhir sebelum April 2025. Matikan pilihan di "
                "atas atau perlebar rentangnya.")
    else:
        st.caption(f"Rentang yang dipakai: {f2['awal']} s/d {f2['akhir']}. Halaman ini selalu "
                   "menampilkan kedua sumber dan semua tema.")
        h2 = db.berita_harian(f2)
        a2, k2 = pd.Timestamp(f2["awal"]), pd.Timestamp(f2["akhir"])
        per = h2.groupby(["tanggal", "sumber"])["jumlah"].sum().unstack(fill_value=0)
        per = per.reindex(pd.date_range(a2, k2), fill_value=0)
        for s in db.SUMBER:
            if s not in per.columns:
                per[s] = 0

        m = st.columns(len(db.SUMBER))
        for kol, s, gaya in zip(m, db.SUMBER, ["lav", "lime"]):
            ui.kartu_angka(kol, f"Total {s}", ui.angka(per[s].sum()), gaya=gaya,
                           ket=f"rata-rata {ui.angka(per[s].mean())} per hari")
        st.write("")

        rata7 = st.toggle("Rata-rata bergerak 7 hari", value=True)
        tampil = per[db.SUMBER].rolling(7, min_periods=1).mean() if rata7 else per[db.SUMBER]
        long = tampil.reset_index().melt(id_vars="index", var_name="Sumber", value_name="Jumlah")
        fig = px.line(long, x="index", y="Jumlah", color="Sumber",
                      color_discrete_map=ui.WARNA_SUMBER,
                      labels={"index": "", "Jumlah": "Jumlah berita"})
        fig.update_traces(line_width=2.6)
        fig.update_layout(hovermode="x unified")
        with ui.kartu("Jumlah berita per hari"):
            ui.tampil(fig, 340)
        if per[db.SUMBER].std().min() > 0:
            r = per["CNN"].corr(per["CNBC"])
            st.caption(f"Korelasi jumlah berita harian CNN dan CNBC: {r:.3f}. Positif berarti "
                       "hari ramai di satu media cenderung ramai juga di media lain.")

        komp = h2.groupby(["sumber", "tema"])["jumlah"].sum().reset_index()
        komp["persen"] = komp["jumlah"] / komp.groupby("sumber")["jumlah"].transform("sum") * 100
        urutan = komp.groupby("tema")["jumlah"].sum().sort_values(ascending=False).index.tolist()
        fk = px.bar(komp, x="tema", y="persen", color="sumber", barmode="group",
                    color_discrete_map=ui.WARNA_SUMBER, category_orders={"tema": urutan},
                    labels={"tema": "", "persen": "Porsi dari seluruh berita sumbernya (%)",
                            "sumber": "Sumber"})
        with ui.kartu("Komposisi tema per media", "Apa yang diutamakan masing-masing media."):
            ui.tampil(fk, 380)

        st.markdown("#### Kata pada judul")
        if st.toggle("Hitung analisis kata", value=False, key="kata_sumber",
                     help="Memproses semua judul pada filter; bisa memakan beberapa detik."):
            kata = db.bersihkan_kata(db.kata_per_sumber(f2))
            kol = st.columns(len(db.SUMBER))
            for k_, s in zip(kol, db.SUMBER):
                top = (kata[kata["sumber"] == s].nlargest(15, "jumlah")
                       .rename(columns={"kata": "Kata", "jumlah": "Jumlah"}))
                with k_:
                    with ui.kartu(f"Kata teratas {s}"):
                        if top.empty:
                            st.info("Tidak ada data.")
                        else:
                            gb = px.bar(top.iloc[::-1], x="Jumlah", y="Kata", orientation="h",
                                        color_discrete_sequence=[ui.WARNA_SUMBER[s]])
                            ui.tampil(gb, 430)
            khas_cnn = db.kata_khas(kata, "sumber", "CNN", "CNBC")
            khas_cnbc = db.kata_khas(kata, "sumber", "CNBC", "CNN")
            if not khas_cnn.empty:
                st.markdown("**Kata yang lebih khas di satu media** (minimal 30 kemunculan)")
                d1, d2 = st.columns(2)
                d1.markdown("Lebih khas **CNN**")
                d1.dataframe(khas_cnn[["CNN", "CNBC"]])
                d2.markdown("Lebih khas **CNBC**")
                d2.dataframe(khas_cnbc[["CNN", "CNBC"]])

# ======================================
# TAB 3: tokoh
# ======================================
with tab3:
    st.caption("Seberapa sering nama tokoh disebut pada judul, per bulan. Mengabaikan filter "
               "Tema dan Kata kunci; rentang tanggal dan sumber tetap berlaku.")
    pilih = st.multiselect("Tokoh", list(db.TOKOH), default=["Prabowo", "Gibran", "Trump"])
    if not pilih:
        st.info("Pilih minimal satu tokoh.")
    else:
        t = db.tren_kata(fs, db.kelompok_dari(db.TOKOH, pilih), "bulan")
        if t.empty or t["jumlah"].sum() == 0:
            st.info("Tidak ada judul yang menyebut tokoh ini pada rentang terpilih.")
        else:
            fig = px.line(t, x="waktu", y="jumlah", color="grup", facet_col="sumber",
                          markers=True, labels={"waktu": "", "jumlah": "Judul yang menyebut",
                                                "grup": "Tokoh", "sumber": "Sumber"},
                          color_discrete_sequence=ui.WARNA)
            fig.for_each_annotation(lambda x: x.update(text=x.text.split("=")[-1]))
            fig.update_layout(hovermode="x unified")
            with ui.kartu("Penyebutan tokoh per bulan"):
                ui.tampil(fig, 400)
            tot = t.groupby("grup")["jumlah"].sum().sort_values(ascending=False)
            st.caption("Total penyebutan: " + "; ".join(f"{n}: {ui.angka(v)}"
                                                       for n, v in tot.items()))

# ======================================
# TAB 4: daftar berita
# ======================================
with tab4:
    c1, c2 = st.columns(2)
    urut = c1.selectbox("Urutan tabel", ["Terbaru", "Terlama"])
    limit = c2.selectbox("Jumlah baris tabel", [50, 100, 500, 1000], index=1)
    tabel = db.cari_berita(f, urut, limit)
    st.caption(f"Menampilkan {len(tabel)} berita ({urut.lower()}) dari filter yang dipilih.")
    st.dataframe(
        tabel.rename(columns={"published": "Terbit", "sumber": "Sumber", "tema": "Tema",
                              "kategori": "Kategori asli", "title": "Judul", "link": "Tautan"}),
        column_config={"Tautan": st.column_config.LinkColumn("Tautan", display_text="Buka")},
        hide_index=True,
    )
    st.download_button("Unduh tabel (CSV)", tabel.to_csv(index=False).encode("utf-8"),
                       file_name="berita_terfilter.csv", mime="text/csv")