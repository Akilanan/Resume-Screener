"""
Demo data seeder for TalentAI.
Run this to populate the database with realistic demo candidates.
"""
import psycopg2
import json
import random
import os
from datetime import datetime, timedelta

# Database connection
DB_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/talentai")

# Demo candidate data with realistic information
DEMO_CANDIDATES = [
    {
        "name": "Priya Sharma",
        "email": "priya.sharma@email.com",
        "phone": "+91 98765 43210",
        "filename": "priya_sharma_resume.pdf",
        "experience": 6,
        "education": "B.Tech Computer Science, IIT Delhi",
        "current_role": "Senior Software Engineer",
        "location": "Bangalore, India",
        "score": 94.5,
        "matched": ["Python", "React", "AWS", "Docker", "TypeScript", "PostgreSQL"],
        "missing": ["Kubernetes", "GraphQL"],
        "summary": "Excellent candidate with 6 years of experience in Python and React. Strong AWS and Docker skills. Experience with microservices architecture.",
        "red_flags": []
    },
    {
        "name": "Aisha Patel",
        "email": "aisha.patel@email.com",
        "phone": "+1 555 123 4567",
        "filename": "aisha_patel_resume.pdf",
        "experience": 4,
        "education": "MSc Machine Learning, Stanford University",
        "current_role": "ML Engineer",
        "location": "San Francisco, CA",
        "score": 92.0,
        "matched": ["Python", "TensorFlow", "Machine Learning", "SQL", "Docker"],
        "missing": ["Kubernetes", "AWS"],
        "summary": "Strong ML background with TensorFlow expertise. Good Python skills and practical Docker experience.",
        "red_flags": []
    },
    {
        "name": "Sofia Rodriguez",
        "email": "sofia.rodriguez@email.com",
        "phone": "+34 612 345 678",
        "filename": "sofia_rodriguez_resume.pdf",
        "experience": 5,
        "education": "B.Design, MIT",
        "current_role": "Product Designer",
        "location": "Barcelona, Spain",
        "score": 88.5,
        "matched": ["Figma", "UI/UX Design", "React", "Prototyping"],
        "missing": ["TypeScript", "Backend"],
        "summary": "Creative designer with strong Figma skills. Some frontend development experience. Good eye for user experience.",
        "red_flags": ["Limited technical skills"]
    },
    {
        "name": "James Okafor",
        "email": "james.okafor@email.com",
        "phone": "+234 803 123 4567",
        "filename": "james_okafor_resume.pdf",
        "experience": 8,
        "education": "MBA, Lagos Business School",
        "current_role": "Technical Lead",
        "location": "Lagos, Nigeria",
        "score": 85.0,
        "matched": ["Python", "JavaScript", "Team Leadership", "Agile", "SQL"],
        "missing": ["React", "AWS"],
        "summary": "Experienced technical lead with strong management skills. Good Python and JavaScript foundation.",
        "red_flags": ["Limited cloud experience"]
    },
    {
        "name": "Elena Volkov",
        "email": "elena.volkov@email.com",
        "phone": "+7 999 123 4567",
        "filename": "elena_volkov_resume.pdf",
        "experience": 3,
        "education": "B.Sc Computer Science, Moscow State University",
        "current_role": "Full Stack Developer",
        "location": "Moscow, Russia",
        "score": 78.5,
        "matched": ["JavaScript", "Node.js", "MongoDB", "Git"],
        "missing": ["React", "AWS", "Docker", "TypeScript"],
        "summary": "Competent full-stack developer with Node.js and MongoDB experience. Growing skill set, would benefit from mentorship.",
        "red_flags": ["Limited cloud and containerization experience"]
    },
    {
        "name": "David Chen",
        "email": "david.chen@email.com",
        "phone": "+1 555 987 6543",
        "filename": "david_chen_resume.pdf",
        "experience": 7,
        "education": "PhD Computer Science, MIT",
        "current_role": "Staff Engineer",
        "location": "Seattle, WA",
        "score": 96.0,
        "matched": ["Python", "Go", "Kubernetes", "AWS", "Machine Learning", "TensorFlow", "PostgreSQL"],
        "missing": [],
        "summary": "Exceptional candidate with PhD-level expertise. Deep experience in distributed systems, ML, and cloud infrastructure.",
        "red_flags": []
    },
    {
        "name": "Marcus Johnson",
        "email": "marcus.johnson@email.com",
        "phone": "+1 555 456 7890",
        "filename": "marcus_johnson_resume.pdf",
        "experience": 2,
        "education": "Bootcamp Graduate",
        "current_role": "Junior Developer",
        "location": "Austin, TX",
        "score": 68.0,
        "matched": ["JavaScript", "React", "HTML", "CSS"],
        "missing": ["Python", "AWS", "SQL", "Docker", "Node.js"],
        "summary": "Junior developer with strong frontend fundamentals. Eager to learn and grow. Limited production experience.",
        "red_flags": ["Limited experience", "No formal degree"]
    },
    {
        "name": "Yuki Tanaka",
        "email": "yuki.tanaka@email.com",
        "phone": "+81 90 1234 5678",
        "filename": "yuki_tanaka_resume.pdf",
        "experience": 5,
        "education": "B.Eng Software Engineering, Tokyo University",
        "current_role": "Senior Backend Engineer",
        "location": "Tokyo, Japan",
        "score": 91.0,
        "matched": ["Java", "Spring Boot", "PostgreSQL", "Docker", "Kubernetes", "REST API"],
        "missing": ["Python", "AWS"],
        "summary": "Strong Java backend developer with Spring Boot expertise. Excellent database and containerization skills.",
        "red_flags": []
    },
    {
        "name": "Fatima Al-Hassan",
        "email": "fatima.alhassan@email.com",
        "phone": "+971 50 123 4567",
        "filename": "fatima_al_hassan_resume.pdf",
        "experience": 4,
        "education": "B.Sc Computer Science, American University of Dubai",
        "current_role": "DevOps Engineer",
        "location": "Dubai, UAE",
        "score": 89.0,
        "matched": ["Docker", "Kubernetes", "Terraform", "AWS", "CI/CD", "Linux"],
        "missing": ["Python", "Machine Learning"],
        "summary": "Skilled DevOps engineer with strong cloud and infrastructure automation skills. Excellent with AWS and Kubernetes.",
        "red_flags": []
    },
    {
        "name": "Lucas Silva",
        "email": "lucas.silva@email.com",
        "phone": "+55 11 91234 5678",
        "filename": "lucas_silva_resume.pdf",
        "experience": 6,
        "education": "B.Sc Computer Science, USP",
        "current_role": "Full Stack Developer",
        "location": "São Paulo, Brazil",
        "score": 82.5,
        "matched": ["JavaScript", "React", "Node.js", "PostgreSQL", "Docker"],
        "missing": ["AWS", "TypeScript", "GraphQL"],
        "summary": "Reliable full-stack developer with solid JavaScript/React skills. Good backend experience with Node.js.",
        "red_flags": []
    }
]

# Sample job descriptions
DEMO_JOBS = [
    {
        "title": "Senior Full Stack Developer",
        "description": """
We are looking for a Senior Full Stack Developer to join our growing engineering team.

Requirements:
- 5+ years of experience with Python or JavaScript
- Strong experience with React, TypeScript
- Experience with cloud platforms (AWS preferred)
- Knowledge of Docker and Kubernetes
- Experience with SQL and NoSQL databases
- Understanding of REST APIs and GraphQL

Nice to have:
- Machine learning experience
- Experience with microservices architecture
- Agile/Scrum experience
        """,
        "status": "open"
    },
    {
        "title": "ML Engineer",
        "description": """
We are seeking a Machine Learning Engineer to build and deploy ML models.

Requirements:
- Strong Python skills
- Experience with TensorFlow or PyTorch
- Knowledge of ML algorithms
- SQL and database experience
- Docker experience

Nice to have:
- Cloud experience (AWS/GCP)
- NLP or Computer Vision expertise
        """,
        "status": "open"
    }
]


def seed_database():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    print("Seeding demo data...")
    
    # Create demo jobs
    job_ids = []
    for job in DEMO_JOBS:
        job_id = f"demo-{job['title'].lower().replace(' ', '-')}"
        cur.execute("""
            INSERT INTO jobs (id, title, description, status, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (job_id, job['title'], job['description'].strip(), job['status'], datetime.now()))
        job_ids.append(job_id)
    
    # Create demo candidates
    for candidate in DEMO_CANDIDATES:
        import uuid
        resume_id = str(uuid.uuid4())
        job_id = job_ids[0]  # Assign to first job
        
        cur.execute("""
            INSERT INTO resumes (
                id, job_id, candidate_name_encrypted, candidate_email_encrypted,
                filename, status, score, match_summary, skills_matched, skills_missing,
                red_flags, uploaded_at, processed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (
            resume_id,
            job_id,
            candidate["name"],  # In production, encrypt these
            candidate["email"],
            candidate["filename"],
            "completed",
            candidate["score"],
            candidate["summary"],
            json.dumps(candidate["matched"]),
            json.dumps(candidate["missing"]),
            json.dumps(candidate["red_flags"]),
            datetime.now() - timedelta(days=random.randint(1, 30)),
            datetime.now() - timedelta(days=random.randint(0, 5))
        ))
        print(f"  Added: {candidate['name']} (score: {candidate['score']})")
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"\nDone! Seeded {len(DEMO_CANDIDATES)} candidates and {len(DEMO_JOBS)} jobs.")


if __name__ == "__main__":
    seed_database()
