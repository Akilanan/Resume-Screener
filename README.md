# TalentAI — Resume Screener & Talent Intelligence Platform

AI-powered bulk resume screening using LLM + event-driven async processing.

## Architecture
Frontend (React) → FastAPI Backend → RabbitMQ Queue → AI Workers (x2) → PostgreSQL

## Quick Start

### 1. Configure Environment
```bash
# Ensure .env is populated with your LLM_API_KEY
# If no key is set, the app will use a mock response fallback for testing.
```

### 2. Start all services
```bash
docker-compose up --build
```
*Wait ~30 seconds for the database, queue, and API to completely initialize.*

### 3. Seed an Admin User
Run this command in a new terminal window while the containers are running:
```bash
docker-compose exec backend python -c "
from app.db.database import SessionLocal
from app.db.models import User, UserRole
from app.core.security import hash_password
from app.core.encryption import encrypt

db = SessionLocal()
if not db.query(User).filter(User.email == 'admin@talentai.com').first():
    admin = User(
        email='admin@talentai.com',
        name_encrypted=encrypt('Admin User'),
        hashed_password=hash_password('Admin@123'),
        role=UserRole.admin
    )
    db.add(admin)
    db.commit()
    print('✅ Admin created successfully!')
else:
    print('Admin already exists.')
"
```

### 4. Access the Platform
- **Frontend App**: [http://localhost:5173](http://localhost:5173)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **RabbitMQ Dashboard**: [http://localhost:15672](http://localhost:15672) (guest / guest)
- **Grafana**: [http://localhost:3001](http://localhost:3001)

### 🔑 Default Credentials
- **Email**: `admin@talentai.com`
- **Password**: `Admin@123`
- **MFA / OTP**: Check the backend console logs for the 6-digit code.

---

## Features Implemented
- ✅ JWT Authentication with MFA (OTP via console/email)
- ✅ Role-based access: Admin vs HR
- ✅ Async resume processing via RabbitMQ
- ✅ PII encryption for all candidate data in DB using Fernet
- ✅ 2 parallel workers with idempotent task processing
- ✅ Beautiful Glassmorphism React Frontend
- ✅ Full JSON structured logging for observability
- ✅ Docker Compose single-command deployment
