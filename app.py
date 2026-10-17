import streamlit as st

import db
import ui

st.set_page_config(page_title="Berita dan IHSG", page_icon="📈", layout="wide")
ui.pasang_css()

halaman = st.navigation([
    st.Page("halaman/hubungan.py", title="Hubungan Berita dan IHSG",
            icon=":material/insights:", default=True),
    st.Page("halaman/berita.py", title="Berita", icon=":material/newspaper:"),
    st.Page("halaman/ihsg.py", title="IHSG", icon=":material/show_chart:"),
    st.Page("halaman/tentang.py", title="Tentang Data", icon=":material/info:"),
])

db.sidebar_filter()   # filter digambar sekali, berlaku di semua halaman
halaman.run()