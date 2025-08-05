from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    company = Column(String(100), nullable=False)
    location = Column(String(100), nullable=True)
    skills_required = Column(String(255), nullable=True)

    # Optional: if you want to link jobs to users (employers)
    # posted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
