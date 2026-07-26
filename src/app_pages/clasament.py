"""app_pages/clasament.py - Clasament ELO + pozitia jucatorului in oras si national."""

import pandas as pd
import streamlit as st

from db import (
    clasament_jucatori_activi,
    get_count_city,
    get_count_national,
    get_rank_in_city,
    get_rank_national,
    orase_active,
)
from ui import MEDALII, antet, nivel_text

user = st.session_state.user
elo = int(user["rating_elo"])
id_oras = int(user["id_oras"])
oras = user.get("nume_oras", "orasul tau")

antet("Clasament", "Unde te situezi fata de ceilalti jucatori CueUp",
      ":material/trophy:")

# ── Randul de indicatori ──────────────────────────────────────────────────────
try:
    rang_oras = get_rank_in_city(id_oras, elo)
    total_oras = get_count_city(id_oras)
    rang_national = get_rank_national(elo)
    total_national = get_count_national()

    with st.container(horizontal=True):
        st.metric("Rating ELO", elo, border=True)
        st.metric("Nivel declarat", nivel_text(user["nivel_declarat"]), border=True)
        st.metric(f"Loc in {oras}", f"#{rang_oras}",
                  delta_description=f"din {total_oras} jucatori", border=True)
        st.metric("Loc national", f"#{rang_national}",
                  delta_description=f"din {total_national} jucatori", border=True)
except Exception:
    st.warning("Nu s-au putut incarca statisticile personale.",
               icon=":material/cloud_off:")

# ── Selectorul de clasament ───────────────────────────────────────────────────
OPTIUNI = ["National", oras, "Orase active"]

alegere = st.segmented_control(
    "Clasament afisat", OPTIUNI, default="National",
    label_visibility="collapsed", key="clasament_scop",
) or "National"


def _tabel_jucatori(doar_orasul_meu: bool) -> None:
    """Clasamentul jucatorilor activi (Q5, HAVING pe numarul de rezervari)."""
    with st.spinner("Se incarca clasamentul…"):
        df = clasament_jucatori_activi(min_rezervari=3)

    if doar_orasul_meu:
        df = df[df["nume_oras"] == user.get("nume_oras", "")]

    if df.empty:
        st.info("Nu exista inca destule date pentru acest clasament.",
                icon=":material/info:")
        return

    df = df.reset_index(drop=True)
    tabel = pd.DataFrame({
        "Loc": [MEDALII.get(i + 1, str(i + 1)) for i in range(len(df))],
        "Jucator": [
            ("⭐ " if str(r["id_jucator"]) == str(user["id_jucator"]) else "") + str(r["nume"])
            for _, r in df.iterrows()
        ],
        "Oras": df["nume_oras"],
        "ELO": df["rating_elo"].astype(int),
        "Nivel": [nivel_text(n) for n in df["nivel_declarat"]],
        "Rezervari finalizate": df["nr_rezervari_finalizate"].astype(int),
    })

    pozitia_mea = tabel.index[tabel["Jucator"].str.startswith("⭐")]
    if len(pozitia_mea):
        st.caption(f"Esti pe locul {int(pozitia_mea[0]) + 1} din {len(tabel)} "
                   "jucatori activi din acest clasament.")

    def _evidentiaza(rand):
        if rand["Jucator"].startswith("⭐"):
            return ["background-color: rgba(212,175,55,.16)"] * len(rand)
        return [""] * len(rand)

    st.dataframe(
        tabel.style.apply(_evidentiaza, axis=1),
        hide_index=True,
        height=520,
        column_config={
            "Loc": st.column_config.TextColumn(width="small", pinned=True),
            "ELO": st.column_config.NumberColumn(format="%d"),
            "Rezervari finalizate": st.column_config.ProgressColumn(
                format="%d",
                min_value=0,
                max_value=int(tabel["Rezervari finalizate"].max()),
            ),
        },
    )


def _tabel_orase() -> None:
    """Comunitatile pe orase (Q4, HAVING pe numarul de jucatori activi)."""
    st.caption("Orase cu cel putin 10 jucatori care au cel putin o rezervare "
               "finalizata, ordonate dupa marimea comunitatii.")
    with st.spinner("Se incarca activitatea pe orase…"):
        df = orase_active(min_jucatori=10)

    if df.empty:
        st.info("Nu exista date despre activitatea pe orase.", icon=":material/info:")
        return

    tabel = df[["nume_oras", "judet", "jucatori_activi", "elo_mediu"]].copy()
    tabel.columns = ["Oras", "Judet", "Jucatori activi", "ELO mediu"]
    tabel["ELO mediu"] = tabel["ELO mediu"].round(0).astype(int)
    tabel.insert(0, "Loc", [str(i + 1) for i in range(len(tabel))])

    stanga, dreapta = st.columns([3, 2])
    with stanga:
        st.dataframe(
            tabel, hide_index=True,
            column_config={
                "Loc": st.column_config.TextColumn(width="small"),
                "Jucatori activi": st.column_config.ProgressColumn(
                    format="%d", min_value=0,
                    max_value=int(tabel["Jucatori activi"].max()),
                ),
            },
        )
    with dreapta:
        with st.container(border=True):
            st.markdown("**Jucatori activi pe oras**")
            st.bar_chart(tabel, x="Oras", y="Jucatori activi", horizontal=True,
                         height=380)


if alegere == "Orase active":
    _tabel_orase()
else:
    _tabel_jucatori(doar_orasul_meu=(alegere != "National"))
