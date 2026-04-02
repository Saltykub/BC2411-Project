from __future__ import annotations

import streamlit as st


def inject_css():
    st.markdown(
        """<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    .stApp { font-family: 'Inter', sans-serif; }

    .hero-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 50%, #7c3aed 100%);
        border-radius: 20px; padding: 2rem 2.2rem; margin-bottom: 1.5rem;
        box-shadow: 0 20px 60px rgba(37,99,235,0.2);
    }
    .hero-login {
    background: linear-gradient(135deg, #5eead4 0%, #38bdf8 50%, #6366f1 100%);
    }

    .hero-admin {
        background: linear-gradient(135deg, #9ca3af 0%, #60a5fa 50%, #2dd4bf 100%);
    }

    .hero-company {
        background: linear-gradient(135deg, #fdba74 0%, #fb923c 50%, #facc15 100%);
    }

    .hero-job {
        background: linear-gradient(135deg, #818cf8 0%, #a78bfa 50%, #f472b6 100%);
    }

    .hero-candidate {
        background: linear-gradient(135deg, #94a3b8 0%, #38bdf8 50%, #34d399 100%);
    }

    .hero-scenario {
        background: linear-gradient(135deg, #86efac 0%, #4ade80 50%, #2dd4bf 100%);
    }
    .hero-card h1 {
        color: #111827;   /* dark gray (not pure black) */
        margin: 0 0 0.3rem 0;
        font-size: 1.8rem;
        font-weight: 800;
    }

    .hero-card p {
        color: #374151;   /* readable secondary text */
        margin: 0;
        font-size: 0.95rem;
        line-height: 1.5;
    }

    .hero-card .eyebrow {
        color: #2563eb;   /* nice accent blue */
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }

    .metric-card {
        background: white; border: 1px solid #e5e7eb; border-radius: 16px;
        padding: 1.2rem; box-shadow: 0 4px 16px rgba(0,0,0,0.04);
    }
    .metric-card .label { color: #6b7280; font-size: 0.78rem; font-weight: 600;
                          text-transform: uppercase; letter-spacing: 0.06em; }
    .metric-card .value { color: #111827; font-size: 1.8rem; font-weight: 800; margin: 0.2rem 0; }
    .metric-card .note  { color: #9ca3af; font-size: 0.82rem; }

    .candidate-card {
        background: white; border: 1px solid #e5e7eb; border-radius: 16px;
        padding: 1.2rem 1.4rem; margin-bottom: 0.8rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.03); transition: box-shadow 0.2s;
    }
    .candidate-card:hover { box-shadow: 0 8px 24px rgba(0,0,0,0.08); }

    .pill { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 999px;
            font-size: 0.78rem; font-weight: 600; margin: 0.15rem 0.2rem 0.15rem 0; }
    .pill-green  { background: #d1fae5; color: #065f46; }
    .pill-red    { background: #fee2e2; color: #991b1b; }
    .pill-blue   { background: #dbeafe; color: #1e40af; }
    .pill-gray   { background: #f3f4f6; color: #374151; }
    .pill-purple { background: #ede9fe; color: #5b21b6; }

    .section-panel {
        background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 16px;
        padding: 1.2rem 1.4rem; margin-bottom: 1rem;
    }
    .insight-box {
        background: #eff6ff; border-left: 4px solid #2563eb; border-radius: 8px;
        padding: 0.9rem 1.1rem; margin: 0.6rem 0; color: #1e40af; font-size: 0.9rem;
    }
    div[data-testid="stSidebar"] { background: #f8fafc; }

    .tf-score-value { color: #2563eb; }
    .tf-muted { color: #9ca3af; font-size: 0.82rem; }

    @media (prefers-color-scheme: light) {
        .metric-card {
            background: #0f172a; border-color: #334155;
            box-shadow: 0 4px 16px rgba(0,0,0,0.35);
        }
        .metric-card .label { color: #94a3b8; }
        .metric-card .value { color: #f8fafc; }
        .metric-card .note  { color: #64748b; }

        .candidate-card {
            background: #0f172a; border-color: #334155; color: #e2e8f0;
            box-shadow: 0 2px 12px rgba(0,0,0,0.35);
        }
        .candidate-card:hover { box-shadow: 0 10px 28px rgba(0,0,0,0.5); }

        .pill-green  { background: #064e3b; color: #a7f3d0; }
        .pill-red    { background: #7f1d1d; color: #fecaca; }
        .pill-blue   { background: #1e3a8a; color: #bfdbfe; }
        .pill-gray   { background: #334155; color: #e2e8f0; }
        .pill-purple { background: #4c1d95; color: #ddd6fe; }

        .section-panel {
            background: #111827; border-color: #374151; color: #e5e7eb;
        }
        .insight-box {
            background: #10223c; border-left-color: #60a5fa; color: #bfdbfe;
        }
        .tf-score-value { color: #60a5fa; }
        .tf-muted { color: #94a3b8; }
        div[data-testid="stSidebar"] { background: #0b1220; }
    }
    </style>""",
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, eyebrow: str = "", variant: str = ""):
    ey = f'<div class="eyebrow">{eyebrow}</div>' if eyebrow else ""
    variant_class = f" hero-{variant}" if variant else ""
    st.markdown(f'<div class="hero-card{variant_class}">{ey}<h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def metric_card(col, label: str, value: str, note: str = ""):
    col.markdown(
        f'<div class="metric-card">'
        f'<div class="label">{label}</div>'
        f'<div class="value">{value}</div>'
        f'<div class="note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def pills_html(items: list[str], tone: str = "gray") -> str:
    if not items:
        return '<span class="pill pill-gray">\u2014</span>'
    return " ".join(f'<span class="pill pill-{tone}">{s}</span>' for s in items)


def pct(v) -> str:
    return f"{100 * float(v):.1f}%"


def score_fmt(v) -> str:
    return f"{float(v):.3f}"


def get_job_status(fill_rate: float, coverage: float) -> str:
    if fill_rate >= 1.0 and coverage >= 0.8:
        return "Ready"
    if fill_rate >= 0.8:
        return "Watch"
    return "At Risk"
