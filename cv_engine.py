"""CV tailoring engine — no UI.

Shared by the Streamlit app (cv_app_Grock.py) and job_agent.
All candidate data comes from profile.yaml; nothing personal is hardcoded here.

    engine = CVEngine()                       # reads profile.yaml next to this file
    result = engine.tailor_cv(job_description)
    result["pdf"], result["pages"], result["latex"], result["ats_after"], ...
"""

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import yaml

DEFAULT_PROFILE = Path(__file__).parent / "profile.yaml"
DEFAULT_MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = (
    "You are a senior resume strategist and ATS expert specializing in engineering and medical technology roles. "
    "You write precise, impactful resume bullets grounded strictly in provided facts. "
    "You always return valid JSON with no LaTeX, no Markdown code blocks, and no invented data. "
    "Your bullet quality is specific, technical, and results-oriented."
)


_NUMBER = re.compile(r"\d+(?:\.\d+)?")


class PDFCompileError(RuntimeError):
    def __init__(self, log):
        super().__init__("pdflatex failed")
        self.log = log


# ============ LATEX UTILS ============
# Characters the default OT1 font prints wrongly (< > come out as ¡ ¿) or that make
# pdflatex fail outright ("Unicode character not set up"). Several appear in profile facts.
_MATH_SYMBOLS = {
    "<": r"$<$", ">": r"$>$", "→": r"$\rightarrow$", "←": r"$\leftarrow$",
    "≤": r"$\leq$", "≥": r"$\geq$", "≈": r"$\approx$", "≠": r"$\neq$",
    "α": r"$\alpha$", "β": r"$\beta$", "γ": r"$\gamma$", "δ": r"$\delta$", "Δ": r"$\Delta$",
    "θ": r"$\theta$", "λ": r"$\lambda$", "μ": r"$\mu$", "π": r"$\pi$", "σ": r"$\sigma$", "ω": r"$\omega$",
}


def escape_latex(text):
    """הופך תווים מיוחדים של LaTeX לטקסט בטוח בצורה חכמה בעזרת Regex"""
    if not isinstance(text, str):
        return text
    text = re.sub(r'(?<!\\)([&%$#_])', r'\\\1', text)
    return "".join(_MATH_SYMBOLS.get(ch, ch) for ch in text)


def normalize_course(course):
    return re.sub(r'\s+', ' ', course.strip().lower())


def select_valid_courses(raw_courses, allowed_courses, max_courses=3):
    requested = [c.strip() for c in raw_courses.split(',') if c.strip()]
    allowed_map = {normalize_course(c): c.strip() for c in allowed_courses}
    selected = []

    for course in requested:
        key = normalize_course(course)
        if key in allowed_map and allowed_map[key] not in selected:
            selected.append(allowed_map[key])

    if len(selected) < max_courses:
        for course in allowed_courses:
            if course not in selected:
                selected.append(course)
            if len(selected) == max_courses:
                break

    return ", ".join(selected[:max_courses])


def trim_words(text, max_words):
    words = text.split()
    return " ".join(words[:max_words]) + ("..." if len(words) > max_words else "")


def trim_bullets(bullets, max_bullets, max_words_each):
    return [trim_words(b, max_words_each) for b in bullets[:max_bullets]]


def _itemize(items_tex):
    latex = r"\begin{itemize}[noitemsep, topsep=2pt]" + "\n"
    for item in items_tex:
        latex += f"    \\item {item}\n"
    return latex + r"\end{itemize}"


class CVEngine:
    def __init__(self, profile_path=DEFAULT_PROFILE, api_key=None, model=DEFAULT_MODEL):
        self.profile = yaml.safe_load(Path(profile_path).read_text(encoding="utf-8"))
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self._client = None
        self.projects = {p["id"]: p for p in self.profile["projects"]}
        self.courses = list(self.profile["courses"])
        self.template = self._build_template()

    # ---------- profile → text ----------
    def fact_sheet(self):
        p = self.profile
        edu, exp = p["education"], p["experience"]
        lines = [
            "[PERSONAL & ACADEMIC]",
            f"- Name: {p['personal']['name']}",
            f"- Education: {edu['fact']}",
            f"- GPA: {edu['gpa']}",
            f"- Honors: {edu['honors']}",
            f"- Key Coursework: {', '.join(self.courses)}.",
            "",
            "[PROFESSIONAL EXPERIENCE]",
            f"- Role: {exp['title']}",
            f"- Company: {exp['company']}, {exp['location']} ({exp['dates_fact']})",
            *[f"- {f}" for f in exp["facts"]],
            "",
            "[ENGINEERING PROJECTS]",
        ]
        for i, proj in enumerate(p["projects"], 1):
            lines.append(f"{i}. {proj.get('fact_title', proj['title'])} (ID: {proj['id']}):")
            lines += [f"   - {f}" for f in proj["facts"]]
            lines.append("")
        lines += [
            "[SKILLS]",
            f"- Technical: {p['skills']['technical']}",
            f"- Soft Skills: {p['skills']['soft']}",
        ]
        return "\n".join(lines) + "\n"

    def build_prompt(self, job_description, allowed_courses=None):
        p = self.profile
        allowed_courses_text = ", ".join(allowed_courses or self.courses)
        exp = p["experience"]
        ids = ", ".join(f'"{pid}"' for pid in self.projects)
        match_guide = "\n".join(f"- {rule}" for rule in p.get("matching_guide", []))
        examples = "\n\n".join(
            f"❌ WEAK: \"{ex['weak']}\"\n✅ STRONG: \"{ex['strong']}\"" for ex in p.get("bullet_examples", [])
        )
        n_achievements = sum(1 for f in exp["facts"] if f.startswith("Achievement"))

        return f"""
You are an expert resume writer and ATS optimization specialist.
Your goal is to reorganize and improve a resume to match a specific job description — WITHOUT inventing experience that does not exist.

=== INPUTS ===
Job Description (JD):
{job_description}

Candidate Fact Sheet (ground truth — do not invent beyond this):
{self.fact_sheet()}

Allowed Courses Pool (select ONLY from this list):
{allowed_courses_text}

=== STEP-BY-STEP INSTRUCTIONS ===

STEP 1 — JD ANALYSIS:
Extract the top ATS keywords, required skills, and key responsibilities from the JD.
Identify which of these the candidate already has, and which are gaps.

STEP 2 — ATS SCORE BEFORE:
Score the candidate's raw resume against the JD on a 0-100 scale. Be honest and realistic.

STEP 3 — CAREER OBJECTIVE:
Write a 4-5 line career objective (max 70 words) that:
- Opens with the candidate's identity ({p['identity']})
- Highlights the 2 most relevant projects for this JD
- Embeds exact ATS keywords from the JD naturally
- Uses industry-specific language (manufacturing / engineering / medical / software — match the JD's domain)
- Is professional, concise, and does NOT hallucinate

STEP 4 — KEY COURSES:
Select 2 to 3 courses that are MOST relevant to the JD.
Rules:
- Select ONLY from the Allowed Courses Pool
- Copy the exact course name and grade (e.g. 'Signals and Systems (91)')
- Never invent or rename courses

STEP 5 — PROJECT SELECTION & BULLETS:
Available projects: {ids}. Select EXACTLY 2 most relevant to the JD.

PROJECT-TO-DOMAIN MATCHING GUIDE (follow this strictly):
{match_guide}

For each selected project write exactly 3 bullets:
- MIN ONE FULL LINE per bullet Max 20 words per bullet
- Embed exact JD keywords naturally
- NEVER invent tools, metrics, or results not in the Fact Sheet

FEW-SHOT QUALITY STANDARD (imitate this level of specificity):

{examples}

STEP 6 — EXPERIENCE BULLETS ({exp['company']}, EXACTLY 4 bullets important, max 15 words each):
Reframe the {exp['role_short']} role to match this JD's domain.
Use the {n_achievements} achievement facts in the Fact Sheet. Same quality standard: specific, action-oriented, no hallucination.

STEP 7 — SKILLS:
Group into exactly 2 categories:
- "Technical": list only tools/technologies confirmed by the projects and experience in the Fact Sheet. Add relevant JD keywords only if they map to real skills.Pick the most relevant ones to the jd
- "Soft Skills": pick the most relevant traits from the JD.

STEP 8 — ATS SCORE AFTER:
Re-score the improved resume against the JD. Estimate the improvement.

=== CRITICAL RULES ===
- Do NOT invent experience, tools, metrics, or results
- Do NOT add LaTeX commands (no \\textbf, \\begin, \\item etc.) — plain text only inside JSON values
- Do NOT use Markdown formatting or ```json blocks

=== OUTPUT FORMAT (JSON ONLY) ===
Return ONLY a raw JSON object with these exact keys:

{{
    "ANALYSIS_TEXT": "Markdown-formatted string with: JD Keywords extracted, ATS Score Before (X/100), ATS Score After (Y/100), Strengths, Gaps, Missing Keywords list.",
    "CAREER_OBJECTIVE": "Plain text, 4-5 lines.",
    "KEY_COURSES": "course1 (grade), course2 (grade), course3 (grade)",
    "SELECTED_PROJECTS": [
        {{"id": "MRAI", "bullets": ["Bullet 1", "Bullet 2", "Bullet 3"]}},
        {{"id": "XRAY", "bullets": ["Bullet 1", "Bullet 2", "Bullet 3"]}}
    ],
    "EXPERIENCE_BULLETS": ["Bullet 1", "Bullet 2", "Bullet 3"],
    "JD_KEYWORDS_USED": ["keyword1", "keyword2", "keyword3"],
    "MISSING_KEYWORDS": ["keyword1", "keyword2"],
    "ATS_SCORE_BEFORE": 65,
    "ATS_SCORE_AFTER": 82,
    "SKILLS": {{
        "Technical": "Python, SolidWorks...",
        "Soft Skills": "Analytical Thinking..."
    }}
}}
            """

    # ---------- LaTeX section builders ----------
    def build_projects_latex(self, selected_projects):
        """בונה את קוד ה-LaTeX לפרויקטים, שומר על הקישורים והכותרות קשיחים"""
        latex = ""
        for project in selected_projects[:2]:
            proj = self.projects.get(project.get("id"))
            bullets = project.get("bullets", [])
            if not proj or not bullets:
                continue
            title = r"\textbf{" + escape_latex(proj["title"]) + "}"
            if proj.get("link"):
                title += r" \hfill \href{" + proj["link"]["url"] + r"}{\uline{" + proj["link"]["label"] + "}}"
            latex += title + "\n"
            latex += _itemize(escape_latex(b) for b in bullets[:3]) + "\n\n"
        return latex.strip() + "\n"

    def build_experience_latex(self, exp_bullets):
        """בונה את קוד ה-LaTeX לניסיון, שומר על הכותרת קשיחה"""
        if not exp_bullets:
            return ""
        exp = self.profile["experience"]
        latex = r"\textbf{" + escape_latex(exp["title"]) + r"} \hfill " + exp["dates_tex"] + r" \newline" + "\n"
        latex += f"{escape_latex(exp['company'])}, {escape_latex(exp['location'])}\n"
        return latex + _itemize(escape_latex(b) for b in exp_bullets) + "\n"

    @staticmethod
    def build_skills_latex(skills_dict):
        """בונה רשימת כישורים מעוצבת בצורה בטוחה הרחק מה-AI"""
        if not skills_dict:
            return ""
        return _itemize(
            f"\\textbf{{{escape_latex(category)}:}} {escape_latex(skills)}" for category, skills in skills_dict.items()
        ) + "\n"

    def _build_template(self):
        p = self.profile
        per, edu, mil = p["personal"], p["education"], p["military"]
        header = (
            r"    {\Huge \textbf{" + escape_latex(per["name"].upper()) + r"}} \\" + "\n"
            r"    \vspace{4pt}" + "\n"
            r"    \textbf{" + escape_latex(per["headline"]) + r"} \\" + "\n"
            r"    \vspace{4pt}" + "\n"
            f"    {per['phone']}  $|$ {per['email']} $|$ "
            r"{ \href{" + per["linkedin"] + r"}{\uline{Linkedin}}} $|$ "
            r"\href{" + per["portfolio"] + r"}{\uline{Project Portfolio}}"
        )
        education = (
            r"\textbf{" + escape_latex(edu["degree"]) + r"} \hfill " + edu["dates"] + r" \\" + "\n"
            + escape_latex(edu["institution"]) + r" \hfill \textbf{GPA: " + str(edu["gpa"]) + "}\n\n"
            + _itemize([*edu["bullets_tex"], "Key Courses: {{KEY_COURSES}}"])
        )
        military = mil["heading_tex"] + "\n" + _itemize(mil["bullets_tex"])

        return r"""\documentclass[10pt,a4paper,sans]{article}

% Packages for formatting
\usepackage{ulem}
\usepackage[utf8]{inputenc}
\usepackage[left=0.75in,top=0.6in,right=0.75in,bottom=0.6in]{geometry}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{xcolor}

% Custom Colors
\definecolor{primary}{RGB}{0, 0, 0}

% Title Formatting
\titleformat{\section}{\large\bfseries\uppercase}{}{0pt}{}[\titlerule]
\titlespacing{\section}{0pt}{10pt}{5pt}

% Document Start
\begin{document}

\pagestyle{empty}

% Header
\begin{center}
""" + header + r"""
\end{center}

% Career Objective
\section{Career Objective}
\begin{flushleft}
{{CAREER_OBJECTIVE}}
\end{flushleft}

% Education
\section{Education}
\begin{flushleft}
""" + education + r"""
\end{flushleft}

% Projects
\section{Projects}
\begin{flushleft}
{{PROJECTS_SECTION}}
\end{flushleft}

% Experience
\section{Professional Experience}
\begin{flushleft}
{{EXPERIENCE_SECTION}}
\end{flushleft}

% Army Service (HARDCODED)
\section{Military Service}
\begin{flushleft}
""" + military + r"""
\end{flushleft}

% Skills
\section{Skills}
{{SKILLS_SECTION}}

% References
\section{References}
Available upon request.

\end{document}
"""

    def render_latex(self, sections):
        latex = self.template
        for key, content in sections.items():
            latex = latex.replace(f"{{{{{key}}}}}", content)
        return latex

    # ---------- LLM ----------
    @property
    def client(self):
        if self._client is None:
            if not self.api_key:
                raise RuntimeError("GROQ_API_KEY is not set")
            from groq import Groq
            self._client = Groq(api_key=self.api_key)
        return self._client

    def _chat(self, messages):
        completion = self.client.chat.completions.create(
            messages=messages,
            model=self.model,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        raw_text = completion.choices[0].message.content
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        return raw_text, json.loads(match.group(0) if match else raw_text)

    def find_invented_numbers(self, data, job_description, allowed_courses):
        """Statements whose numbers (metrics, %, counts) appear in neither the profile nor the JD.

        Only numbers are checked — invented non-numeric claims still need a human eye.
        """
        known = set(_NUMBER.findall(self.fact_sheet() + job_description + " ".join(allowed_courses)))
        statements = [data.get("CAREER_OBJECTIVE", "")]
        statements += [b for p in data.get("SELECTED_PROJECTS", []) for b in p.get("bullets", [])]
        statements += data.get("EXPERIENCE_BULLETS", [])
        issues = []
        for text in statements:
            invented = sorted(set(_NUMBER.findall(text)) - known)
            if invented:
                issues.append({"text": text, "numbers": invented})
        return issues

    def generate(self, job_description, allowed_courses=None):
        """Calls the LLM and returns analysis + ready LaTeX sections.

        If the answer contains numbers not backed by the profile or JD, the LLM gets one
        retry with the offending statements; anything still left is returned in `warnings`.
        """
        allowed_courses = allowed_courses or self.courses
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": self.build_prompt(job_description, allowed_courses)},
        ]
        raw_text, data = self._chat(messages)
        issues = self.find_invented_numbers(data, job_description, allowed_courses)
        retried = bool(issues)
        if issues:
            listed = "\n".join(f'- "{i["text"]}" (invented: {", ".join(i["numbers"])})' for i in issues)
            messages += [
                {"role": "assistant", "content": raw_text},
                {"role": "user", "content": (
                    "These statements contain numbers or metrics that are NOT in the Candidate Fact Sheet "
                    f"or the JD:\n{listed}\n\nRewrite them without any invented numbers, percentages, "
                    "datasets or results. Keep everything else. Return the full JSON object again."
                )},
            ]
            _, data = self._chat(messages)
            issues = self.find_invented_numbers(data, job_description, allowed_courses)

        # One-page content trimmer
        raw_projects = data.get("SELECTED_PROJECTS", [])
        for proj in raw_projects:
            proj["bullets"] = trim_bullets(proj.get("bullets", []), 3, 20)
        raw_exp = trim_bullets(data.get("EXPERIENCE_BULLETS", []), 4, 20)
        raw_objective = trim_words(data.get("CAREER_OBJECTIVE", ""), 70)
        validated_courses = select_valid_courses(data.get("KEY_COURSES", ""), allowed_courses, max_courses=3)

        return {
            "analysis": data.get("ANALYSIS_TEXT", "לא נוצר ניתוח."),
            "keywords_used": data.get("JD_KEYWORDS_USED", []),
            "missing_keywords": data.get("MISSING_KEYWORDS", []),
            "ats_before": data.get("ATS_SCORE_BEFORE", "N/A"),
            "ats_after": data.get("ATS_SCORE_AFTER", "N/A"),
            "selected_projects": [p.get("id") for p in raw_projects[:2]],
            "retried_for_invented_numbers": retried,
            "warnings": issues,
            "sections": {
                "CAREER_OBJECTIVE": escape_latex(raw_objective),
                "KEY_COURSES": escape_latex(validated_courses),
                "PROJECTS_SECTION": self.build_projects_latex(raw_projects),
                "EXPERIENCE_SECTION": self.build_experience_latex(raw_exp),
                "SKILLS_SECTION": self.build_skills_latex(data.get("SKILLS", {})),
            },
        }

    def mock_sections(self):
        """Sample sections for testing the PDF pipeline without spending tokens."""
        first_two = list(self.projects)[:2]
        return {
            "CAREER_OBJECTIVE": "Test objective for PDF generation.",
            "KEY_COURSES": "Python programming (100), Signals and Systems (91)",
            "PROJECTS_SECTION": self.build_projects_latex(
                [{"id": pid, "bullets": [f"Mock {pid} Bullet 1", f"Mock {pid} Bullet 2"]} for pid in first_two]
            ),
            "EXPERIENCE_SECTION": self.build_experience_latex(["Mock Experience Bullet 1"]),
            "SKILLS_SECTION": self.build_skills_latex({"Technical": "Python, LaTeX", "Soft Skills": "Teamwork"}),
        }

    # ---------- PDF ----------
    @staticmethod
    def compile_pdf(latex):
        """Returns (pdf_bytes, page_count). Raises PDFCompileError with the pdflatex log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_file = Path(tmpdir) / "resume.tex"
            pdf_file = Path(tmpdir) / "resume.pdf"
            tex_file.write_text(latex, encoding="utf-8")
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, str(tex_file)],
                capture_output=True, timeout=120,
            )
            log = result.stdout.decode("utf-8", errors="ignore")
            if result.returncode != 0 or not pdf_file.exists():
                raise PDFCompileError(log)
            # TeX hard-wraps its output at ~79 chars, even mid-word ("(1 p\nage"), so unwrap first.
            pages = re.search(r"Output written on .*?\((\d+) pages?", re.sub(r"\r?\n", "", log))
            return pdf_file.read_bytes(), int(pages.group(1)) if pages else None

    def tailor_cv(self, job_description, allowed_courses=None, compile_pdf=True):
        """Full pipeline: JD → LLM → LaTeX → PDF. `pages` should be 1 (PLAN D16)."""
        result = self.generate(job_description, allowed_courses)
        result["latex"] = self.render_latex(result["sections"])
        result["pdf"], result["pages"] = self.compile_pdf(result["latex"]) if compile_pdf else (None, None)
        return result
