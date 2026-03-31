from __future__ import annotations

import ast
import re
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st


APP_TITLE = "TalentFlow Recruiter Portal"
BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "outputs_resume_project_v4"
SHORTLIST_TARGET_DEFAULT = 5
REVIEW_BUDGET_DEFAULT = 25.0

COMPANY_NAMES = [
    "Northstar Digital",
    "Atlas Commerce Cloud",
    "Meridian Health Systems",
    "ForgeStack Enterprise",
]

DEMO_USERS: dict[str, dict[str, str | bool]] = {
    "mia.chen@northstar.demo": {
        "password": "talent123",
        "name": "Mia Chen",
        "role": "Lead Recruiter",
        "company": "Northstar Digital",
        "all_access": False,
    },
    "daniel.ong@atlas.demo": {
        "password": "talent123",
        "name": "Daniel Ong",
        "role": "Hiring Manager",
        "company": "Atlas Commerce Cloud",
        "all_access": False,
    },
    "sofia.reyes@meridian.demo": {
        "password": "talent123",
        "name": "Sofia Reyes",
        "role": "Talent Partner",
        "company": "Meridian Health Systems",
        "all_access": False,
    },
    "arjun.mehta@forgestack.demo": {
        "password": "talent123",
        "name": "Arjun Mehta",
        "role": "Recruiting Lead",
        "company": "ForgeStack Enterprise",
        "all_access": False,
    },
    "ops.admin@talentflow.demo": {
        "password": "talent123",
        "name": "Jordan Lee",
        "role": "Talent Operations Admin",
        "company": "All Companies",
        "all_access": True,
    },
}

CITY_PATTERNS = {
    "Bengaluru": ["bengaluru", "bangalore"],
    "Chennai": ["chennai"],
    "Delhi NCR": ["gurugram", "gurgaon", "delhi", "noida"],
    "Hyderabad": ["hyderabad"],
    "Kolkata": ["kolkata"],
    "Mumbai Region": ["thane", "mumbai", "navi mumbai"],
    "Pune": ["pune"],
    "Remote / Flexible": ["remote", "work remotely", "work from home"],
}

STATUS_ORDER = ["Pending", "Advance", "Hold", "Reject"]


def parse_listlike(value: Any) -> list[str]:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    text = str(value).strip()
    if not text:
        return []
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (list, tuple, set)):
            return [str(item) for item in parsed]
    except Exception:
        pass
    return [item.strip() for item in text.split(",") if item.strip()]


def clipped_text(text: str, limit: int = 420) -> str:
    value = (text or "").strip()
    if len(value) <= limit:
        return value
    return value[:limit].rsplit(" ", 1)[0] + " ..."


def pct(value: float) -> str:
    return f"{100 * float(value):.1f}%"


def derive_department(job_title: str) -> str:
    title = job_title.lower()
    if any(token in title for token in ["ios", "flutter"]):
        return "Mobile Applications"
    if any(token in title for token in ["machine learning", "database"]):
        return "Data and AI"
    if any(token in title for token in ["network", "devops"]):
        return "Infrastructure and Security"
    if any(token in title for token in ["wordpress", "javascript", "php"]):
        return "Customer Platforms"
    return "Platform Engineering"


def derive_company(job_id: int) -> str:
    return COMPANY_NAMES[(int(job_id) - 1) % len(COMPANY_NAMES)]


def derive_seniority(job_description: str) -> str:
    text = (job_description or "").lower()
    ranges = re.findall(r"(\d+)\s*[-to]+\s*(\d+)\s*years?", text)
    if ranges:
        low, high = ranges[0]
        midpoint = (int(low) + int(high)) / 2
    else:
        single = re.search(r"(\d+)\+?\s*years?", text)
        midpoint = float(single.group(1)) if single else 1.0
    if midpoint >= 6:
        return "Senior"
    if midpoint >= 3:
        return "Mid"
    return "Early Career"


def derive_location(job_description: str) -> str:
    text = (job_description or "").lower()
    for city, patterns in CITY_PATTERNS.items():
        if any(pattern in text for pattern in patterns):
            return city
    return "Location not captured"


def derive_fit_band(score: float) -> str:
    if score >= 0.75:
        return "High conviction"
    if score >= 0.60:
        return "Strong fit"
    if score >= 0.50:
        return "Solid fit"
    return "Stretch fit"


def derive_job_status(selected_count: int, target_count: int, weighted_coverage_rate: float) -> str:
    fill_rate = selected_count / max(target_count, 1)
    if fill_rate < 0.8 or weighted_coverage_rate < 0.60:
        return "At risk"
    if fill_rate < 1.0 or weighted_coverage_rate < 0.75:
        return "Watch"
    return "Ready"


def build_skill_weight_lookup(resumes_df: pd.DataFrame, jobs_df: pd.DataFrame) -> dict[tuple[int, str], float]:
    skill_counts: Counter[str] = Counter()
    for skill_set in resumes_df["skill_set"]:
        skill_counts.update(set(skill_set))
    total_candidates = max(len(resumes_df), 1)
    lookup: dict[tuple[int, str], float] = {}
    for row in jobs_df.itertuples(index=False):
        required_skills = list(row.required_skills)
        if not required_skills:
            continue
        raw_weights: dict[str, float] = {}
        for skill in required_skills:
            prevalence = skill_counts.get(skill, 0) / total_candidates
            raw_weights[skill] = 1.0 + (1.0 - prevalence)
        mean_weight = float(np.mean(list(raw_weights.values()))) if raw_weights else 1.0
        for skill, raw_weight in raw_weights.items():
            lookup[(int(row.job_id), skill)] = float(raw_weight / max(mean_weight, 1e-9))
    return lookup


def enrich_selected_pairs(
    selected_df: pd.DataFrame,
    jobs_df: pd.DataFrame,
    resumes_df: pd.DataFrame,
    method_name: str,
) -> pd.DataFrame:
    if selected_df.empty:
        return selected_df.copy()

    selected_df = selected_df.copy()
    for col in ["candidate_skill_set", "job_skill_set"]:
        selected_df[col] = selected_df[col].map(parse_listlike)

    selected_df = selected_df.merge(
        jobs_df[
            [
                "job_id",
                "company",
                "department",
                "location",
                "seniority",
                "required_skills",
                "job_description",
                "title_bucket",
            ]
        ],
        on="job_id",
        how="left",
    )
    selected_df = selected_df.merge(
        resumes_df[
            [
                "candidate_id",
                "resume_text",
                "resume_word_count",
                "skill_set",
            ]
        ].rename(columns={"skill_set": "resume_skill_set"}),
        on="candidate_id",
        how="left",
    )

    selected_df["required_skills"] = selected_df["required_skills"].map(parse_listlike)
    selected_df["resume_skill_set"] = selected_df["resume_skill_set"].map(parse_listlike)
    selected_df["matched_required_skills"] = selected_df.apply(
        lambda row: sorted(set(row["required_skills"]) & set(row["candidate_skill_set"])),
        axis=1,
    )
    selected_df["missing_required_skills"] = selected_df.apply(
        lambda row: sorted(set(row["required_skills"]) - set(row["candidate_skill_set"])),
        axis=1,
    )
    selected_df["match_ratio"] = selected_df.apply(
        lambda row: len(row["matched_required_skills"]) / max(len(row["required_skills"]), 1),
        axis=1,
    )
    selected_df["fit_band"] = selected_df["score"].map(derive_fit_band)
    selected_df["candidate_label"] = selected_df["candidate_id"].map(lambda cid: f"C{int(cid):03d}")
    selected_df["method"] = method_name
    return selected_df


def compute_job_metrics(
    selected_df: pd.DataFrame,
    jobs_df: pd.DataFrame,
    skill_weight_lookup: dict[tuple[int, str], float],
    shortlist_target: int = SHORTLIST_TARGET_DEFAULT,
    review_budget_minutes: float = REVIEW_BUDGET_DEFAULT,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for job in jobs_df.itertuples(index=False):
        job_id = int(job.job_id)
        selected = selected_df[selected_df["job_id"] == job_id] if not selected_df.empty else pd.DataFrame()
        required = set(job.required_skills)
        covered: set[str] = set()
        if len(selected):
            for candidate_skills in selected["candidate_skill_set"]:
                covered |= set(candidate_skills)
        covered_weight = float(sum(skill_weight_lookup.get((job_id, skill), 1.0) for skill in required if skill in covered))
        total_weight = float(sum(skill_weight_lookup.get((job_id, skill), 1.0) for skill in required))
        selected_count = int(len(selected))
        weighted_coverage_rate = covered_weight / max(total_weight, 1.0)
        rows.append(
            {
                "job_id": job_id,
                "job_title": job.job_title,
                "company": job.company,
                "department": job.department,
                "location": job.location,
                "seniority": job.seniority,
                "selected_count": selected_count,
                "target_shortlist_size": int(shortlist_target),
                "fill_rate": selected_count / max(shortlist_target, 1),
                "avg_score": float(selected["score"].mean()) if len(selected) else 0.0,
                "total_review_minutes": float(selected["review_minutes"].sum()) if len(selected) else 0.0,
                "review_budget_minutes": float(review_budget_minutes),
                "avg_must_have_hits": float(selected["must_have_hits"].mean()) if len(selected) else 0.0,
                "distinct_categories_selected": int(selected["resume_category"].nunique()) if len(selected) else 0,
                "selected_clusters": int(selected["redundancy_cluster"].nunique()) if len(selected) else 0,
                "covered_required_skills": int(len(required & covered)),
                "num_required_skills": int(len(required)),
                "coverage_rate": float(len(required & covered) / max(len(required), 1)),
                "weighted_coverage_rate": float(weighted_coverage_rate),
                "selected_categories": ", ".join(sorted(selected["resume_category"].astype(str).unique())) if len(selected) else "",
                "required_skills": list(job.required_skills),
                "readiness_status": derive_job_status(selected_count, shortlist_target, weighted_coverage_rate),
            }
        )
    return pd.DataFrame(rows)


def compute_portfolio_metrics(job_metrics: pd.DataFrame, selected_df: pd.DataFrame) -> dict[str, float]:
    if job_metrics.empty:
        return {
            "jobs": 0.0,
            "avg_fill_rate": 0.0,
            "avg_score": 0.0,
            "avg_coverage_rate": 0.0,
            "avg_weighted_coverage_rate": 0.0,
            "avg_review_minutes": 0.0,
            "jobs_at_risk": 0.0,
            "total_pairs_selected": 0.0,
        }
    return {
        "jobs": float(job_metrics["job_id"].nunique()),
        "avg_fill_rate": float(job_metrics["fill_rate"].mean()),
        "avg_score": float(selected_df["score"].mean()) if len(selected_df) else 0.0,
        "avg_coverage_rate": float(job_metrics["coverage_rate"].mean()),
        "avg_weighted_coverage_rate": float(job_metrics["weighted_coverage_rate"].mean()),
        "avg_review_minutes": float(job_metrics["total_review_minutes"].mean()),
        "jobs_at_risk": float((job_metrics["readiness_status"] == "At risk").sum()),
        "total_pairs_selected": float(len(selected_df)),
    }


@st.cache_data(show_spinner=False)
def load_portal_data(out_dir_str: str) -> dict[str, Any]:
    out_dir = Path(out_dir_str)
    if not out_dir.exists():
        raise FileNotFoundError(f"Could not find outputs folder: {out_dir}")

    jobs = pd.read_csv(out_dir / "jobs_cleaned.csv")
    resumes = pd.read_csv(out_dir / "resumes_cleaned.csv")
    pair_scores = pd.read_csv(out_dir / "pair_scores.csv")
    method_comparison = pd.read_csv(out_dir / "method_comparison.csv")
    sensitivity = pd.read_csv(out_dir / "sensitivity_analysis.csv")

    for col in ["skill_set", "required_skills"]:
        jobs[col] = jobs[col].map(parse_listlike)
    resumes["skill_set"] = resumes["skill_set"].map(parse_listlike)
    for col in ["candidate_skill_set", "job_skill_set"]:
        pair_scores[col] = pair_scores[col].map(parse_listlike)

    jobs["company"] = jobs["job_id"].map(derive_company)
    jobs["department"] = jobs["job_title"].map(derive_department)
    jobs["location"] = jobs["job_description"].map(derive_location)
    jobs["seniority"] = jobs["job_description"].map(derive_seniority)

    skill_weight_lookup = build_skill_weight_lookup(resumes, jobs)

    selected_files = {
        "MILP": out_dir / "selected_pairs_milp.csv",
        "Greedy": out_dir / "selected_pairs_greedy.csv",
        "ScoreOnly": out_dir / "selected_pairs_score_only.csv",
    }
    method_shortlists: dict[str, pd.DataFrame] = {}
    method_job_metrics: dict[str, pd.DataFrame] = {}

    for method_name, file_path in selected_files.items():
        selected = pd.read_csv(file_path)
        enriched = enrich_selected_pairs(selected, jobs, resumes, method_name)
        method_shortlists[method_name] = enriched
        method_job_metrics[method_name] = compute_job_metrics(
            enriched,
            jobs,
            skill_weight_lookup,
            shortlist_target=SHORTLIST_TARGET_DEFAULT,
            review_budget_minutes=REVIEW_BUDGET_DEFAULT,
        )

    pair_scores = pair_scores.merge(
        jobs[["job_id", "company", "department", "location", "required_skills", "job_description"]],
        on="job_id",
        how="left",
    )
    pair_scores["matched_required_skills"] = pair_scores.apply(
        lambda row: sorted(set(row["candidate_skill_set"]) & set(row["required_skills"])),
        axis=1,
    )
    pair_scores["missing_required_skills"] = pair_scores.apply(
        lambda row: sorted(set(row["required_skills"]) - set(row["candidate_skill_set"])),
        axis=1,
    )

    return {
        "jobs": jobs,
        "resumes": resumes,
        "pair_scores": pair_scores,
        "method_shortlists": method_shortlists,
        "method_job_metrics": method_job_metrics,
        "method_comparison": method_comparison,
        "sensitivity": sensitivity,
        "skill_weight_lookup": skill_weight_lookup,
    }


def inject_theme() -> None:
    st.markdown(
        """
        <style>
            :root {
                --ink: #13293d;
                --ink-soft: #486581;
                --paper: #fffdfa;
                --accent: #cf5c36;
                --accent-soft: rgba(207, 92, 54, 0.12);
                --mint: #2c7a7b;
                --gold: #c59d5f;
                --line: rgba(19, 41, 61, 0.10);
            }
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(197, 157, 95, 0.18), transparent 34%),
                    radial-gradient(circle at top right, rgba(44, 122, 123, 0.16), transparent 32%),
                    linear-gradient(180deg, #f9f5ef 0%, #fbfaf7 46%, #ffffff 100%);
                color: var(--ink);
                font-family: "Aptos", "Segoe UI", "Trebuchet MS", sans-serif;
            }
            .hero {
                padding: 1.6rem 1.8rem;
                border: 1px solid var(--line);
                border-radius: 24px;
                background: linear-gradient(135deg, rgba(255,255,255,0.86), rgba(255,250,245,0.95));
                box-shadow: 0 20px 60px rgba(19, 41, 61, 0.08);
                margin-bottom: 1rem;
            }
            .eyebrow {
                color: var(--accent);
                font-size: 0.8rem;
                font-weight: 700;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                margin-bottom: 0.4rem;
            }
            .hero h1 {
                color: var(--ink);
                margin: 0;
            }
            .hero p {
                color: var(--ink-soft);
                margin-top: 0.6rem;
                margin-bottom: 0;
                line-height: 1.55;
            }
            .panel {
                padding: 1rem 1.15rem;
                border-radius: 20px;
                background: rgba(255, 255, 255, 0.82);
                border: 1px solid var(--line);
                box-shadow: 0 10px 34px rgba(19, 41, 61, 0.06);
            }
            .stat-card {
                padding: 1rem 1.1rem;
                border-radius: 18px;
                background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(249,243,233,0.96));
                border: 1px solid var(--line);
                min-height: 116px;
                box-shadow: 0 10px 30px rgba(19, 41, 61, 0.05);
            }
            .stat-label {
                color: var(--ink-soft);
                font-size: 0.82rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 700;
            }
            .stat-value {
                color: var(--ink);
                font-size: 2rem;
                line-height: 1.15;
                font-weight: 700;
                margin-top: 0.35rem;
            }
            .stat-note {
                color: var(--ink-soft);
                font-size: 0.9rem;
                margin-top: 0.3rem;
            }
            .pill {
                display: inline-block;
                padding: 0.28rem 0.62rem;
                border-radius: 999px;
                margin: 0 0.35rem 0.35rem 0;
                font-size: 0.84rem;
                font-weight: 600;
                background: rgba(19, 41, 61, 0.08);
                color: var(--ink);
            }
            .pill.accent { background: var(--accent-soft); color: var(--accent); }
            .pill.mint { background: rgba(44, 122, 123, 0.12); color: var(--mint); }
            .candidate-card {
                padding: 1rem 1.1rem;
                border-radius: 18px;
                border: 1px solid var(--line);
                background: rgba(255, 255, 255, 0.9);
                box-shadow: 0 10px 26px rgba(19, 41, 61, 0.05);
                margin-bottom: 0.8rem;
            }
            .hint {
                padding: 0.85rem 1rem;
                border-left: 4px solid var(--accent);
                border-radius: 12px;
                background: rgba(255, 250, 245, 0.92);
                color: var(--ink-soft);
            }
            div[data-testid="stSidebar"] {
                background: rgba(248, 244, 237, 0.96);
                border-right: 1px solid var(--line);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def banner(title: str, subtitle: str, eyebrow: str = "Recruiter Workspace") -> None:
    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">{eyebrow}</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stat_card(column: Any, label: str, value: str, note: str) -> None:
    column.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
            <div class="stat-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pills(items: list[str], tone: str = "") -> str:
    if not items:
        return '<span class="pill">None</span>'
    cls = f"pill {tone}".strip()
    return "".join(f'<span class="{cls}">{item}</span>' for item in items)


def ensure_session_state() -> None:
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("user_email", "")
    st.session_state.setdefault("review_actions", {})


def current_user() -> dict[str, Any]:
    return DEMO_USERS.get(st.session_state.get("user_email", ""), {})


def scoped_jobs(jobs_df: pd.DataFrame, company_scope: str, department_scope: str | None = None) -> pd.DataFrame:
    scoped = jobs_df.copy()
    if company_scope != "All Companies":
        scoped = scoped[scoped["company"] == company_scope]
    if department_scope and department_scope != "All Departments":
        scoped = scoped[scoped["department"] == department_scope]
    return scoped


def scoped_method_tables(
    data: dict[str, Any],
    method_name: str,
    company_scope: str,
    department_scope: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    shortlist = data["method_shortlists"][method_name]
    job_metrics = data["method_job_metrics"][method_name]
    if company_scope != "All Companies":
        shortlist = shortlist[shortlist["company"] == company_scope]
        job_metrics = job_metrics[job_metrics["company"] == company_scope]
    if department_scope and department_scope != "All Departments":
        shortlist = shortlist[shortlist["department"] == department_scope]
        job_metrics = job_metrics[job_metrics["department"] == department_scope]
    return shortlist, job_metrics


def method_summary_for_scope(data: dict[str, Any], company_scope: str, department_scope: str | None = None) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for method_name in ["MILP", "Greedy", "ScoreOnly"]:
        shortlist, job_metrics = scoped_method_tables(data, method_name, company_scope, department_scope)
        metrics = compute_portfolio_metrics(job_metrics, shortlist)
        rows.append(
            {
                "method": method_name,
                "mean_score": metrics["avg_score"],
                "fill_rate": metrics["avg_fill_rate"],
                "coverage_rate": metrics["avg_coverage_rate"],
                "weighted_coverage_rate": metrics["avg_weighted_coverage_rate"],
                "review_minutes": metrics["avg_review_minutes"],
                "jobs_at_risk": metrics["jobs_at_risk"],
            }
        )
    return pd.DataFrame(rows)


def render_login() -> None:
    banner(
        "Log in to the recruiter portal",
        "Use the v4 shortlist outputs as a recruiter-facing product demo: sign in, view company health, drill into departments and jobs, and review model recommendations.",
        eyebrow="Login",
    )

    left, right = st.columns([1.2, 1], gap="large")
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Work email", placeholder="mia.chen@northstar.demo")
            password = st.text_input("Password", type="password", placeholder="talent123")
            submitted = st.form_submit_button("Enter recruiter workspace", use_container_width=True)
            if submitted:
                profile = DEMO_USERS.get(email.strip().lower())
                if not profile or profile["password"] != password:
                    st.error("That demo login did not match. Use one of the sample accounts on the right.")
                else:
                    st.session_state["logged_in"] = True
                    st.session_state["user_email"] = email.strip().lower()
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Demo accounts")
        demo_rows = [
            {
                "Email": email,
                "Role": profile["role"],
                "Company": profile["company"],
                "Password": profile["password"],
            }
            for email, profile in DEMO_USERS.items()
        ]
        st.dataframe(pd.DataFrame(demo_rows), hide_index=True, use_container_width=True)
        st.markdown(
            """
            <div class="hint">
                Company and department views are demo metadata layered on top of the v4 output files.
                The app stays faithful to the actual model results while giving you a realistic recruiter workflow to present.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)


def render_sidebar(data: dict[str, Any]) -> tuple[str, str]:
    user = current_user()
    with st.sidebar:
        st.markdown(f"## {APP_TITLE}")
        st.caption("v4 shortlist experience")
        st.markdown(
            f"""
            <div class="panel">
                <strong>{user.get("name", "Recruiter")}</strong><br>
                <span style="color:#486581;">{user.get("role", "")}</span><br>
                <span style="color:#486581;">{user.get("company", "")}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        page = st.radio(
            "Navigate",
            [
                "Company Dashboard",
                "Department Dashboard",
                "Job Workbench",
                "Candidate Bench",
                "Scenario Lab",
            ],
        )

        all_companies = ["All Companies"] + sorted(data["jobs"]["company"].unique())
        if user.get("all_access"):
            company_scope = st.selectbox("Company scope", all_companies, index=0)
        else:
            company_scope = str(user["company"])
            st.text_input("Company scope", value=company_scope, disabled=True)

        with st.expander("Data assumptions", expanded=False):
            st.write(
                "This portal reads the v4 CSV outputs directly. Because the source jobs dataset does not contain clean structured company and department columns, those views are assigned deterministically for demo purposes."
            )
        if st.button("Log out", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["user_email"] = ""
            st.rerun()
    return page, company_scope


def render_company_dashboard(data: dict[str, Any], company_scope: str) -> None:
    milp_shortlist, milp_jobs = scoped_method_tables(data, "MILP", company_scope)
    portfolio = compute_portfolio_metrics(milp_jobs, milp_shortlist)

    banner(
        "Company dashboard",
        "Track requisition health, shortlist quality, and recruiter workload at the company level. The default company view uses the MILP recommendations because that is the strongest operating policy in the v4 model.",
        eyebrow=company_scope if company_scope != "All Companies" else "Portfolio view",
    )

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    stat_card(c1, "Open jobs", f"{int(portfolio['jobs'])}", "Active requisitions in scope")
    stat_card(c2, "Avg fill rate", pct(portfolio["avg_fill_rate"]), "Shortlisted candidates vs target size")
    stat_card(c3, "Avg weighted coverage", pct(portfolio["avg_weighted_coverage_rate"]), "Scarcity-weighted required skill coverage")
    stat_card(c4, "Jobs at risk", f"{int(portfolio['jobs_at_risk'])}", "Low fill or weak coverage")

    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        st.subheader("Department performance")
        dept_rollup = (
            milp_jobs.groupby("department", as_index=False)
            .agg(
                open_jobs=("job_id", "nunique"),
                avg_fill_rate=("fill_rate", "mean"),
                avg_coverage_rate=("coverage_rate", "mean"),
                avg_weighted_coverage_rate=("weighted_coverage_rate", "mean"),
                at_risk_jobs=("readiness_status", lambda s: int((s == "At risk").sum())),
            )
            .sort_values(["at_risk_jobs", "avg_weighted_coverage_rate"], ascending=[False, True])
        )
        st.dataframe(
            dept_rollup.assign(
                avg_fill_rate=lambda df: df["avg_fill_rate"].map(pct),
                avg_coverage_rate=lambda df: df["avg_coverage_rate"].map(pct),
                avg_weighted_coverage_rate=lambda df: df["avg_weighted_coverage_rate"].map(pct),
            ),
            hide_index=True,
            use_container_width=True,
        )

        st.subheader("Method view inside this scope")
        method_scope = method_summary_for_scope(data, company_scope)
        st.dataframe(
            method_scope.assign(
                mean_score=lambda df: df["mean_score"].round(3),
                fill_rate=lambda df: df["fill_rate"].map(pct),
                coverage_rate=lambda df: df["coverage_rate"].map(pct),
                weighted_coverage_rate=lambda df: df["weighted_coverage_rate"].map(pct),
                review_minutes=lambda df: df["review_minutes"].round(1),
            ),
            hide_index=True,
            use_container_width=True,
        )

    with right:
        st.subheader("Role health")
        role_health = milp_jobs.sort_values(
            ["readiness_status", "weighted_coverage_rate", "avg_score"],
            ascending=[True, True, False],
        )[
            [
                "job_title",
                "department",
                "location",
                "selected_count",
                "target_shortlist_size",
                "avg_score",
                "coverage_rate",
                "weighted_coverage_rate",
                "readiness_status",
            ]
        ]
        role_health["avg_score"] = role_health["avg_score"].round(3)
        role_health["coverage_rate"] = role_health["coverage_rate"].map(pct)
        role_health["weighted_coverage_rate"] = role_health["weighted_coverage_rate"].map(pct)
        st.dataframe(role_health, hide_index=True, use_container_width=True)

        st.subheader("Recruiter note")
        st.markdown(
            """
            <div class="hint">
                The MILP solution is strongest when you care about coverage and recruiter efficiency together.
                Score-only gives higher average candidate score, but it also pushes review time much higher and loses shortlist diversity.
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_department_dashboard(data: dict[str, Any], company_scope: str) -> None:
    jobs = scoped_jobs(data["jobs"], company_scope)
    departments = ["All Departments"] + sorted(jobs["department"].unique())
    department_scope = st.selectbox("Department", departments)

    milp_shortlist, milp_jobs = scoped_method_tables(data, "MILP", company_scope, department_scope)
    portfolio = compute_portfolio_metrics(milp_jobs, milp_shortlist)

    banner(
        "Department dashboard",
        "Use this view when a recruiting lead wants to understand where the shortlist quality is strongest, where coverage is thin, and which roles need manual attention first.",
        eyebrow=department_scope,
    )

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    stat_card(c1, "Roles", f"{int(portfolio['jobs'])}", "Jobs currently in the department scope")
    stat_card(c2, "Avg score", f"{portfolio['avg_score']:.3f}", "Average shortlisted pair score")
    stat_card(c3, "Coverage", pct(portfolio["avg_coverage_rate"]), "Required skills covered per role")
    stat_card(c4, "Review load", f"{portfolio['avg_review_minutes']:.1f} min", "Average review time per role")

    left, right = st.columns([1.1, 0.9], gap="large")
    with left:
        st.subheader("Jobs in this department")
        display = milp_jobs[
            [
                "job_title",
                "company",
                "location",
                "seniority",
                "selected_count",
                "avg_score",
                "coverage_rate",
                "weighted_coverage_rate",
                "readiness_status",
            ]
        ].copy()
        display["avg_score"] = display["avg_score"].round(3)
        display["coverage_rate"] = display["coverage_rate"].map(pct)
        display["weighted_coverage_rate"] = display["weighted_coverage_rate"].map(pct)
        st.dataframe(display, hide_index=True, use_container_width=True)

    with right:
        st.subheader("Most requested skills")
        skill_counter: Counter[str] = Counter()
        for skills in milp_jobs["required_skills"]:
            skill_counter.update(skills)
        top_skills = pd.DataFrame(skill_counter.most_common(12), columns=["Skill", "Jobs requiring it"])
        st.dataframe(top_skills, hide_index=True, use_container_width=True)

        st.subheader("Method comparison for this department")
        method_scope = method_summary_for_scope(data, company_scope, department_scope)
        st.dataframe(
            method_scope.assign(
                mean_score=lambda df: df["mean_score"].round(3),
                fill_rate=lambda df: df["fill_rate"].map(pct),
                coverage_rate=lambda df: df["coverage_rate"].map(pct),
                weighted_coverage_rate=lambda df: df["weighted_coverage_rate"].map(pct),
                review_minutes=lambda df: df["review_minutes"].round(1),
            ),
            hide_index=True,
            use_container_width=True,
        )


def render_job_workbench(data: dict[str, Any], company_scope: str) -> None:
    jobs = scoped_jobs(data["jobs"], company_scope)
    departments = sorted(jobs["department"].unique())
    if not departments:
        st.warning("No jobs found in this scope.")
        return

    department_scope = st.selectbox("Department", departments)
    job_options = jobs[jobs["department"] == department_scope].sort_values("job_title")
    if job_options.empty:
        st.warning("No jobs found in this department.")
        return

    selected_job_id = st.selectbox(
        "Job",
        options=job_options["job_id"].tolist(),
        format_func=lambda job_id: f"{int(job_id)} - {job_options.loc[job_options['job_id'] == job_id, 'job_title'].iloc[0]}",
    )
    method_name = st.radio("Shortlist method", ["MILP", "Greedy", "ScoreOnly"], horizontal=True)

    job_row = data["jobs"].loc[data["jobs"]["job_id"] == selected_job_id].iloc[0]
    shortlist = data["method_shortlists"][method_name]
    job_metrics = data["method_job_metrics"][method_name]
    current_job_candidates = shortlist[shortlist["job_id"] == selected_job_id].sort_values(["score", "must_have_hits"], ascending=[False, False])
    current_job_metrics = job_metrics[job_metrics["job_id"] == selected_job_id].iloc[0]

    banner(
        f"Job workbench: {job_row['job_title']}",
        "This is the recruiter action screen. Use it to inspect the model's recommended shortlist, compare methods, review candidate fit signals, and decide who advances.",
        eyebrow=f"{job_row['company']} | {job_row['department']}",
    )

    st.markdown(
        f"""
        <div class="panel">
            <strong>Location:</strong> {job_row['location']}<br>
            <strong>Seniority:</strong> {job_row['seniority']}<br>
            <strong>Required skills:</strong><br>
            {pills(job_row['required_skills'], tone="accent")}
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    stat_card(c1, "Selected", f"{int(current_job_metrics['selected_count'])}/{int(current_job_metrics['target_shortlist_size'])}", "Candidates in shortlist")
    stat_card(c2, "Avg score", f"{current_job_metrics['avg_score']:.3f}", "Mean pair score in this shortlist")
    stat_card(c3, "Coverage", pct(current_job_metrics["coverage_rate"]), "Required skills covered")
    stat_card(c4, "Review time", f"{current_job_metrics['total_review_minutes']:.1f} min", "Total recruiter review time")

    tab_shortlist, tab_compare, tab_alternates = st.tabs(["Recommended shortlist", "Method comparison", "Alternates"])

    with tab_shortlist:
        if current_job_candidates.empty:
            st.warning("No shortlisted candidates for this job under the selected method.")
        else:
            for row in current_job_candidates.itertuples(index=False):
                pair_key = f"{method_name}:{int(row.job_id)}:{int(row.candidate_id)}"
                action_state = st.session_state["review_actions"].get(pair_key, {"status": "Pending", "note": ""})
                st.markdown(
                    f"""
                    <div class="candidate-card">
                        <strong>{row.candidate_label}</strong> | {row.resume_category}<br>
                        <span style="color:#486581;">{row.fit_band} | Score {row.score:.3f} | Must-have hits {row.must_have_hits} | Review {row.review_minutes:.1f} min</span><br><br>
                        <strong>Matched skills</strong><br>
                        {pills(list(row.matched_required_skills), tone="mint")}<br>
                        <strong>Missing skills</strong><br>
                        {pills(list(row.missing_required_skills))}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                col_a, col_b = st.columns([0.34, 0.66], gap="medium")
                with col_a:
                    chosen_status = st.selectbox(
                        f"Disposition for {row.candidate_label}",
                        STATUS_ORDER,
                        index=STATUS_ORDER.index(action_state["status"]) if action_state["status"] in STATUS_ORDER else 0,
                        key=f"status_{pair_key}",
                    )
                with col_b:
                    note_value = st.text_input(
                        f"Recruiter note for {row.candidate_label}",
                        value=action_state["note"],
                        key=f"note_{pair_key}",
                    )
                st.session_state["review_actions"][pair_key] = {"status": chosen_status, "note": note_value}
                with st.expander(f"Open profile for {row.candidate_label}"):
                    st.write(clipped_text(str(row.resume_text), 1200))

    with tab_compare:
        compare_rows: list[dict[str, Any]] = []
        for method in ["MILP", "Greedy", "ScoreOnly"]:
            metric_row = data["method_job_metrics"][method]
            metric_row = metric_row[metric_row["job_id"] == selected_job_id].iloc[0]
            compare_rows.append(
                {
                    "Method": method,
                    "Selected": int(metric_row["selected_count"]),
                    "Avg score": round(float(metric_row["avg_score"]), 3),
                    "Coverage": pct(metric_row["coverage_rate"]),
                    "Weighted coverage": pct(metric_row["weighted_coverage_rate"]),
                    "Review minutes": round(float(metric_row["total_review_minutes"]), 1),
                    "Status": metric_row["readiness_status"],
                }
            )
        st.dataframe(pd.DataFrame(compare_rows), hide_index=True, use_container_width=True)

    with tab_alternates:
        pool = data["pair_scores"]
        pool = pool[(pool["job_id"] == selected_job_id) & (pool["eligible"] == 1)].sort_values("score", ascending=False)
        selected_candidate_ids = set(current_job_candidates["candidate_id"].tolist())
        alternates = pool[~pool["candidate_id"].isin(selected_candidate_ids)].head(10).copy()
        alternates["matched_required_skills"] = alternates["matched_required_skills"].map(lambda items: ", ".join(items))
        alternates["missing_required_skills"] = alternates["missing_required_skills"].map(lambda items: ", ".join(items))
        alternates = alternates[
            [
                "candidate_id",
                "resume_category",
                "score",
                "must_have_hits",
                "review_minutes",
                "matched_required_skills",
                "missing_required_skills",
            ]
        ]
        alternates["score"] = alternates["score"].round(3)
        st.dataframe(alternates, hide_index=True, use_container_width=True)


def render_candidate_bench(data: dict[str, Any], company_scope: str) -> None:
    method_name = st.radio("Review shortlist from", ["MILP", "Greedy", "ScoreOnly"], horizontal=True)
    shortlist, job_metrics = scoped_method_tables(data, method_name, company_scope)
    if shortlist.empty:
        st.warning("No shortlisted candidates in this scope.")
        return

    jobs_in_scope = sorted(shortlist["job_title"].unique())
    selected_job_title = st.selectbox("Focus on job", jobs_in_scope)
    candidate_scope = shortlist[shortlist["job_title"] == selected_job_title].sort_values("score", ascending=False)
    candidate_options = candidate_scope["candidate_label"].tolist()
    selected_candidate_label = st.selectbox("Candidate", candidate_options)
    candidate_row = candidate_scope[candidate_scope["candidate_label"] == selected_candidate_label].iloc[0]

    banner(
        "Candidate bench",
        "Review one candidate in context: fit signals, missing skills, recruiter notes, and where this person sits in the shortlist.",
        eyebrow=f"{method_name} | {candidate_row['company']}",
    )

    job_status = job_metrics[job_metrics["job_id"] == candidate_row["job_id"]].iloc[0]["readiness_status"]
    pair_key = f"{method_name}:{int(candidate_row['job_id'])}:{int(candidate_row['candidate_id'])}"
    action_state = st.session_state["review_actions"].get(pair_key, {"status": "Pending", "note": ""})

    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        st.markdown(
            f"""
            <div class="panel">
                <strong>{candidate_row['candidate_label']}</strong><br>
                <span style="color:#486581;">{candidate_row['resume_category']} | {candidate_row['fit_band']} | Current decision: {action_state['status']}</span><br><br>
                <strong>Job:</strong> {candidate_row['job_title']}<br>
                <strong>Job status:</strong> {job_status}<br>
                <strong>Score:</strong> {candidate_row['score']:.3f}<br>
                <strong>Must-have hits:</strong> {candidate_row['must_have_hits']}<br>
                <strong>Review time:</strong> {candidate_row['review_minutes']:.1f} minutes
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("**Matched skills**")
        st.markdown(pills(list(candidate_row["matched_required_skills"]), tone="mint"), unsafe_allow_html=True)
        st.markdown("**Missing skills**")
        st.markdown(pills(list(candidate_row["missing_required_skills"])), unsafe_allow_html=True)

    with right:
        comparison = candidate_scope[
            ["candidate_label", "resume_category", "score", "must_have_hits", "review_minutes", "match_ratio"]
        ].copy()
        comparison["score"] = comparison["score"].round(3)
        comparison["match_ratio"] = comparison["match_ratio"].map(pct)
        st.subheader("How this candidate compares")
        st.dataframe(comparison, hide_index=True, use_container_width=True)

    st.subheader("Resume excerpt")
    st.write(clipped_text(str(candidate_row["resume_text"]), 1500))

    st.subheader("Recruiter note")
    chosen_status = st.selectbox(
        "Disposition",
        STATUS_ORDER,
        index=STATUS_ORDER.index(action_state["status"]) if action_state["status"] in STATUS_ORDER else 0,
        key=f"bench_status_{pair_key}",
    )
    note_value = st.text_area(
        "Note",
        value=action_state["note"],
        key=f"bench_note_{pair_key}",
    )
    st.session_state["review_actions"][pair_key] = {"status": chosen_status, "note": note_value}


def render_scenario_lab(data: dict[str, Any]) -> None:
    sensitivity = data["sensitivity"].copy()
    banner(
        "Scenario lab",
        "This page turns the v4 sensitivity analysis into an operational planning surface. Use it to justify recruiter time budgets and service-level parameters during the presentation.",
        eyebrow="Policy simulator",
    )

    left, right = st.columns(2, gap="large")
    with left:
        shortlist_size = st.selectbox("Shortlist size", sorted(sensitivity["shortlist_size"].unique()))
        review_budget = st.selectbox("Review budget (minutes)", sorted(sensitivity["review_budget_minutes"].unique()))
    with right:
        min_score_floor = st.selectbox("Minimum score floor", sorted(sensitivity["min_score_floor"].unique()))
        coverage_floor = st.selectbox(
            "Minimum weighted coverage ratio",
            sorted(sensitivity["min_weighted_coverage_ratio"].unique()),
        )

    scoped = sensitivity[
        (sensitivity["shortlist_size"] == shortlist_size)
        & (sensitivity["review_budget_minutes"] == review_budget)
        & (sensitivity["min_score_floor"] == min_score_floor)
        & (sensitivity["min_weighted_coverage_ratio"] == coverage_floor)
    ].sort_values(["objective_value", "mean_weighted_coverage_rate"], ascending=[False, False])

    best_global = sensitivity.sort_values(["objective_value", "mean_weighted_coverage_rate"], ascending=[False, False]).iloc[0]
    current_default = sensitivity[
        (sensitivity["shortlist_size"] == 5)
        & (sensitivity["review_budget_minutes"] == 25)
        & (sensitivity["coverage_bonus_weight"] == 0.12)
        & (sensitivity["min_score_floor"] == 0.35)
        & (sensitivity["min_weighted_coverage_ratio"] == 0.55)
    ]

    c1, c2, c3 = st.columns(3, gap="medium")
    stat_card(c1, "Top scoped objective", f"{scoped.iloc[0]['objective_value']:.2f}" if len(scoped) else "n/a", "Best result inside the chosen policy slice")
    stat_card(c2, "Best global coverage", pct(best_global["mean_weighted_coverage_rate"]), "Highest weighted coverage in the full sensitivity grid")
    stat_card(c3, "Best global budget", f"{int(best_global['review_budget_minutes'])} min", "Budget used by the strongest global configuration")

    st.subheader("Scoped configurations")
    if len(scoped):
        display = scoped[
            [
                "coverage_bonus_weight",
                "objective_value",
                "mean_selected_count",
                "mean_avg_score",
                "mean_coverage_rate",
                "mean_weighted_coverage_rate",
                "jobs_underfilled",
                "solve_time_s",
            ]
        ].copy()
        display["mean_coverage_rate"] = display["mean_coverage_rate"].map(pct)
        display["mean_weighted_coverage_rate"] = display["mean_weighted_coverage_rate"].map(pct)
        display["mean_avg_score"] = display["mean_avg_score"].round(3)
        display["objective_value"] = display["objective_value"].round(2)
        display["solve_time_s"] = display["solve_time_s"].round(3)
        st.dataframe(display, hide_index=True, use_container_width=True)
    else:
        st.info("No sensitivity rows matched that exact combination.")

    st.subheader("Recommendation")
    if len(current_default):
        current_default = current_default.iloc[0]
        st.markdown(
            f"""
            <div class="hint">
                The current operating point is shortlist size {int(current_default['shortlist_size'])}, review budget {int(current_default['review_budget_minutes'])} minutes,
                coverage bonus weight {current_default['coverage_bonus_weight']:.2f}, score floor {current_default['min_score_floor']:.2f},
                and weighted coverage floor {current_default['min_weighted_coverage_ratio']:.2f}. In the sensitivity grid, the strongest global configuration uses
                a {int(best_global['review_budget_minutes'])}-minute budget and coverage bonus weight {best_global['coverage_bonus_weight']:.2f}, which materially lifts average coverage.
            </div>
            """,
            unsafe_allow_html=True,
        )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="TF", layout="wide")
    inject_theme()
    ensure_session_state()

    data = load_portal_data(str(OUT_DIR))
    if not st.session_state["logged_in"]:
        render_login()
        return

    page, company_scope = render_sidebar(data)

    if page == "Company Dashboard":
        render_company_dashboard(data, company_scope)
    elif page == "Department Dashboard":
        render_department_dashboard(data, company_scope)
    elif page == "Job Workbench":
        render_job_workbench(data, company_scope)
    elif page == "Candidate Bench":
        render_candidate_bench(data, company_scope)
    else:
        render_scenario_lab(data)


if __name__ == "__main__":
    main()
