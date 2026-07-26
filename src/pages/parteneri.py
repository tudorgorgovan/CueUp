"""pages/parteneri.py – Găsire parteneri de joc după oraș + interval ELO."""

import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import cauta_parteneri

NIVEL = {1: "Începător", 2: "Elementar", 3: "Intermediar", 4: "Avansat", 5: "Expert"}


def show():
    user = st.session_state.user
    my_elo  = int(user["rating_elo"])
    my_city = user.get("nume_oras", "orașul tău")

    # ── Titlu ─────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
            <span style="font-size:1.9rem;">🤝</span>
            <div>
                <div style="font-size:1.65rem;font-weight:900;color:#d4af37;">Găsește Parteneri</div>
                <div style="font-size:.84rem;color:#6a8099;">Jucători din același oraș cu nivel similar</div>
            </div>
        </div>
        <hr style="border-color:rgba(212,175,55,.2);margin-bottom:22px;">
        """,
        unsafe_allow_html=True,
    )

    # ── Banner info ────────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="background:rgba(26,122,74,.1);border:1px solid rgba(26,122,74,.3);
                    border-radius:10px;padding:14px;margin-bottom:20px;font-size:.9rem;">
            📍 Cauți parteneri în
            <strong style="color:#d4af37;">{my_city}</strong>
            &nbsp;·&nbsp; ELO tău:
            <strong style="color:#d4af37;">{my_elo}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Filtre ────────────────────────────────────────────────────────────────
    col_slider, col_btn = st.columns([4, 1])
    with col_slider:
        elo_range = st.slider(
            "Diferență ELO maximă față de al tău",
            min_value=25, max_value=600, value=150, step=25,
            help="De exemplu, 150 → caută jucători cu ELO între "
                 f"{my_elo - 150} și {my_elo + 150}.",
        )
    with col_btn:
        st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        cauta = st.button("🔍 Caută", use_container_width=True, key="btn_cauta")

    elo_min = max(800, my_elo - elo_range)
    elo_max = my_elo + elo_range

    st.markdown(
        f"<div style='font-size:.82rem;color:#6a8099;margin-bottom:16px;'>"
        f"Interval ELO: <strong>{elo_min}</strong> – <strong>{elo_max}</strong>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Căutare ───────────────────────────────────────────────────────────────
    if cauta or "partners_df" not in st.session_state:
        try:
            df = cauta_parteneri(
                id_oras=int(user["id_oras"]),
                elo_min=elo_min,
                elo_max=elo_max,
                exclude_id=int(user["id_jucator"]),
            )
            st.session_state.partners_df = df
        except Exception as exc:
            st.error(f"Eroare la căutare: {exc}")
            return

    df: pd.DataFrame = st.session_state.get("partners_df", pd.DataFrame())

    if df.empty:
        st.info(
            "Nu au fost găsiți parteneri cu aceste criterii. "
            "Încearcă un interval ELO mai mare."
        )
        return

    st.markdown(
        f"<div style='font-weight:600;color:#e8edf5;margin-bottom:18px;'>"
        f"✅ {len(df)} jucători găsiți</div>",
        unsafe_allow_html=True,
    )

    # ── Carduri rezultate – 3 pe rând ─────────────────────────────────────────
    COLS = 3
    for i in range(0, len(df), COLS):
        cols = st.columns(COLS)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(df):
                break
            row      = df.iloc[idx]
            elo_diff = int(row["rating_elo"]) - my_elo
            sign     = "+" if elo_diff >= 0 else ""
            nivel    = NIVEL.get(int(row["nivel_declarat"]), "–")

            # culoare badge diferență ELO
            if abs(elo_diff) <= 50:
                diff_color = "#4ade80"   # verde – nivel foarte aproape
            elif abs(elo_diff) <= 150:
                diff_color = "#facc15"   # galben – nivel apropiat
            else:
                diff_color = "#f87171"   # roșu – diferență mare

            with col:
                st.markdown(
                    f"""
                    <div style="background:rgba(255,255,255,.04);
                                border:1px solid rgba(26,122,74,.25);
                                border-radius:14px;padding:18px;
                                margin-bottom:14px;
                                transition:border-color .2s,transform .2s;">
                        <div style="font-size:1rem;font-weight:700;
                                    color:#e8edf5;margin-bottom:8px;">
                            👤 {row['nume']}
                        </div>
                        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;">
                            <span style="background:rgba(212,175,55,.15);color:#d4af37;
                                         padding:3px 10px;border-radius:20px;
                                         font-size:.78rem;font-weight:600;">
                                ELO {int(row['rating_elo'])}
                            </span>
                            <span style="background:rgba(255,255,255,.06);
                                         color:{diff_color};
                                         padding:3px 10px;border-radius:20px;
                                         font-size:.78rem;">
                                {sign}{elo_diff} față de tine
                            </span>
                        </div>
                        <div style="font-size:.82rem;color:#9eafc0;">
                            🎯 {nivel}
                        </div>
                        <div style="font-size:.78rem;color:#6a8099;margin-top:4px;
                                    word-break:break-all;">
                            📧 {row['email']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
