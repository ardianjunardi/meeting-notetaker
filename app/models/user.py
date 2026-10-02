from sqlalchemy import Column, Integer, String, DateTime, func
from app.models.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    google_refresh_token = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
