import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import db
import ui

ui.judul("IHSG", "Harga harian indeks ^JKSE (Yahoo Finance) selama pemerintahan Prabowo")

f = db.filter_aktif()
awal, akhir = pd.Timestamp(f["awal"]), pd.Timestamp(f["akhir"])
ihsg = db.muat_ihsg()
ih = ihsg[(ihsg["tanggal"] >= awal) & (ihsg["tanggal"] <= akhir)].copy()
if ih.empty:
    st.info("Tidak ada data IHSG pada rentang ini.")
    st.stop()

# ---- Kartu angka ----
h = ih.dropna(subset=["return_pct"])
k = st.columns(4)
kum = (ih["close"].iloc[-1] / ih["close"].iloc[0] - 1) * 100 if len(ih) >= 2 else 0
ui.kartu_angka(k[0], "Penutupan terakhir", ui.angka(ih["close"].iloc[-1]),
               f"{kum:+.2f}%", "naik" if kum >= 0 else "turun", gaya="lime",
               ket="perubahan sejak awal rentang")
ui.kartu_angka(k[1], "Hari bursa", len(ih))
ui.kartu_angka(k[2], "Rata-rata return harian", f"{h['return_pct'].mean():.3f}%" if len(h) else "-")
ui.kartu_angka(k[3], "Volatilitas (simpangan baku)",
               f"{h['return_pct'].std():.2f}%" if len(h) > 1 else "-")
st.write("")

tab1, tab2, tab3 = st.tabs(["Grafik harga", "Return harian", "Rapor per 100 hari"])

# ======================================
# TAB 1: grafik harga
# ======================================
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    gran = c1.radio("Granularitas", ["Harian", "Mingguan", "Bulanan"], horizontal=True)
    jenis = c2.radio("Jenis grafik", ["Garis", "Candlestick"], horizontal=True)
    tampil_volume = c3.toggle("Tampilkan volume", value=False)
    penanda = c4.toggle("Tandai peristiwa penting", value=False,
                        help="Daftar peristiwa ada di db.py (PERISTIWA), bisa kamu ubah.")


    def agregasi(df, gran):
        if gran == "Harian":
            return df
        aturan = "W" if gran == "Mingguan" else "MS"
        out = (df.set_index("tanggal").resample(aturan)
                 .agg({"open": "first", "high": "max", "low": "min",
                       "close": "last", "volume": "sum"})
                 .dropna(subset=["close"]).reset_index())
        out["return_pct"] = out["close"].pct_change() * 100
        return out


    g = agregasi(ih, gran)
    n_baris = 1 + int(tampil_volume)
    fig = make_subplots(rows=n_baris, cols=1, shared_xaxes=True,
                        row_heights=[0.7, 0.3][:n_baris], vertical_spacing=0.03)
    if jenis == "Candlestick":
        fig.add_trace(go.Candlestick(x=g["tanggal"], open=g["open"], high=g["high"],
                                     low=g["low"], close=g["close"], name="IHSG",
                                     increasing_line_color=ui.NAIK,
                                     decreasing_line_color=ui.TURUN), row=1, col=1)
        fig.update_layout(xaxis_rangeslider_visible=False)
    else:
        fig.add_trace(go.Scatter(x=g["tanggal"], y=g["close"], mode="lines", name="IHSG",
                                 line=dict(color=ui.LAVENDER_TUA, width=2.5),
                                 fill="tozeroy", fillcolor="rgba(184,189,251,0.25)"),
                      row=1, col=1)
        lo, hi = g["close"].min(), g["close"].max()
        fig.update_yaxes(range=[lo * 0.97, hi * 1.02], row=1, col=1)
    fig.update_yaxes(title_text="IHSG", row=1, col=1)
    if tampil_volume:
        fig.add_trace(go.Bar(x=g["tanggal"], y=g["volume"], name="Volume",
                             marker_color=ui.LIME_TUA), row=2, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
    if penanda:
        for tgl, nama in db.PERISTIWA:
            t = pd.Timestamp(tgl)
            if awal <= t <= akhir:
                fig.add_shape(type="line", x0=t, x1=t, xref="x", y0=0, y1=1, yref="paper",
                              line=dict(color=ui.REDUP, width=1, dash="dot"))
                fig.add_annotation(x=t, xref="x", y=1, yref="paper", text=nama, textangle=-90,
                                   showarrow=False, xanchor="right", yanchor="top",
                                   font=dict(size=10, color=ui.REDUP))
    fig.update_layout(hovermode="x unified", showlegend=False)
    with ui.kartu("Pergerakan IHSG"):
        ui.tampil(fig, 320 + 150 * n_baris)

    st.markdown("#### Insight IHSG")
    ui.kartu_insight(db.insight_ihsg(ih), per_baris=4)

# ======================================
# TAB 2: return harian
# ======================================
with tab2:
    d1, d2 = st.columns(2)
    arah = d1.selectbox("Arah hari", ["Semua", "Hanya naik", "Hanya turun"])
    ambang = d2.slider("Ambang |return| minimal (%)", 0.0, 5.0, 0.0, 0.25)
    hh = h.copy()
    if arah == "Hanya naik":
        hh = hh[hh["return_pct"] > 0]
    elif arah == "Hanya turun":
        hh = hh[hh["return_pct"] < 0]
    hh = hh[hh["return_pct"].abs() >= ambang]

    if hh.empty:
        st.info("Tidak ada hari yang memenuhi filter ini.")
    else:
        m = st.columns(4)
        ui.kartu_angka(m[0], "Jumlah hari", len(hh))
        ui.kartu_angka(m[1], "Rata-rata return", f"{hh['return_pct'].mean():.3f}%")
        ui.kartu_angka(m[2], "Simpangan baku",
                       f"{hh['return_pct'].std():.3f}%" if len(hh) > 1 else "-")
        ui.kartu_angka(m[3], "Hari naik / turun",
                       f"{(hh['return_pct'] > 0).sum()} / {(hh['return_pct'] < 0).sum()}")
        st.write("")
        a, b = st.columns([3, 2])
        with a:
            with ui.kartu("Sebaran return harian"):
                hist = px.histogram(hh, x="return_pct", nbins=40,
                                    labels={"return_pct": "Return harian (%)"},
                                    color_discrete_sequence=[ui.LAVENDER_TUA])
                hist.update_layout(yaxis_title="Jumlah hari", bargap=0.05)
                ui.tampil(hist, 320)
        with b:
            with ui.kartu("Naik vs turun"):
                n_n, n_t = int((hh["return_pct"] > 0).sum()), int((hh["return_pct"] < 0).sum())
                dn = go.Figure(go.Pie(labels=["Naik", "Turun"], values=[n_n, n_t], hole=0.62,
                                      marker_colors=[ui.LIME_TUA, ui.LAVENDER_TUA],
                                      textinfo="percent"))
                ui.tampil(dn, 320)
        tabel = hh.assign(abs_ret=hh["return_pct"].abs()).sort_values("abs_ret", ascending=False)
        tabel = tabel[["tanggal", "close", "return_pct"]].head(50)
        tabel["tanggal"] = tabel["tanggal"].dt.date
        st.markdown("**50 hari dengan |return| terbesar**")
        st.dataframe(tabel.rename(columns={"close": "Penutupan", "return_pct": "Return (%)"}),
                     hide_index=True)

# ======================================
# TAB 3: rapor per 100 hari
# ======================================
with tab3:
    st.caption("Ringkasan per 100 hari sejak pelantikan (20 Oktober 2024). Tabel ini selalu "
               "memakai seluruh data, tidak terpengaruh filter di sidebar.")
    semua = db.berita_harian({"awal": db.START, "akhir": db.END, "sumber": (), "tema": (),
                              "kata": "", "mode": "Salah satu kata"})
    rapor = db.rapor_periode(ihsg, semua, 100)
    st.dataframe(rapor, hide_index=True)
    if not rapor.empty:
        fig = px.bar(rapor, x="Periode", y="Perubahan IHSG (%)",
                     color=rapor["Perubahan IHSG (%)"] >= 0,
                     color_discrete_map={True: ui.LIME_TUA, False: ui.LAVENDER_TUA})
        fig.update_layout(showlegend=False)
        with ui.kartu("Perubahan IHSG per 100 hari"):
            ui.tampil(fig, 320)