# BC2411-Project

Resume-to-job shortlisting project for BC2411 using text matching, feature engineering, and MILP optimisation.

**Project Layout**
- `resume_split.ipynb`: main notebook for data loading, scoring, optimisation, evaluation, and chart generation.
- `UpdatedResumeDataSet.csv`: resume dataset.
- `job_title_des.csv`: job description dataset.
- `outputs_resume_project_v4/`: generated CSV outputs and chart images.
- `pyproject.toml`: project metadata and dependencies for `uv`.

**Quick Start**
```powershell
uv sync --extra notebook
```

This installs the base dependencies plus Jupyter support.

If you also want the optimisation solver and embedding model support:

```powershell
uv sync --extra notebook --extra optimization --extra embeddings
```

**Run The Notebook**
```powershell
uv run jupyter lab
```

Then open `resume_split.ipynb`.

**Useful Notes**
- `streamlit` is included in the base dependencies, so you can add a Streamlit app later without reworking the environment.
- `gurobipy` is optional because it requires a working Gurobi installation and license for the MILP section.
- `sentence-transformers` is optional because the notebook currently keeps dense embeddings disabled by default.
- `requirements.txt` can still be used with `pip` or `uv pip`, but `pyproject.toml` is now the main source of truth for dependency management.
