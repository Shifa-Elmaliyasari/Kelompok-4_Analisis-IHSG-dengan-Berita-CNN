import re

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ==============================
# PALET WARNA (mengikuti dashboard contoh, selalu mode terang)
# ==============================

BG = "#F3F4F9"
KARTU = "#FFFFFF"
TEKS = "#1A1A22"
REDUP = "#7B7F95"
GARIS = "#ECEEF6"
LIME = "#D6F44A"
LIME_TUA = "#B7DB1F"
LAVENDER = "#B8BDFB"
LAVENDER_TUA = "#7C83F0"
NAIK = "#2E9E5B"
TURUN = "#E5484D"

# urutan warna untuk grafik kategori (CNN = lavender, CNBC = lime, sesuai contoh)
WARNA = [LAVENDER_TUA, LIME_TUA, "#3FC1B0", "#FFA95C", "#F48FB1", "#6EC1F5", "#8E6CE0",
         "#F2D14C", "#F2766B", "#2E3270", "#8FB339", "#B5B8C8", "#5B63D6"]
WARNA_SUMBER = {"CNN": LAVENDER_TUA, "CNBC": LIME_TUA}


def _daftarkan_template():
    t = go.layout.Template()
    t.layout = go.Layout(
        font=dict(family="Plus Jakarta Sans, Segoe UI, Arial, sans-serif", color=TEKS, size=13),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", colorway=WARNA,
        xaxis=dict(gridcolor=GARIS, linecolor=GARIS, zerolinecolor=GARIS, title_font_size=12,
                   automargin=True),
        yaxis=dict(gridcolor=GARIS, linecolor=GARIS, zerolinecolor=GARIS, title_font_size=12,
                   automargin=True),
        legend=dict(orientation="h", y=1.12, x=0, bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=30, b=20, l=10, r=10),
        hoverlabel=dict(bgcolor="#FFFFFF", font_color=TEKS, bordercolor=GARIS),
    )
    pio.templates["dashboard"] = t
    pio.templates.default = "dashboard"


_daftarkan_template()


# ==============================
# CSS
# ==============================

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
:root {{ color-scheme: light; }}
html, body, .stApp, [class*="css"] {{
    font-family: 'Plus Jakarta Sans', 'Segoe UI', Arial, sans-serif;
}}
.stApp {{ background: {BG}; color: {TEKS}; }}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.8rem; padding-bottom: 3rem; max-width: 1400px; }}

/* sidebar */
[data-testid="stSidebar"] {{ background: {KARTU}; border-right: 1px solid {GARIS}; }}
[data-testid="stSidebarNav"]::before {{
    content: "Berita & IHSG"; display: block; font-weight: 700; font-size: 1.25rem;
    padding: 0.4rem 0.8rem 1rem 2.1rem; position: relative; color: {TEKS};
}}
[data-testid="stSidebarNav"]::after {{
    content: ""; position: absolute; left: 0.9rem; top: 0.75rem; width: 14px; height: 14px;
    border-radius: 4px; background: linear-gradient({LIME} 50%, {LAVENDER} 50%);
}}
[data-testid="stSidebarNav"] {{ position: relative; }}
[data-testid="stSidebarNavLink"] {{ border-radius: 10px; margin-bottom: 2px; }}
[data-testid="stSidebarNavLink"][aria-current="page"] {{
    background: {LAVENDER}; font-weight: 600;
}}
[data-testid="stSidebarNavLink"]:hover {{ background: #E9EBFF; }}

/* judul halaman */
.judul {{ background: {KARTU}; border-radius: 16px; padding: 18px 24px; margin-bottom: 18px; }}
.judul h1 {{ font-size: 1.6rem; font-weight: 700; margin: 0; padding: 0; }}
.judul p {{ color: {REDUP}; margin: 4px 0 0 0; font-size: 0.9rem; }}

/* kartu angka */
.kpi {{ background: {KARTU}; border-radius: 16px; padding: 16px 20px; height: 100%; }}
.kpi.lime {{ background: {LIME}; }}
.kpi.lav {{ background: {LAVENDER}; }}
.kpi .lbl {{ font-size: 0.85rem; font-weight: 500; color: {REDUP}; }}
.kpi.lime .lbl, .kpi.lav .lbl {{ color: #3b3f2a; }}
.kpi .val {{ font-size: 1.9rem; font-weight: 700; line-height: 1.25; margin-top: 2px; }}
.chip {{ display: inline-block; font-size: 0.72rem; font-weight: 600; padding: 2px 8px;
         border-radius: 6px; background: #E6F6EC; color: {NAIK}; margin-left: 6px;
         vertical-align: middle; }}
.chip.neg {{ background: #FDE8E8; color: {TURUN}; }}
.chip.net {{ background: {GARIS}; color: {REDUP}; }}
.kpi .ket {{ font-size: 0.78rem; color: {REDUP}; margin-top: 2px; }}
.kpi.lime .ket, .kpi.lav .ket {{ color: #3b3f2a; }}

/* kartu insight */
.ins {{ background: {KARTU}; border-radius: 14px; padding: 14px 18px; height: 100%;
        border-left: 5px solid {LAVENDER_TUA}; }}
.ins.b {{ border-left-color: {LIME_TUA}; }}
.ins .t {{ font-size: 0.8rem; font-weight: 600; color: {REDUP}; }}
.ins .v {{ font-size: 1.25rem; font-weight: 700; margin: 2px 0; line-height: 1.3; }}
.ins .k {{ font-size: 0.8rem; color: {REDUP}; line-height: 1.4; }}

/* kartu grafik (container ber-key "kartu_...") */
[class*="st-key-kartu"] {{ background: {KARTU}; border-radius: 16px; padding: 18px 22px;
                            box-shadow: 0 1px 2px rgba(20,20,50,0.04); }}
[class*="st-key-kartu"] h4 {{ margin: 0 0 6px 0; font-size: 1.05rem; font-weight: 600; }}
.cat {{ font-size: 0.82rem; color: {REDUP}; margin: 0 0 8px 0; }}

/* tab, tombol */
button[data-baseweb="tab"] {{ font-weight: 600; }}
[data-testid="stDownloadButton"] button, .stButton button {{
    border-radius: 10px; border: 1px solid {GARIS}; background: {KARTU}; }}
[data-testid="stMetric"] {{ background: {KARTU}; border-radius: 14px; padding: 12px 16px; }}
</style>
"""


def pasang_css():
    st.markdown(CSS, unsafe_allow_html=True)


# ==============================
# KOMPONEN
# ==============================

def judul(teks, sub=""):
    sub_html = f"<p>{sub}</p>" if sub else ""
    st.markdown(f'<div class="judul"><h1>{teks}</h1>{sub_html}</div>', unsafe_allow_html=True)


def kartu_angka(kolom, label, nilai, delta=None, arah=None, gaya="", ket=""):
    """arah: 'naik' / 'turun' / None untuk warna chip. gaya: '', 'lime', 'lav'."""
    chip = ""
    if delta:
        kelas = {"naik": "", "turun": " neg"}.get(arah, " net")
        chip = f'<span class="chip{kelas}">{delta}</span>'
    ket_html = f'<div class="ket">{ket}</div>' if ket else ""
    kolom.markdown(f'<div class="kpi {gaya}"><div class="lbl">{label}</div>'
                   f'<div class="val">{nilai}{chip}</div>{ket_html}</div>',
                   unsafe_allow_html=True)


def kartu_insight(daftar, per_baris=3):
    """daftar: [(judul, nilai, keterangan)]. Digambar sebagai kisi kartu."""
    for i in range(0, len(daftar), per_baris):
        kolom = st.columns(per_baris)
        for j, (t, v, k) in enumerate(daftar[i:i + per_baris]):
            kelas = "ins b" if (i // per_baris + j) % 2 else "ins"
            kolom[j].markdown(f'<div class="{kelas}"><div class="t">{t}</div>'
                              f'<div class="v">{v}</div><div class="k">{k}</div></div>',
                              unsafe_allow_html=True)


def kartu(judul_kartu, catatan=""):
    """Container bergaya kartu putih. Pakai: `with ui.kartu("Judul"):`."""
    slug = re.sub(r"[^a-z0-9]+", "_", judul_kartu.lower()).strip("_")[:40]
    c = st.container(key=f"kartu_{slug}")
    c.markdown(f"#### {judul_kartu}")
    if catatan:
        c.markdown(f'<p class="cat">{catatan}</p>', unsafe_allow_html=True)
    return c


def tampil(fig, tinggi=360, **kw):
    """Tampilkan grafik Plotly dengan warna dari palet ini (bukan tema Streamlit)."""
    fig.update_layout(height=tinggi, paper_bgcolor=KARTU, plot_bgcolor=KARTU)
    try:
        st.plotly_chart(fig, theme=None, width="stretch", **kw)
    except TypeError:
        st.plotly_chart(fig, theme=None, use_container_width=True, **kw)


def angka(n):
    return f"{int(round(n)):,}".replace(",", ".")