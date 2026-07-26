"""pages/login.py – Autentificare / Creare Cont (parolă din Azure SQL Jucatori)."""

import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import verify_user, email_registered, register_user
from db import get_orase


def show():
    # ── Hero centrat ─────────────────────────────────────────────────────────
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown(
            """
            <div style="text-align:center; padding: 3.5rem 0 2.5rem;">
                <div style="font-size:4.5rem; margin-bottom:.6rem;">🎱</div>
                <div style="font-size:2.8rem; font-weight:900;
                            background:linear-gradient(135deg,#d4af37,#f5d87a);
                            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                            letter-spacing:.04em;">CueUp</div>
                <div style="font-size:.95rem; color:#6a8099; margin-top:6px; letter-spacing:.06em;">
                    PLATFORMA ROMÂNĂ DE BILIARD
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_login, tab_register = st.tabs(["🔑  Autentificare", "📝  Creare Cont"])

        # ── Tab Login ─────────────────────────────────────────────────────────
        with tab_login:
            with st.form("form_login", clear_on_submit=False):
                email = st.text_input(
                    "Email", placeholder="adresa@email.com", key="l_email"
                )
                parola = st.text_input(
                    "Parolă", type="password", placeholder="••••••••", key="l_pass"
                )
                submit = st.form_submit_button(
                    "Intră în cont", use_container_width=True
                )

            if submit:
                if not email or not parola:
                    st.error("❌ Completează email-ul și parola.")
                else:
                    user_dict = verify_user(email.strip(), parola)
                    if user_dict:
                        st.session_state.user = user_dict
                        st.session_state.logged_in = True
                        st.session_state.page = "clasament"
                        st.rerun()
                    else:
                        st.error("❌ Email sau parolă incorectă.")

        # ── Tab Register ──────────────────────────────────────────────────────
        with tab_register:
            st.markdown(
                """
                <div style="background:rgba(212,175,55,.08);border:1px solid rgba(212,175,55,.25);
                            border-radius:10px;padding:13px;margin-bottom:16px;
                            font-size:.84rem;color:#c8b870;line-height:1.6;">
                ℹ️ Completează datele de mai jos pentru a-ți crea un cont nou.
                Contul va fi adăugat direct în baza de date CueUp.
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Încarcă orașele pentru selectbox
            try:
                orase_df  = get_orase()
                oras_map  = dict(zip(orase_df["nume_oras"], orase_df["id_oras"]))
                oras_list = list(oras_map.keys())
            except Exception as exc:
                st.error(f"Eroare la încărcarea orașelor: {exc}")
                return

            NIVEL_OPTIONS = {
                "1 – Începător":   1,
                "2 – Elementar":   2,
                "3 – Intermediar": 3,
                "4 – Avansat":     4,
                "5 – Expert":      5,
            }

            with st.form("form_register", clear_on_submit=False):
                reg_nume  = st.text_input(
                    "Nume complet", placeholder="Ex: Ioan Popescu", key="r_nume"
                )
                reg_email = st.text_input(
                    "Email", placeholder="adresa@email.com", key="r_email"
                )
                reg_oras  = st.selectbox(
                    "Oraș", oras_list, key="r_oras"
                )
                reg_nivel = st.selectbox(
                    "Nivel de joc", list(NIVEL_OPTIONS.keys()), key="r_nivel"
                )
                reg_pass  = st.text_input(
                    "Parolă", type="password",
                    placeholder="minimum 6 caractere", key="r_pass"
                )
                reg_pass2 = st.text_input(
                    "Confirmă parola", type="password",
                    placeholder="••••••••", key="r_pass2"
                )
                submit_reg = st.form_submit_button(
                    "Creează Cont", use_container_width=True
                )

            if submit_reg:
                reg_email = reg_email.strip()
                reg_nume  = reg_nume.strip()

                if not reg_nume or not reg_email or not reg_pass:
                    st.error("❌ Completează toate câmpurile obligatorii.")
                elif len(reg_pass) < 6:
                    st.error("❌ Parola trebuie să aibă cel puțin 6 caractere.")
                elif reg_pass != reg_pass2:
                    st.error("❌ Parolele nu coincid.")
                elif email_registered(reg_email):
                    st.warning(
                        "⚠️ Acest email este deja înregistrat. "
                        "Folosește tabul Autentificare."
                    )
                else:
                    id_oras = oras_map[reg_oras]
                    nivel   = NIVEL_OPTIONS[reg_nivel]
                    ok = register_user(reg_nume, reg_email, reg_pass, id_oras, nivel)
                    if ok:
                        st.success(
                            "✅ Cont creat cu succes! "
                            "Mergi la tabul Autentificare și intră în cont."
                        )
                    else:
                        st.error(
                            "❌ Eroare la creare cont. "
                            "Verifică dacă email-ul nu este deja folosit."
                        )
