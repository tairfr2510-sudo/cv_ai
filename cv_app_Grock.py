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
    {\Huge \textbf{TAIR FRIDMAN}} \\
    \vspace{4pt}
    \textbf{Third Year Biomedical Engineering Student at the Technion} \\
    \vspace{4pt}
    054-9988143  $|$ tairfr2510@gmail.com $|$ { \href{http://www.linkedin.com/in/tairfridman}{\uline{Linkedin}}} $|$ \href{https://technionmail-my.sharepoint.com/:f:/g/personal/tair_fridman_campus_technion_ac_il/IgB6kjkw2NY_Q7lWN8LxAKPkAZNCp29HqfC-8IRGrvIwpbQ?e=Adc87l}{\uline{Project Portfolio}}
\end{center}

% Career Objective
\section{Career Objective}
\begin{flushleft}
{{CAREER_OBJECTIVE}}
\end{flushleft}

% Education
\section{Education}
\begin{flushleft}
\textbf{B.Sc. in Biomedical Engineering (In Progress)} \hfill 2023 -- Present \\
Technion - Israel Institute of Technology \hfill \textbf{GPA: 90}

\begin{itemize}[noitemsep, topsep=2pt]
    \item Dean's List (Academic Excellence): Winter 2024, Spring 2025, Winter 2026.
    \item Key Courses: {{KEY_COURSES}}
\end{itemize}
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
\textbf{Soldier in the special unit ``Dia''} --- \textbf{869th Combat Collection Battalion}
\begin{itemize}[noitemsep, topsep=2pt]
    \item Received excellence recognition in training and granted a parachute course as a prize.
    \item Selected for the commanders' training course, Trainees commander, commander in operational line.
    \item Team Sergeant (Operational Line): Led the team in the absence of the team leader, made critical decisions under pressure, and oversaw soldiers while managing the team logistics.
\end{itemize}
\end{flushleft}

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
- Responsibilities: Operated and optimized industrial 3D printers for food-tech meat-substitute production.
- Achievement 1: Initiated and built a SharePoint knowledge base for the printing team from scratch, centralizing documentation and improving cross-shift productivity.
- Achievement 2: Implemented Excel-based data tracking and analysis system to monitor print quality metrics and enhance work quality.
- Achievement 3: Collaborated directly with the R&D team on troubleshooting printer failures and co-developing improved printing protocols.
- Achievement 4: Managed full technical and operational processes including equipment calibration, fault diagnosis, and protocol development.

[ENGINEERING PROJECTS]
1. AI-Powered MRI/CT Diagnostic & 3D Reconstruction Platform (ID: MRAI):
   - Tech Stack: Python, PyTorch, fastai, nibabel, pydicom, scipy, scikit-image, numpy-stl, fpdf, Tkinter, matplotlib.
   - Data Pipeline: Built DICOM loader with spatial sorting via ImageOrientationPatient cross-product (slice normal vector); NIfTI loader via nibabel. Aspect-ratio correction using PixelSpacing + SliceThickness via scipy.ndimage.zoom.
   - AI Model: 3D U-Net (PyTorch/fastai) for automated brain tumor segmentation. Outputs: tumor confidence %, Z-slice range, peak slice index, 3D binary mask, centroid coordinates (x,y).
   - 3D Reconstruction: Gaussian filter (σ=1) → Marching Cubes (skimage.measure) with physical voxel spacing → STL export (numpy-stl). Tumor volume computed via get_mass_properties() in cm³.
   - MPR Viewer: Synchronized Axial/Coronal/Sagittal crosshairs with click-to-navigate between planes. Supports rotation, zoom, colormap switching (gray/hot/viridis/inferno).
   - DSP Module: FFT high-pass filter + Unsharp Masking (α=1.5) for edge enhancement.
   - PDF Report: Auto-generated clinical report via fpdf with AI findings + orthogonal slice screenshots.
   - Architecture: Non-blocking AI analysis via threading.Thread; GUI built with Tkinter + matplotlib TkAgg backend.

2. Autonomous X-Ray Targeting & Positioning System (ID: XRAY):
   - Tech Stack: Python, OpenCV, MediaPipe PoseLandmarker, Tkinter, threading, pynput, math.
   - State Machine: 4-state visual servoing: IDLE → MACRO_MOVE (error >100px, step=15px) → MICRO_CENTER (error ≤100px & >20px, step=3px) → READY (error ≤20px tolerance).
   - Computer Vision: MediaPipe PoseLandmarker (33 landmarks, visibility threshold >0.3) for real-time pose detection at 1280×720, 30fps.
   - NLP: Hebrew free-text input parsed to 13 anatomical targets (chest, head, abdomen, bilateral shoulder/elbow/wrist/hip/knee/ankle) via keyword mapping.
   - Dynamic Zoom: 4x zoom via crop-and-resize (not digital zoom), centered on detected target; crosshair locked at frame center.
   - Angle Calculation: atan2-based limb angle computation for X-ray tube rotation alignment.
   - Medical Protocols: Auto-detects clinical condition from text (fracture→AP+Lateral 0°+90°, sprain→Mortise 15-20°, fluid→Weight-bearing, foreign body→Tangential multi-angle).
   - Image Enhancement: CLAHE (clipLimit=3.0, tileGridSize=8×8) applied to final scan frame.
   - Output: Motor command string (direction + error px), tube tilt angle, rotation angle; X-ray simulation saved as JPG.
   - UX: Recording mode — state machine activates only on RECORD button press; STOP pauses at current position.

3. Mechanical Hand Design & Modeling (ID: MECH):
   - Tool: SolidWorks (CAD/CAM).
   - Design: Multi-articulated mechanical hand mechanism mimicking anatomical joint movements (finger joints, knuckles).
   - Engineering: Performed tolerance analysis to ensure fit and function across assembly components.
   - Output: Full assembly files (.SLDASM) designed for 3D printing manufacturing.

[SKILLS]
- Technical: Python, PyTorch, OpenCV, MediaPipe, fastai, nibabel, pydicom, SolidWorks, MATLAB, Excel, SharePoint.
- Soft Skills: Analytical Thinking, Quick Learner, Team Leadership, Problem Solving, Cross-functional Collaboration.
"""

# ============ STREAMLIT PAGE CONFIG ============
st.set_page_config(
    page_title="CV.AI — Resume Customizer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ DARK THEME CSS ============
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, .stApp {
    background: #070d1a !important;
    font-family: 'Inter', sans-serif !important;
    color: #c8d8f0 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0b1325 !important;
    border-right: 1px solid #1a2e50 !important;
}
[data-testid="stSidebar"] * { color: #8aa8d4 !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #00c8ff !important;
}

/* Headings */
h1 { color: #00c8ff !important; font-weight: 700 !important; letter-spacing: -0.5px !important; }
h2, h3 { color: #5ba3ff !important; font-weight: 600 !important; }

/* Text areas */
textarea {
    background-color: #0d1829 !important;
    color: #a8c7fa !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 10px !important;
    font-family: 'Inter', monospace !important;
    font-size: 13px !important;
}
textarea:focus {
    border: 1px solid #00c8ff !important;
    box-shadow: 0 0 0 2px rgba(0,200,255,0.15) !important;
}
textarea:disabled {
    background-color: #080f1c !important;
    color: #4a6080 !important;
    border-color: #112035 !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #0a2a6e 0%, #0057cc 100%) !important;
    color: #ffffff !important;
    border: 1px solid #1a6fff !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    letter-spacing: 0.3px !important;
    padding: 10px 20px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(0,80,200,0.3) !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #0f3a8a 0%, #0070ff 100%) !important;
    box-shadow: 0 4px 20px rgba(0,100,255,0.5) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0px) !important; }

/* Download button — green accent */
.stDownloadButton > button {
    background: linear-gradient(135deg, #0a4a2a 0%, #00a854 100%) !important;
    border: 1px solid #00cc66 !important;
    box-shadow: 0 4px 15px rgba(0,180,80,0.3) !important;
}
.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #0d5c34 0%, #00cc66 100%) !important;
    box-shadow: 0 4px 20px rgba(0,200,100,0.5) !important;
}

/* Expanders */
[data-testid="stExpander"] {
    background: #0b1628 !important;
    border: 1px solid #1a2e50 !important;
    border-radius: 12px !important;
    margin-bottom: 8px !important;
}
.streamlit-expanderHeader {
    color: #5ba3ff !important;
    font-weight: 600 !important;
}
.streamlit-expanderContent {
    background: #080f1e !important;
    border-top: 1px solid #1a2e50 !important;
}

/* Metrics (ATS scores) */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0b1628 0%, #0f1f3a 100%) !important;
    border: 1px solid #1a2e50 !important;
    border-radius: 14px !important;
    padding: 20px !important;
}
[data-testid="stMetricLabel"] { color: #7a9cc4 !important; font-size: 13px !important; }
[data-testid="stMetricValue"] { color: #00c8ff !important; font-size: 28px !important; font-weight: 700 !important; }
[data-testid="stMetricDelta"] { color: #00e676 !important; }

/* Info / success / error boxes */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border: none !important;
}
.stSuccess {
    background-color: #071e12 !important;
    border-left: 3px solid #00e676 !important;
    color: #00e676 !important;
}
.stInfo {
    background-color: #071525 !important;
    border-left: 3px solid #00c8ff !important;
    color: #7ec8ff !important;
}
.stError {
    background-color: #1e0707 !important;
    border-left: 3px solid #ff4d4d !important;
}

/* Code blocks */
code { background: #0d1829 !important; color: #7ec8ff !important; border-radius: 4px !important; }
pre { background: #0a1220 !important; border: 1px solid #1a2e50 !important; border-radius: 10px !important; }

/* Divider */
hr { border-color: #1a2e50 !important; }

/* Labels */
label { color: #7a9cc4 !important; font-size: 13px !important; font-weight: 500 !important; }

/* Column containers */
[data-testid="column"] {
    background: #0b1628 !important;
    border: 1px solid #1a2e50 !important;
    border-radius: 14px !important;
    padding: 20px !important;
}
</style>
""", unsafe_allow_html=True)

# ============ HEADER ============
st.markdown("""
<div style="text-align:center; padding: 24px 0 8px 0;">
    <h1 style="font-size:2.6rem; margin:0; background: linear-gradient(90deg,#00c8ff,#5ba3ff); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        ⚡ CV.AI
    </h1>
    <p style="color:#4a7aaa; font-size:15px; margin-top:6px; letter-spacing:1px;">
        ATS-OPTIMIZED RESUME CUSTOMIZER — POWERED BY GROQ / LLAMA 3.3
    </p>
</div>
""", unsafe_allow_html=True)
st.markdown("<hr style='margin:0 0 24px 0;'>", unsafe_allow_html=True)

# ============ SIDEBAR ============
with st.sidebar:
    st.markdown("""
    <div style="padding:10px 0;">
        <h2 style="color:#00c8ff !important; font-size:1.1rem; margin-bottom:16px;">⚡ HOW IT WORKS</h2>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    **1.** Paste the job description
    **2.** Click **Customize Resume**
    **3.** Download your tailored PDF

    ---
    **Protected (hardcoded):**
    - Military service section
    - Project titles & links
    - Job titles & dates

    ---
    *These are locked to prevent AI hallucinations and protect PDF formatting.*
    """)
    st.markdown("---")
    st.markdown("<p style='color:#2a4a70; font-size:11px;'>Model: Llama 3.3 70B via Groq</p>", unsafe_allow_html=True)

# ============ MAIN LAYOUT ============
col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    st.markdown("### 📋 Job Description")
    job_description = st.text_area(
        "Paste the full job posting here:",
        height=320,
        placeholder="Copy-paste the entire job description...\n\nThe AI will extract ATS keywords and tailor every section to this role.",
        key="jd_input",
        label_visibility="collapsed"
    )

with col2:
    st.markdown("### 🎓 Courses Pool")
    courses_input = st.text_area(
        "Courses the AI can select from (comma separated):",
        value="Introduction to Computing with Python (100), Biological Fluid Mechanics (100), Physics 1M (100), Differential and Integral Calculus 1M2 (99), Directions in Biomedical Engineering (97), Introduction to Human Anatomy (97), Partial Differential Equations/T (96), Physical Chemistry 1B (96), Fundamentals of Medical Materials (96), Metabolic Pathways (96), Physics 2 (95), From Cells to Tissues (94), Introduction to Probability H (93), General Chemistry (92), Laboratory in Bio-Medical Engineering 1 (92), Body Systems Physiology for Engineers (92), Signals and Systems (91)",
        height=320,
        key="courses_input",
        label_visibility="collapsed"
    )

st.markdown("<br>", unsafe_allow_html=True)

# ============ DEBUG BUTTON ============
with st.expander("🧪 Debug — Test PDF without AI tokens", expanded=False):
    if st.button("Load mock data & test PDF pipeline", use_container_width=True):
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
        st.success("✅ Mock data loaded — now click Generate PDF below.")

st.markdown("<hr>", unsafe_allow_html=True)

# ============ CUSTOMIZE BUTTON ============
if st.button("⚡  CUSTOMIZE RESUME", key="customize_btn", use_container_width=True):
    if not job_description.strip():
        st.error("Paste a job description first.")
    else:
        st.info("Analyzing JD and rewriting your resume with Llama 3.3 via Groq...")
        
        try:
            allowed_courses = [c.strip() for c in courses_input.split(",") if c.strip()]
            allowed_courses_text = ", ".join(allowed_courses)

            master_prompt = f"""
You are an expert resume writer and ATS optimization specialist.
Your goal is to reorganize and improve a resume to match a specific job description — WITHOUT inventing experience that does not exist.

=== INPUTS ===
Job Description (JD):
{job_description}

Candidate Fact Sheet (ground truth — do not invent beyond this):
{FACT_SHEET}

Allowed Courses Pool (select ONLY from this list):
{allowed_courses_text}

=== STEP-BY-STEP INSTRUCTIONS ===

STEP 1 — JD ANALYSIS:
Extract the top ATS keywords, required skills, and key responsibilities from the JD.
Identify which of these the candidate already has, and which are gaps.

STEP 2 — ATS SCORE BEFORE:
Score the candidate's raw resume against the JD on a 0-100 scale. Be honest and realistic.

STEP 3 — CAREER OBJECTIVE:
Write a 5-6 line career objective (max 80 words) that:
- Opens with the candidate's identity (Biomedical Engineering student, Technion)
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
Available projects: "MRAI", "XRAY", "MECH". Select EXACTLY 2 most relevant to the JD.

PROJECT-TO-DOMAIN MATCHING GUIDE (follow this strictly):
- JD mentions mechanical / machinery / manufacturing / CAD / SolidWorks / assembly / production / tolerance / machine design / mechatronics → MECH is your FIRST choice
- JD mentions AI / machine learning / deep learning / medical imaging / DICOM / segmentation / neural network / image processing → MRAI is your first choice
- JD mentions robotics / automation / computer vision / embedded / real-time / sensors / positioning / motion control → XRAY is your first choice
- When two domains overlap, pick the best two. NEVER default to MRAI+XRAY just because they seem more impressive — match the JD domain.

For each selected project write EXACTLY 3 bullets:
- Max 22 words per bullet
- Format: Strong Action Verb + specific technical detail (tool/algorithm/mechanism) + outcome
- Embed exact JD keywords naturally
- NEVER invent tools, metrics, or results not in the Fact Sheet

FEW-SHOT QUALITY STANDARD (imitate this level of specificity):

❌ WEAK: "Implemented a U-Net model for tumor detection."
✅ STRONG: "Engineered a 3D U-Net (PyTorch/fastai) for automated brain tumor segmentation, outputting confidence score, Z-slice range, and 3D binary mask."

❌ WEAK: "Built a system for X-ray targeting using computer vision."
✅ STRONG: "Designed a 4-state visual servoing pipeline (IDLE→MACRO→MICRO→READY) using MediaPipe and OpenCV, achieving ±20px anatomical centering precision."

❌ WEAK: "Designed a mechanical hand in SolidWorks."
✅ STRONG: "Modeled a multi-articulated mechanical hand in SolidWorks, mimicking anatomical joint kinematics, with full tolerance analysis and assembly files for 3D printing."

STEP 6 — EXPERIENCE BULLETS (Redefinemeat, EXACTLY 2 bullets, max 20 words each):
Reframe the 3D Printer Operator role to match this JD's domain.
Use the 4 achievement facts in the Fact Sheet. Same quality standard: specific, action-oriented, no hallucination.

STEP 7 — SKILLS:
Group into exactly 2 categories:
- "Technical": list only tools/technologies confirmed by the projects and experience in the Fact Sheet. Add relevant JD keywords only if they map to real skills.
- "Soft Skills": pick the most relevant traits from both the JD and the Fact Sheet.

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
    "CAREER_OBJECTIVE": "Plain text, 5-6 lines.",
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

            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a senior resume strategist and ATS expert specializing in engineering and medical technology roles. "
                            "You write precise, impactful resume bullets grounded strictly in provided facts. "
                            "You always return valid JSON with no LaTeX, no Markdown code blocks, and no invented data. "
                            "Your bullet quality is specific, technical, and results-oriented."
                        )
                    },
                    {
                        "role": "user",
                        "content": master_prompt,
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.15,
                response_format={"type": "json_object"}
            )
            
            raw_text = chat_completion.choices[0].message.content
            
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
            else:
                data = json.loads(raw_text)
            
            # ── One-page content trimmer ──────────────────────────────
            def trim_words(text, max_words):
                words = text.split()
                return " ".join(words[:max_words]) + ("..." if len(words) > max_words else "")

            def trim_bullets(bullets, max_bullets, max_words_each):
                return [trim_words(b, max_words_each) for b in bullets[:max_bullets]]

            raw_projects = data.get("SELECTED_PROJECTS", [])
            for proj in raw_projects:
                proj["bullets"] = trim_bullets(proj.get("bullets", []), 3, 22)

            raw_exp = trim_bullets(data.get("EXPERIENCE_BULLETS", []), 2, 20)
            raw_objective = trim_words(data.get("CAREER_OBJECTIVE", ""), 75)
            # ─────────────────────────────────────────────────────────

            validated_courses = select_valid_courses(data.get("KEY_COURSES", ""), allowed_courses, max_courses=3)
            st.session_state.analysis = data.get("ANALYSIS_TEXT", "לא נוצר ניתוח.")
            st.session_state.keywords_used = data.get("JD_KEYWORDS_USED", [])
            st.session_state.missing_keywords = data.get("MISSING_KEYWORDS", [])
            st.session_state.ats_before = data.get("ATS_SCORE_BEFORE", "N/A")
            st.session_state.ats_after = data.get("ATS_SCORE_AFTER", "N/A")
            st.session_state.generated_sections = {
                "CAREER_OBJECTIVE": escape_latex(raw_objective),
                "KEY_COURSES": escape_latex(validated_courses),
                "PROJECTS_SECTION": build_projects_latex(raw_projects),
                "EXPERIENCE_SECTION": build_experience_latex(raw_exp),
                "SKILLS_SECTION": build_skills_latex(data.get("SKILLS", {}))
            }

            st.success("✅ הניתוח והשכתוב הושלמו בהצלחה ובמהירות האור!")
            
        except Exception as e:
            st.error(f"❌ שגיאת API/קוד: {str(e)}")

# ============ DISPLAY ANALYSIS ============
if "analysis" in st.session_state:
    st.markdown("<hr>", unsafe_allow_html=True)

    # ATS Score Banner
    if "ats_before" in st.session_state and "ats_after" in st.session_state:
        ats_before = st.session_state.ats_before
        ats_after = st.session_state.ats_after
        st.markdown("### 📊 ATS Score")
        col_a, col_b = st.columns(2)
        col_a.metric("Before Customization", f"{ats_before} / 100")
        col_b.metric("After Customization", f"{ats_after} / 100",
                     delta=f"+{ats_after - ats_before}" if isinstance(ats_after, int) and isinstance(ats_before, int) else None)
        st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("🧠 Full ATS Analysis & Match Report", expanded=True):
        st.markdown(st.session_state.analysis)

    kw_col, gap_col = st.columns(2)
    with kw_col:
        with st.expander("✅ Keywords embedded", expanded=False):
            keywords = st.session_state.get("keywords_used", [])
            if keywords:
                st.markdown("  ".join([f"`{k}`" for k in keywords]))
            else:
                st.caption("None reported.")
    with gap_col:
        with st.expander("⚠️ Keyword gaps", expanded=False):
            missing = st.session_state.get("missing_keywords", [])
            if missing:
                st.markdown("  ".join([f"`{k}`" for k in missing]))
            else:
                st.success("No major gaps.")

# ============ RESUME PREVIEW + PDF ============
if "generated_sections" in st.session_state:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 📄 Resume Preview")

    sections_display = {
        "CAREER_OBJECTIVE": "Career Objective",
        "KEY_COURSES": "Selected Courses",
        "PROJECTS_SECTION": "Projects (links locked)",
        "EXPERIENCE_SECTION": "Professional Experience (title locked)",
        "SKILLS_SECTION": "Skills"
    }
    for section_key, section_title in sections_display.items():
        with st.expander(f"✏️ {section_title}", expanded=False):
            st.code(st.session_state.generated_sections.get(section_key, ""), language="latex")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("📥  GENERATE PDF", key="generate_pdf", use_container_width=True):
        with st.spinner("Compiling LaTeX..."):
            try:
                latex_content = LATEX_TEMPLATE
                for section_key, section_content in st.session_state.generated_sections.items():
                    latex_content = latex_content.replace(f"{{{{{section_key}}}}}", section_content)

                with tempfile.TemporaryDirectory() as tmpdir:
                    tex_file = Path(tmpdir) / "resume.tex"
                    pdf_file = Path(tmpdir) / "resume.pdf"
                    with open(tex_file, "w", encoding="utf-8") as f:
                        f.write(latex_content)
                    result = subprocess.run(
                        ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, str(tex_file)],
                        capture_output=True, timeout=120
                    )
                    if result.returncode != 0:
                        st.error("PDF compilation failed — pdflatex error below.")
                        st.text_area("LaTeX log:", value=result.stdout.decode("utf-8", errors="ignore"), height=200)
                    else:
                        with open(pdf_file, "rb") as f:
                            pdf_data = f.read()
                        st.success("PDF compiled successfully!")
                        st.download_button(
                            label="⬇️  Download Resume PDF",
                            data=pdf_data,
                            file_name="Tair_Fridman_Resume.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; color:#1e3a5f; font-size:12px;'>"
    "⚡ CV.AI — Powered by Groq / Llama 3.3 · Core sections are hardcoded to prevent hallucinations"
    "</p>", unsafe_allow_html=True
)
