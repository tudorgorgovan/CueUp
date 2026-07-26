"""
auth.py – Autentificare via coloana `parola` din Jucatori (Azure SQL).
SQLite-ul local nu mai este necesar.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import verify_login, email_exists, register_player


def verify_user(email: str, parola: str):
    """
    Verifică credențialele direct în Azure SQL.
    Returnează dict-ul jucătorului dacă sunt corecte, altfel None.
    """
    return verify_login(email.strip(), parola)


def email_registered(email: str) -> bool:
    """Returnează True dacă email-ul există deja în Jucatori."""
    return email_exists(email.strip())


def register_user(
    nume: str,
    email: str,
    parola: str,
    id_oras: int,
    nivel: int,
) -> bool:
    """
    Înregistrează un jucător nou în Azure SQL.
    Returnează True la succes, False dacă email-ul există deja sau INSERT eșuează.
    """
    email = email.strip()
    if email_exists(email):
        return False
    try:
        register_player(nume, email, parola, id_oras, nivel)
        return True
    except Exception:
        return False
