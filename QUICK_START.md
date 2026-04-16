# 🚀 Quick Start - Phase 2 Implementation

## ⚡ Priority 1: Do These First (This Week)

### 1. Fix Critical Errors ✅
- [x] JWT token expiry extended to 24 hours
- [x] Frontend auto-clears expired tokens
- [ ] Add refresh token endpoint

### 2. Add WebSocket Support (High Impact!)
```bash
# 1. Install dependencies
cd backend && pip install fastapi-socketio websockets

# 2. Create websocket endpoint
# backend/app/api/v1/websocket.py -> copy from plan

# 3. Test
cd .. && docker-compose up --build
```

### 3. Implement Retry Logic
```bash
# Files created for you:
# - backend/app/core/circuit_breaker.py
# - backend/app/core/retry_handler.py
# - backend/app/core/audit.py

# Just integrate them into worker/main.py
```

---

## 🎯 Quick Implementation Commands

### Step 1: Enable Debug Mode
```bash
cd C:\Users\12aki\Downloads\hack
docker-compose down
docker-compose up --build -d
```

### Step 2: Test Current State
```bash
# Health check
curl http://localhost:8000/health

# Auth test
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@talentai.com","password":"Admin@123"}'
```

### Step 3: Watch Logs
```bash
# Important: Watch for JWT errors
docker-compose logs -f backend | grep -i "expired\|error\|signature"

# Check if expired errors are gone (should be 0)
docker-compose logs --since=1h backend | grep -c "ExpiredSignatureError"
```

---

## ✅ Verification Checklist

### Security
- [x] Token expiry = 24 hours
- [x] Frontend auto-logout on expiry
- [ ] Refresh token rotation (add this)
- [ ] Rate limiting on login (add this)

### Stability
- [x] Circuit breaker pattern ready
- [x] DLQ handler ready
- [ ] WebSocket real-time updates (add this)
- [ ] Retry with exponential backoff (add this)

### Features
- [ ] Bulk upload with progress bar
- [ ] Export to Excel
- [ ] Advanced filters on candidate table
- [ ] Real-time progress notifications

---

## 🔥 Demo-Killer Features

Add these 3 features to win:

### 1. Real-time Progress (1 day)
```typescript
// Add to frontend
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (e) => {
  const { progress, status } = JSON.parse(e.data);
  updateProgressBar(progress);
};
```

### 2. Bulk Upload with Drag-Drop (1 day)
```bash
npm install react-dropzone @tanstack/react-table
# Use existing code from IMPLEMENTATION_PLAN.md
```

### 3. Export to Excel/PDF (1 day)
```python
# Add to backend/app/api/v1/exports.py
# Use pandas.to_excel() - code in plan
```

---

## 📊 Demo Data Setup

```python
# Run this to seed demo data
# seed_demo.py

import requests

def seed_jobs():
    """Create sample jobs for demo"""
    jobs = [
        {
            "title": "Senior Python Developer",
            "description": "5+ years Python, FastAPI, PostgreSQL...",
            "required_skills": ["Python", "FastAPI", "PostgreSQL"],
            "salary_range": "$100k-$150k"
        },
        {
            "title": "ML Engineer",
            "description": "PyTorch, LLMs, NLP...",
            "required_skills": ["Python", "PyTorch", "LLM"],
            "salary_range": "$120k-$180k"
        }
    ]
    
    for job in jobs:
        # Create via API
        pass

if __name__ == "__main__":
    seed_jobs()
```

---

## 🚨 Common Issues + Fixes

### Issue: "Failed to fetch" when screening
```
Cause: Old expired token in browser
Fix: Clear localStorage or logout/login
```

### Issue: `ExpiredSignatureError` in logs
```
Cause: Container running old code
Fix: docker-compose down && docker-compose up --build
```

### Issue: 403 Forbidden on API calls
```
Cause: Token format issues or CORS
Fix: Check browser console, ensure token is valid
```

### Issue: WebSocket connection refused
```
Cause: Backend not running or port blocked
Fix: docker-compose ps (check all services up)
```

---

## 📝 What Judges Want to See

1. **Numbers That Impress**
   - "Processes 10,000 resumes/hour"
   - "Sub-200ms API response time"
   - "99.9% uptime with circuit breakers"

2. **Live Demo Flow** (5 min)
   ```
   0:00 - Login with MFA
   0:30 - Bulk upload 20 resumes
   1:00 - Show real-time progress bars
   2:00 - View AI results with explanations
   3:00 - Export to Excel
   3:30 - Technical deep-dive
   4:30 - Business impact
   ```

3. **Technical Differentiation**
   - Circuit breaker visualization
   - Bias detection explanation
   - Semantic matching (not just keywords)

---

## 📞 Need Help?

```bash
# Check all systems
docker-compose ps

# View recent errors
docker-compose logs --tail=50 backend

# Restart just the backend
docker-compose restart backend

# Full rebuild (nuclear option)
docker-compose down -v && docker-compose up --build
```

---

**Current Status: ✅ JWT Fixed, Ready for Phase 2 Features!**

Next tasks:
1. Add WebSocket real-time updates
2. Implement retry/DLQ in worker
3. Add bulk upload to frontend
4. Create export functionality

**You're 30% done - 70% to go!** 🚀
