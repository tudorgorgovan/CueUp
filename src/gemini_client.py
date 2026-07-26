"""
gemini_client.py - Apel Gemini prin SDK-ul google-genai pentru sfat de antrenament.

Folosit in pagina Profilul Meu -> tab "Sfat AI".

Nota tehnica: modelele Gemini 3.x consuma tokeni pe rationament intern
(thoughtsTokenCount) din acelasi buget ca raspunsul. Cu max_output_tokens mic
raspunsul se termina cu finishReason=MAX_TOKENS si textul iese trunchiat.
De aceea fixam thinking_level pe "low" si lasam un buget generos.
"""

import os
import logging
from functools import lru_cache

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip() or "gemini-3.6-flash"

# Buget de output. Masurat pe gemini-3.6-flash cu thinking_level="low":
# rationamentul intern consuma ~1000 de tokeni inainte sa inceapa textul,
# deci sub ~2000 raspunsul se termina cu finishReason=MAX_TOKENS si iese taiat.
_MAX_OUTPUT_TOKENS = 3000

# Raspuns de rezerva, ca demo-ul sa mearga si fara retea sau cheie.
_FALLBACK = (
    "Concentreaza-te pe consistenta loviturii: pozitie stabila, tac relaxat si "
    "privirea fixata pe punctul de contact al bilei tinta, nu pe buzunar. "
    "Lucreaza 15 minute pe zi la lovituri drepte de-a lungul mesei, pana cand "
    "bila alba se intoarce singura pe aceeasi linie."
)

# Linkuri video: se completeaza DOAR cu adrese verificate manual.
# Prompt-ul interzice explicit modelului sa genereze alte URL-uri, pentru ca
# altfel inventeaza ID-uri de YouTube care dau 404.
LINKURI_RECOMANDATE: list[str] = []

_NIVEL_MAP = {
    1: "incepator",
    2: "elementar",
    3: "intermediar",
    4: "avansat",
    5: "expert",
}

_SYSTEM_INSTRUCTION = (
    "Esti antrenorul virtual de biliard al aplicatiei CueUp, o platforma "
    "romaneasca de rezervari si matchmaking pentru cluburi de biliard. "
    "Raspunzi mereu in limba romana, la persoana a doua, concret si "
    "motivational, fara introduceri de politete.\n"
    "Reguli obligatorii:\n"
    "- Citezi cifrele reale primite despre jucator (ELO, numar de meciuri, "
    "rata de victorii) si legi sfatul de ele.\n"
    "- Nu inventezi statistici care nu ti-au fost date.\n"
    "- Nu generezi niciun URL. Folosesti doar linkurile din lista primita, "
    "daca lista exista; daca lista e goala, nu pui niciun link.\n"
    "- Nu generezi cod SQL si nu vorbesti despre baza de date."
)


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    """Client Gemini reutilizat intre apeluri (creare o singura data)."""
    return genai.Client(api_key=_API_KEY)


def _extrage_text(resp) -> str:
    """
    Extrage textul din raspuns fara sa presupuna ca exista parti de text.
    Un candidat poate avea doar parti de gandire sau poate fi blocat.
    """
    bucati: list[str] = []
    for cand in (resp.candidates or []):
        continut = getattr(cand, "content", None)
        for parte in (getattr(continut, "parts", None) or []):
            # Sarim peste partile de rationament intern.
            if getattr(parte, "thought", False):
                continue
            if getattr(parte, "text", None):
                bucati.append(parte.text)
    return "".join(bucati).strip()


def _construieste_prompt(
    nume: str,
    rating_elo: int,
    nivel: int,
    win_rate: float,
    nr_meciuri: int,
    intrebare: str = "",
    evolutie_elo: int | None = None,
    ultimele_meciuri: list[str] | None = None,
) -> str:
    """Construieste prompt-ul cu statisticile reale ale jucatorului."""
    nivel_text = _NIVEL_MAP.get(nivel, "intermediar")

    linii = [
        "Profilul real al jucatorului, din baza de date CueUp:",
        f"- nume: {nume}",
        f"- rating ELO actual: {rating_elo}",
        f"- nivel declarat: {nivel_text} ({nivel} din 5)",
        f"- meciuri finalizate: {nr_meciuri}",
        f"- rata de victorii: {win_rate:.0%}",
    ]

    if evolutie_elo is not None:
        sens = "crescut" if evolutie_elo >= 0 else "scazut"
        linii.append(
            f"- evolutie ELO fata de primul meci inregistrat: a {sens} cu "
            f"{abs(evolutie_elo)} puncte"
        )

    if ultimele_meciuri:
        linii.append("- ultimele meciuri (adversar si scor):")
        linii.extend(f"    {m}" for m in ultimele_meciuri[:10])

    if LINKURI_RECOMANDATE:
        linii.append("Linkuri permise (foloseste maximum doua, exact asa cum sunt scrise):")
        linii.extend(f"    {url}" for url in LINKURI_RECOMANDATE)

    if intrebare.strip():
        linii.append(f'Problema descrisa de jucator: "{intrebare.strip()}"')
        linii.append(
            "Raspunde exact la problema lui, in 4-6 propozitii, cu un exercitiu "
            "practic concret, si leaga sfatul de cifrele de mai sus."
        )
    else:
        linii.append(
            "Ofera un sfat de antrenament personalizat in 3-4 propozitii, "
            "adaptat exact acestui profil, cu un exercitiu practic concret."
        )

    return "\n".join(linii)


def sfat_coaching(
    nume: str,
    rating_elo: int,
    nivel: int,
    win_rate: float,
    nr_meciuri: int,
    intrebare: str = "",
    evolutie_elo: int | None = None,
    ultimele_meciuri: list[str] | None = None,
) -> str:
    """
    Returneaza un sfat de antrenament personalizat in romana, generat de Gemini
    pe baza statisticilor reale ale jucatorului.

    Nu ridica exceptii: la orice eroare de retea sau API intoarce raspunsul
    de rezerva, ca demo-ul sa functioneze in orice conditii.
    """
    if not _API_KEY:
        logger.warning("GEMINI_API_KEY lipseste din .env; se foloseste raspunsul de rezerva.")
        return _FALLBACK

    prompt = _construieste_prompt(
        nume=nume,
        rating_elo=rating_elo,
        nivel=nivel,
        win_rate=win_rate,
        nr_meciuri=nr_meciuri,
        intrebare=intrebare,
        evolutie_elo=evolutie_elo,
        ultimele_meciuri=ultimele_meciuri,
    )

    try:
        resp = _get_client().models.generate_content(
            model=_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_INSTRUCTION,
                temperature=0.75,
                max_output_tokens=_MAX_OUTPUT_TOKENS,
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        )
    except Exception:
        logger.exception("Apelul Gemini a esuat pentru modelul %s", _MODEL)
        return _FALLBACK

    text = _extrage_text(resp)
    if not text:
        finish = None
        if resp.candidates:
            finish = getattr(resp.candidates[0], "finish_reason", None)
        logger.warning("Gemini a returnat raspuns gol (finish_reason=%s)", finish)
        return _FALLBACK

    return text
