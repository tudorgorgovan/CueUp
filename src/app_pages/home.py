"""app_pages/home.py - Pagina de start: ce este CueUp si de ce exista."""

import streamlit as st

from ui import antet

user = st.session_state.user

antet("Acasa", f"Bine ai venit, {user['nume'].split()[0]}", ":material/home:")

st.markdown(
    "**CueUp** este o platforma de rezervari si matchmaking pentru cluburile de "
    "biliard din Romania. Rezervi o masa intr-un club real, la o ora reala, si "
    "gasesti un adversar care joaca la nivelul tau."
)

# ── Motivatia ─────────────────────────────────────────────────────────────────
st.subheader("De ce exista")

st.markdown(
    "Un club de biliard este o afacere de **utilizare a capacitatii**. Venitul "
    "inseamna ore-masa vandute inmultite cu tariful orar, costurile sunt fixe, "
    "iar o masa goala marti la ora 15:00 este venit pierdut definitiv - nu se "
    "recupereaza niciodata.\n\n"
    "Cererea insa nu este distribuita uniform. Se aglomereaza vineri si sambata "
    "seara si aproape dispare de luni pana joi la pranz. Problema clubului nu "
    "este pretul, ci **distributia cererii in timp**."
)

with st.container(horizontal=True):
    st.metric("Ocupare vineri-sambata, 19-24", "41,2%", border=True)
    st.metric("Ocupare luni-joi, 10-17", "6,9%", border=True)
    st.metric("Meciuri echilibrate", "69,8%",
              delta_description="diferenta de ELO sub 150", border=True)

st.caption("Cifre calculate pe setul de date CueUp: 44.259 rezervari si 17.514 "
           "meciuri, in 18 cluburi din 10 orase, intre ianuarie si august 2026.")

# ── Cele doua laturi ──────────────────────────────────────────────────────────
st.subheader("Cine castiga")

pentru_jucator, pentru_club = st.columns(2)

with pentru_jucator.container(border=True, height="stretch"):
    st.markdown("**:material/sports_and_outdoors: Jucatorul**")
    st.markdown(
        "Vrea doua lucruri: o masa garantata la ora la care ajunge si un "
        "adversar pe nivelul lui. Un meci pierdut 5-0 nu distreaza pe nimeni, "
        "asa ca potrivirea se face dupa rating ELO, nu dupa cine e liber."
    )

with pentru_club.container(border=True, height="stretch"):
    st.markdown("**:material/storefront: Clubul**")
    st.markdown(
        "Vrea clienti in intervalele moarte si date despre propria afacere: "
        "cand se umple, cat pierde din anulari si neprezentari, ce mese aduc "
        "bani si care stau degeaba."
    )

# ── Ce gasesti in aplicatie ───────────────────────────────────────────────────
st.subheader("Ce poti face aici")

st.markdown(
    "- :material/trophy: **Clasament** - unde te situezi in orasul tau si la "
    "nivel national, plus comunitatile active pe orase.\n"
    "- :material/handshake: **Parteneri** - jucatori din orasul tau cu rating "
    "apropiat de al tau, filtrati dupa cat de stransa vrei partida.\n"
    "- :material/event_available: **Rezerva o masa** - alegi clubul, intervalul "
    "si tipul de masa, iar aplicatia iti arata doar mesele chiar libere atunci.\n"
    "- :material/person: **Profilul meu** - rezervarile, meciurile, evolutia "
    "ratingului si un antrenor AI care iti citeste statisticile reale inainte "
    "sa iti dea un sfat."
)

st.caption("Proiect de hackathon. Datele sunt sintetice, generate pentru a "
           "reproduce tiparele reale de cerere dintr-un club de biliard.")
