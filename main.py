import streamlit as st
import PyPDF2
from docx import Document
from pathlib import Path
import pytesseract
from PIL import Image
import re
import json
import io

# Page configuration
st.set_page_config(
    page_title="Resume Critique Engine",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Resume Critique Engine")
st.markdown("*AI-Powered Resume Improvement Analysis*")

# Load model once with caching
def load_model():
    """Load FLAN-T5 model once globally"""
    try:
        import torch
        from transformers import pipeline
        
        device = 0 if torch.cuda.is_available() else -1
        return pipeline(
            "text2text-generation",
            model="google/flan-t5-base",
            device=device,
            max_length=512
        )
    except Exception as e:
        st.warning(f"Model load failed — falling back to local rule-based generator: {e}")
        return None

def extract_text_from_pdf(file) -> str:
    """Extract text from PDF"""
    text = ""
    try:
        try:
            file.seek(0)
        except Exception:
            pass
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            page_text = page.extract_text() or ""
            text += page_text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
    return text

def extract_text_from_docx(file) -> str:
    """Extract text from DOCX"""
    try:
        try:
            file.seek(0)
        except Exception:
            pass
        data = file.read()
        # python-docx accepts a path or a file-like object
        doc = Document(io.BytesIO(data))
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
        return ""

def extract_text_from_txt(file) -> str:
    """Extract text from TXT"""
    try:
        try:
            file.seek(0)
        except Exception:
            pass
        data = file.read()
        if isinstance(data, bytes):
            return data.decode("utf-8", errors="ignore")
        return str(data)
    except Exception as e:
        st.error(f"Error reading TXT: {e}")
        return ""

def extract_text_from_image(file) -> str:
    """Extract text from image using OCR"""
    try:
        try:
            file.seek(0)
        except Exception:
            pass
        image = Image.open(file)
        return pytesseract.image_to_string(image)
    except Exception as e:
        st.error(f"Error reading image: {e}")
        return ""

def extract_resume_text(uploaded_file) -> str:
    """Extract text from various file formats"""
    file_extension = uploaded_file.name.split(".")[-1].lower()
    
    if file_extension == "pdf":
        return extract_text_from_pdf(uploaded_file)
    elif file_extension == "docx":
        return extract_text_from_docx(uploaded_file)
    elif file_extension == "txt":
        return extract_text_from_txt(uploaded_file)
    elif file_extension in ["png", "jpg", "jpeg", "bmp", "tiff"]:
        return extract_text_from_image(uploaded_file)
    else:
        st.error(f"Unsupported file format: {file_extension}")
        return ""

def generate_improvement_json(generator, resume_text: str, job_description: str) -> str:
    """Generate ONLY valid JSON improvement suggestions"""
    
    prompt = f"""You are a resume critique engine. Analyze this resume against the job description.
Return ONLY a valid JSON object. No text before or after. No explanations. No markdown.
Start with {{ and end with }}.

RESUME:
{resume_text[:1000]}

JOB DESCRIPTION:
{job_description[:1000]}

Return this exact format:
{{
  "missing_skills": [],
  "skills_to_strengthen": [],
  "keywords_to_add": [],
  "experience_improvements": [],
  "project_improvements": [],
  "resume_structure_improvements": [],
  "language_and_wording": [],
  "ats_optimization": []
}}"""
    
    def _fallback(resume_text: str, job_description: str) -> str:
        resume_lower = resume_text.lower()
        jd_lower = job_description.lower()
        
        # Extended tech keywords
        tech_keywords = [
            'python','sql','aws','docker','kubernetes','react','node','tensorflow',
            'pandas','spark','java','javascript','cloud','ci/cd','etl','linux','git',
            'rest','api','mongodb','postgresql','mysql','azure','gcp','jenkins','kafka',
            'scala','golang','rust','typescript','vue','angular','django','flask','fastapi'
        ]
        
        # Find missing skills (in JD but not in resume)
        missing = []
        for kw in tech_keywords:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, jd_lower) and not re.search(pattern, resume_lower):
                missing.append(kw)
        
        # Find skills to strengthen (in resume but could be better highlighted)
        skills_to_strengthen = []
        present_tech = []
        for kw in tech_keywords:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, resume_lower):
                present_tech.append(kw)
        
        if present_tech:
            skills_to_strengthen = [
                f"Quantify proficiency for {present_tech[0]} (years, projects, outcomes)",
                f"Add specific use-cases for {present_tech[0]} (e.g., built X, optimized Y)"
            ]
        
        # Extract JD keywords (non-stopwords, frequent terms)
        words = re.findall(r"\b[a-zA-Z0-9\+\-#]+\b", jd_lower)
        stopwords = set(['the','and','a','to','of','in','for','with','on','as','is','be','by','or','are','at','from','that','this','it','you','we','your','our','not','can','have','been','has','was','were','do','does','did','would','could','should','may','might','must'])
        freq = {}
        for w in words:
            if w in stopwords or len(w) < 3 or w in missing or w in present_tech:
                continue
            freq[w] = freq.get(w, 0) + 1
        top = sorted(freq.items(), key=lambda x: -x[1])[:10]
        keywords_to_add = [w for w, _ in top][:8]
        
        # Detect resume patterns
        has_metrics = bool(re.search(r'\d+%|\$\d+|\d+x|\d+ (users|customers|transactions)', resume_text))
        has_projects = bool(re.search(r'project|github|portfolio|built|created|developed', resume_lower))
        has_experience = bool(re.search(r'\d+ (years?|months?)|experience|worked|employed', resume_lower))
        
        # Dynamic suggestions based on actual content
        experience_improvements = []
        if not has_metrics:
            experience_improvements.append('Add quantified outcomes (%, revenue, time saved) to experience bullets')
        if has_experience:
            experience_improvements.append('Highlight achievements from most recent roles that match job responsibilities')
        experience_improvements.append('Include team size, reporting relationships, and scope of impact for major roles')
        if len(experience_improvements) < 3:
            experience_improvements.append('Reorder bullets to prioritize items matching the job description')
        
        project_improvements = []
        if has_projects:
            project_improvements.append('Specify technologies used for each project (stack details)')
            project_improvements.append('Add measurable outcomes or impact (performance gains, user metrics)')
        else:
            project_improvements.append('Add a Projects section if applicable (GitHub, portfolio work)')
        project_improvements.append('Include project timelines and team size/collaboration model')
        
        resume_structure_improvements = [
            'Add a headline summary (job title + 2–3 key strengths aligned to role)',
            'Create a dedicated Skills section grouped by category (Languages, Frameworks, Cloud, Tools)',
            'Ensure consistent formatting with clear section headers and proper spacing'
        ]
        
        language_and_wording = [
            'Replace passive phrases ("responsible for") with active verbs (led, implemented, delivered)',
            'Quantify or make specific vague claims (change "experienced with" to "5+ years of")'
        ]
        if not has_metrics:
            language_and_wording.append('Add metrics to action verbs (reduced X by Y%, increased Z)')
        
        ats_optimization = [
            'Include keyword phrases from job posting in Skills and Experience sections naturally',
            'Use standard section headers (no symbols or special formatting) for ATS parsing',
            'Save as clean PDF or DOCX; avoid tables, images, and unusual fonts'
        ]

        result = {
            'missing_skills': missing[:8] or ['Review job posting for domain-specific skills not on resume'],
            'skills_to_strengthen': skills_to_strengthen or ['Add proficiency levels and use-cases for existing skills'],
            'keywords_to_add': keywords_to_add or ['scalability','optimization','architecture'],
            'experience_improvements': experience_improvements,
            'project_improvements': project_improvements,
            'resume_structure_improvements': resume_structure_improvements,
            'language_and_wording': language_and_wording,
            'ats_optimization': ats_optimization
        }
        return json.dumps(result, separators=(',', ':'))

    try:
        # Try using the model-based generator
        result = generator(prompt, max_length=1500, num_beams=2)
        # different transformers versions use different keys
        json_text = result[0].get('generated_text') or result[0].get('summary_text') or str(result[0])
        json_text = str(json_text).strip()

        # Extract JSON from response - find first { and last }
        start_idx = json_text.find('{')
        end_idx = json_text.rfind('}') + 1

        if start_idx != -1 and end_idx > start_idx:
            json_text = json_text[start_idx:end_idx]

        # Try to parse and validate JSON
        json_data = json.loads(json_text)

        # Ensure all required keys exist
        required_keys = [
            "missing_skills", "skills_to_strengthen", "keywords_to_add",
            "experience_improvements", "project_improvements",
            "resume_structure_improvements", "language_and_wording", "ats_optimization"
        ]

        for key in required_keys:
            if key not in json_data:
                json_data[key] = []
            elif not isinstance(json_data[key], list):
                json_data[key] = [str(json_data[key])]

        cleaned_data = {k: v for k, v in json_data.items() if k in required_keys}
        # Ensure no empty arrays (some consumers expect entries)
        for k in required_keys:
            if not cleaned_data.get(k):
                cleaned_data[k] = ["Add relevant details here"]

        return json.dumps(cleaned_data, separators=(',', ':'))

    except Exception:
        # Fallback to rule-based generator
        return _fallback(resume_text, job_description)

def display_json_improvements(json_str: str):
    """Display JSON improvements in formatted sections"""
    try:
        data = json.loads(json_str)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if data.get("missing_skills") and len(data["missing_skills"]) > 0:
                st.subheader("Missing Skills to Add")
                for skill in data["missing_skills"]:
                    if skill.strip():
                        st.write(f"• {skill}")
            
            if data.get("skills_to_strengthen") and len(data["skills_to_strengthen"]) > 0:
                st.subheader("Skills to Strengthen")
                for skill in data["skills_to_strengthen"]:
                    if skill.strip():
                        st.write(f"• {skill}")
            
            if data.get("keywords_to_add") and len(data["keywords_to_add"]) > 0:
                st.subheader("Keywords to Add")
                for keyword in data["keywords_to_add"]:
                    if keyword.strip():
                        st.write(f"• {keyword}")
            
            if data.get("experience_improvements") and len(data["experience_improvements"]) > 0:
                st.subheader("Experience Improvements")
                for exp in data["experience_improvements"]:
                    if exp.strip():
                        st.write(f"• {exp}")
        
        with col2:
            if data.get("project_improvements") and len(data["project_improvements"]) > 0:
                st.subheader("Project Improvements")
                for proj in data["project_improvements"]:
                    if proj.strip():
                        st.write(f"• {proj}")
            
            if data.get("resume_structure_improvements") and len(data["resume_structure_improvements"]) > 0:
                st.subheader("Resume Structure")
                for struct in data["resume_structure_improvements"]:
                    if struct.strip():
                        st.write(f"• {struct}")
            
            if data.get("language_and_wording") and len(data["language_and_wording"]) > 0:
                st.subheader("Language & Wording")
                for lang in data["language_and_wording"]:
                    if lang.strip():
                        st.write(f"• {lang}")
            
            if data.get("ats_optimization") and len(data["ats_optimization"]) > 0:
                st.subheader("ATS Optimization")
                for ats in data["ats_optimization"]:
                    if ats.strip():
                        st.write(f"• {ats}")
    
    except json.JSONDecodeError:
        st.error("Could not parse JSON response.")
        st.code(json_str, language="json")

# Main interface
st.subheader("Resume Analysis")

col1, col2 = st.columns(2)

with col1:
    st.write("**Upload Your Resume**")
    resume_file = st.file_uploader(
        "Choose resume file",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        key="resume_upload",
        label_visibility="collapsed"
    )

with col2:
    st.write("**Job Description**")
    job_input_method = st.radio(
        "Input method:",
        ["Paste Text", "Upload File"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if job_input_method == "Paste Text":
        job_description = st.text_area(
            "Paste job description:",
            height=250,
            placeholder="Copy and paste the full job description...",
            key="job_paste"
        )
    else:
        job_file = st.file_uploader(
            "Upload job description",
            type=["txt", "pdf"],
            key="job_file"
        )
        if job_file:
            if job_file.name.endswith(".pdf"):
                job_description = extract_text_from_pdf(job_file)
            else:
                job_description = extract_text_from_txt(job_file)
        else:
            job_description = ""

# Process and analyze
if resume_file and job_description:
    use_fallback = st.checkbox("Use local fallback (no model download)", value=True)

    if st.button("Analyze", use_container_width=True, type="primary"):
        with st.spinner("Extracting resume..."):
            resume_text = extract_resume_text(resume_file)
        
        if resume_text:
            # Generate improvements
            with st.spinner("Analyzing resume against job description..."):
                generator = None
                if not use_fallback:
                    generator = load_model()

                json_improvements = generate_improvement_json(
                    generator,
                    resume_text,
                    job_description
                )
            
            st.divider()
            st.subheader("Improvement Suggestions")
            
            # Display formatted JSON
            display_json_improvements(json_improvements)
            
            # Download options
            st.divider()
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="Download JSON",
                    data=json_improvements,
                    file_name="resume_improvements.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col2:
                st.code(json_improvements, language="json")
else:
    if not resume_file:
        st.info("Step 1: Upload your resume")
    if not job_description:
        st.info("Step 2: Paste or upload the job description")

# Sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("Features")
    st.markdown(
        """
        JSON formatted output
        Multiple resume formats
        No API keys needed
        100% local processing
        Download suggestions
        ATS optimization tips
        """
    )
    
    st.markdown("---")
    if st.checkbox("Show system info"):
        try:
            import torch
            gpu_status = 'Yes' if torch.cuda.is_available() else 'No'
        except Exception:
            gpu_status = 'No'
        st.write(f"GPU: {gpu_status}")
        st.write(f"Model: FLAN-T5 Base (optional)")
        st.write(f"Privacy: 100% Local")