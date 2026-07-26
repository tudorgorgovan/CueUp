"""app_pages/login.py - Autentificare si creare cont (coloana `parola` din Jucatori)."""

import streamlit as st

from auth import verify_user, email_registered, register_user
from db import get_orase
from ui import NIVEL

# Coloana Jucatori.email este VARCHAR(150).
EMAIL_MAX_LEN = 150

_, mijloc, _ = st.columns([1, 2, 1])

with mijloc:
    with st.container(horizontal_alignment="center"):
        st.markdown("# 🎱")
        st.title("CueUp", text_alignment="center")
        st.caption("Platforma romaneasca de biliard", text_alignment="center")

    tab_login, tab_cont_nou = st.tabs(["Autentificare", "Cont nou"])

    # ── Autentificare ─────────────────────────────────────────────────────────
    with tab_login:
        with st.form("form_login"):
            email = st.text_input("Email", placeholder="adresa@email.com",
                                  max_chars=EMAIL_MAX_LEN)
            parola = st.text_input("Parola", type="password", placeholder="••••••••")
            intra = st.form_submit_button("Intra in cont", type="primary",
                                          width="stretch")

        if intra:
            if not email or not parola:
                st.error("Completeaza email-ul si parola.", icon=":material/error:")
            else:
                try:
                    jucator = verify_user(email, parola)
                except Exception:
                    st.error("Nu ne putem conecta la baza de date. Incearca din nou.",
                             icon=":material/cloud_off:")
                    st.stop()

                if jucator:
                    st.session_state.user = jucator
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    # Mesaj generic: nu spunem daca email-ul sau parola e gresita.
                    st.error("Email sau parola incorecta.", icon=":material/lock:")

    # ── Cont nou ──────────────────────────────────────────────────────────────
    with tab_cont_nou:
        try:
            orase_df = get_orase()
        except Exception:
            st.error("Nu s-au putut incarca orasele din baza de date.",
                     icon=":material/cloud_off:")
            st.stop()

        oras_map = dict(zip(orase_df["nume_oras"], orase_df["id_oras"]))

        with st.form("form_register"):
            nume = st.text_input("Nume complet", placeholder="Ex: Ioan Popescu")
            email_nou = st.text_input("Email", placeholder="adresa@email.com",
                                      max_chars=EMAIL_MAX_LEN, key="reg_email")
            oras = st.selectbox("Oras", list(oras_map.keys()))
            nivel = st.select_slider(
                "Nivelul tau de joc",
                options=list(NIVEL.keys()),
                value=3,
                format_func=lambda n: f"{n} · {NIVEL[n]}",
            )
            parola_noua = st.text_input("Parola", type="password",
                                        placeholder="minimum 6 caractere")
            parola_conf = st.text_input("Confirma parola", type="password",
                                        placeholder="••••••••")
            creeaza = st.form_submit_button("Creeaza cont", type="primary",
                                            width="stretch")

        if creeaza:
            nume = nume.strip()
            email_nou = email_nou.strip()

            if not nume or not email_nou or not parola_noua:
                st.error("Completeaza toate campurile.", icon=":material/error:")
            elif len(parola_noua) < 6:
                st.error("Parola trebuie sa aiba cel putin 6 caractere.",
                         icon=":material/error:")
            elif parola_noua != parola_conf:
                st.error("Parolele nu coincid.", icon=":material/error:")
            elif email_registered(email_nou):
                st.warning("Acest email este deja inregistrat. Foloseste tabul Autentificare.",
                           icon=":material/info:")
            elif register_user(nume, email_nou, parola_noua, oras_map[oras], nivel):
                st.success("Cont creat. Intra in cont din tabul Autentificare.",
                           icon=":material/check_circle:")
            else:
                st.error("Nu s-a putut crea contul. Incearca din nou.",
                         icon=":material/error:")

    with st.expander("Conturi de test", icon=":material/science:"):
        st.markdown(
            "- `adrian.lupu@gmail.com` · `Dinvyb834`\n"
            "- `tudor.gheorghe@gmail.com` · `Jitvus242`\n"
            "- `razvan.serban@gmail.com` · `Xurbow982`"
        )
