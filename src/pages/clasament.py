"""pages/clasament.py – Clasament ELO + locul jucătorului în oraș / național."""

import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import (
    clasament_jucatori_activi,
    get_rank_in_city,
    get_rank_national,
    get_count_city,
    get_count_national,
    orase_active,
)

NIVEL = {1: "Începător", 2: "Elementar", 3: "Intermediar", 4: "Avansat", 5: "Expert"}
MEDALII = {1: "🥇", 2: "🥈", 3: "🥉"}


def _medal(pos: int) -> str:
    return MEDALII.get(pos, str(pos))


def show():
    user = st.session_state.user

    # ── Titlu ────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
            <span style="font-size:1.9rem;">🏆</span>
            <div>
                <div style="font-size:1.65rem;font-weight:900;color:#d4af37;">Clasament</div>
                <div style="font-size:.84rem;color:#6a8099;">Top jucători CueUp după rating ELO</div>
            </div>
        </div>
        <hr style="border-color:rgba(212,175,55,.2);margin-bottom:22px;">
        """,
        unsafe_allow_html=True,
    )

    # ── Carduri statistici ───────────────────────────────────────────────────
    try:
        elo        = int(user["rating_elo"])
        nivel_txt  = NIVEL.get(int(user["nivel_declarat"]), "–")
        id_oras    = int(user["id_oras"])
        nume_oras  = user.get("nume_oras", "Oraș")

        rank_oras    = get_rank_in_city(id_oras, elo)
        rank_nat     = get_rank_national(elo)
        total_oras   = get_count_city(id_oras)
        total_nat    = get_count_national()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("⚡ Rating ELO", f"{elo}")
        c2.metric("🎯 Nivel", nivel_txt)
        c3.metric(
            f"📍 Loc în {nume_oras}",
            f"#{rank_oras}",
            f"din {total_oras} jucători",
        )
        c4.metric(
            "🌍 Loc Național",
            f"#{rank_nat}",
            f"din {total_nat} jucători",
        )

    except Exception as exc:
        st.warning(f"⚠️ Nu s-au putut încărca statisticile: {exc}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tab-uri clasament ────────────────────────────────────────────────────────
    tab_nat, tab_oras, tab_orase = st.tabs(
        ["🌍 Clasament Național", f"📍 Clasament {user.get('nume_oras','Oraș')}", "📊 Activitate pe Orașe"]
    )

    with tab_nat:
        _render_table(national=True, user=user)

    with tab_oras:
        _render_table(national=False, user=user)

    with tab_orase:
        _render_orase_active()


def _render_orase_active():
    st.markdown(
        """
        <div style="font-size:.85rem;color:#9eafc0;margin-bottom:16px;line-height:1.6;">
        Orașe cu cel puțin <strong style="color:#d4af37;">10 jucători activi</strong>
        (jucători care au cel puțin o rezervare finalizată), ordonate după comunitate.
        </div>
        """,
        unsafe_allow_html=True,
    )
    try:
        df = orase_active(min_jucatori=10)
        if df.empty:
            st.info("Nu există date despre activitatea pe orașe.")
            return
        df_display = df[["nume_oras", "judet", "jucatori_activi", "elo_mediu"]].copy()
        df_display["elo_mediu"] = df_display["elo_mediu"].round(0).astype(int)
        df_display.columns = ["Oraș", "Județ", "Jucători activi", "ELO mediu"]
        df_display.insert(0, "🏅", [str(i + 1) for i in range(len(df_display))])
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    except Exception as exc:
        st.error(f"Eroare la încărcarea statisticilor: {exc}")


def _render_table(national: bool, user: dict):
    try:
        df = clasament_jucatori_activi(min_rezervari=3)
    except Exception as exc:
        st.error(f"Eroare la încărcarea clasamentului: {exc}")
        return

    if not national:
        df = df[df["nume_oras"] == user.get("nume_oras", "")]

    if df.empty:
        st.info("Nu există date suficiente pentru clasament (minimum 3 rezervări finalizate per jucător).")
        return

    df = df.reset_index(drop=True)

    # Construiește tabelul afișat
    rows = []
    for i, row in df.iterrows():
        pos      = i + 1
        is_me    = str(row["id_jucator"]) == str(user.get("id_jucator", ""))
        rows.append(
            {
                "Loc":                    _medal(pos),
                "Jucător":               ("⭐ " if is_me else "") + str(row["nume"]),
                "Oraș":                  row["nume_oras"],
                "ELO":                   int(row["rating_elo"]),
                "Nivel":                 NIVEL.get(int(row["nivel_declarat"]), "–"),
                "Rezervări finalizate":  int(row["nr_rezervari_finalizate"]),
            }
        )

    import pandas as pd

    display_df = pd.DataFrame(rows)

    # Evidențiază rândul utilizatorului curent
    def highlight(row):
        if row["Jucător"].startswith("⭐"):
            return ["background-color:rgba(212,175,55,.15); color:#f5d87a"] * len(row)
        return [""] * len(row)

    st.dataframe(
        display_df.style.apply(highlight, axis=1),
        use_container_width=True,
        hide_index=True,
    )
