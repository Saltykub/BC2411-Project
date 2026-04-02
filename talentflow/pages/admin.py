from __future__ import annotations

from collections import Counter

import pandas as pd
import plotly.express as px
import streamlit as st

from ..config import COMPANIES, DEG_MAP, DEMO_USERS, STATUS_ORDER, candidate_name
from ..ui import get_job_status, hero, metric_card, pct, pills_html, score_fmt

def page_admin_overview(data: dict, company_id: int):
    hero("Platform Overview", "Cross-company performance, method benchmarking, and system health. This dashboard is view-only.", eyebrow="Admin Dashboard", variant="admin")

    milp = data["methods"].get("MILP", pd.DataFrame())
    job_df = data["job_df"]
    if milp.empty:
        st.warning("No MILP results found.")
        return

    c1, c2, c3, c4, c5 = st.columns(5)
    metric_card(c1, "Total Jobs", str(len(job_df)), "Active requisitions")
    metric_card(c2, "Talent Pool", str(len(data["resume_df"])), "Candidates")
    metric_card(c3, "Shortlisted", str(len(milp)), "MILP selections")
    metric_card(c4, "Avg Match Score", score_fmt(milp["pair_score"].mean()), "Normalised 0–1")
    avg_time = milp.groupby("job_id")["review_minutes_capped"].sum().mean()
    metric_card(c5, "Avg Review Time", f"{avg_time:.0f} min", "Per job (budget: 65)")

    st.markdown("---")
    st.subheader("Method Comparison")
    st.caption("Greedy and ScoreOnly baselines are visible here for benchmarking. Recruiters see only the optimised results.")
    comp_rows = []
    for mname in ["MILP", "Greedy", "ScoreOnly"]:
        mdf = data["methods"].get(mname, pd.DataFrame())
        if mdf.empty:
            continue
        jfill = mdf.groupby("job_id").size()
        comp_rows.append({"Method": mname, "Selected Pairs": len(mdf), "Avg Score": round(mdf["pair_score"].mean(), 3), "Full Shortlists (5/5)": int((jfill >= 5).sum()), "Underfilled Jobs": int((jfill < 5).sum()), "Avg Review (min)": round(mdf.groupby("job_id")["review_minutes_capped"].sum().mean(), 1), "Unique Candidates": mdf["resume_id"].nunique()})
    if comp_rows:
        st.dataframe(pd.DataFrame(comp_rows), hide_index=True, use_container_width=True)

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Company Performance")
        cm = []
        for cid, info in COMPANIES.items():
            csel = milp[milp["company_id"] == cid]
            cjobs = job_df[job_df["company_id"] == cid]
            cm.append({"Company": info["name"], "Jobs": len(cjobs), "Avg Score": round(csel["pair_score"].mean(), 3) if len(csel) else 0, "Selected": len(csel)})
        st.dataframe(pd.DataFrame(cm), hide_index=True, use_container_width=True)

    with col_right:
        st.subheader("Score Distribution")
        fig = px.histogram(milp, x="pair_score", nbins=40, color_discrete_sequence=["#2563eb"], labels={"pair_score": "Match Score"})
        fig.update_layout(height=320, margin=dict(t=20, b=40))
        st.plotly_chart(fig, use_container_width=True)

   