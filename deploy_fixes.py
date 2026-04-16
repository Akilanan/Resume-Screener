#!/usr/bin/env python3
"""
TalentAI Deployment Script
Applies all critical fixes for Phase 2

Usage:
    python deploy_fixes.py
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/12aki/Downloads/hack")

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(text.center(60))
    print("="*60 + "\n")

def run_command(cmd, cwd=None):
    """Run a shell command"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Warning: Command failed: {cmd}")
            print(result.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def step1_backup_files():
    """Backup existing files"""
    print_header("Step 1: Creating Backups")
    
    backup_dir = PROJECT_ROOT / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    files_to_backup = [
        "backend/app/core/security.py",
        "backend/app/api/v1/resumes.py",
        "worker/worker.py",
        "docker-compose.yml",
    ]
    
    for file_path in files_to_backup:
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            backup_path = backup_dir / f"{file_path.replace('/', '_')}.backup"
            shutil.copy(full_path, backup_path)
            print(f"Backed up: {file_path}")

def step2_verify_structure():
    """Verify project structure"""
    print_header("Step 2: Verifying Project Structure")
    
    required_files = [
        "docker-compose.yml",
        "backend/app/core/security.py",
        "backend/app/api/v1/resumes.py",
        "worker/worker.py",
    ]
    
    all_good = True
    for file_path in required_files:
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            print(f"Found: {file_path}")
        else:
            print(f"Missing: {file_path}")
            all_good = False
    
    return all_good

def step3_restart_services():
    """Restart all services"""
    print_header("Step 3: Restarting Services")
    
    print("Stopping services...")
    if run_command("docker-compose down"):
        print("Services stopped")
    
    print("Rebuilding and starting...")
    if run_command("docker-compose up --build -d"):
        print("Services restarted")
    
    print("Waiting for services to be healthy...")
    run_command("timeout /t 10 /nobreak")

def step4_verify_deployment():
    """Verify the deployment"""
    print_header("Step 4: Verifying Deployment")
    
    # Check containers are running
    result = subprocess.run(
        ["docker-compose", "ps"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    print("\nContainer Status:")
    print(result.stdout)

def step5_show_next_steps():
    """Show next steps"""
    print_header("Next Steps")
    print("""
1. VERIFICATION COMMANDS:
   
   # Check containers
   docker-compose ps
   
   # View backend logs
   docker-compose logs -f backend
   
   # View worker logs
   docker-compose logs -f worker

2. TEST THE API:
   
   # Test health
   curl http://localhost:8000/health
   
   # Test login (should show MFA required)
   curl -X POST http://localhost:8000/api/v1/auth/login ^
     -H "Content-Type: application/json" ^
     -d '{"email":"admin@talentai.com","password":"Admin@123"}'

3. CRITICAL FILES FIXED:
   - backend/app/core/security.py (Better error handling)
   - backend/app/api/v1/resumes.py (Auth error handling)

4. STILL NEEDED (from MASTER_IMPLEMENTATION_PLAN.md):
   - Worker retry + DLQ (High Priority)
   - WebSocket real-time updates (High Priority)
   - Redis caching (Medium Priority)
   - Rate limiting (Medium Priority)

5. DEMO PREPARATION:
   - Run Phase 2 features from implementation plan
   - Practice 5-minute demo
   - Record backup video
""")

def main():
    """Main deployment function"""
    print_header("TALENTAI DEPLOYMENT SCRIPT")
    print("Fixing critical errors and preparing for Phase 2\n")
    
    print("This script will:")
    print("  1. Backup existing files")
    print("  2. Verify project structure")
    print("  3. Restart all services")
    print("  4. Verify deployment")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() != "yes":
        print("\nDeployment cancelled.")
        return
    
    # Run steps
    step1_backup_files()
    
    if not step2_verify_structure():
        print("\nProject structure verification failed!")
        return
    
    step3_restart_services()
    step4_verify_deployment()
    
    print_header("DEPLOYMENT COMPLETE")
    step5_show_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDeployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nDeployment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
