import requests
import time
import json

# Step 1: Login to get token
print('=== Step 1: Logging in ===')
login_resp = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'email': 'admin@talentai.com',
    'password': 'Admin@123'
})
print(f'Login status: {login_resp.status_code}')
login_data = login_resp.json()
print(f'Login response: {json.dumps(login_data, indent=2)[:300]}')

if login_status := login_resp.status_code == 200:
    # Get OTP if in demo mode
    if 'otp' in login_data:
        otp = login_data['otp']
        print(f'\nGot OTP: {otp}')
        
        # Verify OTP
        print('\n=== Step 2: Verifying OTP ===')
        otp_resp = requests.post('http://localhost:8000/api/v1/auth/verify-otp', json={
            'email': 'admin@talentai.com',
            'otp': otp
        })
        print(f'OTP verify status: {otp_resp.status_code}')
        otp_data = otp_resp.json()
        print(f'OTP response: {json.dumps(otp_data, indent=2)[:300]}')
        
        if otp_resp.status_code == 200 and 'access_token' in otp_data:
            token = otp_data['access_token']
            print(f'\nGot access token: {token[:50]}...')
            
            # Step 3: Create a job first
            print('\n=== Step 3: Creating job ===')
            headers = {'Authorization': f'Bearer {token}'}
            job_resp = requests.post('http://localhost:8000/api/v1/jobs', 
                                    json={'title': 'Python Developer', 'description': 'Looking for Python developer with ML experience'},
                                    headers=headers)
            print(f'Job creation status: {job_resp.status_code}')
            if job_resp.status_code == 200:
                job_data = job_resp.json()
                job_id = job_data.get('id')
                print(f'Created job ID: {job_id}')
                
                # Step 4: Upload resume
                print('\n=== Step 4: Uploading resume ===')
                pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Test Resume) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000056 00000 n 
0000000109 00000 n 
0000000253 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
350
%%EOF"""
                
                files = [('files', ('test_resume.pdf', pdf_content, 'application/pdf'))]
                upload_resp = requests.post(f'http://localhost:8000/api/v1/resumes/upload/{job_id}', 
                                           files=files, headers=headers)
                print(f'Upload status: {upload_resp.status_code}')
                print(f'Upload response: {upload_resp.text[:500]}')
                
                time.sleep(2)
                
                print('\n=== Step 5: Checking queue ===')
                import subprocess
                result = subprocess.run(['docker', 'exec', 'hack-rabbitmq-1', 'rabbitmqctl', 'list_queues', 'name', 'durable', 'messages'], 
                                       capture_output=True, text=True)
                print(result.stdout)
