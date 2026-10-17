import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import db
import ui

ui.judul("Hubungan Berita dan IHSG",
         "Apakah ramainya pemberitaan berkaitan dengan pergerakan IHSG selama pemerintahan "
         "Prabowo? Korelasi hanya menunjukkan keterkaitan, bukan sebab-akibat.")

f = db.filter_aktif()
db.peringatan_cakupan(f)
awal, akhir = pd.Timestamp(f["awal"]), pd.Timestamp(f["akhir"])

ihsg = db.muat_ihsg().reset_index(drop=True)
harian = db.berita_harian(f)
if harian.empty:
    st.info("Tidak ada berita yang cocok dengan filter ini.")
    st.stop()
total = harian.groupby("tanggal")["jumlah"].sum().reset_index()
ih = ihsg[(ihsg["tanggal"] >= awal) & (ihsg["tanggal"] <= akhir)]

# ---- pengaturan bersama ----
p1, p2 = st.columns(2)
geser = p1.toggle("Pindahkan berita akhir pekan/libur ke hari bursa berikutnya", value=True)
target = p2.radio("Yang dibandingkan", ["Return (%)", "|Return| (volatilitas)"], horizontal=True)

df, kor = db.korelasi_lag(total, ihsg, awal, akhir, target, geser)

# ---- kartu angka ----
k = st.columns(4)
ui.kartu_angka(k[0], "Berita (sesuai filter)", ui.angka(total["jumlah"].sum()), gaya="lime")
ui.kartu_angka(k[1], "Hari bursa", len(ih))
if len(ih) >= 2:
    kum = (ih["close"].iloc[-1] / ih["close"].iloc[0] - 1) * 100
    ui.kartu_angka(k[2], "IHSG (penutupan terakhir)", ui.angka(ih["close"].iloc[-1]),
                   f"{kum:+.2f}%", "naik" if kum >= 0 else "turun")
else:
    ui.kartu_angka(k[2], "IHSG (penutupan terakhir)", "-")
r0 = kor["Korelasi"].iloc[0]
ui.kartu_angka(k[3], "Korelasi berita vs " + ("return" if target == "Return (%)" else "|return|"),
               "-" if pd.isna(r0) else f"{r0:.3f}",
               None if pd.isna(r0) else db.kekuatan(r0), "net", gaya="lav",
               ket="lag 0 (hari yang sama)")
st.write("")

tab1, tab2, tab3, tab4 = st.tabs(["Ringkasan & insight", "Korelasi", "Topik & peristiwa",
                                  "Kata pada judul"])

# ======================================
# TAB 1: ringkasan & insight
# ======================================
with tab1:
    per_sumber = harian.groupby(["tanggal", "sumber"])["jumlah"].sum().reset_index()
    if ih.empty:
        st.info("Tidak ada data IHSG pada rentang ini.")
    else:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        for nama, g in per_sumber.groupby("sumber"):
            fig.add_trace(go.Bar(x=g["tanggal"], y=g["jumlah"], name=f"Berita {nama}",
                                 marker_color=ui.WARNA_SUMBER.get(nama), opacity=0.75),
                          secondary_y=True)
        fig.add_trace(go.Scatter(x=ih["tanggal"], y=ih["close"], mode="lines",
                                 name="IHSG (penutupan)", line=dict(color="#2E3270", width=2.2)),
                      secondary_y=False)
        fig.update_yaxes(title_text="IHSG", secondary_y=False)
        fig.update_yaxes(title_text="Jumlah berita", secondary_y=True, showgrid=False)
        fig.update_layout(barmode="stack", hovermode="x unified")
        with ui.kartu("IHSG dan jumlah berita per hari"):
            ui.tampil(fig, 440)

    st.markdown("#### Insight")
    st.caption("Dihitung otomatis dari data pada rentang dan sumber terpilih (semua tema).")
    daftar = db.insight_hubungan(f, geser)
    if daftar:
        ui.kartu_insight(daftar, per_baris=3)
    else:
        st.info("Data terlalu sedikit untuk menghitung insight. Perlebar rentang tanggal.")

# ======================================
# TAB 2: korelasi
# ======================================
with tab2:
    lag = st.slider("Lag (hari bursa)", 0, 5, 0,
                    help="0 = berita dan return di hari yang sama; 1 = return keesokan hari "
                         "bursa, dst.")
    pasangan = pd.DataFrame({"x": df["jumlah"], "y": df["y"].shift(-lag)}).dropna()
    if len(pasangan) < 10:
        st.info("Data terlalu sedikit untuk dihitung. Perlebar rentang tanggal.")
    else:
        r = pasangan["x"].corr(pasangan["y"])
        a, b = st.columns([3, 2])
        with a:
            with ui.kartu(f"Sebaran data (korelasi lag {lag}: {r:.3f})",
                          f"Hubungan {db.kekuatan(r)}. Tiap titik = satu hari bursa."):
                sc = px.scatter(pasangan, x="x", y="y", opacity=0.65,
                                labels={"x": "Jumlah berita pada hari bursa",
                                        "y": target + f" (lag {lag})"},
                                color_discrete_sequence=[ui.LAVENDER_TUA])
                koef = np.polyfit(pasangan["x"], pasangan["y"], 1)
                xs = np.array([pasangan["x"].min(), pasangan["x"].max()])
                sc.add_trace(go.Scatter(x=xs, y=koef[0] * xs + koef[1], mode="lines",
                                        name="Garis tren", line=dict(color=ui.TURUN)))
                sc.update_layout(showlegend=False)
                ui.tampil(sc, 380)
        with b:
            with ui.kartu("Korelasi pada lag 0-5"):
                bar = px.bar(kor, x="Lag", y="Korelasi", color_discrete_sequence=[ui.LIME_TUA])
                ambang = 1.96 / np.sqrt(len(pasangan))
                bar.add_hline(y=ambang, line_dash="dot", line_color=ui.REDUP)
                bar.add_hline(y=-ambang, line_dash="dot", line_color=ui.REDUP)
                ui.tampil(bar, 380)
        st.caption(f"Garis putus-putus = batas kira-kira signifikan (±{ambang:.3f}). "
                   "Batang yang tidak melewati garis berarti hubungannya tidak berbeda nyata "
                   "dari nol.")

# ======================================
# TAB 3: topik & peristiwa
# ======================================
with tab3:
    f2 = db.semua_tema(f)
    st.caption("Grafik topik mengabaikan filter Tema dan Kata kunci di sidebar; rentang tanggal "
               "dan sumber tetap berlaku.")
    c1, c2, c3 = st.columns([3, 2, 2])
    pilih = c1.multiselect("Topik kebijakan", list(db.TOPIK),
                           default=["MBG (makan bergizi)", "Danantara", "Efisiensi anggaran"])
    bebas = c2.text_input("Kata bebas (pisahkan koma)", "",
                          help="Contoh: nikel, pajak. Dihitung sebagai satu kelompok.")
    per = c3.radio("Satuan", ["Harian", "Bulanan"], horizontal=True)
    o1, o2, o3 = st.columns(3)
    rata7 = o1.toggle("Rata-rata bergerak 7 hari", value=True, disabled=(per == "Bulanan"))
    tindih = o2.toggle("Tampilkan IHSG", value=True)
    tandai = o3.toggle("Tandai peristiwa penting", value=True)

    kelompok = list(db.kelompok_dari(db.TOPIK, pilih))
    kata_bebas = [x.strip() for x in bebas.split(",") if x.strip()]
    if kata_bebas:
        kelompok.append(("Kata bebas: " + ", ".join(kata_bebas), tuple(kata_bebas)))

    if not kelompok:
        st.info("Pilih minimal satu topik atau isi kata bebas.")
    else:
        t = db.tren_kata(f2, tuple(kelompok), "hari" if per == "Harian" else "bulan")
        t = t.groupby(["waktu", "grup"])["jumlah"].sum().reset_index()
        if t["jumlah"].sum() == 0:
            st.info("Tidak ada judul yang cocok dengan topik/kata ini pada rentang terpilih.")
        else:
            lebar = t.pivot(index="waktu", columns="grup", values="jumlah").fillna(0)
            if per == "Harian":
                lebar = lebar.reindex(pd.date_range(awal, akhir), fill_value=0)
                if rata7:
                    lebar = lebar.rolling(7, min_periods=1).mean()
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            for i, kol in enumerate(lebar.columns):
                fig.add_trace(go.Scatter(x=lebar.index, y=lebar[kol], mode="lines", name=kol,
                                         line=dict(width=2.4, color=ui.WARNA[i % len(ui.WARNA)])),
                              secondary_y=False)
            if tindih and not ih.empty:
                fig.add_trace(go.Scatter(x=ih["tanggal"], y=ih["close"], mode="lines",
                                         name="IHSG", line=dict(color="#9A9DB0", width=1.5,
                                                                dash="dot")),
                              secondary_y=True)
            if tandai:
                for tgl, nama in db.PERISTIWA:
                    tt = pd.Timestamp(tgl)
                    if awal <= tt <= akhir:
                        fig.add_shape(type="line", x0=tt, x1=tt, xref="x", y0=0, y1=1,
                                      yref="paper", line=dict(color=ui.REDUP, width=1,
                                                              dash="dot"))
                        fig.add_annotation(x=tt, xref="x", y=1, yref="paper", text=nama,
                                           textangle=-90, showarrow=False, xanchor="right",
                                           yanchor="top", font=dict(size=10, color=ui.REDUP))
            fig.update_yaxes(title_text="Jumlah berita", secondary_y=False)
            fig.update_yaxes(title_text="IHSG", secondary_y=True, showgrid=False)
            fig.update_layout(hovermode="x unified")
            with ui.kartu("Tren topik dan IHSG"):
                ui.tampil(fig, 440)
            tot = t.groupby("grup")["jumlah"].sum().sort_values(ascending=False)
            st.caption("Total judul yang cocok: " + "; ".join(
                f"{n}: {ui.angka(v)}" for n, v in tot.items()))

    st.markdown("#### Studi peristiwa")
    st.caption("Pergerakan IHSG beberapa hari bursa sebelum dan sesudah sebuah peristiwa. "
               "Hari 0 = hari bursa pertama pada atau setelah tanggal peristiwa. Tanggal "
               "peristiwa bisa disesuaikan di db.py.")
    s1, s2 = st.columns([3, 1])
    nama_p = s1.selectbox("Peristiwa", [f"{db._tgl(t)}: {n}" for t, n in db.PERISTIWA])
    jendela = s2.slider("Jendela (hari bursa)", 3, 10, 5)
    tgl_p = db.PERISTIWA[[f"{db._tgl(t)}: {n}" for t, n in db.PERISTIWA].index(nama_p)][0]
    w = db.studi_peristiwa(ihsg, tgl_p, jendela)
    if w.empty:
        st.info("Tidak ada data IHSG pada sekitar tanggal ini.")
    else:
        a, b = st.columns([3, 2])
        with a:
            with ui.kartu("Indeks IHSG (hari -1 = 100)"):
                fg = go.Figure(go.Scatter(x=w["hari"], y=w["indeks"], mode="lines+markers",
                                          line=dict(color=ui.LAVENDER_TUA, width=2.5),
                                          marker=dict(size=7)))
                fg.add_vline(x=0, line_dash="dot", line_color=ui.REDUP)
                fg.update_layout(xaxis_title="Hari bursa terhadap peristiwa",
                                 yaxis_title="Indeks")
                ui.tampil(fg, 330)
        with b:
            tb = w.copy()
            tb["tanggal"] = tb["tanggal"].dt.date
            st.dataframe(tb.rename(columns={"hari": "Hari", "tanggal": "Tanggal",
                                            "close": "Penutupan", "indeks": "Indeks",
                                            "return_pct": "Return (%)"}).round(2),
                         hide_index=True)

# ======================================
# TAB 4: kata pada judul
# ======================================
with tab4:
    st.caption("Kata yang sering muncul pada judul di hari IHSG naik vs turun. Kata umum dan "
               "kata bukan isi berita (video, foto, simak, dst.) sudah disaring. Daftar "
               "penyaring ada di db.py (STOPWORD).")
    if st.toggle("Hitung analisis kata", value=False,
                 help="Memproses semua judul pada filter; bisa memakan beberapa detik."):
        kata, n = db.kata_naik_turun(f, geser)
        kata = db.bersihkan_kata(kata)
        if kata.empty:
            st.info("Tidak ada judul yang cocok dengan filter.")
        else:
            kol = st.columns(2)
            for k_, (arah, nama, warna) in zip(kol, [("naik", "Hari naik", ui.LIME_TUA),
                                                      ("turun", "Hari turun", ui.LAVENDER_TUA)]):
                top = (kata[kata["arah"] == arah].nlargest(15, "jumlah")
                       .rename(columns={"kata": "Kata", "jumlah": "Jumlah"}))
                with k_:
                    with ui.kartu(f"{nama} ({ui.angka(n.get(arah, 0))} judul)"):
                        if top.empty:
                            st.info("Tidak ada data.")
                        else:
                            gb = px.bar(top.iloc[::-1], x="Jumlah", y="Kata", orientation="h",
                                        color_discrete_sequence=[warna])
                            ui.tampil(gb, 430)
            khas_t = db.kata_khas(kata, "arah", "turun", "naik")
            khas_n = db.kata_khas(kata, "arah", "naik", "turun")
            st.markdown("**Kata yang lebih khas** (muncul minimal 30 kali di kedua kelompok)")
            d1, d2 = st.columns(2)
            if not khas_t.empty:
                d1.markdown("Lebih khas di **hari turun**")
                d1.dataframe(khas_t[["turun", "naik"]].rename(
                    columns={"turun": "Hari turun", "naik": "Hari naik"}))
                d2.markdown("Lebih khas di **hari naik**")
                d2.dataframe(khas_n[["naik", "turun"]].rename(
                    columns={"turun": "Hari turun", "naik": "Hari naik"}))
            else:
                st.info("Kata terlalu sedikit untuk dibandingkan pada filter ini.")