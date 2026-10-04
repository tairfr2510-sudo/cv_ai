# cv_ai

Tailors my one-page LaTeX resume to a job description using an LLM (Groq), without inventing experience.

| File | What it is |
|------|------------|
| `profile.yaml` | **All facts about me** — the only place to edit personal data, courses, projects, experience |
| `cv_engine.py` | The engine: prompt → Groq → LaTeX → PDF. No UI; also used by `job_agent` |
| `cv_app_Grock.py` | Streamlit UI on top of the engine |

```python
from cv_engine import CVEngine
result = CVEngine().tailor_cv(job_description)   # needs GROQ_API_KEY
result["pdf"], result["pages"], result["ats_after"], result["missing_keywords"]
```

Run the app: `streamlit run cv_app_Grock.py`. Requires `pdflatex` (see `packages.txt`).
