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

# ============ LATEX UTILS ============
def escape_latex(text):
    """הופך תווים מיוחדים של LaTeX לטקסט בטוח בלי לשבור פקודות"""
    if not isinstance(text, str):
        return text
    
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
    }
    
    for char, replacement in replacements.items():
        if f'\\{char}' not in text: 
            text = text.replace(char, replacement)
    
    return text

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
    \item Key Courses: Python programming (100), "Signals and Systems" (91).
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

% Army Service
\section{Military Service}
{{MILITARY_SERVICE}}

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
- Key Coursework & Grades: Python Programming (100), Biological Fluid Mechanics (100), Signals and Systems (91).

[PROFESSIONAL EXPERIENCE]
- Role: 3D Printer Operator for Meat-Replacement Products
- Company: Redefine Meat (06/2022 - 07/2023)
- Details: Operated and optimized 3D printers specifically for meat substitutes (not medical bioprinting). 
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

3. Bionic Hand Design:
   - Tech Stack: SolidWorks.
   - Details: Mechanical design and modeling of a tendon-driven "Pull Block" mechanism. Conducted stress analysis (FEA) and buckling simulations.

[MILITARY SERVICE]
- Role: Team Sergeant, Special Unit "DIA" (869th Combat Collection Battalion).
- Details: Led the team in operational lines, managed logistics, and made critical decisions under pressure. 
- Honors: Received excellence recognition in training and granted a parachute course as a prize. Trainees commander.

[SKILLS]
- Programming & AI: Python, PyTorch, OpenCV, MediaPipe, NLP.
- Engineering Tools: SolidWorks (FEA, Buckling), MATLAB.
- General Tech & Soft Skills: Excel, SharePoint, Analytical Thinking, Quick Learner, Team Leadership.
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
    
    ⚠️ **Note:** Your personal data is hardcoded to prevent AI hallucinations.
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
        height=300,
        disabled=True,
        key="fact_sheet"
    )

st.markdown("---")

# ============ כפתור בדיקה ללא טוקנים ============
st.subheader("🧪 Debugging Area")
if st.button("בדיקת PDF עם נתוני דמי (חוסך זמן)", use_container_width=True):
    mock_data = {
        "CAREER_OBJECTIVE": "Test objective for PDF generation.",
        "PROJECTS_SECTION": r"\textbf{Test Project} \hfill \href{https://google.com}{\uline{Link}} \begin{itemize}[noitemsep, topsep=2pt] \item Item 1 \item Item 2 \end{itemize}",
        "EXPERIENCE_SECTION": r"\textbf{Test Exp} \hfill 2024 \newline Company \begin{itemize}[noitemsep, topsep=2pt] \item Exp 1 \end{itemize}",
        "MILITARY_SERVICE": r"Test military service description.",
        "SKILLS_SECTION": r"\begin{itemize}[noitemsep, topsep=2pt] \item \textbf{Tech:} Python, LaTeX \end{itemize}"
    }
    st.session_state.generated_sections = mock_data
    st.success("✅ נתוני דמי נטענו! עכשיו אפשר ללחוץ על 'Generate PDF Resume' למטה.")

st.markdown("---")

# ============ CUSTOMIZE BUTTON ============
if st.button("🚀 Customize Resume", key="customize_btn", use_container_width=True):
    if not job_description.strip():
        st.error("❌ אנא הכנס תיאור משרה קודם!")
    else:
        st.info("⏳ מנוע Llama 3 (Groq) מנתח את המשרה ומשכתב את קורות החיים...")
        
        try:
            master_prompt = f"""
            Act as a Senior Israeli Headhunter and ATS Expert. 
            Your goal is to execute a full CV Optimization Pipeline: analyze a Job Description (JD), analyze the candidate's Fact Sheet, and output a highly targeted, ATS-optimized resume.

            INPUTS:
            - Job Description (JD): {job_description}
            - Candidate Fact Sheet: {FACT_SHEET}

            PIPELINE INSTRUCTIONS:
            1. JD Breakdown & Match Analysis: 
               Identify must-have requirements, critical skills, and exact keywords from the JD. Evaluate the candidate's match (Strengths, Gaps).
            
            2. Targeted Rewrite (The core task): 
               Rewrite the candidate's Experience and Projects to perfectly align with the JD.
               - Use 3-5 bullet points per role/project.
               - RULE: EVERY bullet MUST follow the 'Action + Impact + Result' formula.
               - RULE: Naturally embed EXACT keywords from the JD into the bullet points.
               - RULE: DO NOT invent or hallucinate metrics, experience, or numbers. Stay 100% truthful to the Fact Sheet.
            
            3. Headline & Summary: 
               Create a sharp, tailored headline and a 3-4 line summary highlighting the candidate's professional identity, relevant experience, and unique differentiation for this specific role.
            
            4. Skills Optimization: 
               Filter and prioritize ONLY the skills from the Fact Sheet that are highly relevant to the JD.

            OUTPUT FORMAT:
            You MUST return ONLY a valid JSON object. Do not wrap it in markdown block quotes (no ```json).
            The JSON MUST contain these EXACT keys. The values for all keys (except ANALYSIS_TEXT) must be written in strict LaTeX code.

            - "ANALYSIS_TEXT": A detailed Markdown string containing: JD Breakdown, CV Score (0-100), Match Score (0-100), Quick Verdict, Strengths, Gaps, and areas for immediate improvement.
            - "CAREER_OBJECTIVE": The tailored Headline and Summary. (Use LaTeX formatting).
            - "PROJECTS_SECTION": The tailored projects. MUST use \\begin{{itemize}} ... \\item [Action + Impact + Result] ... \\end{{itemize}}.
            - "EXPERIENCE_SECTION": The tailored experience. MUST use \\begin{{itemize}} ... \\item [Action + Impact + Result] ... \\end{{itemize}}.
            - "MILITARY_SERVICE": Tailored military service emphasizing relevant soft/hard skills. MUST use \\begin{{itemize}} ... \\item ... \\end{{itemize}}.
            - "SKILLS_SECTION": Relevant skills grouped logically. MUST use \\begin{{itemize}} ... \\item \\textbf{{Category:}} Skills ... \\end{{itemize}}.

            LATEX RULES FOR SECTIONS:
            - Use \\textbf{{}} for bold text.
            - Ensure all special characters like &, $, %, or _ are escaped (e.g., \\&).
            - Keep a linear, clean structure suitable for ATS parsers (No tables, no graphics).
            """

            # קריאה לשרתי Groq תוך כפיית JSON
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": master_prompt,
                    }
                ],
                model="llama-3.3-70b-versatile", # מודל חזק ומהיר מאוד
                temperature=0.2, # שומר על התשובה מדויקת ולא יצירתית מדי
                response_format={"type": "json_object"} # מונע קריסות - השרת חייב להחזיר JSON
            )
            
            raw_text = chat_completion.choices[0].message.content
            
            # וידוא גיבוי למקרה שיש טקסט מסביב ל-JSON
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
            else:
                data = json.loads(raw_text)
            
            # אחסון התוצאות
            st.session_state.analysis = data.get("ANALYSIS_TEXT", "לא נוצר ניתוח.")
            st.session_state.generated_sections = {
                "CAREER_OBJECTIVE": data.get("CAREER_OBJECTIVE", ""),
                "PROJECTS_SECTION": data.get("PROJECTS_SECTION", ""),
                "EXPERIENCE_SECTION": data.get("EXPERIENCE_SECTION", ""),
                "MILITARY_SERVICE": data.get("MILITARY_SERVICE", ""),
                "SKILLS_SECTION": data.get("SKILLS_SECTION", "")
            }
            
            st.success("✅ הניתוח והשכתוב הושלמו בהצלחה ובמהירות האור!")
            
        except Exception as e:
            st.error(f"❌ שגיאת API/קוד: {str(e)}")

# ============ DISPLAY ANALYSIS ============
if "analysis" in st.session_state:
    st.markdown("---")
    with st.expander("🧐 Professional Analysis & Match Score", expanded=True):
        st.markdown(st.session_state.analysis)

# ============ DISPLAY & GENERATE PDF ============
if "generated_sections" in st.session_state:
    st.markdown("---")
    st.subheader("📄 Customized Resume Preview")
    
    sections_display = {
        "CAREER_OBJECTIVE": "Career Objective",
        "PROJECTS_SECTION": "Projects",
        "EXPERIENCE_SECTION": "Professional Experience",
        "MILITARY_SERVICE": "Military Service",
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
                clean_content = escape_latex(section_content)
                latex_content = latex_content.replace(placeholder, clean_content)
            
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
st.caption("🔐 Powered by Groq. Your personal data is hardcoded to prevent AI hallucinations.")