from __future__ import annotations

from collections import Counter

import pandas as pd
import plotly.express as px
import streamlit as st

from ..config import COMPANIES, DEG_MAP, DEMO_USERS, STATUS_ORDER, candidate_name
from ..ui import get_job_status, hero, metric_card, pct, pills_html, score_fmt

def page_candidate_explorer(data: dict, company_id: int):
    milp = data["methods"].get("MILP", pd.DataFrame())
    cm = milp[milp["company_id"] == company_id] if not milp.empty else pd.DataFrame()

    hero("Candidate Explorer", "Search and compare candidates across all shortlisted roles.", eyebrow="Talent Pool", variant="candidate")

    if cm.empty:
        st.info("No candidates in scope.")
        return

    col_a, col_b = st.columns(2)
    with col_a:
        min_score = st.slider("Minimum Match Score", 0.0, 1.0, 0.5, 0.05)
    with col_b:
        dept_filter = st.multiselect("Departments", sorted(cm["department"].unique()), default=sorted(cm["department"].unique()))

    filtered = cm[(cm["pair_score"] >= min_score) & (cm["department"].isin(dept_filter))]
    filtered = filtered.sort_values("pair_score", ascending=False)
    st.markdown(f"**{len(filtered)} candidates** match your filters")

    display = filtered[["candidate_name", "job_title", "department", "pair_score", "must_have_hits", "exp_years", "degree_level", "review_minutes_capped"]].copy()
    display.columns = ["Name", "Role", "Department", "Score", "Skill Hits", "Exp (yrs)", "Degree", "Review (min)"]
    display["Score"] = display["Score"].round(3)
    display["Review (min)"] = display["Review (min)"].round(1)
    display["Degree"] = display["Degree"].map(lambda x: DEG_MAP.get(int(x), "?") if pd.notna(x) else "?")
    st.dataframe(display, hide_index=True, use_container_width=True, height=500)

    st.subheader("Score Distribution")
    fig = px.histogram(filtered, x="pair_score", nbins=30, color="department", labels={"pair_score": "Match Score", "department": "Department"})
    fig.update_layout(height=350, margin=dict(t=20, b=40))
    st.plotly_chart(fig, use_container_width=True)