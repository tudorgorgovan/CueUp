"""pages/profil.py – Profil personal, evoluție ELO, meciuri, sfat AI Gemini."""

import streamlit as st
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import rezervari_jucator, get_istoric_rating, get_meciuri_jucator
from gemini_client import sfat_coaching

NIVEL = {1: "Începător", 2: "Elementar", 3: "Intermediar", 4: "Avansat", 5: "Expert"}
STATUS_LABEL = {
    "Toate":      "Toate",
    "finalizata": "Finalizate",
    "confirmata": "Confirmate",
    "anulata":    "Anulate",
}


def show():
    user = st.session_state.user

    # ── Titlu ─────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
            <span style="font-size:1.9rem;">👤</span>
            <div>
                <div style="font-size:1.65rem;font-weight:900;color:#d4af37;">Profilul Meu</div>
                <div style="font-size:.84rem;color:#6a8099;">Statistici personale, rezervări și evoluție ELO</div>
            </div>
        </div>
        <hr style="border-color:rgba(212,175,55,.2);margin-bottom:22px;">
        """,
        unsafe_allow_html=True,
    )

    # ── Card profil + grafic ELO ───────────────────────────────────────────────
    col_info, col_chart = st.columns([1, 2])

    with col_info:
        nivel = NIVEL.get(int(user["nivel_declarat"]), "–")
        st.markdown(
            f"""
            <div style="background:linear-gradient(145deg,rgba(26,122,74,.14),rgba(212,175,55,.07));
                        border:1px solid rgba(26,122,74,.35);border-radius:18px;
                        padding:26px;text-align:center;">
                <div style="font-size:3.2rem;margin-bottom:10px;">👤</div>
                <div style="font-size:1.25rem;font-weight:800;color:#e8edf5;">
                    {user['nume']}
                </div>
                <div style="font-size:.82rem;color:#9eafc0;margin-top:4px;
                            word-break:break-all;">
                    {user.get('email', '')}
                </div>
                <div style="margin-top:14px;display:flex;gap:8px;justify-content:center;flex-wrap:wrap;">
                    <span style="background:rgba(212,175,55,.2);color:#d4af37;
                                 padding:5px 14px;border-radius:20px;
                                 font-size:.88rem;font-weight:700;">
                        ELO {user['rating_elo']}
                    </span>
                    <span style="background:rgba(26,122,74,.2);color:#4ade80;
                                 padding:5px 14px;border-radius:20px;font-size:.84rem;">
                        {nivel}
                    </span>
                </div>
                <div style="font-size:.79rem;color:#6a8099;margin-top:14px;line-height:1.9;">
                    📍 {user.get('nume_oras','–')}<br>
                    📅 Înscris: {str(user.get('data_inscriere',''))[:10]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_chart:
        try:
            rating_df = get_istoric_rating(int(user["id_jucator"]))
            if not rating_df.empty:
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=rating_df["data"],
                        y=rating_df["rating_dupa"],
                        mode="lines+markers",
                        name="ELO",
                        line=dict(color="#d4af37", width=2.5, shape="spline"),
                        marker=dict(size=5, color="#d4af37"),
                        fill="tozeroy",
                        fillcolor="rgba(212,175,55,.07)",
                    )
                )
                fig.update_layout(
                    title=dict(text="Evoluție Rating ELO", font=dict(color="#d4af37", size=14)),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#9eafc0", family="Inter"),
                    xaxis=dict(showgrid=False, color="#6a8099", zeroline=False),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor="rgba(255,255,255,.05)",
                        color="#6a8099",
                        zeroline=False,
                    ),
                    margin=dict(l=10, r=10, t=40, b=10),
                    height=290,
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nu există încă istoric de rating.")
        except Exception as exc:
            st.warning(f"Nu s-a putut încărca istoricul ELO: {exc}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Taburi ────────────────────────────────────────────────────────────────
    tab_rez, tab_meciuri, tab_ai = st.tabs(
        ["📅 Rezervările Mele", "⚔️ Meciuri", "🤖 Sfat AI"]
    )

    # ── Tab Rezervări ─────────────────────────────────────────────────────────
    with tab_rez:
        status_sel = st.selectbox(
            "Filtrează după status",
            list(STATUS_LABEL.keys()),
            format_func=lambda x: STATUS_LABEL[x],
        )
        try:
            s_filter = None if status_sel == "Toate" else status_sel
            rez_df   = rezervari_jucator(int(user["id_jucator"]), s_filter)
            if rez_df.empty:
                st.info("Nu ai rezervări cu acest status.")
            else:
                display = rez_df.drop(columns=["id_rezervare"], errors="ignore").rename(
                    columns={
                        "cod_masa":     "Masă",
                        "tip_masa":     "Tip",
                        "club":         "Club",
                        "nume_oras":    "Oraș",
                        "data_start":   "Start",
                        "data_sfarsit": "Sfârșit",
                        "status":       "Status",
                        "suma":         "Sumă (RON)",
                    }
                )
                st.dataframe(display, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(f"Eroare la încărcarea rezervărilor: {exc}")

    # ── Tab Meciuri ───────────────────────────────────────────────────────────
    with tab_meciuri:
        try:
            meciuri_df = get_meciuri_jucator(int(user["id_jucator"]))
            if meciuri_df.empty:
                st.info("Nu ai meciuri finalizate încă.")
            else:
                victorii  = sum(
                    1 for _, m in meciuri_df.iterrows()
                    if str(m["id_castigator"]) == str(user["id_jucator"])
                )
                infrangeri = len(meciuri_df) - victorii
                total      = len(meciuri_df)
                win_rate   = f"{victorii / total * 100:.0f}%" if total else "–"

                c1, c2, c3 = st.columns(3)
                c1.metric("🏆 Victorii", victorii)
                c2.metric("💔 Înfrângeri", infrangeri)
                c3.metric("📊 Rată victorii", win_rate)

                st.markdown("<br>", unsafe_allow_html=True)

                display_m = meciuri_df[
                    ["jucator_1", "scor_1", "scor_2", "jucator_2", "tip", "stare"]
                ].rename(
                    columns={
                        "jucator_1": "Jucător 1",
                        "scor_1":    "Scor 1",
                        "scor_2":    "Scor 2",
                        "jucator_2": "Jucător 2",
                        "tip":       "Tip",
                        "stare":     "Stare",
                    }
                )
                st.dataframe(display_m, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(f"Eroare la încărcarea meciurilor: {exc}")

    # ── Tab Sfat AI ───────────────────────────────────────────────────────────
    with tab_ai:
        st.markdown(
            """
            <div style="background:rgba(26,122,74,.08);border:1px solid rgba(26,122,74,.25);
                        border-radius:14px;padding:22px;margin-bottom:22px;">
                <div style="font-size:1.1rem;font-weight:700;color:#d4af37;margin-bottom:8px;">
                    🤖 Antrenor Virtual AI (Gemini)
                </div>
                <div style="font-size:.88rem;color:#9eafc0;line-height:1.6;">
                    Primești un sfat de antrenament personalizat generat de Gemini,
                    bazat pe ratingul tău ELO, nivelul declarat și istoricul de meciuri.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("✨ Generează sfat", key="btn_sfat"):
            with st.spinner("Antrenorul analizează profilul tău…"):
                try:
                    meciuri_df = get_meciuri_jucator(int(user["id_jucator"]))
                    total_m    = len(meciuri_df)
                    victorii   = sum(
                        1 for _, m in meciuri_df.iterrows()
                        if str(m["id_castigator"]) == str(user["id_jucator"])
                    )
                    win_rate = victorii / total_m if total_m > 0 else 0.0

                    sfat = sfat_coaching(
                        nume=user["nume"],
                        rating_elo=int(user["rating_elo"]),
                        nivel=int(user["nivel_declarat"]),
                        win_rate=win_rate,
                        nr_meciuri=total_m,
                    )
                    st.markdown(
                        f"""
                        <div style="background:rgba(212,175,55,.08);
                                    border:1px solid rgba(212,175,55,.3);
                                    border-radius:14px;padding:22px;margin-top:10px;">
                            <div style="font-size:.82rem;color:#9eafc0;margin-bottom:10px;">
                                💬 Sfatul antrenorului tău:
                            </div>
                            <div style="font-size:.98rem;color:#e8edf5;
                                        line-height:1.7;font-style:italic;">
                                „{sfat}"
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                except Exception as exc:
                    st.error(f"Eroare la apelul AI: {exc}")
