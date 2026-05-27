from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.sql import func

from .database import Base


class Ping(Base):
    __tablename__ = "pings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )
