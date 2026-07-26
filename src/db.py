"""
db.py - Conexiune Azure SQL + cele 5 interogari SQL obligatorii.

Q1 (WHERE) : cauta_parteneri           - jucatori din acelasi oras cu ELO in interval
Q2 (WHERE) : mese_active_club          - mese active dintr-un club (+ filtru optional tip)
Q3 (WHERE) : rezervari_jucator         - rezervarile unui jucator filtrate dupa status
Q4 (HAVING): orase_active              - orase cu cel putin N jucatori activi
Q5 (HAVING): clasament_jucatori_activi - jucatori cu > N rezervari finalizate

Autentificare: verify_login / email_exists / register_player
  -> folosesc coloana `parola` din tabelul Jucatori (fara SQLite local)

Toate interogarile sunt parametrizate cu `?`, niciodata construite prin
concatenare de string-uri. Citirile care nu depind de utilizator sunt puse in
cache cu st.cache_data, iar scrierile golesc cache-ul.
"""

import os
from contextlib import closing

import pyodbc
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Cat timp tinem in cache datele citite din baza.
_TTL_REFERINTA = "30m"   # orase, cluburi, mese - se schimba rar
_TTL_STATISTICI = "5m"   # clasamente, agregari


# ── Conexiune ─────────────────────────────────────────────────────────────────

def get_conn() -> pyodbc.Connection:
    conn_str = (
        f"DRIVER={os.getenv('DB_DRIVER', '{ODBC Driver 17 for SQL Server}')};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USER')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)


def _df(sql: str, params=None) -> pd.DataFrame:
    """
    Ruleaza o interogare si intoarce un DataFrame.

    `closing` este obligatoriu: context managerul propriu al pyodbc face doar
    commit/rollback, NU inchide conexiunea. Fara el fiecare interogare lasa in
    urma o conexiune deschisa si Azure SQL le refuza pe urmatoarele.
    """
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute(sql, params or [])
        coloane = [d[0] for d in cur.description]
        return pd.DataFrame.from_records(cur.fetchall(), columns=coloane)


def _executa(sql: str, params) -> None:
    """Ruleaza un INSERT/UPDATE si face commit."""
    with closing(get_conn()) as conn:
        conn.cursor().execute(sql, params)
        conn.commit()


# ── Q1: WHERE - Parteneri din acelasi oras cu ELO in interval ─────────────────
@st.cache_data(ttl=_TTL_STATISTICI, show_spinner=False)
def cauta_parteneri(id_oras: int, elo_min: int, elo_max: int,
                    exclude_id: int) -> pd.DataFrame:
    sql = """
        SELECT j.id_jucator, j.nume, j.email,
               j.nivel_declarat, j.rating_elo,
               j.data_inscriere, o.nume_oras
        FROM   Jucatori j
        JOIN   Orase    o ON j.id_oras = o.id_oras
        WHERE  j.id_oras   = ?
          AND  j.rating_elo BETWEEN ? AND ?
          AND  j.id_jucator != ?
        ORDER  BY j.rating_elo DESC
    """
    return _df(sql, [id_oras, elo_min, elo_max, exclude_id])


# ── Q2: WHERE - Mese active dintr-un club ─────────────────────────────────────
@st.cache_data(ttl=_TTL_REFERINTA, show_spinner=False)
def mese_active_club(id_club: int, tip_masa: str = None) -> pd.DataFrame:
    if tip_masa:
        sql = """
            SELECT id_masa, cod_masa, tip_masa, tarif_orar
            FROM   Mese
            WHERE  id_club = ? AND activa = 1 AND tip_masa = ?
            ORDER  BY tip_masa, tarif_orar
        """
        return _df(sql, [id_club, tip_masa])
    sql = """
        SELECT id_masa, cod_masa, tip_masa, tarif_orar
        FROM   Mese
        WHERE  id_club = ? AND activa = 1
        ORDER  BY tip_masa, tarif_orar
    """
    return _df(sql, [id_club])


# ── Q3: WHERE - Rezervarile unui jucator filtrate dupa status ─────────────────
def rezervari_jucator(id_jucator: int, status: str = None) -> pd.DataFrame:
    base = """
        SELECT r.id_rezervare, m.cod_masa, m.tip_masa,
               c.nume AS club, o.nume_oras,
               r.data_start, r.data_sfarsit, r.status, r.suma
        FROM   Rezervari r
        JOIN   Mese    m ON r.id_masa  = m.id_masa
        JOIN   Cluburi c ON m.id_club  = c.id_club
        JOIN   Orase   o ON c.id_oras  = o.id_oras
        WHERE  r.id_jucator = ?
    """
    if status:
        return _df(base + " AND r.status = ? ORDER BY r.data_start DESC",
                   [id_jucator, status])
    return _df(base + " ORDER BY r.data_start DESC", [id_jucator])


# ── Q4: HAVING - Orase cu cel putin N jucatori activi ─────────────────────────
@st.cache_data(ttl=_TTL_STATISTICI, show_spinner=False)
def orase_active(min_jucatori: int = 10) -> pd.DataFrame:
    """
    Orasele care au cel putin `min_jucatori` jucatori cu rezervari finalizate
    - masura a comunitatii active pe oras.
    """
    sql = """
        SELECT o.id_oras, o.nume_oras, o.judet,
               COUNT(DISTINCT j.id_jucator) AS jucatori_activi,
               AVG(CAST(j.rating_elo AS FLOAT)) AS elo_mediu
        FROM   Orase     o
        JOIN   Jucatori  j ON j.id_oras     = o.id_oras
        JOIN   Rezervari r ON r.id_jucator  = j.id_jucator
        WHERE  r.status = 'finalizata'
        GROUP  BY o.id_oras, o.nume_oras, o.judet
        HAVING COUNT(DISTINCT j.id_jucator) >= ?
        ORDER  BY jucatori_activi DESC
    """
    return _df(sql, [min_jucatori])


# ── Q5: HAVING - Jucatori cu > N rezervari finalizate (clasament activi) ──────
@st.cache_data(ttl=_TTL_STATISTICI, show_spinner=False)
def clasament_jucatori_activi(min_rezervari: int = 3) -> pd.DataFrame:
    sql = """
        SELECT j.id_jucator, j.nume, o.nume_oras,
               j.rating_elo, j.nivel_declarat,
               COUNT(r.id_rezervare) AS nr_rezervari_finalizate
        FROM   Jucatori  j
        JOIN   Orase     o ON j.id_oras     = o.id_oras
        JOIN   Rezervari r ON j.id_jucator  = r.id_jucator
        WHERE  r.status = 'finalizata'
        GROUP  BY j.id_jucator, j.nume, o.nume_oras,
                  j.rating_elo, j.nivel_declarat
        HAVING COUNT(r.id_rezervare) > ?
        ORDER  BY j.rating_elo DESC
    """
    return _df(sql, [min_rezervari])


# ── Helpers generale ──────────────────────────────────────────────────────────

@st.cache_data(ttl=_TTL_REFERINTA, show_spinner=False)
def get_orase() -> pd.DataFrame:
    return _df("SELECT id_oras, nume_oras, judet FROM Orase ORDER BY nume_oras")


@st.cache_data(ttl=_TTL_REFERINTA, show_spinner=False)
def get_cluburi_oras(id_oras: int) -> pd.DataFrame:
    sql = """
        SELECT c.id_club, c.nume, c.adresa, c.telefon,
               c.ora_deschidere, c.ora_inchidere, c.rating_club
        FROM   Cluburi c
        WHERE  c.id_oras = ?
        ORDER  BY c.rating_club DESC
    """
    return _df(sql, [id_oras])


def get_jucator_by_email(email: str) -> pd.DataFrame:
    sql = """
        SELECT j.*, o.nume_oras
        FROM   Jucatori j
        JOIN   Orase    o ON j.id_oras = o.id_oras
        WHERE  j.email = ?
    """
    return _df(sql, [email])


def get_jucator_by_id(id_jucator: int) -> pd.DataFrame:
    sql = """
        SELECT j.*, o.nume_oras
        FROM   Jucatori j
        JOIN   Orase    o ON j.id_oras = o.id_oras
        WHERE  j.id_jucator = ?
    """
    return _df(sql, [id_jucator])


# ── Autentificare - folosind coloana `parola` din Jucatori ────────────────────

def verify_login(email: str, parola: str):
    """
    Verifica email + parola direct in Azure SQL.
    Returneaza dict-ul jucatorului (cu nume_oras) daca sunt corecte, altfel None.
    """
    sql = """
        SELECT j.*, o.nume_oras
        FROM   Jucatori j
        JOIN   Orase    o ON j.id_oras = o.id_oras
        WHERE  j.email                         = ?
          AND  REPLACE(j.parola, CHAR(13), '') = ?
    """
    df = _df(sql, [email, parola])
    return df.iloc[0].to_dict() if not df.empty else None


def email_exists(email: str) -> bool:
    """True daca email-ul exista deja in Jucatori."""
    sql = "SELECT COUNT(*) AS cnt FROM Jucatori WHERE email = ?"
    return int(_df(sql, [email]).iloc[0]["cnt"]) > 0


def register_player(nume: str, email: str, parola: str,
                    id_oras: int, nivel_declarat: int) -> None:
    """
    Insereaza un jucator nou in Jucatori cu ELO 1200 si data de azi.
    Ridica exceptie daca INSERT esueaza.
    """
    sql = """
        INSERT INTO Jucatori
               (nume, email, id_oras, nivel_declarat,
                rating_elo, data_inscriere, parola)
        VALUES (?, ?, ?, ?, 1200, CAST(GETDATE() AS DATE), ?)
    """
    _executa(sql, [nume, email, id_oras, nivel_declarat, parola])
    # Clasamentele si numaratorile pe oras s-au schimbat.
    st.cache_data.clear()


# ── Clasamente si numaratori ──────────────────────────────────────────────────

@st.cache_data(ttl=_TTL_STATISTICI, show_spinner=False)
def get_rank_in_city(id_oras: int, rating_elo: int) -> int:
    sql = "SELECT COUNT(*) + 1 AS rank_oras FROM Jucatori WHERE id_oras = ? AND rating_elo > ?"
    return int(_df(sql, [id_oras, rating_elo]).iloc[0]["rank_oras"])


@st.cache_data(ttl=_TTL_STATISTICI, show_spinner=False)
def get_rank_national(rating_elo: int) -> int:
    sql = "SELECT COUNT(*) + 1 AS rank_national FROM Jucatori WHERE rating_elo > ?"
    return int(_df(sql, [rating_elo]).iloc[0]["rank_national"])


@st.cache_data(ttl=_TTL_STATISTICI, show_spinner=False)
def get_count_city(id_oras: int) -> int:
    return int(_df("SELECT COUNT(*) AS total FROM Jucatori WHERE id_oras = ?",
                   [id_oras]).iloc[0]["total"])


@st.cache_data(ttl=_TTL_STATISTICI, show_spinner=False)
def get_count_national() -> int:
    return int(_df("SELECT COUNT(*) AS total FROM Jucatori").iloc[0]["total"])


# ── Rezervari ─────────────────────────────────────────────────────────────────

def check_masa_disponibila(id_masa: int, data_start: str, data_sfarsit: str) -> bool:
    """
    Masa e libera daca nu exista rezervare care se suprapune peste interval.
    Doar 'confirmata' si 'finalizata' ocupa masa; 'anulata' si 'no_show' o elibereaza.
    Suprapunere: start_existent < sfarsit_cerut AND sfarsit_existent > start_cerut.
    """
    sql = """
        SELECT COUNT(*) AS conflicte
        FROM   Rezervari
        WHERE  id_masa = ?
          AND  status IN ('confirmata', 'finalizata')
          AND  data_start   < ?
          AND  data_sfarsit > ?
    """
    return int(_df(sql, [id_masa, data_sfarsit, data_start]).iloc[0]["conflicte"]) == 0


def create_rezervare(id_masa: int, id_jucator: int,
                     data_start: str, data_sfarsit: str, suma: float) -> None:
    sql = """
        INSERT INTO Rezervari (id_masa, id_jucator, data_start, data_sfarsit,
                               status, suma, creata_la)
        VALUES (?, ?, ?, ?, 'confirmata', ?, GETDATE())
    """
    _executa(sql, [id_masa, id_jucator, data_start, data_sfarsit, suma])


# ── Istoric si meciuri ────────────────────────────────────────────────────────

@st.cache_data(ttl=_TTL_STATISTICI, show_spinner=False)
def get_istoric_rating(id_jucator: int) -> pd.DataFrame:
    sql = """
        SELECT ir.data, ir.rating_inainte, ir.rating_dupa
        FROM   IstoricRating ir
        WHERE  ir.id_jucator = ?
        ORDER  BY ir.data ASC
    """
    return _df(sql, [id_jucator])


@st.cache_data(ttl=_TTL_STATISTICI, show_spinner=False)
def get_meciuri_jucator(id_jucator: int) -> pd.DataFrame:
    """
    Doar meciurile finalizate: au adversar si scor, deci pot intra in win-rate.
    Meciurile 'fara_rezultat', 'programat', 'asteptare' si 'expirat' au scor NULL
    si ar strica numitorul.
    """
    sql = """
        SELECT m.id_meci, m.scor_1, m.scor_2, m.tip, m.stare,
               j1.nume AS jucator_1, j2.nume AS jucator_2,
               m.id_castigator
        FROM   Meciuri  m
        JOIN   Jucatori j1 ON m.id_jucator_1 = j1.id_jucator
        JOIN   Jucatori j2 ON m.id_jucator_2 = j2.id_jucator
        WHERE  (m.id_jucator_1 = ? OR m.id_jucator_2 = ?)
          AND  m.stare = 'finalizat'
        ORDER  BY m.id_meci DESC
    """
    return _df(sql, [id_jucator, id_jucator])
