from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Anchor the workshop DB to the repository root regardless of the launch CWD,
# so `rm -f workshop.db` at the repo root and the app always refer to the same
# file. REQ-016.
REPO_ROOT = Path(__file__).resolve().parents[2]
SQLALCHEMY_DATABASE_URL = f"sqlite:///{REPO_ROOT / 'workshop.db'}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
