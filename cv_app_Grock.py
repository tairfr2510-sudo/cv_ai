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

def build_projects_latex(mrai_bullets, xray_bullets):
    """בונה את קוד ה-LaTeX לפרויקטים, שומר על הקישורים והכותרות קשיחים"""
    latex = ""
    if mrai_bullets:
        latex += r"\textbf{AI-Powered MRI/CT Diagnostic \& 3D Reconstruction Platform} \hfill \href{https://github.com/tairfr2510-sudo/MRAI-Tumor-Segmentation-3D-Export-Engine}{\uline{GitHub}}" + "\n"
        latex += r"\begin{itemize}[noitemsep, topsep=2pt]" + "\n"
        for bullet in mrai_bullets:
            latex += f"    \\item {escape_latex(bullet)}\n"
        latex += r"\end{itemize}" + "\n\n"
    
    if xray_bullets:
        latex += r"\textbf{Autonomous X-ray Targeting \& Positioning System} \hfill \href{https://aistudio.google.com/apps/e4bd7e56-afa3-41d2-984a-88577243b839?fullscreenApplet=true&showPreview=true&showAssistant=true}{\uline{Demo}}" + "\n"
        latex += r"\begin{itemize}[noitemsep, topsep=2pt]" + "\n"
        for bullet in xray_bullets:
            latex += f"    \\item {escape_latex(bullet)}\n"
        latex += r"\end{itemize}" + "\n"
        
    return latex

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
        "KEY_COURSES": "Python programming (100), Signals and Systems (91)",
        "PROJECTS_SECTION": build_projects_latex(["Mock MRAI Bullet 1", "Mock MRAI Bullet 2"], ["Mock XRAY Bullet 1"]),
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
            master_prompt = f"""
            Act as a Senior Israeli Headhunter and ATS Expert.
            Your task is to tailor the candidate's content to perfectly match the provided Job Description (JD) while strictly adhering to a 1-page CV limit (maximum 400 words total).
            
            INPUTS:
            - Job Description (JD): {job_description}
            - Candidate Fact Sheet: {FACT_SHEET}
            
            INSTRUCTIONS:
            1. ATS ANALYSIS: Evaluate the match between the candidate and the JD. Calculate an ATS score (0-100) and explicitly list missing keywords.
            2. CAREER OBJECTIVE: Write a sharp 3-4 line objective tailored to the JD. Do NOT hallucinate.
            3. KEY COURSES: Select EXACTLY 2 or 3 most relevant courses from the Fact Sheet.
            4. PROJECTS (DYNAMIC SELECTION):
               - Review all projects listed in the Candidate Fact Sheet.
               - Select EXACTLY 2 projects that are MOST RELEVANT to the provided Job Description.
               - For EACH of the 2 selected projects, write exactly 3-4 highly concise bullet points.
               - CRITICAL RULE: EVERY bullet MUST follow the 'Action + Impact + Result' formula.
               - CRITICAL RULE: Embed EXACT keywords from the JD naturally. Do NOT invent metrics, skills, or fake experience. Keep sentences short.
            5. EXPERIENCE: Write exactly 3-4 highly concise bullet points for the 3D Printer Operator role.
            6. SKILLS: Select and group the most relevant skills into exactly 2 categories (e.g., "Technical", "Soft Skills").
            7. SUMMARY_OF_CHANGES: Provide 2-3 brief bullets explaining the main modifications made to improve ATS compatibility.
            
            OUTPUT FORMAT (JSON ONLY):
            Return ONLY a raw JSON object. Do not use Markdown formatting (no ```json). 
            Do NOT include any LaTeX commands. Return pure plain text inside the JSON values.
            
            {{
                "ATS_ANALYSIS": {{
                    "Score": 85,
                    "Explanation": "Short sentence explaining the score.",
                    "Missing_Keywords": ["Keyword1", "Keyword2"]
                }},
                "CAREER_OBJECTIVE": "Plain text summary.",
                "KEY_COURSES": "Plain text courses string.",
                "PROJECTS": [
                    {{
                        "Project_Name": "Name of the first selected project",
                        "Bullets": ["Bullet 1", "Bullet 2", "Bullet 3"]
                    }},
                    {{
                        "Project_Name": "Name of the second selected project",
                        "Bullets": ["Bullet 1", "Bullet 2", "Bullet 3"]
                    }}
                ],
                "EXPERIENCE_BULLETS": ["Bullet 1", "Bullet 2", "Bullet 3"],
                "SKILLS": {{
                    "Technical": "Python, SolidWorks...",
                    "Soft Skills": "Analytical Thinking..."
                }},
                "SUMMARY_OF_CHANGES": ["Change 1", "Change 2"]
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
            
            # הרכבה בטוחה של ה-LaTeX (הסוף לקריסות!)
            st.session_state.analysis = data.get("ANALYSIS_TEXT", "לא נוצר ניתוח.")
            st.session_state.generated_sections = {
                "CAREER_OBJECTIVE": escape_latex(data.get("CAREER_OBJECTIVE", "")),
                "KEY_COURSES": escape_latex(data.get("KEY_COURSES", "")),
                "PROJECTS_SECTION": build_projects_latex(data.get("MRAI_BULLETS", []), data.get("XRAY_BULLETS", [])),
                "EXPERIENCE_SECTION": build_experience_latex(data.get("EXPERIENCE_BULLETS", [])),
                "SKILLS_SECTION": build_skills_latex(data.get("SKILLS", {}))
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
