import argparse
import io
import json
import re
from pathlib import Path

from docx import Document
from PIL import Image
import PyPDF2
import pytesseract


def extract_text_from_pdf(path: Path) -> str:
    text = ""
    try:
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    except Exception:
        return ""
    return text


def extract_text_from_docx(path: Path) -> str:
    try:
        data = path.read_bytes()
        doc = Document(io.BytesIO(data))
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception:
        return ""


def extract_text_from_txt(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def extract_text_from_image(path: Path) -> str:
    try:
        img = Image.open(path)
        return pytesseract.image_to_string(img)
    except Exception:
        return ""


def extract_resume_text(path: Path) -> str:
    ext = path.suffix.lower().lstrip('.')
    if ext == 'pdf':
        return extract_text_from_pdf(path)
    if ext == 'docx':
        return extract_text_from_docx(path)
    if ext in ('png', 'jpg', 'jpeg', 'bmp', 'tiff'):
        return extract_text_from_image(path)
    if ext == 'txt':
        return extract_text_from_txt(path)
    return ""


def fallback_generator(resume_text: str, job_description: str) -> str:
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


def main():
    parser = argparse.ArgumentParser(description='CLI Resume Critic (local fallback)')
    parser.add_argument('--resume', required=True, help='Path to resume file')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--job-file', help='Path to job description text file')
    group.add_argument('--job-text', help='Job description text')
    args = parser.parse_args()

    resume_path = Path(args.resume)
    if not resume_path.exists():
        print(json.dumps({'error': 'Resume file not found'}))
        return

    resume_text = extract_resume_text(resume_path)

    if args.job_file:
        jd_path = Path(args.job_file)
        if not jd_path.exists():
            print(json.dumps({'error': 'Job description file not found'}))
            return
        job_description = jd_path.read_text(encoding='utf-8', errors='ignore')
    else:
        job_description = args.job_text

    output = fallback_generator(resume_text, job_description)
    print(output)


if __name__ == '__main__':
    main()
