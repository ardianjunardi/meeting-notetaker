from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.models.database import Base


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    meet_link = Column(String, nullable=False)
    scheduled_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="pending", index=True)
    audio_path = Column(String, nullable=True)
    transcript_path = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", backref="meetings")
    minutes = relationship("MeetingMinute", back_populates="meeting", uselist=False)


class MeetingMinute(Base):
    __tablename__ = "meeting_minutes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), unique=True, nullable=False)
    summary = Column(Text, nullable=True)
    action_items = Column(Text, nullable=True)
    pending_questions = Column(Text, nullable=True)
    raw_transcript = Column(Text, nullable=True)
    generated_at = Column(DateTime, server_default=func.now())

    meeting = relationship("Meeting", back_populates="minutes")
