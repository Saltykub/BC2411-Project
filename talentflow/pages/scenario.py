from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from ..ui import hero, pct


def _lucide_icon(name: str) -> str:
    paths = {
        "lightbulb": '<path d="M15.09 14.91A5 5 0 1 0 8.9 14.9"></path><path d="M9 18h6"></path><path d="M10 22h4"></path>',
    }
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        'style="vertical-align:-2px; margin-right:0.35rem;">'
        f"{paths.get(name, '')}"
        "</svg>"
    )


def page_scenario_lab(data: dict):
    hero("Scenario Lab", "Understand how operational decisions affect your shortlist quality. Use these insights when planning review capacity or setting hiring policies.", eyebrow="What-If Analysis", variant="scenario")

    sens = data.get("sensitivity", {})
    if not sens:
        st.warning("No scenario data available. Run the sensitivity analysis notebook first.")
        return

    tabs = st.tabs(["Recruiter Time Budget", "Shortlist Size", "Candidate Reuse Limit", "Quality Threshold"])

    with tabs[0]:
        if "budget" not in sens:
            st.info("No budget scenario data.")
        else:
            df = sens["budget"]
            st.markdown("### How Much Review Time Should Each Recruiter Get Per Role?")
            st.markdown(f"""<div class="insight-box">{_lucide_icon("lightbulb")}<strong>Key Insight:</strong> Below 35 minutes per role, some positions can't be fully staffed because there aren't enough short-resume candidates. Between 55–65 minutes gives the best quality for each minute spent. Beyond 65 minutes, improvements are marginal — the system has already found the best candidates.</div>""", unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            fig = px.line(df, x="budget", y="mean_score", markers=True, color_discrete_sequence=["#2563eb"], labels={"budget": "Time Budget (minutes)", "mean_score": "Candidate Quality"})
            fig.update_layout(height=300, margin=dict(t=30, b=30), title="Candidate Quality vs Time Budget")
            c1.plotly_chart(fig, use_container_width=True)

            fig = px.line(df, x="budget", y="mean_coverage", markers=True, color_discrete_sequence=["#059669"], labels={"budget": "Time Budget (minutes)", "mean_coverage": "Skill Coverage"})
            fig.update_layout(height=300, margin=dict(t=30, b=30), title="Skill Coverage vs Time Budget")
            c2.plotly_chart(fig, use_container_width=True)

            fig = px.bar(df, x="budget", y="underfilled", color_discrete_sequence=["#dc2626"], labels={"budget": "Time Budget (minutes)", "underfilled": "Roles Not Fully Staffed"})
            fig.update_layout(height=300, margin=dict(t=30, b=30), title="Incomplete Shortlists")
            c3.plotly_chart(fig, use_container_width=True)

            disp = df[["budget", "mean_score", "mean_coverage", "underfilled"]].copy()
            disp.columns = ["Time Budget (min)", "Avg Candidate Quality", "Skill Coverage Rate", "Roles Not Fully Staffed"]
            disp["Avg Candidate Quality"] = disp["Avg Candidate Quality"].round(3)
            disp["Skill Coverage Rate"] = disp["Skill Coverage Rate"].apply(pct)
            disp["Roles Not Fully Staffed"] = disp["Roles Not Fully Staffed"].astype(int)
            st.dataframe(disp, hide_index=True, use_container_width=True)

    with tabs[1]:
        if "k" not in sens:
            st.info("No shortlist size data.")
        else:
            df = sens["k"]
            st.markdown("### How Many Candidates Should Each Shortlist Contain?")
            st.markdown(f"""<div class="insight-box">{_lucide_icon("lightbulb")}<strong>Key Insight:</strong> Smaller shortlists (3–4) give higher average quality but offer less choice. At 8 candidates per role, the talent pool starts running thin and some roles can't be filled. 5 candidates is the sweet spot for most hiring teams.</div>""", unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            fig = px.line(df, x="k", y="mean_score", markers=True, color_discrete_sequence=["#2563eb"], labels={"k": "Candidates Per Shortlist", "mean_score": "Candidate Quality"})
            fig.update_layout(height=300, margin=dict(t=30, b=30), title="Quality vs Shortlist Size")
            c1.plotly_chart(fig, use_container_width=True)

            fig = px.line(df, x="k", y="mean_coverage", markers=True, color_discrete_sequence=["#059669"], labels={"k": "Candidates Per Shortlist", "mean_coverage": "Skill Coverage"})
            fig.update_layout(height=300, margin=dict(t=30, b=30), title="Skill Coverage vs Shortlist Size")
            c2.plotly_chart(fig, use_container_width=True)

            underfill_col = "underfilled" if "underfilled" in df.columns else None
            if underfill_col:
                fig = px.bar(df, x="k", y=underfill_col, color_discrete_sequence=["#dc2626"], labels={"k": "Candidates Per Shortlist", underfill_col: "Roles Not Fully Staffed"})
                fig.update_layout(height=300, margin=dict(t=30, b=30), title="Incomplete Shortlists")
                c3.plotly_chart(fig, use_container_width=True)

            cols_to_show = ["k", "mean_score", "mean_coverage", "total_selected"]
            nice_names = ["Shortlist Size", "Avg Quality", "Skill Coverage", "Total Interview Slots"]
            if "underfilled" in df.columns:
                cols_to_show.append("underfilled")
                nice_names.append("Incomplete Roles")
            disp = df[cols_to_show].copy()
            disp.columns = nice_names
            disp["Avg Quality"] = disp["Avg Quality"].round(3)
            disp["Skill Coverage"] = disp["Skill Coverage"].apply(pct)
            st.dataframe(disp, hide_index=True, use_container_width=True)

    with tabs[2]:
        if "exposure" not in sens:
            st.info("No exposure cap data.")
        else:
            df = sens["exposure"]
            st.markdown("### How Many Roles Can One Candidate Appear In?")
            st.markdown(f"""<div class="insight-box">{_lucide_icon("lightbulb")}<strong>Key Insight:</strong> Limiting each candidate to 1 role maximises diversity but forces the system to skip top talent for some roles&#x2E; The biggest quality jump comes from allowing 2 roles per candidate (+7&#x2E;4%). Beyond 3, returns diminish while you start seeing the same people across many shortlists.</div>""", unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            fig = px.line(df, x="max_exposure", y="mean_score", markers=True, color_discrete_sequence=["#2563eb"], labels={"max_exposure": "Max Roles Per Candidate", "mean_score": "Candidate Quality"})
            fig.update_layout(height=300, margin=dict(t=30, b=30), title="Quality vs Reuse Limit")
            c1.plotly_chart(fig, use_container_width=True)

            fig = px.line(df, x="max_exposure", y="mean_coverage", markers=True, color_discrete_sequence=["#059669"], labels={"max_exposure": "Max Roles Per Candidate", "mean_coverage": "Skill Coverage"})
            fig.update_layout(height=300, margin=dict(t=30, b=30), title="Coverage vs Reuse Limit")
            c2.plotly_chart(fig, use_container_width=True)

            if "novelty" in df.columns:
                fig = px.line(df, x="max_exposure", y="novelty", markers=True, color_discrete_sequence=["#d97706"], labels={"max_exposure": "Max Roles Per Candidate", "novelty": "Candidate Diversity"})
                fig.update_layout(height=300, margin=dict(t=30, b=30), title="Diversity vs Reuse Limit")
                c3.plotly_chart(fig, use_container_width=True)

            disp = df[["max_exposure", "mean_score", "mean_coverage"]].copy()
            nice = ["Max Roles Per Candidate", "Avg Quality", "Skill Coverage"]
            if "novelty" in df.columns:
                disp = pd.concat([disp, df[["novelty"]]], axis=1)
                nice.append("Candidate Diversity")
            disp.columns = nice
            disp["Avg Quality"] = disp["Avg Quality"].round(3)
            disp["Skill Coverage"] = disp["Skill Coverage"].apply(pct)
            if "Candidate Diversity" in disp.columns:
                disp["Candidate Diversity"] = disp["Candidate Diversity"].apply(pct)
            st.dataframe(disp, hide_index=True, use_container_width=True)

    with tabs[3]:
        if "floor" not in sens:
            st.info("No quality floor data.")
        else:
            df = sens["floor"]
            st.markdown("### What's The Minimum Acceptable Candidate Quality?")
            st.markdown(f"""<div class="insight-box">{_lucide_icon("lightbulb")}<strong>Key Insight:</strong> The quality threshold has almost no effect on results because TalentFlow's optimiser naturally selects strong candidates. This setting acts as a safety net, not an active filter. A threshold between 0.35–0.45 is recommended.</div>""", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            fig = px.line(df, x="floor", y="mean_score", markers=True, color_discrete_sequence=["#2563eb"], labels={"floor": "Quality Threshold", "mean_score": "Actual Candidate Quality"})
            fig.update_layout(height=320, margin=dict(t=30, b=30), title="Actual Quality vs Threshold Setting")
            c1.plotly_chart(fig, use_container_width=True)

            fig = px.bar(df, x="floor", y="underfilled", color_discrete_sequence=["#dc2626"], labels={"floor": "Quality Threshold", "underfilled": "Roles Not Fully Staffed"})
            fig.update_layout(height=320, margin=dict(t=30, b=30), title="Incomplete Shortlists vs Threshold")
            c2.plotly_chart(fig, use_container_width=True)

            disp = df[["floor", "mean_score", "mean_coverage", "underfilled"]].copy()
            disp.columns = ["Quality Threshold", "Actual Avg Quality", "Skill Coverage", "Incomplete Roles"]
            disp["Actual Avg Quality"] = disp["Actual Avg Quality"].round(3)
            disp["Skill Coverage"] = disp["Skill Coverage"].apply(pct)
            disp["Incomplete Roles"] = disp["Incomplete Roles"].astype(int)
            st.dataframe(disp, hide_index=True, use_container_width=True)
