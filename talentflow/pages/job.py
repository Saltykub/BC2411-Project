from __future__ import annotations

import streamlit as st
import pandas as pd
from ..config import COMPANIES, DEG_MAP, DEMO_USERS, STATUS_ORDER, candidate_name
from ..ui import hero, metric_card, pills_html, score_fmt


def _lucide_icon(name: str) -> str:
    paths = {
        "user-round": '<circle cx="12" cy="8" r="5"></circle><path d="M20 21a8 8 0 0 0-16 0"></path>',
        "file-text": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><path d="M14 2v6h6"></path><path d="M16 13H8"></path><path d="M16 17H8"></path><path d="M10 9H8"></path>',
        "mail": '<path d="M22 6H2v12h20V6z"></path><path d="m2 7 10 7L22 7"></path>',
    }
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        'style="vertical-align:-2px; margin-right:0.35rem;">'
        f"{paths.get(name, '')}"
        "</svg>"
    )


def _clear_resume_dialog_state():
    st.session_state.resume_dialog_open = False
    st.session_state.pop("resume_dialog_candidate_name", None)
    st.session_state.pop("resume_dialog_resume_text", None)
    st.session_state.pop("resume_preview_len", None)
    st.session_state.pop("resume_dialog_method", None)
    st.session_state.pop("resume_dialog_dept", None)
    st.session_state.pop("resume_dialog_job_id", None)


def _resume_dialog_context(method: str, dept: str, job_id: int) -> tuple[str, str, int]:
    return method, dept, job_id


@st.dialog("Resume Preview", width="large")
def _show_resume_dialog():
    candidate_name = st.session_state.get("resume_dialog_candidate_name", "Candidate")
    resume_text = st.session_state.get("resume_dialog_resume_text", "Resume text not available.")
    preview_chars = st.slider(
        "Preview length",
        min_value=800,
        max_value=12000,
        value=4000,
        step=200,
        key="resume_preview_len",
    )
    st.markdown(
        '<div style="display:flex; align-items:center; gap:0.4rem; margin-bottom:0.35rem;">'
        f'{_lucide_icon("file-text")}'
        f'<strong>{candidate_name}</strong></div>',
        unsafe_allow_html=True,
    )
    st.text_area(
        "Resume text",
        value=resume_text[:preview_chars],
        height=420,
        disabled=True,
        label_visibility="collapsed",
    )
    if st.button("Close", key="close_resume_dialog", type="primary", use_container_width=True):
        _clear_resume_dialog_state()
        st.rerun()


def page_job_workbench(data: dict, company_id: int, is_admin: bool):
    company_jobs = data["job_df"][data["job_df"]["company_id"] == company_id]

    hero("Job Workbench", "Review shortlisted candidates, compare skill fit, and take hiring actions.", eyebrow="Recruiter Workspace", variant="job")

    if company_jobs.empty:
        st.info("No jobs for this company.")
        return

    col_a, col_b = st.columns(2)
    dept_options = sorted(company_jobs["department"].unique())
    with col_a:
        dept = st.selectbox("Department", dept_options, key="wb_dept")
    dept_jobs = company_jobs[company_jobs["department"] == dept].sort_values("job_id")

    title_counts = dept_jobs["job_title"].value_counts()

    def _role_label(row):
        if title_counts[row["job_title"]] > 1:
            return f"{row['job_title']}  #{row['job_id']}"
        return row["job_title"]

    role_labels = {int(r["job_id"]): _role_label(r) for _, r in dept_jobs.iterrows()}

    with col_b:
        job_id = st.selectbox("Role", dept_jobs["job_id"].tolist(), format_func=lambda jid: role_labels.get(jid, str(jid)), key="wb_role")

    method = st.radio("Method", ["MILP", "Greedy", "ScoreOnly"], horizontal=True, key="wb_method")

    current_context = _resume_dialog_context(method, dept, job_id)
    saved_context = (
        st.session_state.get("resume_dialog_method"),
        st.session_state.get("resume_dialog_dept"),
        st.session_state.get("resume_dialog_job_id"),
    )
    if st.session_state.get("resume_dialog_open") and saved_context != current_context:
        _clear_resume_dialog_state()

    sel_df = data["methods"].get(method, pd.DataFrame())
    job_sel = sel_df[sel_df["job_id"] == job_id].sort_values("pair_score", ascending=False) if not sel_df.empty else pd.DataFrame()
    job_row = data["job_df"][data["job_df"]["job_id"] == job_id].iloc[0]

    req_skills = job_row["required_skills"] if isinstance(job_row["required_skills"], list) else []
    st.markdown(f'<div class="section-panel"><strong>Required Skills:</strong><br>{pills_html(req_skills, "blue")}</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    label_method = "Optimised by TalentFlow" if not is_admin else f"{method} method"
    metric_card(c1, "Shortlisted", f"{len(job_sel)}/5", label_method)
    metric_card(c2, "Top Score", score_fmt(job_sel["pair_score"].max()) if len(job_sel) else "—", "Best candidate match")
    total_time = job_sel["review_minutes_capped"].sum() if len(job_sel) else 0
    metric_card(c3, "Total Review Time", f"{total_time:.0f} min", "Budget: 65 min")

    st.markdown("---")

    if job_sel.empty:
        st.warning("No candidates shortlisted for this role.")
        return

    candidates = list(job_sel.iterrows())
    for i in range(0, len(candidates), 2):
        left_col, right_col = st.columns(2)
        for card_col, (_, row) in zip([left_col, right_col], candidates[i:i + 2]):
            with card_col:
                rid = int(row["resume_id"])
                cname = row.get("candidate_name", candidate_name(rid))
                score = row["pair_score"]
                matched = row["matched_skills"] if isinstance(row["matched_skills"], list) else []
                missing = row["missing_skills"] if isinstance(row["missing_skills"], list) else []
                exp = row.get("exp_years", "?")
                deg = DEG_MAP.get(int(row.get("degree_level", 0)), "?")
                resume_text = row.get("_resume_text", "Resume text not available.")

                pair_key = f"{method}:{job_id}:{rid}"
                st.session_state.setdefault("actions", {})
                st.session_state["actions"].setdefault(pair_key, "Pending")

                st.markdown(
                    f'<div class="candidate-card">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                    f'<div>{_lucide_icon("user-round")}'
                    f'<strong style="font-size:1.1rem;">{cname}</strong> '
                    f'<span class="pill pill-purple">{deg}</span> '
                    f'<span class="pill pill-gray">{exp} yrs exp</span></div>'
                    f'<div style="font-size:1.3rem; font-weight:800; color:#2563eb;">{score:.3f}</div></div>'
                    f'<div style="margin-top:0.6rem;">'
                    f'<strong>Matched Skills:</strong> {pills_html(matched, "green")}<br>'
                    f'<strong>Missing Skills:</strong> {pills_html(missing, "red")}</div></div>',
                    unsafe_allow_html=True,
                )

                text = str(resume_text) if isinstance(resume_text, str) else "Resume text not available."
                # resume_col_a, resume_col_b = st.columns([1, 4])
                # with resume_col_a:
                if st.button("View Resume", key=f"resume_btn_{pair_key}", use_container_width=True):
                    st.session_state.resume_dialog_candidate_name = cname
                    st.session_state.resume_dialog_resume_text = text
                    st.session_state.resume_dialog_open = True
                    st.session_state.resume_dialog_method = method
                    st.session_state.resume_dialog_dept = dept
                    st.session_state.resume_dialog_job_id = job_id
                    st.rerun()

                if not is_admin:
                    ac1, ac2, ac3 = st.columns([1, 2.5, 1.5])
                    with ac1:
                        cur_idx = STATUS_ORDER.index(st.session_state["actions"][pair_key]) if st.session_state["actions"][pair_key] in STATUS_ORDER else 0
                        new_status = st.selectbox("Decision", STATUS_ORDER, key=f"dec_{pair_key}", index=cur_idx)
                        st.session_state["actions"][pair_key] = new_status
                    with ac2:
                        st.text_input("Recruiter Note", key=f"note_{pair_key}", placeholder="Add note…")
                    with ac3:
                        st.markdown("""
                                        <style>
                                        div.stButton > button {
                                            height: 48px;
                                            font-size: 14px;
                                            padding: 0 16px;
                                        }
                                        </style>
                                """, unsafe_allow_html=True)
                        if st.button("Send Interview Invite", key=f"email_{pair_key}"):
                            st.session_state.resume_dialog_open = False
                            st.session_state.pop("resume_dialog_candidate_name", None)
                            st.session_state.pop("resume_dialog_resume_text", None)
                            st.session_state.pop("resume_preview_len", None)
                            st.session_state.pop("resume_dialog_method", None)
                            st.session_state.pop("resume_dialog_dept", None)
                            st.session_state.pop("resume_dialog_job_id", None)
                            st.session_state[f"show_email_{pair_key}"] = True

                    if st.session_state.get(f"show_email_{pair_key}"):
                        with st.expander("Compose Interview Email", expanded=True):
                            st.markdown(
                                '<div style="display:flex; align-items:center; gap:0.4rem; margin-bottom:0.35rem;">'
                                f'{_lucide_icon("mail")}'
                                '<strong>Interview Invitation</strong></div>',
                                unsafe_allow_html=True,
                            )
                            recruiter = DEMO_USERS[st.session_state.user_email]
                            comp_name = COMPANIES[company_id]["name"]
                            to_email = st.text_input("Candidate Email", value="candidate123@gmail.com", key=f"to_{pair_key}")
                            subject = st.text_input("Subject", value=f"Interview Invitation — {job_row['job_title']} at {comp_name}", key=f"subj_{pair_key}")
                            body = st.text_area(
                                "Body",
                                height=260,
                                key=f"body_{pair_key}",
                                value=(
                                    f"Dear {cname},\n\n"
                                    f"We are pleased to inform you that your application for the "
                                    f"{job_row['job_title']} position at {comp_name} has been shortlisted.\n\n"
                                    f"After a thorough review of your qualifications, we believe your "
                                    f"background is a strong fit for this role and we would like to invite "
                                    f"you for an interview.\n\n"
                                    f"Please reply to this email with your availability over the next two "
                                    f"weeks, and we will schedule a session at a time that works for you.\n\n"
                                    f"If you have any questions in the meantime, feel free to reach out.\n\n"
                                    f"Best regards,\n"
                                    f"{recruiter['name']}\n"
                                    f"{recruiter['role']}\n"
                                    f"{comp_name}"
                                ),
                            )
                            if st.button("Send Email", key=f"send_{pair_key}", type="primary"):
                                st.success(f"Interview invitation sent to {cname} at {to_email}.")
                                st.session_state["actions"][pair_key] = "Interview"
                else:
                    cur_status = st.session_state.get("actions", {}).get(pair_key, "Pending")
                    st.markdown(f'<span class="pill pill-gray">Current Status: {cur_status}</span> <span style="color:#9ca3af; font-size:0.82rem;">(view-only)</span>', unsafe_allow_html=True)

                st.markdown("---")

    if st.session_state.get("resume_dialog_open"):
        _show_resume_dialog()
