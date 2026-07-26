"""
app.py - Entry point CueUp.

Rulare (din radacina proiectului, ca .env sa fie gasit):
    streamlit run src/app.py

Navigarea se face cu st.navigation + st.Page peste folderul app_pages/.
Folderul NU se poate numi `pages/`: acel nume este rezervat de mecanismul vechi
de multipage al Streamlit, care ar prelua rutarea si ar afisa mereu aceeasi
pagina, ignorand navigarea proprie.
"""

import os
import sys

# Permite `from db import ...` din paginile aflate in app_pages/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

st.set_page_config(
    page_title="CueUp - biliard Romania",
    page_icon="🎱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Stare partajata intre pagini ──────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

# ── Nefautentificat -> doar pagina de login, fara meniu ───────────────────────
if not st.session_state.logged_in:
    st.navigation(
        [st.Page("app_pages/login.py", title="Autentificare")],
        position="hidden",
    ).run()
    st.stop()

# ── Navigare ──────────────────────────────────────────────────────────────────
user = st.session_state.user

# Lista plata, fara sectiuni: sectiunile din st.navigation se pot plia la click
# si ar ascunde pagini.
pagina = st.navigation(
    [
        st.Page("app_pages/home.py", title="Acasa",
                icon=":material/home:", default=True),
        st.Page("app_pages/clasament.py", title="Clasament",
                icon=":material/trophy:"),
        st.Page("app_pages/parteneri.py", title="Parteneri",
                icon=":material/handshake:"),
        st.Page("app_pages/rezervari.py", title="Rezerva o masa",
                icon=":material/event_available:"),
        st.Page("app_pages/profil.py", title="Profilul meu",
                icon=":material/person:"),
    ],
    position="sidebar",
    expanded=True,
)

# ── Card utilizator + deconectare, sub meniu ──────────────────────────────────
with st.sidebar:
    with st.container(border=True):
        st.markdown(f"**{user['nume']}**")
        st.caption(f":material/location_on: {user.get('nume_oras', '–')}")
        st.markdown(
            f":orange-badge[:material/bolt: ELO {int(user['rating_elo'])}]"
        )

    if st.button("Deconectare", icon=":material/logout:", width="stretch"):
        for cheie in ["logged_in", "user", "parteneri_df", "mese_dispo",
                      "rez_params", "sfat_ai"]:
            st.session_state.pop(cheie, None)
        st.session_state.logged_in = False
        st.rerun()

pagina.run()
