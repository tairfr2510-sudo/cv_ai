import streamlit as st
import os
from dotenv import load_dotenv

from cv_engine import CVEngine, PDFCompileError

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

# כל הלוגיקה (פרומפט, LaTeX, PDF) נמצאת ב-cv_engine.py, וכל המידע ב-profile.yaml
engine = CVEngine(api_key=API_KEY)

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
        value=", ".join(engine.courses),
        height=320,
        key="courses_input",
        label_visibility="collapsed"
    )

st.markdown("<br>", unsafe_allow_html=True)

# ============ DEBUG BUTTON ============
with st.expander("🧪 Debug — Test PDF without AI tokens", expanded=False):
    if st.button("Load mock data & test PDF pipeline", use_container_width=True):
        mock_data = engine.mock_sections()
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
            result = engine.generate(job_description, allowed_courses)

            st.session_state.analysis = result["analysis"]
            st.session_state.keywords_used = result["keywords_used"]
            st.session_state.missing_keywords = result["missing_keywords"]
            st.session_state.ats_before = result["ats_before"]
            st.session_state.ats_after = result["ats_after"]
            st.session_state.generated_sections = result["sections"]

            for w in result["warnings"]:
                st.warning(f"⚠️ מספר שלא מופיע בפרופיל ({', '.join(w['numbers'])}) — לבדוק: {w['text']}")

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

# === הוספת קוד ה-LaTeX המלא להעתקה ===
if "generated_sections" in st.session_state:
    latex_content_full = engine.render_latex(st.session_state.generated_sections)
    with st.expander("📋 קוד LaTeX מלא להעתקה (לחץ על כפתור ההעתקה בצד ימין)", expanded=True):
        st.code(latex_content_full, language="latex")
# ======================================

st.markdown("<br>", unsafe_allow_html=True)

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
                latex_content = engine.render_latex(st.session_state.generated_sections)
                pdf_data, pages = engine.compile_pdf(latex_content)
                st.success("PDF compiled successfully!")
                if pages and pages > 1:
                    st.warning(f"⚠️ The resume is {pages} pages — it should fit on one page.")
                st.download_button(
                    label="⬇️  Download Resume PDF",
                    data=pdf_data,
                    file_name="Tair_Fridman_Resume.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except PDFCompileError as e:
                st.error("PDF compilation failed — pdflatex error below.")
                st.text_area("LaTeX log:", value=e.log, height=200)
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; color:#1e3a5f; font-size:12px;'>"
    "⚡ CV.AI — Powered by Groq / Llama 3.3 · Core sections are hardcoded to prevent hallucinations"
    "</p>", unsafe_allow_html=True
)
