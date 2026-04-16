import os
import json
import re
from openai import OpenAI
import logging

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
}}

Do NOT include any text outside the JSON. Score strictly based on job requirements match."""


def score_resume(resume_text: str, job_description: str) -> dict:
    try:
        api_key = os.getenv("LLM_API_KEY")
        if not api_key:
            # Fallback mock for testing without API key
            logger.warning("No LLM_API_KEY provided. Using mock response.")
            return {
                "score": 7.5,
                "summary": "[MOCK] This candidate has strong frontend skills but lacks advanced backend experience mentioned in the JD.",
                "skills_matched": ["React", "JavaScript", "CSS"],
                "skills_missing": ["FastAPI", "PostgreSQL"],
                "red_flags": ["Frequent job changes"]
            }

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

        # Safe JSON parse
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Extract JSON from response if wrapped in markdown
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {
                "score": 0.0,
                "summary": "Could not parse LLM response",
                "skills_matched": [],
                "skills_missing": [],
                "red_flags": ["LLM parsing error"],
            }
    except Exception as e:
        logger.error(f"LLM scoring failed: {e}")
        return {
            "score": 0.0,
            "summary": f"Scoring failed due to API error: {e}",
            "skills_matched": [],
            "skills_missing": [],
            "red_flags": ["Error calling LLM provider"],
        }
