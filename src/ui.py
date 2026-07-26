"""
ui.py - Elemente comune de interfata, folosite de toate paginile.

Aici stau doar lucruri partajate (etichete, iconite, antet de pagina).
Culorile si fonturile NU se seteaza din cod, ci in .streamlit/config.toml.
"""

import streamlit as st

NIVEL = {
    1: "Incepator",
    2: "Elementar",
    3: "Intermediar",
    4: "Avansat",
    5: "Expert",
}

# Iconite Material Symbols pentru tipurile de masa
TIP_ICON = {
    "pool": ":material/sports_and_outdoors:",
    "snooker": ":material/circle:",
    "carambol": ":material/adjust:",
}

MEDALII = {1: "🥇", 2: "🥈", 3: "🥉"}

STATUS_CULOARE = {
    "confirmata": "green",
    "finalizata": "blue",
    "anulata": "red",
    "no_show": "orange",
}


def antet(titlu: str, subtitlu: str, icon: str) -> None:
    """Antetul standard al unei pagini: titlu cu iconita + o linie de context."""
    st.title(f"{icon} {titlu}")
    st.caption(subtitlu)


def nivel_text(nivel) -> str:
    """Eticheta nivelului declarat, tolerantă la NULL sau valori neasteptate."""
    try:
        return NIVEL.get(int(nivel), "–")
    except (TypeError, ValueError):
        return "–"


def badge_elo_diferenta(diferenta: int) -> str:
    """
    Badge colorat pentru diferenta de ELO fata de utilizatorul curent.
    Sub 50 = potrivire foarte buna, sub 150 = potrivire buna, peste = dezechilibru.
    """
    semn = "+" if diferenta >= 0 else ""
    text = f"{semn}{diferenta} ELO"
    if abs(diferenta) <= 50:
        return f":green-badge[{text}]"
    if abs(diferenta) <= 150:
        return f":orange-badge[{text}]"
    return f":red-badge[{text}]"
