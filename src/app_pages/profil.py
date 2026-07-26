"""app_pages/profil.py - Profil personal, evolutie ELO, meciuri si antrenorul AI."""

import streamlit as st

from db import get_istoric_rating, get_meciuri_jucator, rezervari_jucator
from gemini_client import sfat_coaching
from ui import STATUS_CULOARE, antet, nivel_text

user = st.session_state.user
id_jucator = int(user["id_jucator"])

antet("Profilul meu", "Statistici personale, rezervari, meciuri si antrenorul AI",
      ":material/person:")

# ── Card profil + evolutie ELO ────────────────────────────────────────────────
coloana_profil, coloana_grafic = st.columns([1, 2])

with coloana_profil:
    with st.container(border=True, height="stretch"):
        st.subheader(user["nume"])
        st.caption(user.get("email", ""))
        st.markdown(
            f":orange-badge[:material/bolt: ELO {int(user['rating_elo'])}] "
            f":green-badge[{nivel_text(user['nivel_declarat'])}]"
        )
        st.caption(f":material/location_on: {user.get('nume_oras', '–')}")
        st.caption(f":material/calendar_month: Inscris "
                   f"{str(user.get('data_inscriere', ''))[:10]}")

with coloana_grafic:
    with st.container(border=True, height="stretch"):
        st.markdown("**Evolutia ratingului ELO**")
        try:
            istoric = get_istoric_rating(id_jucator)
        except Exception:
            istoric = None
            st.warning("Nu s-a putut incarca istoricul de rating.",
                       icon=":material/cloud_off:")

        if istoric is not None and not istoric.empty:
            serie = istoric.rename(columns={"data": "Data", "rating_dupa": "ELO"})
            st.line_chart(serie, x="Data", y="ELO", height=260)
        elif istoric is not None:
            st.caption("Nu ai inca meciuri care sa iti schimbe ratingul.")

# ── Sectiuni ──────────────────────────────────────────────────────────────────
sectiune = st.segmented_control(
    "Sectiune",
    ["Rezervarile mele", "Meciuri", "Antrenor AI"],
    default="Rezervarile mele",
    label_visibility="collapsed",
) or "Rezervarile mele"

# ── Rezervari ─────────────────────────────────────────────────────────────────
if sectiune == "Rezervarile mele":
    STATUSURI = ["Toate", "confirmata", "finalizata", "anulata", "no_show"]
    status = st.selectbox("Filtreaza dupa status", STATUSURI, width=260)

    try:
        rezervari = rezervari_jucator(
            id_jucator, None if status == "Toate" else status
        )
    except Exception:
        st.error("Nu s-au putut incarca rezervarile.", icon=":material/cloud_off:")
        st.stop()

    if rezervari.empty:
        st.info("Nu ai rezervari cu acest status.", icon=":material/info:")
    else:
        total_platit = float(
            rezervari.loc[rezervari["status"].isin(["confirmata", "finalizata"]), "suma"].sum()
        )
        with st.container(horizontal=True):
            st.metric("Rezervari afisate", len(rezervari), border=True)
            st.metric("Total platit", f"{total_platit:,.0f} RON",
                      delta_description="confirmate si finalizate", border=True)

        tabel = rezervari.drop(columns=["id_rezervare"], errors="ignore").rename(
            columns={
                "cod_masa": "Masa", "tip_masa": "Tip", "club": "Club",
                "nume_oras": "Oras", "data_start": "Start",
                "data_sfarsit": "Sfarsit", "status": "Status", "suma": "Suma",
            }
        )
        st.dataframe(
            tabel, hide_index=True, height=430,
            column_config={
                "Start": st.column_config.DatetimeColumn(format="DD.MM.YYYY HH:mm"),
                "Sfarsit": st.column_config.DatetimeColumn(format="HH:mm"),
                "Suma": st.column_config.NumberColumn(format="%.0f RON"),
            },
        )
        legenda = " ".join(
            f":{culoare}-badge[{stare}]" for stare, culoare in STATUS_CULOARE.items()
        )
        st.caption(f"Statusuri posibile: {legenda}")

# ── Meciuri ───────────────────────────────────────────────────────────────────
elif sectiune == "Meciuri":
    try:
        meciuri = get_meciuri_jucator(id_jucator)
    except Exception:
        st.error("Nu s-au putut incarca meciurile.", icon=":material/cloud_off:")
        st.stop()

    if meciuri.empty:
        st.info("Nu ai inca meciuri finalizate.", icon=":material/info:")
    else:
        victorii = int((meciuri["id_castigator"].astype("string")
                        == str(id_jucator)).sum())
        total = len(meciuri)
        infrangeri = total - victorii

        with st.container(horizontal=True):
            st.metric("Victorii", victorii, border=True)
            st.metric("Infrangeri", infrangeri, border=True)
            st.metric("Rata de victorii", f"{victorii / total:.0%}",
                      delta_description=f"din {total} meciuri finalizate",
                      border=True)

        tabel = meciuri[["jucator_1", "scor_1", "scor_2", "jucator_2", "tip"]].rename(
            columns={
                "jucator_1": "Jucator 1", "scor_1": "Scor 1",
                "scor_2": "Scor 2", "jucator_2": "Jucator 2", "tip": "Tip",
            }
        )
        st.dataframe(tabel, hide_index=True, height=430)

# ── Antrenor AI ───────────────────────────────────────────────────────────────
else:
    st.markdown("**Antrenorul virtual CueUp**")
    st.caption("Sfatul este generat de Gemini pornind de la statisticile tale "
               "reale din baza de date: rating, evolutie ELO si ultimele meciuri.")

    intrebare = st.text_area(
        "Descrie o problema tehnica (optional)",
        placeholder="Ex: nu reusesc sa tin tacul drept la loviturile lungi…",
        key="ai_intrebare",
    )

    if st.button("Genereaza sfat", icon=":material/auto_awesome:", type="primary"):
        with st.spinner("Antrenorul analizeaza profilul tau…"):
            try:
                meciuri = get_meciuri_jucator(id_jucator)
                istoric = get_istoric_rating(id_jucator)
            except Exception:
                st.error("Nu s-au putut citi statisticile pentru prompt.",
                         icon=":material/cloud_off:")
                st.stop()

            total = len(meciuri)
            victorii = int((meciuri["id_castigator"].astype("string")
                            == str(id_jucator)).sum()) if total else 0

            ultimele = [
                f"{m['jucator_1']} {m['scor_1']} - {m['scor_2']} {m['jucator_2']}"
                for _, m in meciuri.head(10).iterrows()
            ]
            evolutie = None
            if not istoric.empty:
                evolutie = int(istoric.iloc[-1]["rating_dupa"]) - \
                           int(istoric.iloc[0]["rating_inainte"])

            st.session_state.sfat_ai = sfat_coaching(
                nume=user["nume"],
                rating_elo=int(user["rating_elo"]),
                nivel=int(user["nivel_declarat"]),
                win_rate=victorii / total if total else 0.0,
                nr_meciuri=total,
                intrebare=intrebare,
                evolutie_elo=evolutie,
                ultimele_meciuri=ultimele,
            )

    if st.session_state.get("sfat_ai"):
        with st.container(border=True):
            st.markdown(f":material/format_quote: {st.session_state.sfat_ai}")
