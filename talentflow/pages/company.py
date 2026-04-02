from __future__ import annotations

from collections import Counter

import pandas as pd
import plotly.express as px
import streamlit as st

from ..config import COMPANIES
from ..ui import get_job_status, hero, metric_card, pct, score_fmt


def page_company_dashboard(data: dict, company_id: int):
    info = COMPANIES[company_id]
    milp = data["methods"].get("MILP", pd.DataFrame())
    cm = milp[milp["company_id"] == company_id] if not milp.empty else pd.DataFrame()
    cj = data["job_df"][data["job_df"]["company_id"] == company_id]

    hero(f"{info['name']}", f"Shortlist health — {info['industry']} | HQ: {info['hq']}", eyebrow="Company Dashboard", variant="company")

    if cm.empty:
        st.info("No shortlisted candidates for this company.")
        return

    job_fill = cm.groupby("job_id").size().reindex(cj["job_id"], fill_value=0)
    full = int((job_fill >= 5).sum())

    c1, c2, c3, c4 = st.columns(4)
    metric_card(c1, "Open Roles", str(len(cj)), f"{full} fully shortlisted")
    metric_card(c2, "Total Shortlisted", str(len(cm)), "Candidates selected")
    metric_card(c3, "Avg Match Score", score_fmt(cm["pair_score"].mean()), "Normalised 0–1")
    metric_card(c4, "Skill Hit Rate", pct(cm["weighted_required_hit"].mean()), "Required skill coverage")

    st.markdown("---")
    col_left, col_right = st.columns([0.9, 0.8])

    with col_left:
        st.subheader("Role Health")
        title_counts_cd = cj["job_title"].value_counts()
        rows = []
        for _, job in cj.iterrows():
            jsel = cm[cm["job_id"] == job["job_id"]]
            n = len(jsel)
            req = set(job["required_skills"]) if isinstance(job["required_skills"], list) else set()
            covered = set()
            for _, r in jsel.iterrows():
                sk = r["skill_set"] if isinstance(r["skill_set"], list) else []
                covered |= (set(sk) & req)
            cov = len(covered) / max(len(req), 1)
            status = get_job_status(n / 5, cov)
            role_label = job["job_title"]
            if title_counts_cd[role_label] > 1:
                role_label = f"{role_label}  #{job['job_id']}"
            rows.append({"Role": role_label, "Department": job["department"], "Shortlisted": f"{n}/5", "Avg Score": round(jsel["pair_score"].mean(), 3) if n else 0, "Skill Coverage": pct(cov), "Status": status})
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height = 700)

    with col_right:
        st.subheader("Department Breakdown")
        dept = cm.groupby("department").agg(roles=("job_id", "nunique"), candidates=("resume_id", "count"), score=("pair_score", "mean")).reset_index()
        dept["score"] = dept["score"].round(3)
        st.dataframe(dept, hide_index=True, use_container_width=True)

        st.subheader("Top Skills In Demand")
        sc = Counter()
        for skills in cj["required_skills"]:
            if isinstance(skills, list):
                sc.update(skills)
        top = pd.DataFrame(sc.most_common(10), columns=["Skill", "Demand"])
        fig = px.bar(top, x="Demand", y="Skill", orientation="h", color_discrete_sequence=["#fdba74"])
        fig.update_layout(height=320, margin=dict(t=10, b=30), yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)
