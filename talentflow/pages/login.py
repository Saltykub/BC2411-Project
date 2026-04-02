from __future__ import annotations

import pandas as pd
import streamlit as st

from ..config import COMPANIES, DEMO_USERS


def page_login():
    st.markdown(
        '<div style="text-align:center; padding: 3rem 0 1rem;">'
        '<h1 style="font-size:2.5rem; font-weight:800; color:#1e3a5f;">🎯 TalentFlow</h1>'
        '<p style="color:#6b7280; font-size:1.1rem;">AI-Powered Shortlisting Platform</p></div>',
        unsafe_allow_html=True,
    )

    _, col_center, _ = st.columns([1, 1.2, 1])
    with col_center:
        with st.form("login"):
            email = st.text_input("Email", placeholder="mia.chen@apexdigital.com")
            pwd = st.text_input("Password", type="password", placeholder="talent2025")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
            if submitted:
                user = DEMO_USERS.get(email.strip().lower())
                if user and user["password"] == pwd:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email.strip().lower()
                    st.rerun()
                else:
                    st.error("Invalid credentials. Try one of the demo accounts below.")
        st.markdown("**Demo Accounts**")
        rows = [
            {"Email": e, "Name": u["name"], "Company": COMPANIES[u["company_id"]]["name"] if u["company_id"] >= 0 else "All (Admin)", "Password": u["password"]}
            for e, u in DEMO_USERS.items()
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)