"""
app.py – Entry point CueUp Streamlit.

Rulare:
    streamlit run src/app.py
"""

import sys
import os

# Adaugă directorul src/ în path pentru importuri relative
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

st.set_page_config(
    page_title="CueUp – Biliard România",
    page_icon="🎱",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── CSS Global ────────────────────────────────────────────────────────────────
def _inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        /* ── Reset & bază ── */
        html, body, [class*="css"], [class*="st-"] {
            font-family: 'Inter', sans-serif !important;
        }
        .stApp {
            background: #070d1a !important;
        }
        /* Ascunde elemente Streamlit implicite */
        #MainMenu, footer, header { visibility: hidden !important; }
        .stDeployButton { display: none !important; }
        /* Ascunde navigarea automată generată de Streamlit pentru pages/ */
        [data-testid="stSidebarNav"] { display: none !important; }
        /* Ascunde butonul keyboard shortcuts din colțul stânga-sus */
        [data-testid="stToolbar"],
        [data-testid="stToolbarActions"],
        .stToolbar,
        button[kind="header"] { display: none !important; }

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0c1526 0%, #08101e 100%) !important;
            border-right: 1px solid rgba(26,122,74,.22) !important;
        }
        [data-testid="stSidebar"] * {
            color: #c4d4e8 !important;
        }

        /* ── Butoane ── */
        .stButton > button {
            background: linear-gradient(135deg, #1a7a4a 0%, #0e5232 100%) !important;
            color: #fff !important;
            border: none !important;
            border-radius: 9px !important;
            font-weight: 600 !important;
            font-size: .88rem !important;
            letter-spacing: .02em !important;
            padding: .52rem 1.3rem !important;
            transition: all .25s ease !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #22a05f 0%, #1a7a4a 100%) !important;
            box-shadow: 0 6px 22px rgba(26,122,74,.45) !important;
            transform: translateY(-2px) !important;
        }
        .stButton > button:active {
            transform: translateY(0) !important;
        }

        /* ── Inputs ── */
        .stTextInput input,
        .stSelectbox [data-baseweb="select"] > div,
        .stDateInput input {
            background: rgba(255,255,255,.05) !important;
            border: 1px solid rgba(26,122,74,.35) !important;
            border-radius: 8px !important;
            color: #e8edf5 !important;
        }
        .stTextInput input:focus {
            border-color: #1a7a4a !important;
            box-shadow: 0 0 0 2px rgba(26,122,74,.22) !important;
        }
        /* Labels */
        .stTextInput label, .stSelectbox label,
        .stDateInput label, .stSlider label,
        .stRadio label { color: #9eafc0 !important; font-size:.84rem !important; }

        /* ── Metrics ── */
        [data-testid="stMetric"] {
            background: rgba(26,122,74,.1) !important;
            border: 1px solid rgba(26,122,74,.28) !important;
            border-radius: 13px !important;
            padding: 1rem 1.2rem !important;
        }
        [data-testid="stMetricValue"] {
            color: #d4af37 !important;
            font-size: 1.75rem !important;
            font-weight: 800 !important;
        }
        [data-testid="stMetricLabel"] { color: #9eafc0 !important; }
        [data-testid="stMetricDelta"]  { color: #6a9fc0 !important; font-size:.78rem !important; }

        /* ── DataFrame ── */
        [data-testid="stDataFrame"] {
            border: 1px solid rgba(26,122,74,.22) !important;
            border-radius: 12px !important;
            overflow: hidden !important;
        }

        /* ── Tabs ── */
        .stTabs [data-baseweb="tab-list"] {
            background: rgba(255,255,255,.03) !important;
            border-radius: 12px !important;
            padding: 4px !important;
            gap: 4px !important;
        }
        .stTabs [data-baseweb="tab"] {
            color: #6a8099 !important;
            font-weight: 500 !important;
            border-radius: 8px !important;
            padding: .45rem 1rem !important;
        }
        .stTabs [aria-selected="true"] {
            background: rgba(26,122,74,.18) !important;
            color: #d4af37 !important;
        }

        /* ── Alerts ── */
        .stSuccess  {
            background: rgba(26,122,74,.13) !important;
            border: 1px solid rgba(26,122,74,.45) !important;
            border-radius: 9px !important;
            color: #b2f5c4 !important;
        }
        .stError {
            background: rgba(200,50,50,.1) !important;
            border: 1px solid rgba(200,50,50,.4) !important;
            border-radius: 9px !important;
        }
        .stInfo {
            background: rgba(30,80,160,.1) !important;
            border: 1px solid rgba(30,80,160,.35) !important;
            border-radius: 9px !important;
        }
        .stWarning {
            background: rgba(212,175,55,.08) !important;
            border: 1px solid rgba(212,175,55,.35) !important;
            border-radius: 9px !important;
        }

        /* ── Slider ── */
        [data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
            background: #1a7a4a !important;
            border-color: #d4af37 !important;
        }
        [data-testid="stSlider"] [data-baseweb="slider"] [data-testid="stTickBarMin"],
        [data-testid="stSlider"] [data-baseweb="slider"] [data-testid="stTickBarMax"] {
            color: #6a8099 !important;
        }

        /* ── Scrollbar ── */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: rgba(255,255,255,.03); }
        ::-webkit-scrollbar-thumb {
            background: rgba(26,122,74,.4);
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover { background: rgba(26,122,74,.65); }
        </style>
        """,
        unsafe_allow_html=True,
    )


_inject_css()

# ── Session state ─────────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "clasament"
if "user" not in st.session_state:
    st.session_state.user = None

# ── Dacă nu e autentificat → login ────────────────────────────────────────────
if not st.session_state.logged_in:
    from pages.login import show
    show()
    st.stop()

# ── Sidebar navigare ──────────────────────────────────────────────────────────
user = st.session_state.user

with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center;padding:1.4rem 0 1.8rem;">
            <div style="font-size:2.8rem;">🎱</div>
            <div style="font-size:1.5rem;font-weight:900;
                        background:linear-gradient(135deg,#d4af37,#f5d87a);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                        letter-spacing:.05em;margin-top:4px;">CueUp</div>
            <div style="font-size:.72rem;color:#4a6070;letter-spacing:.07em;margin-top:2px;">
                BILIARD · ROMÂNIA
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Card utilizator curent
    st.markdown(
        f"""
        <div style="background:rgba(26,122,74,.12);border:1px solid rgba(26,122,74,.28);
                    border-radius:12px;padding:14px;margin-bottom:18px;text-align:center;">
            <div style="font-size:.78rem;color:#6a8099;margin-bottom:2px;">Bun venit,</div>
            <div style="font-weight:700;color:#e8edf5;font-size:1rem;">{user['nume']}</div>
            <div style="font-size:.78rem;color:#d4af37;margin-top:5px;font-weight:600;">
                ELO {user['rating_elo']}
            </div>
            <div style="font-size:.74rem;color:#6a8099;margin-top:3px;">
                📍 {user.get('nume_oras','–')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav = [
        ("🏆", "Clasament",           "clasament"),
        ("🤝", "Găsește Parteneri",   "parteneri"),
        ("📅", "Rezervă Masă",        "rezervari"),
        ("👤", "Profilul Meu",        "profil"),
    ]

    for icon, label, key in nav:
        active  = st.session_state.page == key
        btn_style = "" if not active else "border: 1px solid rgba(212,175,55,.5) !important;"
        if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key
            st.rerun()

    st.markdown(
        "<hr style='border-color:rgba(26,122,74,.15);margin:16px 0;'>",
        unsafe_allow_html=True,
    )

    if st.button("🚪  Deconectare", key="logout", use_container_width=True):
        for k in ["logged_in", "user", "page", "partners_df",
                  "mese_dispo", "rez_params"]:
            st.session_state.pop(k, None)
        st.session_state.logged_in = False
        st.session_state.page = "clasament"
        st.rerun()

# ── Rutare pagini ─────────────────────────────────────────────────────────────
page = st.session_state.page

if page == "clasament":
    from pages.clasament  import show; show()
elif page == "parteneri":
    from pages.parteneri  import show; show()
elif page == "rezervari":
    from pages.rezervari  import show; show()
elif page == "profil":
    from pages.profil     import show; show()
else:
    from pages.clasament  import show; show()
