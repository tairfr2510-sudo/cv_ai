import streamlit as st
import json
import re
import os
from groq import Groq
from dotenv import load_dotenv

# טעינת משתני סביבה (למשל מפתח ה-API של Groq)
load_dotenv()

# הגדרת הלקוח של Groq
# ודא שיש לך קובץ .env עם GROQ_API_KEY=your_key_here
try:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
except Exception as e:
    client = None

# ==========================================
# 1. מידע קורות החיים הקשיח (Fact Sheet)
# ==========================================
FACT_SHEET = """
Name: Tair Fridman
Role: Third Year Biomedical Engineering Student at the Technion
Contact: 054-9988143 | tairfr2510@gmail.com
Education: B.Sc. in Biomedical Engineering (In Progress), Technion - Israel Institute of Technology. GPA: 90. Dean's List (Winter 2024, Spring 2025, Winter 2026). Key Courses: Python Programming, Biological Fluid Mechanics, Signals and Systems.

PROJECTS:
1. AI-Powered MRI/CT Diagnostic & 3D Reconstruction Platform (MRAI Engine): Developed an end-to-end pipeline for processing volumetric DICOM/NIFTI imaging data. Generated 3D anatomical models using Marching Cubes and exported STL. Implemented a U-Net deep learning model for automated tumor segmentation. Built a multi-planar reconstruction (MPR) tool for slice-by-slice manual inspection.
2. Autonomous X-ray Targeting & Positioning System: Designed a system integrating Computer Vision and NLP to automate X-ray arm alignment. Utilized OpenCV and MediaPipe for real-time pose detection and micro-centering. Developed a Python-based state machine for motion control and Tkinter GUI.
3. Bionic Arm / Prosthetics Planner: Worked on bionic arm development utilizing 3D printing and AI integration. 

EXPERIENCE:
3D Printer Operator (Meat-Replacement Printing) at Redefinemeat, Rehovot (06/2022-07/2023): Operated and optimized 3D printers for meat substitutes. Initiated and built a SharePoint site for the team, implementing Excel data tracking to enhance productivity. Collaborated with R&D on troubleshooting and protocol development.

MILITARY:
Soldier in special unit "Dia", 869th Combat Collection Battalion. Team Sergeant (Operational Line), led the team, made critical decisions under pressure, oversaw soldiers and logistics. Selected for commanders' training course.

SKILLS:
Technical: Python, PyTorch, OpenCV, MediaPipe, SolidWorks, MATLAB, SharePoint, Excel.
Soft Skills: Analytical Thinking, Quick Learner, Team Leadership, Problem Solving under pressure.
"""

# ==========================================
# 2. פונקציות עזר לבניית LaTeX
# ==========================================
def escape_latex(text):
    """מנקה תווים שיכולים לשבור את הקימפול של ה-PDF"""
    if not text:
        return ""
    chars = {
        '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
        '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}', '\\': r'\textbackslash{}'
    }
    return "".join(chars.get(c, c) for c in str(text))

def build_projects_latex(dynamic_projects):
    """
    מקבל מערך של פרויקטים ובונה את ה-LaTeX.
    מזהה אוטומטית איזה פרויקט נבחר ומצמיד לו את הקישור הנכון.
    """
    if not dynamic_projects:
        return ""
        
    latex = ""
    PROJECTS_DB = {
        "mrai": {
            "keywords": ["mrai", "mri", "ct", "diagnostic", "reconstruction"],
            "title": r"\textbf{AI-Powered MRI/CT Diagnostic \& 3D Reconstruction Platform}",
            "link": r"\hfill \href{https://github.com/tairfr2510-sudo/MRAI-Tumor-Segmentation-3D-Export-Engine}{\uline{GitHub}}"
        },
        "xray": {
            "keywords": ["x-ray", "xray", "autonomous", "targeting", "positioning"],
            "title": r"\textbf{Autonomous X-ray Targeting \& Positioning System}",
            "link": r"\hfill \href{https://aistudio.google.com/apps/e4bd7e56-afa3-41d2-984a-88577243b839?fullscreenApplet=true&showPreview=true&showAssistant=true}{\uline{Demo}}"
        },
        "bionic": {
            "keywords": ["bionic", "arm", "prosthetic", "hand"],
            "title": r"\textbf{Bionic Arm Development Project}",
            "link": r"\hfill \href{#}{\uline{Project}}" 
        }
    }

    for project in dynamic_projects:
        model_project_name = project.get("Project_Name", "").lower()
        bullets = project.get("Bullets", [])
        
        if not bullets:
            continue
            
        matched_project = None
        for key, db_data in PROJECTS_DB.items():
            if any(kw in model_project_name for kw in db_data["keywords"]):
                matched_project = db_data
                break
        
        if matched_project:
            latex += matched_project["title"] + " " + matched_project["link"] + "\n"
        else:
            fallback_title = escape_latex(project.get("Project_Name", "Unknown Project"))
            latex += rf"\textbf{{{fallback_title}}}" + "\n"
            
        latex += r"\begin{itemize}[noitemsep, topsep=2pt]" + "\n"
        for bullet in bullets:
            latex += f"    \\item {escape_latex(bullet)}\n"
        latex += r"\end{itemize}" + "\n\n"
        
    return latex

# ==========================================
# 3. הפקת קורות החיים המלאים ב-LaTeX
# ==========================================
def generate_full_latex(parsed_data, projects_latex):
    """מרכיב את קובץ ה-LaTeX השלם"""
    objective = escape_latex(parsed_data.get("CAREER_OBJECTIVE", ""))
    courses = escape_latex(parsed_data.get("KEY_COURSES", ""))
    
    # חילוץ ניסיון תעסוקתי
    exp_bullets_latex = ""
    for bullet in parsed_data.get("EXPERIENCE_BULLETS", []):
        exp_bullets_latex += f"    \\item {escape_latex(bullet)}\n"
        
    # חילוץ כישורים
    skills_data = parsed_data.get("SKILLS", {})
    tech_skills = escape_latex(skills_data.get("Technical", ""))
    soft_skills = escape_latex(skills_data.get("Soft Skills", ""))

    latex_document = f"""\\documentclass[11pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{geometry}}
\\geometry{{left=1in, right=1in, top=1in, bottom=1in}}
\\usepackage{{hyperref}}
\\usepackage{{enumitem}}
\\usepackage[normalem]{{ulem}}

\\begin{{document}}
\\pagestyle{{empty}}

\\begin{{center}}
\\textbf{{\\Huge TAIR FRIDMAN}} \\\\
\\vspace{{0.2cm}}
Third Year Biomedical Engineering Student at the Technion \\\\
054-9988143 | \\href{{mailto:tairfr2510@gmail.com}}{{tairfr2510@gmail.com}} | \\href{{#}}{{Linkedin}} | \\href{{#}}{{Project Portfolio}}
\\end{{center}}

\\vspace{{0.2cm}}
\\noindent \\textbf{{\\large CAREER OBJECTIVE}} \\\\
\\rule{{\\textwidth}}{{0.4pt}}
{objective}

\\vspace{{0.4cm}}
\\noindent \\textbf{{\\large EDUCATION}} \\\\
\\rule{{\\textwidth}}{{0.4pt}}
\\textbf{{B.Sc. in Biomedical Engineering (In Progress)}} \\hfill 2023 - Present \\\\
Technion - Israel Institute of Technology \\hfill GPA: 90
\\begin{{itemize}}[noitemsep, topsep=2pt]
    \\item Dean's List (Academic Excellence): Winter 2024, Spring 2025, Winter 2026.
    \\item Key Courses: {courses}
\\end{{itemize}}

\\vspace{{0.4cm}}
\\noindent \\textbf{{\\large PROJECTS}} \\\\
\\rule{{\\textwidth}}{{0.4pt}}
{projects_latex}
\\vspace{{0.2cm}}
\\noindent \\textbf{{\\large PROFESSIONAL EXPERIENCE}} \\\\
\\rule{{\\textwidth}}{{0.4pt}}
\\textbf{{3D Printer Operator}} \\hfill 06/2022 - 07/2023 \\\\
Redefinemeat, Rehovot
\\begin{{itemize}}[noitemsep, topsep=2pt]
{exp_bullets_latex}
\\end{{itemize}}

\\vspace{{0.4cm}}
\\noindent \\textbf{{\\large MILITARY SERVICE}} \\\\
\\rule{{\\textwidth}}{{0.4pt}}
\\textbf{{Soldier in special unit "Dia" / Team Sergeant}} \\hfill 869th Combat Collection Battalion
\\begin{{itemize}}[noitemsep, topsep=2pt]
    \\item Received excellence recognition in training and granted a parachute course as a prize.
    \\item Led the team in the absence of the team leader, making critical decisions under pressure.
\\end{{itemize}}

\\vspace{{0.4cm}}
\\noindent \\textbf{{\\large SKILLS}} \\\\
\\rule{{\\textwidth}}{{0.4pt}}
\\begin{{itemize}}[noitemsep, topsep=2pt]
    \\item \\textbf{{Technical:}} {tech_skills}
    \\item \\textbf{{Soft Skills:}} {soft_skills}
\\end{{itemize}}

\\end{{document}}
"""
    return latex_document

# ==========================================
# 4. אפליקציית Streamlit (UI והרצת המודל)
# ==========================================
def main():
    st.title("CV ATS Optimizer 🚀")
    
    if not client:
        st.error("Groq API key is missing. Please check your .env file.")
        return

    job_desc = st.text_area("Paste Job Description Here:", height=200)

    if st.button("Optimize My CV"):
        if not job_desc.strip():
            st.warning("Please paste a job description first.")
            return

        with st.spinner("Analyzing and Optimizing..."):
            prompt = f"""
Act as a Senior Israeli Headhunter and ATS Expert.
Your task is to tailor the candidate's content to perfectly match the provided Job Description (JD) while strictly adhering to a 1-page CV limit (maximum 400 words total).

INPUTS:
- Job Description (JD): {job_desc}
- Candidate Fact Sheet: {FACT_SHEET}

INSTRUCTIONS:
1. ATS ANALYSIS: Evaluate the match. Calculate an ATS score (0-100) and explicitly list missing keywords.
2. CAREER OBJECTIVE: Write a sharp 3-4 line objective tailored to the JD. Do NOT hallucinate.
3. KEY COURSES: Select EXACTLY 2 or 3 most relevant courses from the Fact Sheet.
4. PROJECTS (DYNAMIC SELECTION):
   - Review all projects listed in the Candidate Fact Sheet.
   - Select EXACTLY 2 projects that are MOST RELEVANT to the provided Job Description. You MUST NOT leave this section empty.
   - For EACH of the 2 selected projects, write exactly 3-4 highly concise bullet points.
   - CRITICAL RULE: EVERY bullet MUST follow the 'Action + Impact + Result' formula.
   - CRITICAL RULE: Embed EXACT keywords from the JD naturally. Do NOT invent metrics, skills, or fake experience.
5. EXPERIENCE: Write exactly 3-4 highly concise bullet points for the 3D Printer Operator role.
6. SKILLS: Select and group the most relevant skills into exactly 2 categories (e.g., "Technical", "Soft Skills").
7. SUMMARY_OF_CHANGES: Provide 2-3 brief bullets explaining the main modifications.

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
            try:
                # קריאה ל-Groq
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama3-70b-8192", # או כל מודל אחר של Groq שאתה מעדיף
                    temperature=0.2,
                )
                
                response_text = chat_completion.choices[0].message.content
                
                # ניקוי ופיענוח ה-JSON
                json_string = re.sub(r'```json\n|\n```', '', response_text).strip()
                parsed_data = json.loads(json_string)
                
                # תצוגה למשתמש
                st.success("Optimization Complete!")
                st.write(f"**ATS Score:** {parsed_data.get('ATS_ANALYSIS', {}).get('Score', 'N/A')}/100")
                
                st.subheader("Summary of Changes")
                for change in parsed_data.get("SUMMARY_OF_CHANGES", []):
                    st.write(f"- {change}")

                # הרכבת ה-LaTeX
                projects_latex_code = build_projects_latex(parsed_data.get("PROJECTS", []))
                final_latex = generate_full_latex(parsed_data, projects_latex_code)
                
                st.subheader("Generated LaTeX Code")
                st.code(final_latex, language="latex")
                
                st.download_button(
                    label="Download .tex file",
                    data=final_latex,
                    file_name="Optimized_CV.tex",
                    mime="text/plain"
                )

            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.write("Raw response from model (for debugging):", response_text)

if __name__ == "__main__":
    main()
