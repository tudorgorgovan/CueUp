"""app_pages/rezervari.py - Cautare mese libere si rezervare."""

from datetime import date, datetime, time, timedelta

import streamlit as st

from db import (
    check_masa_disponibila,
    create_rezervare,
    get_cluburi_oras,
    get_orase,
    mese_active_club,
)
from ui import TIP_ICON, antet

user = st.session_state.user

antet("Rezerva o masa", "Alege clubul, intervalul si masa libera",
      ":material/event_available:")

# ── Pasul 1: oras si club ─────────────────────────────────────────────────────
try:
    orase_df = get_orase()
except Exception:
    st.error("Nu s-au putut incarca orasele.", icon=":material/cloud_off:")
    st.stop()

# Numele oraselor vin din baza (fara diacritice), niciodata dintr-o lista scrisa in cod.
oras_map = dict(zip(orase_df["nume_oras"], orase_df["id_oras"]))
orase = list(oras_map.keys())
oras_implicit = user.get("nume_oras")
index_implicit = orase.index(oras_implicit) if oras_implicit in orase else 0

with st.container(border=True):
    st.markdown("**Unde vrei sa joci**")
    coloana_oras, coloana_club = st.columns(2)

    with coloana_oras:
        oras_ales = st.selectbox("Oras", orase, index=index_implicit)
        id_oras = oras_map[oras_ales]

    with coloana_club:
        try:
            cluburi_df = get_cluburi_oras(id_oras)
        except Exception:
            st.error("Nu s-au putut incarca cluburile.", icon=":material/cloud_off:")
            st.stop()

        if cluburi_df.empty:
            st.info("Nu exista cluburi in acest oras.", icon=":material/info:")
            st.stop()

        club_map = {
            f"{r['nume']} · ⭐ {r['rating_club']}": r["id_club"]
            for _, r in cluburi_df.iterrows()
        }
        club_ales = st.selectbox("Club", list(club_map.keys()))
        id_club = club_map[club_ales]
        club = cluburi_df[cluburi_df["id_club"] == id_club].iloc[0]

    st.caption(
        f":material/location_on: {club['adresa']} · "
        f":material/call: {club['telefon']} · "
        f":material/schedule: {club['ora_deschidere']}–{club['ora_inchidere']}"
    )

# ── Pasul 2: interval ─────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("**Cand**")
    coloana_data, coloana_ora, coloana_durata = st.columns(3)

    with coloana_data:
        zi = st.date_input(
            "Data", value=date.today(), min_value=date.today(),
            max_value=date.today() + timedelta(days=30), format="DD.MM.YYYY",
        )
    with coloana_ora:
        ora_start = st.select_slider(
            "Ora de start", options=list(range(8, 23)), value=18,
            format_func=lambda o: f"{o:02d}:00",
        )
    with coloana_durata:
        durata = st.segmented_control(
            "Durata", options=[1, 2, 3, 4], default=2,
            format_func=lambda h: f"{h} h",
        ) or 1

    tip_ales = st.segmented_control(
        "Tip de masa", options=["Orice tip", "pool", "snooker", "carambol"],
        default="Orice tip",
    ) or "Orice tip"
    tip_filtru = None if tip_ales == "Orice tip" else tip_ales

start = datetime.combine(zi, time(ora_start, 0))
sfarsit = start + timedelta(hours=durata)

st.caption(
    f":material/schedule: Interval selectat: **{start.strftime('%d.%m.%Y, %H:00')} → "
    f"{sfarsit.strftime('%H:00')}** ({durata} h)"
)

if st.button("Cauta mese libere", icon=":material/search:", type="primary"):
    try:
        with st.spinner("Verificam disponibilitatea…"):
            mese_df = mese_active_club(id_club, tip_filtru)
            libere = [
                masa for _, masa in mese_df.iterrows()
                if check_masa_disponibila(
                    int(masa["id_masa"]),
                    start.strftime("%Y-%m-%d %H:%M:%S"),
                    sfarsit.strftime("%Y-%m-%d %H:%M:%S"),
                )
            ]
    except Exception:
        st.error("Verificarea a esuat. Incearca din nou.", icon=":material/cloud_off:")
        st.stop()

    if not libere:
        st.session_state.pop("mese_dispo", None)
        st.warning("Nicio masa libera in acest interval. Incearca alta ora sau alt club.",
                   icon=":material/event_busy:")
    else:
        st.session_state.mese_dispo = libere
        st.session_state.rez_params = {
            "start": start, "sfarsit": sfarsit,
            "durata": durata, "club": club["nume"],
        }

# ── Pasul 3: mesele libere ────────────────────────────────────────────────────
libere = st.session_state.get("mese_dispo")

if libere:
    parametri = st.session_state.rez_params
    st.subheader(f"{len(libere)} mese libere la {parametri['club']}")
    st.caption(
        f"{parametri['start'].strftime('%d.%m.%Y, %H:00')} → "
        f"{parametri['sfarsit'].strftime('%H:00')}"
    )

    for start_rand in range(0, len(libere), 4):
        for coloana, masa in zip(st.columns(4), libere[start_rand:start_rand + 4]):
            cost = float(masa["tarif_orar"]) * parametri["durata"]
            with coloana.container(border=True, height="stretch",
                                   horizontal_alignment="center"):
                st.markdown(f"### {TIP_ICON.get(str(masa['tip_masa']), '')}")
                st.markdown(f"**{masa['cod_masa']}**")
                st.caption(str(masa["tip_masa"]))
                st.metric("Total", f"{cost:.0f} RON",
                          delta_description=f"{float(masa['tarif_orar']):.0f} RON/ora",
                          label_visibility="collapsed")

                if st.button("Rezerva", key=f"rez_{masa['id_masa']}",
                             icon=":material/check:", width="stretch"):
                    try:
                        create_rezervare(
                            id_masa=int(masa["id_masa"]),
                            id_jucator=int(user["id_jucator"]),
                            data_start=parametri["start"].strftime("%Y-%m-%d %H:%M:%S"),
                            data_sfarsit=parametri["sfarsit"].strftime("%Y-%m-%d %H:%M:%S"),
                            suma=cost,
                        )
                    except Exception:
                        st.error("Rezervarea nu a putut fi salvata. "
                                 "Poate masa tocmai a fost ocupata.",
                                 icon=":material/error:")
                    else:
                        st.session_state.pop("mese_dispo", None)
                        st.toast(f"Masa {masa['cod_masa']} rezervata la "
                                 f"{parametri['club']}.", icon="🎱")
                        st.balloons()
                        st.rerun()
