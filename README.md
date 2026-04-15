# TalentFlow — Resume Shortlisting Optimisation

TalentFlow is a **prescriptive analytics project for technical recruitment**.  
TalentFlow demonstrates how prescriptive analytics can be applied to recruitment shortlisting.
Rather than treating shortlisting as a simple ranking problem, the project formulates it as a constrained optimisation problem that balances quality, feasibility, skill coverage, and diversity across multiple roles. 
It extends traditional Applicant Tracking System (ATS) scoring by adding a **decision-optimisation layer** that jointly selects candidate shortlists across multiple jobs.

Instead of only asking *“How well does a candidate match a job?”*, TalentFlow asks:

> **Which combination of candidates should be shortlisted for each role so that the overall outcome is high-quality, skill-covering, time-feasible, and non-redundant?**

The project combines:

- NLP-based resume and job description preprocessing
- Feature engineering for candidate-job matching
- Mixed-Integer Linear Programming (MILP) for shortlist optimisation
- Baseline comparison against greedy and score-only approaches
- Sensitivity analysis on key recruitment policy parameters
- A Streamlit app for interactive demonstration

---

## Project Scope

TalentFlow studies how recruitment shortlisting can be improved beyond simple ranking.  
The workflow covers:

- Resume text consolidation from raw `.txt` files
- Data cleaning and exploratory data analysis
- Structured extraction of experience and degree signals
- Skill extraction and candidate-job feature engineering
- MILP formulation for shortlist optimisation
- Comparison with heuristic and ranking-only baselines
- Sensitivity analysis on operational constraints
- Interactive app-based demonstration of the workflow

---

## Key Features

- **Joint shortlist optimisation** across multiple jobs
- **Skill coverage emphasis** through required-skill engineering and scarcity weighting
- **Operational realism** through review-time budgets, shortlist size limits, exposure caps, and anti-redundancy rules
- **Transparent experimentation** through notebook-based preprocessing, modelling, and sensitivity analysis
- **Interactive demo interface** through a Streamlit app

---

## Repository Structure

```text
.
├─ .devcontainer/
├─ .streamlit/
├─ data/
│  ├─ job_title_des.csv
│  ├─ resume_txt_combined.csv
│  ├─ jobs_milp_sample.csv
│  ├─ resumes_milp_sample.csv
│  ├─ pair_features.csv
├─ outputs/
├─ talentflow/
│  ├─ __init__.py
│  ├─ company.py
│  ├─ config.py
│  ├─ data.py
│  ├─ main.py
│  ├─ ui.py
│  └─ pages/
│     ├─ admin.py
│     ├─ candidate.py
│     ├─ company.py
│     ├─ job.py
│     ├─ login.py
│     └─ scenario.py
│
├─ 00_Data_Preprocessing.ipynb
├─ 01_DataCleaning_EDA.ipynb
├─ 02_Scoring_MILP_Results.ipynb
├─ 03_Sensitivity_Analysis.ipynb
├─ app.py
├─ README.md
├─ requirements.txt
├─ pyproject.toml
├─ uv.lock
├─ .gitattributes
└─ .gitignore
```

---

## Main Components

### `data/`

Contains the input data files and intermediate artifacts used by the notebooks and app workflow.

**Raw datasets**
- `resume_txt_combined.csv`: Consolidated full-text resume dataset built from raw resume files
- `job_title_des.csv`: Job description dataset used for job-side text processing

**Model-ready artifacts**
- `resumes_milp_sample.csv`
- `jobs_milp_sample.csv`
- `pair_features.csv`

### `outputs/`

Stores selected analysis artifacts and experiment outputs, such as:
- Best model configuration files
- Method comparison results
- Sensitivity analysis figures
- Exported charts for reporting

This folder is used across the modelling and policy-analysis workflow.

### `talentflow/`

Contains the main app modules for configuration, UI logic, and shared functionality.

### `talentflow/pages/`

Contains the Streamlit page-level views for different user flows and scenarios.

### `00_Data_Preprocessing.ipynb`

Builds the consolidated resume dataset from raw text files.

### `01_DataCleaning_EDA.ipynb`

Handles preprocessing, extraction, feature engineering, and exploratory analysis.

### `02_Scoring_MILP_Results.ipynb`

Implements the optimisation model, baselines, and results analysis.

### `03_Sensitivity_Analysis.ipynb`

Studies how structural parameters affect shortlist performance and feasibility.

---

## How to Run

### 1. Clone the repository

```shell
git clone <https://github.com/Saltykub/BC2411-Project.git>
cd BC2411-Project
git lfs pull
```

### 2. Create a virtual environment

```shell
python -m venv .venv
```

### 3. Activate the virtual environment on Windows

```shell
.venv\Scripts\activate
```

### 4. Install dependencies

```shell
pip install -r requirements.txt
```

### 5. Run the notebooks

```shell
jupyter notebook
```

Then open and run these notebooks in order:

1. `00_Data_Preprocessing.ipynb`
2. `01_DataCleaning_EDA.ipynb`
3. `02_Scoring_MILP_Results.ipynb`
4. `03_Sensitivity_Analysis.ipynb`

--- 
## Recommended Execution Order

```text
1. Clone repository
2. Pull Git LFS files
3. Create and activate virtual environment
4. Install dependencies
5. Run 00_Data_Preprocessing.ipynb
6. Run 01_DataCleaning_EDA.ipynb
7. Run 02_Scoring_MILP_Results.ipynb
8. Run 03_Sensitivity_Analysis.ipynb
9. Run streamlit run app.py
```

