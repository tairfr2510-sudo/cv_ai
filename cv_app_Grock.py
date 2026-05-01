import streamlit as st
import os
import subprocess
import tempfile
import json
import re
from dotenv import load_dotenv
from pathlib import Path
from groq import Groq

# ============ CONFIGURATION ============
load_dotenv()

# מנגנון חכם: קודם בודק בכספת של הענן, ואם אין - בודק בקובץ המקומי
if "GROQ_API_KEY" in st.secrets:
    API_KEY = st.secrets["GROQ_API_KEY"]
else:
    API_KEY = os.getenv('GROQ_API_KEY')

if not API_KEY:
    st.error("❌ GROQ_API_KEY לא נמצא בהגדרות הענן או בקובץ .env מקומי")
    st.stop()

# אתחול הלקוח של Groq
client = Groq(api_key=API_KEY)

# ============ LATEX UTILS & BUILDERS ============
def escape_latex(text):
    """הופך תווים מיוחדים של LaTeX לטקסט בטוח בצורה חכמה בעזרת Regex"""
    if not isinstance(text, str):
        return text
    return re.sub(r'(?<!\\)([&%$#_])', r'\\\1', text)

def build_projects_latex(selected_projects):
    """בונה את קוד ה-LaTeX לפרויקטים, שומר על הקישורים והכותרות קשיחים"""
    project_catalog = {
        "MRAI": {
            "title": r"\textbf{AI-Powered MRI/CT Diagnostic \& 3D Reconstruction Platform} \hfill \href{https://github.com/tairfr2510-sudo/MRAI-Tumor-Segmentation-3D-Export-Engine}{\uline{GitHub}}"
        },
        "XRAY": {
            "title": r"\textbf{Autonomous X-ray Targeting \& Positioning System} \hfill \href{https://aistudio.google.com/apps/e4bd7e56-afa3-41d2-984a-88577243b839?fullscreenApplet=true&showPreview=true&showAssistant=true}{\uline{Demo}}"
        },
        "MECH": {
            "title": r"\textbf{Mechanical Hand Design \& Modeling (SolidWorks Project)}"
        }
    }

    latex = ""
    for project in selected_projects[:2]:
        key = project.get("id")
        bullets = project.get("bullets", [])
        if key not in project_catalog or not bullets:
            continue
        latex += project_catalog[key]["title"] + "\n"
        latex += r"\begin{itemize}[noitemsep, topsep=2pt]" + "\n"
        for bullet in bullets[:3]:
            latex += f"    \\item {escape_latex(bullet)}\n"
        latex += r"\end{itemize}" + "\n\n"

    return latex.strip() + "\n"

def build_experience_latex(exp_bullets):
    """בונה את קוד ה-LaTeX לניסיון, שומר על הכותרת קשיחה"""
    if not exp_bullets: return ""
    latex = r"\textbf{3D Printer Operator (Meat-Replacement Printing)} \hfill 06/2022 -- 07/2023 \newline" + "\n"
    latex += r"Redefinemeat, Rehovot" + "\n"
    latex += r"\begin{itemize}[noitemsep, topsep=2pt]" + "\n"
    for bullet in exp_bullets:
        latex += f"    \\item {escape_latex(bullet)}\n"
    latex += r"\end{itemize}" + "\n"
    return latex

def build_skills_latex(skills_dict):
    """בונה רשימת כישורים מעוצבת בצורה בטוחה הרחק מה-AI"""
    if not skills_dict: return ""
    latex = r"\begin{itemize}[noitemsep, topsep=2pt]" + "\n"
    for category, skills in skills_dict.items():
        latex += f"    \\item \\textbf{{{escape_latex(category)}:}} {escape_latex(skills)}\n"
    latex += r"\end{itemize}" + "\n"
    return latex



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

# ============ LOAD LATEX TEMPLATE ============
LATEX_TEMPLATE = r"""\documentclass[11pt,a4paper,sans]{article}

% Packages
\usepackage{ulem}
\usepackage[utf8]{inputenc}
\usepackage[left=0.65in,top=0.45in,right=0.65in,bottom=0.45in]{geometry}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{xcolor}

% Global list tightening
\setlist[itemize]{noitemsep, topsep=1pt, parsep=0pt, partopsep=0pt}

% Section formatting
\titleformat{\section}{\large\bfseries\uppercase}{}{0pt}{}[\titlerule]
\titlespacing{\section}{0pt}{5pt}{2pt}

\begin{document}
\pagestyle{empty}
\raggedright
\setlength{\parskip}{2pt}
\setlength{\parindent}{0pt}

% Header
\begin{center}
    {\Huge \textbf{TAIR FRIDMAN}} \\
    \vspace{2pt}
    \textbf{Third Year Biomedical Engineering Student at the Technion} \\
    \vspace{2pt}
    054-9988143  $|$ tairfr2510@gmail.com $|$ \href{http://www.linkedin.com/in/tairfridman}{\uline{LinkedIn}} $|$ \href{https://technionmail-my.sharepoint.com/:f:/g/personal/tair_fridman_campus_technion_ac_il/IgB6kjkw2NY_Q7lWN8LxAKPkAZNCp29HqfC-8IRGrvIwpbQ?e=Adc87l}{\uline{Project Portfolio}}
\end{center}

% Career Objective
\section{Career Objective}
{{CAREER_OBJECTIVE}}

% Education
\section{Education}
\textbf{B.Sc. in Biomedical Engineering (In Progress)} \hfill 2023 -- Present \\
Technion - Israel Institute of Technology \hfill \textbf{GPA: 90}
\begin{itemize}
    \item Dean's List (Academic Excellence): Winter 2024, Spring 2025, Winter 2026.
    \item Key Courses: {{KEY_COURSES}}
\end{itemize}

% Projects
\section{Projects}
{{PROJECTS_SECTION}}

% Experience
\section{Professional Experience}
{{EXPERIENCE_SECTION}}

% Military Service
\section{Military Service}
\textbf{Soldier in the special unit ``Dia''} --- \textbf{869th Combat Collection Battalion}
\begin{itemize}
    \item Received excellence recognition in training and granted a parachute course as a prize.
    \item Selected for the commanders' training course; served as Trainees Commander and operational line commander.
    \item Team Sergeant (Operational Line): led team in absence of team leader, made critical decisions under pressure, managed team logistics.
\end{itemize}

% Skills
\section{Skills}
{{SKILLS_SECTION}}

% References
\section{References}
Available upon request.

\end{document}
"""

# ============ HARDCODED FACT SHEET ============
FACT_SHEET = """
[PERSONAL & ACADEMIC]
- Name: Tair Fridman
- Education: 3rd-year B.Sc. in Biomedical Engineering, Technion - Israel Institute of Technology.
- GPA: 90
- Honors: Dean's List (Winter 2024, Spring 2025, Winter 2026).
- Key Coursework: Python Programming (100), Biological Fluid Mechanics (100), Signals and Systems (91).

[PROFESSIONAL EXPERIENCE]
- Role: 3D Printer Operator (Meat-Replacement Printing)
- Company: Redefinemeat, Rehovot (06/2022 - 07/2023)
- Details: Operated and optimized 3D printers specifically for meat substitutes. 
- Achievements: Collaborated with R&D on troubleshooting and protocol development. Initiated and built a SharePoint site for the team and implemented Excel data tracking to enhance productivity.

[ENGINEERING PROJECTS]
1. AI-Powered MRI/CT Diagnostic & 3D Reconstruction Platform (MRAI Engine):
   - Tech Stack: Python, PyTorch, DICOM/NIfTI processing.
   - Details: Developed an end-to-end pipeline processing volumetric imaging. 
   - AI/CV: Implemented a 3D U-Net deep learning model for automated brain tumor segmentation. 
   - Rendering: Generated 3D anatomical models using the Marching Cubes algorithm (STL export) and built a Multi-Planar Reconstruction (MPR) tool for slice inspection.

2. Autonomous X-Ray Targeting & Positioning System:
   - Tech Stack: Python, OpenCV, MediaPipe, Tkinter, threading.
   - Details: Designed an autonomous system integrating Computer Vision and NLP (Hebrew text input) for automated X-ray arm alignment.
   - Mechanism: Developed a Python-based state machine (Idle, Macro Move, Micro Center) for precise motion control.
   - Features: Real-time pose detection, dynamic 3x auto-zooming, moving crosshair alignment, and image enhancement (CLAHE).

3. Mechanical Hand Design & Modeling (SolidWorks Project)
    - Designed a multi-articulated mechanical hand mechanism using SolidWorks, focusing on mimicking anatomical joint movements.
    -Performed tolerance analysis and created detailed assembly files for potential 3D printing manufacturing.

[SKILLS]
- Technical: Python, PyTorch, OpenCV, MediaPipe, NLP, SolidWorks, MATLAB, Excel, SharePoint.
- Soft Skills: Analytical Thinking, Quick Learner, Team Leadership, Problem Solving.
"""

# ============ STREAMLIT PAGE CONFIG ============
st.set_page_config(
    page_title="Resume Customizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎯 AI-Powered Resume Customizer (Groq Engine)")
st.markdown("---")

# ============ SIDEBAR - INSTRUCTIONS ============
with st.sidebar:
    st.header("📋 How It Works")
    st.markdown("""
    1. **Paste a Job Description (JD)** - Copy-paste the job requirements
    2. **Click "Customize Resume"** - AI tailors your CV to the JD
    3. **Download PDF** - Get your personalized resume
    
    ⚠️ **Note:** Military Service, Project Links, and Job Titles are hardcoded to protect PDF integrity.
    """)

# ============ MAIN APP ============
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Job Description")
    job_description = st.text_area(
        "Paste the job description here:",
        height=300,
        placeholder="Copy-paste the entire job posting...",
        key="jd_input"
    )

with col2:
    st.subheader("👤 Your Fact Sheet")
    st.info("✅ Hardcoded to prevent AI hallucinations")
    st.text_area(
        "Your data (read-only):",
        value=FACT_SHEET,
        height=220,
        disabled=True,
        key="fact_sheet"
    )
    courses_input = st.text_area(
        "📚 Courses you allow the AI to choose from (comma separated):",
        value="Introduction to Computing with Python (100), Biological Fluid Mechanics (100), Physics 1M (100), Differential and Integral Calculus 1M2 (99), Directions in Biomedical Engineering (97), Introduction to Human Anatomy (97), Partial Differential Equations/T (96), Physical Chemistry 1B (96), Fundamentals of Medical Materials (96), Metabolic Pathways (96), Physics 2 (95), From Cells to Tissues (94), Introduction to Probability H (93), General Chemistry (92), Laboratory in Bio-Medical Engineering 1 (92), Body Systems Physiology for Engineers (92), Signals and Systems (91)",
        height=70,
        key="courses_input"
    )

st.markdown("---")

# ============ כפתור בדיקה ללא טוקנים ============
st.subheader("🧪 Debugging Area")
if st.button("בדיקת PDF עם נתוני דמי (חוסך זמן)", use_container_width=True):
    mock_data = {
        "CAREER_OBJECTIVE": "Test objective for PDF generation.",
        "KEY_COURSES": "Python programming (100), Signals and Systems (91)",
        "PROJECTS_SECTION": build_projects_latex([
            {"id": "MRAI", "bullets": ["Mock MRAI Bullet 1", "Mock MRAI Bullet 2"]},
            {"id": "XRAY", "bullets": ["Mock XRAY Bullet 1", "Mock XRAY Bullet 2"]}
        ]),
        "EXPERIENCE_SECTION": build_experience_latex(["Mock Experience Bullet 1"]),
        "SKILLS_SECTION": build_skills_latex({"Technical": "Python, LaTeX", "Soft Skills": "Teamwork"})
    }
    st.session_state.analysis = "This is a mock analysis text."
    st.session_state.generated_sections = mock_data
    st.success("✅ נתוני דמי נטענו! עכשיו אפשר ללחוץ על 'Generate PDF Resume' למטה.")

st.markdown("---")

# ============ CUSTOMIZE BUTTON ============
if st.button("🚀 Customize Resume", key="customize_btn", use_container_width=True):
    if not job_description.strip():
        st.error("❌ אנא הכנס תיאור משרה קודם!")
    else:
        st.info("⏳ מנוע Llama 3.3 (Groq) מנתח את המשרה ומשכתב את קורות החיים...")
        
        try:
            allowed_courses = [c.strip() for c in courses_input.split(",") if c.strip()]
            allowed_courses_text = ", ".join(allowed_courses)

            master_prompt = f"""
You are a senior resume strategist and ATS specialist. Your job is to produce the strongest possible one-page resume for the candidate against a specific job description.

PHILOSOPHY: You may use bold, impactful language and present real experiences in the most impressive, industry-relevant way possible. Reframe, reorder emphasis, use strong action verbs, and adopt the vocabulary of the JD's industry. You may infer skills that are clearly implied by the projects (e.g. if a project used PyTorch you can claim deep learning). What you must NEVER do: invent jobs, tools, metrics, or experiences that have no basis in the Fact Sheet.

=== INPUTS ===
Job Description:
{job_description}

Candidate Fact Sheet (ground truth):
{FACT_SHEET}

Allowed Courses Pool:
{allowed_courses_text}

=== STEPS ===

STEP 1 — ATS ANALYSIS:
- Extract the top 10 ATS keywords / required skills from the JD.
- Identify which the candidate has (strengths) and which are gaps.
- Score the raw resume vs. JD: ATS_SCORE_BEFORE (0-100).

STEP 2 — CAREER OBJECTIVE (strict length: 3-4 sentences, MAX 80 words):
- Sentence 1: Who the candidate is + most relevant degree/institution.
- Sentence 2-3: The 2 most relevant projects, with JD-specific vocabulary.
- Sentence 4: What value the candidate brings to this role.
- Use powerful industry language. No filler phrases. No hallucination.

STEP 3 — KEY COURSES (select 2-3, ONLY from Allowed Courses Pool):
- Pick the most relevant to the JD.
- Copy course name and grade exactly as written (e.g. "Signals and Systems (91)").
- Never invent or rename.

STEP 4 — PROJECTS (select EXACTLY 2 from: "MRAI", "XRAY", "MECH"):
Project facts:
- MRAI: Python, PyTorch, 3D U-Net, brain tumor segmentation, DICOM/NIfTI, Marching Cubes 3D reconstruction, MPR viewer.
- XRAY: Python, OpenCV, MediaPipe, NLP (Hebrew input), state machine (Idle/Macro/Micro), real-time pose detection, CLAHE, automated alignment.
- MECH: SolidWorks, multi-articulated mechanical hand, anatomical joint mimicry, tolerance analysis, assembly for 3D printing.

For each selected project write EXACTLY 3 bullets (no more, no less):
- Max 22 words per bullet.
- Format: Strong Action Verb + technical detail + impact/outcome.
- Embed JD keywords naturally. Use industry vocabulary.
- Imply skills strongly (e.g. "engineered", "deployed", "optimized" are fine for real work).
- NEVER invent tools or results not in the facts above.

STEP 5 — EXPERIENCE (Redefinemeat, EXACTLY 2 bullets):
- Max 20 words per bullet.
- Reframe the 3D Printer Operator role to highlight what is most relevant to this JD.
- Allowed: process optimization, cross-functional collaboration, troubleshooting, data tracking, R&D support, protocol development.
- Strong language is encouraged. No invented facts.

STEP 6 — SKILLS (exactly 2 categories: "Technical" and "Soft Skills"):
- Technical: tools/technologies from projects + experience. Add JD-relevant terms only if genuinely implied.
- Soft Skills: 4-5 traits, most relevant to the JD, drawn from the Fact Sheet.
- Keep each list short and punchy (comma-separated, no sentences).

STEP 7 — ATS SCORE AFTER:
Re-score the improved resume vs. JD (ATS_SCORE_AFTER).

=== HARD RULES ===
- Total bullet content must fit on ONE A4 page with other fixed sections.
- Do NOT add LaTeX commands inside JSON values (no \\textbf, \\item, \\begin).
- Return plain text only inside all JSON string values.
- Do NOT use Markdown code blocks or ```json formatting.

=== OUTPUT (raw JSON only) ===
{{
    "ANALYSIS_TEXT": "## JD Analysis\\n**Top ATS Keywords:** ...\\n**ATS Score Before:** X/100\\n**ATS Score After:** Y/100\\n**Strengths:** ...\\n**Gaps:** ...",
    "CAREER_OBJECTIVE": "3-4 sentence plain text, max 60 words.",
    "KEY_COURSES": "Course Name (grade), Course Name (grade)",
    "SELECTED_PROJECTS": [
        {{"id": "MRAI", "bullets": ["Bullet 1", "Bullet 2", "Bullet 3"]}},
        {{"id": "XRAY", "bullets": ["Bullet 1", "Bullet 2", "Bullet 3"]}}
    ],
    "EXPERIENCE_BULLETS": ["Bullet 1", "Bullet 2"],
    "JD_KEYWORDS_USED": ["keyword1", "keyword2", "keyword3"],
    "MISSING_KEYWORDS": ["keyword1", "keyword2"],
    "ATS_SCORE_BEFORE": 65,
    "ATS_SCORE_AFTER": 82,
    "SKILLS": {{
        "Technical": "Python, PyTorch, OpenCV...",
        "Soft Skills": "Analytical Thinking, Team Leadership..."
    }}
}}
            """

            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": master_prompt,
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            raw_text = chat_completion.choices[0].message.content
            
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
            else:
                data = json.loads(raw_text)
            
            validated_courses = select_valid_courses(data.get("KEY_COURSES", ""), allowed_courses, max_courses=3)
            st.session_state.analysis = data.get("ANALYSIS_TEXT", "לא נוצר ניתוח.")
            st.session_state.keywords_used = data.get("JD_KEYWORDS_USED", [])
            st.session_state.missing_keywords = data.get("MISSING_KEYWORDS", [])
            st.session_state.ats_before = data.get("ATS_SCORE_BEFORE", "N/A")
            st.session_state.ats_after = data.get("ATS_SCORE_AFTER", "N/A")
            st.session_state.generated_sections = {
                "CAREER_OBJECTIVE": escape_latex(data.get("CAREER_OBJECTIVE", "")),
                "KEY_COURSES": escape_latex(validated_courses),
                "PROJECTS_SECTION": build_projects_latex(data.get("SELECTED_PROJECTS", [])),
                "EXPERIENCE_SECTION": build_experience_latex(data.get("EXPERIENCE_BULLETS", [])),
                "SKILLS_SECTION": build_skills_latex(data.get("SKILLS", {}))
            }

            st.success("✅ הניתוח והשכתוב הושלמו בהצלחה ובמהירות האור!")
            
        except Exception as e:
            st.error(f"❌ שגיאת API/קוד: {str(e)}")

# ============ DISPLAY ANALYSIS ============
if "analysis" in st.session_state:
    st.markdown("---")

    # ATS Score Banner
    if "ats_before" in st.session_state and "ats_after" in st.session_state:
        ats_before = st.session_state.ats_before
        ats_after = st.session_state.ats_after
        col_a, col_b = st.columns(2)
        col_a.metric("ATS Score — Before", f"{ats_before}/100")
        col_b.metric("ATS Score — After", f"{ats_after}/100",
                     delta=f"+{ats_after - ats_before}" if isinstance(ats_after, int) and isinstance(ats_before, int) else None)

    with st.expander("🧐 Professional Analysis & Match Score", expanded=True):
        st.markdown(st.session_state.analysis)

if "keywords_used" in st.session_state:
    with st.expander("🏷️ JD Keywords inserted into resume", expanded=False):
        keywords = st.session_state.keywords_used
        if keywords:
            st.markdown("**Keywords embedded from JD:**")
            st.markdown("  ".join([f"`{str(k)}`" for k in keywords]))
        else:
            st.warning("No keywords were reported by the model for this run.")

if "missing_keywords" in st.session_state:
    with st.expander("⚠️ Missing Keywords (gaps vs JD)", expanded=False):
        missing = st.session_state.missing_keywords
        if missing:
            st.markdown("**Keywords in JD that could not be naturally embedded:**")
            st.markdown("  ".join([f"`{str(k)}`" for k in missing]))
        else:
            st.success("No major keyword gaps detected.")

# ============ DISPLAY & GENERATE PDF ============
if "generated_sections" in st.session_state:
    st.markdown("---")
    st.subheader("📄 Customized Resume Preview")
    
    sections_display = {
        "CAREER_OBJECTIVE": "Career Objective",
        "KEY_COURSES": "Selected Courses",
        "PROJECTS_SECTION": "Projects (Protected Links)",
        "EXPERIENCE_SECTION": "Professional Experience (Protected Title)",
        "SKILLS_SECTION": "Skills"
    }
    
    for section_key, section_title in sections_display.items():
        with st.expander(f"✏️ {section_title}"):
            st.markdown("**LaTeX Code:**")
            section_content = st.session_state.generated_sections.get(section_key, "")
            st.code(section_content, language="latex")
    
    st.markdown("---")
    
    # ============ PDF GENERATION ============
    if st.button("📥 Generate PDF Resume", key="generate_pdf", use_container_width=True):
        try:
            latex_content = LATEX_TEMPLATE
            
            for section_key, section_content in st.session_state.generated_sections.items():
                placeholder = f"{{{{{section_key}}}}}"
                # אנחנו לא עושים escape_latex פה כי זה כבר נעשה בפונקציות הבנייה
                latex_content = latex_content.replace(placeholder, section_content)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                tex_file = Path(tmpdir) / "resume.tex"
                pdf_file = Path(tmpdir) / "resume.pdf"
                
                with open(tex_file, "w", encoding="utf-8") as f:
                    f.write(latex_content)
                
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, str(tex_file)],
                    capture_output=True,
                    timeout=120
                )
                
                if result.returncode != 0:
                    st.error("❌ PDF compilation failed!")
                    st.error("Make sure pdflatex is installed and added to PATH.")
                    st.text_area("LaTeX Output:", value=result.stdout.decode('utf-8', errors='ignore'), height=200)
                else:
                    with open(pdf_file, "rb") as f:
                        pdf_data = f.read()
                    
                    st.success("✅ PDF generated successfully!")
                    st.download_button(
                        label="⬇️ Download Resume.pdf",
                        data=pdf_data,
                        file_name="Tair_Fridman_Resume.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
        except Exception as e:
            st.error(f"❌ Error generating PDF: {str(e)}")

st.markdown("---")
st.caption("🔐 Powered by Groq. Core structures are hardcoded to prevent AI hallucinations.")
