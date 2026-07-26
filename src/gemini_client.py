"""
gemini_client.py – Apel REST către Gemini API pentru sfat de antrenament.

Folosit în pagina Profilul Meu → tab „Sfat AI".
"""

import os
import requests
from google import genai
from dotenv import load_dotenv

load_dotenv()

_API_KEY = os.getenv("GEMINI_API_KEY", "")
_MODEL   = os.getenv("GEMINI_MODEL")
_URL     = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"


def sfat_coaching(
    nume: str,
    rating_elo: int,
    nivel: int,
    win_rate: float,
    nr_meciuri: int,
) -> str:
    """
    Returnează un sfat de antrenament personalizat în română,
    generat de Gemini pe baza profilului jucătorului.
    """
    if not _API_KEY:
        return "⚠️ Cheia API Gemini nu este configurată în fișierul .env."

    nivel_map = {
        1: "începător",
        2: "elementar",
        3: "intermediar",
        4: "avansat",
        5: "expert",
    }
    nivel_text = nivel_map.get(nivel, "intermediar")

    prompt = (
        f"Ești un antrenor virtual de biliard pentru aplicația CueUp, o platformă română.\n"
        f"Jucătorul {nume} are ELO {rating_elo}, nivel {nivel_text}, "
        f"{nr_meciuri} meciuri finalizate și o rată de victorii de {win_rate:.0%}.\n"
        f"Oferă un sfat de antrenament personalizat în română, în maxim 3 propoziții, "
        f"adaptat exact profilului său. Fii motivațional și concret. "
        f"Nu folosi liste, doar text continuu. Nu include salutări."
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.75,
            "maxOutputTokens": 300,
        },
    }

    try:
        resp = requests.post(
            _URL.format(model=_MODEL, key=_API_KEY),
            json=payload,
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except requests.exceptions.HTTPError:
        try:
            err_msg = resp.json().get("error", {}).get("message", "eroare necunoscută")
            # Scurtăm mesajul dacă e prea lung
            if len(err_msg) > 200:
                err_msg = err_msg[:200] + "..."
        except Exception:
            err_msg = resp.text[:200]
        return f"⚠️ Eroare Gemini {resp.status_code}: {err_msg}"
    except Exception as e:
        return f"⚠️ Eroare la apelul Gemini: {e}"
