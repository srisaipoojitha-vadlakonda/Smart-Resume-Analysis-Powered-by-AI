# 🤖 Smart-Resume-Analysis-Powered-by-AI
An AI-based resume analysis tool built using Python and Streamlit that compares resumes with job descriptions to identify skill gaps, missing keywords, and improvement areas. The system provides structured, actionable suggestions to improve resume quality, relevance, and job matching.

 ### 📌 Project Overview
The AI Resume Critique CLI Tool is a Python-based application that analyzes resumes and compares them with job descriptions to generate improvement suggestions. This tool helps users understand how well their resume aligns with a specific role and provides actionable feedback to improve relevance, clarity, and job matching.

### 🎯 Project Goals
- Compare resumes with job descriptions
- Identify missing skills and keywords
- Highlight improvement areas in experience, projects, and wording
- Provide structured AI suggestions
- Improve resume relevance for specific roles
- Support ATS-friendly resume optimization

### 🧾Inputs
- Resume files (.txt, .pdf, .docx – in this project, sample_resume.txt is used)
- Job description text (sample_job.txt)

### 📤 Outputs
The CLI tool generates structured feedback such as:
- Skill gaps
- Keywords to add
- Resume structure suggestions
- Experience alignment improvements
- Project relevance feedback
- Language and wording suggestions
- ATS optimization tips

### 🛠 Technologies Used
-  Programming Language: Python
- Application Interface: Command-Line Interface (CLI)
- AI/NLP Libraries: Transformers, spaCy
- Text Processing: PyPDF2, docx2txt
- Environment Management: Virtual Environment (venv)
- Version Control: Git, GitHub

### 🔄 How the System Works
1. User provides a resume and a job description
2. Text is extracted from files and cleaned
3. AI models analyze the resume and JD
4. Matching and comparison logic is applied
5. Suggestions are generated
6. Results are displayed in the terminal

### 📊 Output Format
The application produces structured JSON-style feedback:

  ``` {
  "missing_skills": [],
  "skills_to_strengthen": [],
  "keywords_to_add": [],
  "experience_improvements": [],
  "project_improvements": [],
  "resume_structure_improvements": [],
  "language_and_wording": [],
  "ats_optimization": []
}
```
### 📁 Project Structure
```
RESUME-ANALYZER/
│
├── assets/
│   └── resume-demo
├── cli_critic.py
├── main.py
├── pyproject.toml
├── requirements.txt
├── sample_job.txt
├── sample_resume.txt
└── README.md

```
### 📸 Application Preview

This demo shows how the AI Resume Critique Tool analyzes a resume based on a job description and provides tailored improvement insights.

[Watch the demo](https://github.com/srisaipoojitha-vadlakonda/Smart-Resume-Analysis-Powered-by-AI/blob/main/resume-demo.mp4)

### 🎓 Learning Outcomes
- Practical AI integration
- NLP application development
- File handling and parsing
- Building AI-powered CLI tools
- Prompt-based AI systems
- Real-world project structuring

  ### 🚀 Project Value
  This project demonstrates the ability to integrate AI into real-world applications, build functional CLI-based AI tools, and deliver meaningful, user-focused solutions using modern Python development workflows.

  ### 🔮 Future Improvements
  - Resume scoring system
  - Match percentage calculation
  - Multi-resume comparison
  - Resume ranking
  - Cover letter generation
  - Interview preparation module
  - Career guidance features
 
  ## 📬 Contact
  
  ## Name: Sri Sai Poojitha
  ## GitHub: https://github.com//srisaipoojitha-vadlakonda
