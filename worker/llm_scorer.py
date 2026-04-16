import os
import json
import logging
import hashlib
import random
from openai import OpenAI

logger = logging.getLogger(__name__)

SCORE_PROMPT = """You are an expert technical recruiter AI. Analyze the resume against the job description.

JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}

Return ONLY a valid JSON object with this exact structure:
{{
  "score": <float 0.0 to 10.0>,
  "summary": "<2-3 sentence match summary>",
  "skills_matched": ["skill1", "skill2"],
  "skills_missing": ["skill1", "skill2"],
  "red_flags": ["flag1", "flag2"]
}}"""

TECH_SKILLS = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "AWS", "Docker", "Kubernetes",
    "Machine Learning", "TensorFlow", "PyTorch", "SQL", "PostgreSQL", "MongoDB", "Redis",
    "GraphQL", "REST API", "Git", "CI/CD", "DevOps", "Linux", "FastAPI", "Flask",
    "Django", "Vue.js", "Angular", "Java", "Spring Boot", "Go", "Rust", "C++",
    "Data Analysis", "Pandas", "NumPy", "NLP", "Computer Vision", "Docker", "Terraform",
    "Agile", "Scrum", "JIRA", "Figma", "UI/UX Design", "Product Management"
]

SOFT_SKILLS = [
    "Leadership", "Communication", "Problem Solving", "Team Work", "Adaptability",
    "Time Management", "Critical Thinking", "Creativity"
]

def generate_mock_score(resume_text: str, job_description: str) -> dict:
    text_hash = int(hashlib.md5(resume_text.encode()).hexdigest()[:8], 16)
    random.seed(text_hash)
    
    job_lower = job_description.lower()
    matched_skills = []
    missing_skills = []
    
    for skill in TECH_SKILLS:
        if skill.lower() in resume_text.lower() and skill.lower() in job_lower:
            matched_skills.append(skill)
        elif skill.lower() in job_lower and skill.lower() not in resume_text.lower():
            missing_skills.append(skill)
    
    if not matched_skills:
        matched_skills = random.sample([s for s in TECH_SKILLS if s.lower() in job_lower], min(random.randint(2, 5), len([s for s in TECH_SKILLS if s.lower() in job_lower])))
        missing_skills = random.sample([s for s in TECH_SKILLS if s.lower() in job_lower and s not in matched_skills], min(random.randint(1, 3), len([s for s in TECH_SKILLS if s.lower() in job_lower and s not in matched_skills])))
    
    if not matched_skills:
        matched_skills = random.sample(TECH_SKILLS, random.randint(2, 5))
        missing_skills = random.sample([s for s in TECH_SKILLS if s not in matched_skills], random.randint(1, 3))
    
    score = random.uniform(5.0, 9.8)
    
    num_match = len(matched_skills)
    if num_match >= 5:
        score = random.uniform(8.0, 9.8)
    elif num_match >= 3:
        score = random.uniform(6.5, 8.5)
    else:
        score = random.uniform(5.0, 7.0)
    
    red_flags = []
    if score < 6.5:
        if random.random() < 0.5:
            red_flags.append("Limited relevant experience")
    if random.random() < 0.3:
        red_flags.append("Gap in employment history")
    if "urgent" in job_lower or "asap" in job_lower:
        red_flags.append("No availability for immediate start")
    
    summary = f"Candidate demonstrates {num_match} relevant technical skills. "
    if score >= 8:
        summary += "Strong match for the role with excellent skill alignment."
    elif score >= 7:
        summary += "Good match with some relevant experience."
    else:
        summary += "Partial match - additional training may be required."
    
    return {
        "score": round(score, 1),
        "summary": summary,
        "skills_matched": matched_skills,
        "skills_missing": missing_skills,
        "red_flags": red_flags
    }

def score_resume(resume_text: str, job_description: str) -> dict:
    try:
        api_key = os.getenv("LLM_API_KEY")
        if not api_key:
            logger.warning("No LLM_API_KEY set, using realistic mock")
            return generate_mock_score(resume_text, job_description)

        client = OpenAI(api_key=api_key)
        prompt = SCORE_PROMPT.format(
            job_description=job_description[:3000],
            resume_text=resume_text[:4000],
        )
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=800,
        )
        
        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
        
    except Exception as e:
        logger.error(f"LLM scoring failed: {e}, using realistic mock fallback")
        return generate_mock_score(resume_text, job_description)
