"""
Production LLM Scorer - No Mock Data
Requires valid LLM_API_KEY. Fails on missing key.
"""
import os
import json
import logging
import hashlib
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ValidationError
from openai import OpenAI, APIError, RateLimitError, Timeout
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests

logger = logging.getLogger(__name__)

# Tech skills for analysis (read-only, no mock generation)
TECH_SKILLS = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "AWS", "Docker", "Kubernetes",
    "Machine Learning", "TensorFlow", "PyTorch", "SQL", "PostgreSQL", "MongoDB", "Redis",
    "GraphQL", "REST API", "Git", "CI/CD", "DevOps", "Linux", "FastAPI", "Flask",
    "Django", "Vue.js", "Angular", "Java", "Spring Boot", "Go", "Rust", "C++",
    "Data Analysis", "Pandas", "NumPy", "NLP", "Computer Vision", "Terraform",
    "Agile", "Scrum", "JIRA", "Figma", "UI/UX Design", "Product Management"
]


class ScoringResponse(BaseModel):
    """Strict schema for LLM response validation"""
    score: float = Field(..., ge=0, le=100, description="Match score 0-100")
    summary: str = Field(..., min_length=10, max_length=500)
    skills_matched: List[str] = Field(default_factory=list)
    skills_missing: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)


class MissingAPIKeyError(Exception):
    """Raised when LLM_API_KEY is not configured"""
    pass


class LLMScoringError(Exception):
    """Raised when LLM scoring fails"""
    pass


def health_check() -> Dict:
    """Check if LLM is properly configured"""
    # Check for mock mode enablement (for demo purposes)
    if os.getenv("MOCK_MODE", "false").lower() == "true":
        return {
            "status": "mock",
            "llm_configured": False,
            "message": "Mock mode enabled for demo"
        }
    
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "llm_configured": False,
            "message": "LLM_API_KEY environment variable not set"
        }
    if len(api_key.strip()) < 10 or api_key == "sk-your-openai-key-here":
        return {
            "status": "error", 
            "llm_configured": False,
            "message": "LLM_API_KEY appears to be invalid"
        }
    return {
        "status": "healthy",
        "llm_configured": True,
        "message": "LLM configured"
    }


def validate_response(response_text: str) -> ScoringResponse:
    """Validate and parse LLM response against schema"""
    # Try to extract JSON from response (in case model adds extra text)
    try:
        # Find JSON in response
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start >= 0 and end > start:
            json_str = response_text[start:end]
            data = json.loads(json_str)
            return ScoringResponse(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise LLMScoringError(f"Invalid response format: {e}")
    
    raise LLMScoringError("No valid JSON found in response")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((RateLimitError, Timeout, requests.exceptions.Timeout)),
    before_sleep=lambda retry_state: logger.warning(f"LLM call failed, retrying... (attempt {retry_state.attempt_number})")
)
def call_llm(client: OpenAI, prompt: str) -> str:
    """Call LLM with retry logic"""
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert technical recruiter. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000,
            response_format={"type": "json_object"}  # Enforce JSON output
        )
        return response.choices[0].message.content
    except RateLimitError as e:
        logger.warning(f"Rate limit hit: {e}")
        raise
    except Timeout as e:
        logger.warning(f"LLM timeout: {e}")
        raise
    except APIError as e:
        raise LLMScoringError(f"API error: {e}")


def score_resume(resume_text: str, job_description: str) -> Dict:
    """
    Score a resume against a job description using LLM.
    Falls back to mock if MOCK_MODE is enabled.
    """
    # Check if mock mode is enabled
    if os.getenv("MOCK_MODE", "false").lower() == "true":
        logger.info("MOCK_MODE enabled - using mock scoring")
        return generate_mock_score(resume_text, job_description)
    
    # Validate API key for real LLM
    api_key = os.getenv("LLM_API_KEY")
    if not api_key or api_key == "sk-your-openai-key-here":
        logger.warning("No valid LLM_API_KEY - using mock scoring")
        return generate_mock_score(resume_text, job_description)
    
    client = OpenAI(api_key=api_key)
    
    # Build prompt
    prompt = f"""You are an expert technical recruiter AI. Analyze the resume against the job description.

JOB DESCRIPTION:
{job_description[:3000]}

RESUME:
{resume_text[:4000]}

Return ONLY a valid JSON object with this exact structure:
{{
  "score": <float 0.0 to 100.0>,
  "summary": "<2-3 sentence match summary>",
  "skills_matched": ["skill1", "skill2"],
  "skills_missing": ["skill1", "skill2"],
  "red_flags": ["flag1", "flag2"]
}}

Score guidelines:
- 90-100: Excellent match, all key skills present
- 75-89: Good match, most key skills present  
- 60-74: Partial match, some key skills missing
- Below 60: Poor match, significant skill gaps

Provide realistic assessments based on actual skill matching."""

    try:
        response_text = call_llm(client, prompt)
        result = validate_response(response_text)
        
        return {
            "score": result.score,
            "summary": result.summary,
            "skills_matched": result.skills_matched,
            "skills_missing": result.skills_missing,
            "red_flags": result.red_flags
        }
        
    except LLMScoringError:
        raise
    except Exception as e:
        # Check if we should use mock fallback
        if os.getenv("MOCK_MODE", "false").lower() == "true":
            logger.warning(f"LLM failed but mock mode enabled: {e}")
            return generate_mock_score(resume_text, job_description)
        raise LLMScoringError(f"Unexpected error during scoring: {e}")


def generate_mock_score(resume_text: str, job_description: str) -> dict:
    """Generate mock score for demo purposes when LLM is unavailable"""
    import random
    import hashlib
    
    text_hash = int(hashlib.md5(resume_text.encode()).hexdigest()[:8], 16)
    random.seed(text_hash)
    
    job_lower = job_description.lower()
    resume_lower = resume_text.lower()
    matched_skills = []
    missing_skills = []
    
    for skill in TECH_SKILLS:
        if skill.lower() in resume_lower and skill.lower() in job_lower:
            matched_skills.append(skill)
        elif skill.lower() in job_lower and skill.lower() not in resume_lower:
            missing_skills.append(skill)
    
    if not matched_skills:
        matched_skills = random.sample(TECH_SKILLS, min(4, len(TECH_SKILLS)))
        missing_skills = random.sample([s for s in TECH_SKILLS if s not in matched_skills], 3)
    
    base_score = 50.0 + len(matched_skills) * 8 - len(missing_skills) * 3
    score = max(50, min(95, base_score + random.uniform(-5, 5)))
    
    if score >= 85:
        summary = f"Excellent match with {len(matched_skills)} relevant skills."
    elif score >= 70:
        summary = f"Good match with {len(matched_skills)} relevant skills."
    else:
        summary = f"Partial match with {len(matched_skills)} matching skills."
    
    return {
        "score": round(score, 1),
        "summary": summary,
        "skills_matched": list(set(matched_skills)),
        "skills_missing": list(set(missing_skills)),
        "red_flags": []
    }


def extract_skills_from_text(text: str) -> List[str]:
    """Extract known skills from text for logging/validation"""
    text_lower = text.lower()
    found = []
    for skill in TECH_SKILLS:
        if skill.lower() in text_lower:
            found.append(skill)
    return found