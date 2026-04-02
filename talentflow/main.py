from __future__ import annotations

import streamlit as st

from .config import APP_ICON, APP_TITLE, COMPANIES, DEMO_USERS
from .data import load_data
from .pages.admin import page_admin_overview
from .pages.candidate import page_candidate_explorer
from .pages.company import page_company_dashboard
from .pages.job import page_job_workbench
from .pages.scenario import page_scenario_lab
from .pages.login import page_login
from .ui import inject_css


def main():
    st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide", initial_sidebar_state="expanded")
    inject_css()

    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("user_email", "")
    st.session_state.setdefault("actions", {})
    st.session_state.setdefault("nav_page", "Company Dashboard")
    st.session_state.setdefault("company_scope", 0)
    st.session_state.setdefault("active_user_email", "")

    if not st.session_state.logged_in:
        page_login()
        return

    data = load_data()
    user = DEMO_USERS[st.session_state.user_email]
    company_id = user["company_id"]
    is_admin = company_id == -1

    if st.session_state.active_user_email != st.session_state.user_email:
        st.session_state.active_user_email = st.session_state.user_email
        st.session_state.nav_page = "Admin Overview" if is_admin else "Company Dashboard"
        if is_admin:
            st.session_state.company_scope = 0

    with st.sidebar:
        st.markdown(f"## {APP_ICON} {APP_TITLE}")
        st.caption("AI-Powered Shortlisting")
        st.markdown(
            f'<div class="section-panel">'
            f'<strong>{user["name"]}</strong><br>'
            f'<span style="color:#6b7280;">{user["role"]}</span><br>'
            f'<span style="color:#6b7280;">'
            f'{COMPANIES[company_id]["name"] if company_id >= 0 else "All Companies"}'
            f'</span></div>',
            unsafe_allow_html=True,
        )

        if is_admin:
            pages = ["Admin Overview", "Company Dashboard", "Job Workbench", "Candidate Explorer", "Scenario Lab"]
            company_id = st.selectbox(
                "Company Scope",
                list(COMPANIES.keys()),
                format_func=lambda x: COMPANIES[x]["name"],
                key="company_scope",
            )
        else:
            pages = ["Company Dashboard", "Job Workbench", "Candidate Explorer", "Scenario Lab"]

        if st.session_state.nav_page not in pages:
            st.session_state.nav_page = pages[0]

        page = st.radio("Navigate", pages, key="nav_page")
        st.markdown("---")
        if st.button("Sign Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.active_user_email = ""
            st.session_state.nav_page = "Company Dashboard"
            st.rerun()

    if page != "Job Workbench":
        st.session_state.resume_dialog_open = False
        st.session_state.pop("resume_dialog_candidate_name", None)
        st.session_state.pop("resume_dialog_resume_text", None)
        st.session_state.pop("resume_preview_len", None)

    if page == "Admin Overview" and is_admin:
        page_admin_overview(data, company_id)
    elif page == "Company Dashboard":
        page_company_dashboard(data, company_id)
    elif page == "Job Workbench":
        page_job_workbench(data, company_id, is_admin)
    elif page == "Candidate Explorer":
        page_candidate_explorer(data, company_id)
    elif page == "Scenario Lab":
        page_scenario_lab(data)


if __name__ == "__main__":
    main()
