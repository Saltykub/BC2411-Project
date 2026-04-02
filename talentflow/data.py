from __future__ import annotations

import json

import numpy as np
import pandas as pd
import streamlit as st

from .config import COMPANIES, DATA_DIR, DEPARTMENTS, OUT_DIR, PAIR_WEIGHTS, candidate_name


def _parse_json(val):
    if isinstance(val, (list, dict, set)):
        return val
    if pd.isna(val):
        return []
    try:
        return json.loads(str(val))
    except Exception:
        return []


@st.cache_data(show_spinner="Loading platform data …")
def load_data():
    pair_df = pd.read_csv(DATA_DIR / "pair_features.csv")
    resume_df = pd.read_csv(DATA_DIR / "resumes_milp_sample.csv")
    job_df = pd.read_csv(DATA_DIR / "jobs_milp_sample.csv")

    for col in ["skill_set", "required_skills"]:
        for df in [resume_df, job_df]:
            if col in df.columns:
                df[col] = df[col].apply(_parse_json)
    if "required_skill_weights" in job_df.columns:
        job_df["required_skill_weights"] = job_df["required_skill_weights"].apply(_parse_json)

    job_df["company_id"] = job_df["job_id"] % len(COMPANIES)
    job_df["company"] = job_df["company_id"].map(lambda x: COMPANIES[x]["name"])
    job_df["department"] = job_df["job_title"].map(lambda t: DEPARTMENTS.get(t, "Engineering"))

    resume_df["candidate_name"] = resume_df["resume_id"].apply(candidate_name)

    if "text_clean" in resume_df.columns:
        resume_df["_resume_text"] = resume_df["text_clean"]
    elif "text_raw" in resume_df.columns:
        resume_df["_resume_text"] = resume_df["text_raw"]
    elif "text_no_stop" in resume_df.columns:
        resume_df["_resume_text"] = resume_df["text_no_stop"]
    else:
        resume_df["_resume_text"] = "Resume text not available in the sample data."

    signals = {
        "tfidf_sim": "pos",
        "bm25_sim": "pos",
        "skill_overlap_jaccard": "pos",
        "weighted_required_hit": "pos",
        "exp_gap": "neg",
        "degree_gap": "neg",
        "length_penalty": "neg",
    }
    norm_df = pair_df.copy()
    for signal, direction in signals.items():
        g = norm_df.groupby("job_id")[signal]
        mins = g.transform("min")
        maxs = g.transform("max")
        rng = maxs - mins
        norm_df[f"{signal}_norm"] = np.where(rng > 1e-9, (norm_df[signal] - mins) / rng, 0.5)
        if direction == "neg":
            norm_df[f"{signal}_norm"] = 1.0 - norm_df[f"{signal}_norm"]

    norm_df["pair_score"] = (
        PAIR_WEIGHTS["w_tfidf"] * norm_df["tfidf_sim_norm"]
        + PAIR_WEIGHTS["w_bm25"] * norm_df["bm25_sim_norm"]
        + PAIR_WEIGHTS["w_skill"] * norm_df["skill_overlap_jaccard_norm"]
        + PAIR_WEIGHTS["w_coverage"] * norm_df["weighted_required_hit_norm"]
        + PAIR_WEIGHTS["w_exp"] * norm_df["exp_gap_norm"]
        + PAIR_WEIGHTS["w_deg"] * norm_df["degree_gap_norm"]
        + PAIR_WEIGHTS["w_length"] * norm_df["length_penalty_norm"]
    )

    merge_cols_norm = [
        "resume_id",
        "job_id",
        "pair_score",
        "review_minutes_capped",
        "skill_overlap_jaccard",
        "weighted_required_hit",
        "must_have_hits",
        "exp_gap",
        "degree_gap",
        "redundancy_cluster",
    ]
    merge_cols_job = ["job_id", "job_title", "company", "company_id", "department", "required_skills"]
    merge_cols_res = ["resume_id", "candidate_name", "skill_set", "word_count", "exp_years", "degree_level", "_resume_text"]

    methods: dict[str, pd.DataFrame] = {}
    for method, fname in [("MILP", "milp_best_selected.csv"), ("Greedy", "greedy_selected.csv"), ("ScoreOnly", "scoreonly_selected.csv")]:
        fp = OUT_DIR / fname
        if not fp.exists():
            continue
        sel = pd.read_csv(fp)
        sel = sel.merge(norm_df[merge_cols_norm], on=["resume_id", "job_id"], how="left")
        sel = sel.merge(job_df[merge_cols_job], on="job_id", how="left")
        sel = sel.merge(resume_df[merge_cols_res], on="resume_id", how="left")
        sel["matched_skills"] = sel.apply(
            lambda r: sorted(set(r["skill_set"]) & set(r["required_skills"]))
            if isinstance(r["skill_set"], list) and isinstance(r["required_skills"], list) else [],
            axis=1,
        )
        sel["missing_skills"] = sel.apply(
            lambda r: sorted(set(r["required_skills"]) - set(r["skill_set"]))
            if isinstance(r["skill_set"], list) and isinstance(r["required_skills"], list) else [],
            axis=1,
        )
        methods[method] = sel

    sens: dict[str, pd.DataFrame] = {}
    for name in ["budget", "k", "exposure", "floor"]:
        fp = OUT_DIR / f"sensitivity_{name}.csv"
        if fp.exists():
            sens[name] = pd.read_csv(fp)

    mc_path = OUT_DIR / "method_comparison.csv"
    method_comp = pd.read_csv(mc_path, index_col=0) if mc_path.exists() else pd.DataFrame()

    return {
        "pair_df": pair_df,
        "norm_df": norm_df,
        "resume_df": resume_df,
        "job_df": job_df,
        "methods": methods,
        "sensitivity": sens,
        "method_comparison": method_comp,
    }
