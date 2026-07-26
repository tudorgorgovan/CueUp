"""pages/rezervari.py – Rezervare masă de biliard."""

import streamlit as st
from datetime import date, datetime, time, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import (
    get_orase,
    get_cluburi_oras,
    mese_active_club,
    check_masa_disponibila,
    create_rezervare,
)

TIP_ICON = {"pool": "🔵", "snooker": "🔴", "carambol": "🟡"}


def show():
    user = st.session_state.user

    # ── Titlu ─────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
            <span style="font-size:1.9rem;">📅</span>
            <div>
                <div style="font-size:1.65rem;font-weight:900;color:#d4af37;">Rezervă o Masă</div>
                <div style="font-size:.84rem;color:#6a8099;">Găsește și rezervă masa perfectă</div>
            </div>
        </div>
        <hr style="border-color:rgba(212,175,55,.2);margin-bottom:22px;">
        """,
        unsafe_allow_html=True,
    )

    # ── Pasul 1 – Oraș & Club ─────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        try:
            orase_df   = get_orase()
            oras_map   = dict(zip(orase_df["nume_oras"], orase_df["id_oras"]))
            oras_list  = list(oras_map.keys())
            default    = user.get("nume_oras", oras_list[0])
            default_i  = oras_list.index(default) if default in oras_list else 0
            sel_oras   = st.selectbox("🏙️ Oraș", oras_list, index=default_i)
            id_oras    = oras_map[sel_oras]
        except Exception as exc:
            st.error(f"Eroare la încărcarea orașelor: {exc}")
            return

    with col2:
        try:
            club_df = get_cluburi_oras(id_oras)
            if club_df.empty:
                st.info("Nu există cluburi în acest oraș.")
                return
            club_map  = {
                f"{r['nume']}  ⭐{r['rating_club']}": r["id_club"]
                for _, r in club_df.iterrows()
            }
            sel_club_label = st.selectbox("🎱 Club", list(club_map.keys()))
            id_club        = club_map[sel_club_label]
            club_row       = club_df[club_df["id_club"] == id_club].iloc[0]
        except Exception as exc:
            st.error(f"Eroare la încărcarea cluburilor: {exc}")
            return

    # Info club
    st.markdown(
        f"""
        <div style="background:rgba(255,255,255,.04);border:1px solid rgba(26,122,74,.2);
                    border-radius:10px;padding:13px;margin-bottom:20px;font-size:.85rem;
                    color:#9eafc0;line-height:1.9;">
            📍 {club_row['adresa']}
            &nbsp;·&nbsp; 📞 {club_row['telefon']}
            &nbsp;·&nbsp; 🕐 {club_row['ora_deschidere']} – {club_row['ora_inchidere']}
            &nbsp;·&nbsp; <span style="color:#d4af37;font-weight:600;">⭐ {club_row['rating_club']}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Pasul 2 – Tip, dată, oră, durată ─────────────────────────────────────
    col3, col4, col5 = st.columns(3)

    with col3:
        tip_optiuni = ["Orice tip", "pool", "snooker", "carambol"]
        tip_sel     = st.selectbox("🎯 Tip masă", tip_optiuni)
        tip_filter  = None if tip_sel == "Orice tip" else tip_sel

    with col4:
        sel_data = st.date_input(
            "📅 Data",
            value=date.today(),
            min_value=date.today(),
            max_value=date.today() + timedelta(days=30),
        )

    with col5:
        durata = st.selectbox(
            "⏱️ Durată",
            [1, 2, 3, 4],
            format_func=lambda x: f"{x} {'oră' if x == 1 else 'ore'}",
        )

    ora_start = st.slider(
        "🕐 Ora de start",
        min_value=8, max_value=22, value=18, step=1,
        format="%d:00",
    )

    dt_start = datetime.combine(sel_data, time(ora_start, 0))
    dt_end   = dt_start + timedelta(hours=durata)

    st.markdown(
        f"""
        <div style="background:rgba(26,122,74,.08);border:1px solid rgba(26,122,74,.2);
                    border-radius:8px;padding:12px;margin:4px 0 16px;font-size:.9rem;">
            ⏰ Interval selectat:
            <strong style="color:#d4af37;">
                {dt_start.strftime('%d %b %Y, %H:00')} → {dt_end.strftime('%H:00')}
            </strong>
            &nbsp;({durata} {'oră' if durata == 1 else 'ore'})
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Verificare disponibilitate ────────────────────────────────────────────
    if st.button("🔍 Verifică disponibilitate", key="btn_verifica"):
        try:
            mese_df = mese_active_club(id_club, tip_filter)
            if mese_df.empty:
                st.warning("Nu există mese active de acest tip în clubul selectat.")
                st.session_state.pop("mese_dispo", None)
            else:
                disponibile = []
                for _, m in mese_df.iterrows():
                    if check_masa_disponibila(
                        int(m["id_masa"]),
                        dt_start.strftime("%Y-%m-%d %H:%M:%S"),
                        dt_end.strftime("%Y-%m-%d %H:%M:%S"),
                    ):
                        disponibile.append(m)

                if not disponibile:
                    st.error(
                        "❌ Nu există mese disponibile pentru intervalul ales. "
                        "Încearcă altă oră sau dată."
                    )
                    st.session_state.pop("mese_dispo", None)
                else:
                    st.session_state.mese_dispo   = disponibile
                    st.session_state.rez_params   = {
                        "dt_start":  dt_start,
                        "dt_end":    dt_end,
                        "durata":    durata,
                        "club_name": club_row["nume"],
                    }
                    st.success(f"✅ {len(disponibile)} mese disponibile!")

        except Exception as exc:
            st.error(f"Eroare la verificare: {exc}")

    # ── Afișare mese disponibile ──────────────────────────────────────────────
    if "mese_dispo" in st.session_state and st.session_state.mese_dispo:
        disponibile = st.session_state.mese_dispo
        params      = st.session_state.rez_params

        st.markdown(
            "<div style='font-size:1.05rem;font-weight:700;color:#d4af37;"
            "margin:20px 0 12px;'>Mese disponibile</div>",
            unsafe_allow_html=True,
        )

        n_cols = min(len(disponibile), 4)
        cols   = st.columns(n_cols)

        for i, masa in enumerate(disponibile):
            cost = float(masa["tarif_orar"]) * params["durata"]
            icon = TIP_ICON.get(str(masa["tip_masa"]), "⚫")

            with cols[i % n_cols]:
                st.markdown(
                    f"""
                    <div style="background:rgba(255,255,255,.05);
                                border:1px solid rgba(26,122,74,.3);
                                border-radius:14px;padding:18px;
                                text-align:center;margin-bottom:8px;">
                        <div style="font-size:1.6rem;">{icon}</div>
                        <div style="font-weight:700;color:#e8edf5;
                                    font-size:1.05rem;margin:4px 0;">
                            {masa['cod_masa']}
                        </div>
                        <div style="color:#9eafc0;font-size:.8rem;text-transform:uppercase;
                                    letter-spacing:.04em;">
                            {masa['tip_masa']}
                        </div>
                        <div style="color:#d4af37;font-weight:800;
                                    font-size:1.2rem;margin-top:10px;">
                            {cost:.0f} RON
                        </div>
                        <div style="font-size:.75rem;color:#6a8099;margin-bottom:12px;">
                            {float(masa['tarif_orar']):.0f} RON/oră
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button(
                    f"Rezervă {masa['cod_masa']}",
                    key=f"rez_{masa['id_masa']}",
                    use_container_width=True,
                ):
                    try:
                        create_rezervare(
                            id_masa=int(masa["id_masa"]),
                            id_jucator=int(user["id_jucator"]),
                            data_start=params["dt_start"].strftime("%Y-%m-%d %H:%M:%S"),
                            data_sfarsit=params["dt_end"].strftime("%Y-%m-%d %H:%M:%S"),
                            suma=cost,
                        )
                        st.success(
                            f"✅ Masa {masa['cod_masa']} la {params['club_name']} "
                            f"a fost rezervată cu succes!"
                        )
                        st.balloons()
                        del st.session_state["mese_dispo"]
                    except Exception as exc:
                        st.error(f"Eroare la rezervare: {exc}")
