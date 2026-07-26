"""app_pages/parteneri.py - Gasire parteneri de joc din acelasi oras, cu ELO apropiat."""

import pandas as pd
import streamlit as st

from db import cauta_parteneri
from ui import antet, badge_elo_diferenta, nivel_text

PE_PAGINA = 9  # 3 randuri x 3 carduri

user = st.session_state.user
elo_meu = int(user["rating_elo"])
id_oras = int(user["id_oras"])
oras = user.get("nume_oras", "orasul tau")

antet("Parteneri de joc", f"Jucatori din {oras} cu un nivel apropiat de al tau",
      ":material/handshake:")

# ── Filtre ────────────────────────────────────────────────────────────────────
with st.form("filtre_parteneri", border=True):
    coloana_slider, coloana_nivel = st.columns([3, 2], vertical_alignment="bottom")

    with coloana_slider:
        toleranta = st.slider(
            "Diferenta maxima de ELO fata de tine",
            min_value=25, max_value=600, value=150, step=25,
            help="150 inseamna adversari intre "
                 f"{max(800, elo_meu - 150)} si {elo_meu + 150} ELO.",
        )
    with coloana_nivel:
        niveluri = st.pills(
            "Nivel declarat", options=[1, 2, 3, 4, 5],
            selection_mode="multi",
            format_func=lambda n: nivel_text(n),
        )

    cauta = st.form_submit_button("Cauta parteneri", icon=":material/search:",
                                  type="primary")

elo_min = max(800, elo_meu - toleranta)
elo_max = elo_meu + toleranta

# Cautam la prima intrare pe pagina si apoi la fiecare apasare pe buton.
if cauta or "parteneri_df" not in st.session_state:
    try:
        st.session_state.parteneri_df = cauta_parteneri(
            id_oras=id_oras,
            elo_min=elo_min,
            elo_max=elo_max,
            exclude_id=int(user["id_jucator"]),
        )
    except Exception:
        st.error("Cautarea a esuat. Verifica legatura cu baza de date.",
                 icon=":material/cloud_off:")
        st.stop()

df: pd.DataFrame = st.session_state.get("parteneri_df", pd.DataFrame())

if niveluri and not df.empty:
    df = df[df["nivel_declarat"].isin(niveluri)]

if df.empty:
    st.info("Niciun jucator nu se potriveste criteriilor. Mareste intervalul de ELO.",
            icon=":material/search_off:")
    st.stop()

# ── Sumar ─────────────────────────────────────────────────────────────────────
apropiati = int((df["rating_elo"].astype(int) - elo_meu).abs().le(50).sum())

with st.container(horizontal=True):
    st.metric("Jucatori gasiti", len(df), border=True)
    st.metric("Potriviri foarte bune", apropiati,
              delta_description="diferenta sub 50 ELO", border=True)
    st.metric("Interval cautat", f"{elo_min}–{elo_max}",
              delta_description="rating ELO", border=True)

# ── Rezultate paginate, 3 carduri pe rand ─────────────────────────────────────
nr_pagini = max(1, (len(df) + PE_PAGINA - 1) // PE_PAGINA)
grila = st.container()

with st.container(horizontal_alignment="right"):
    pagina = st.pagination(nr_pagini, key="parteneri_pagina")

felie = df.iloc[(pagina - 1) * PE_PAGINA: pagina * PE_PAGINA]

with grila:
    for start in range(0, len(felie), 3):
        for coloana, (_, jucator) in zip(
            st.columns(3), felie.iloc[start:start + 3].iterrows()
        ):
            diferenta = int(jucator["rating_elo"]) - elo_meu
            with coloana.container(border=True, height="stretch"):
                st.markdown(f"**{jucator['nume']}**")
                st.markdown(
                    f":orange-badge[:material/bolt: {int(jucator['rating_elo'])}] "
                    f"{badge_elo_diferenta(diferenta)}"
                )
                st.caption(f":material/target: {nivel_text(jucator['nivel_declarat'])}")
                st.caption(f":material/mail: {jucator['email']}")
