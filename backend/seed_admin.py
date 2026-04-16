from app.db.database import SessionLocal
from app.db.models import User, UserRole
from app.core.security import hash_password
from app.core.encryption import encrypt

db = SessionLocal()
try:
    user = db.query(User).filter(User.email == 'admin@talentai.com').first()
    if not user:
        admin = User(
            email='admin@talentai.com',
            name_encrypted=encrypt('Admin User'),
            hashed_password=hash_password('Admin@123'),
            role=UserRole.admin
        )
        db.add(admin)
        db.commit()
        print('Admin created successfully!')
    else:
        print('Admin already exists.')
finally:
    db.close()
