from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.core.config import settings

# Engine with proper connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_pre_ping=True,           # Test connections before using
    pool_size=10,                 # Base pool size
    max_overflow=20,              # Additional connections when needed
    pool_recycle=3600,           # Recycle connections after 1 hour
    pool_timeout=30,             # Wait for connection max 30s
    connect_args={
        "connect_timeout": 10,
    }
)

# Add event listener for connection errors and set session timeout
@event.listens_for(engine, "connect")
def set_session_timeout(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("SET statement_timeout = 30000")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()