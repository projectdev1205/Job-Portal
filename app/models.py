from sqlalchemy import Column, Integer, String, Text, Date
from app.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)

    company_name = Column(String(100), nullable=False)
    company_address = Column(String(255), nullable=True)
    company_description = Column(Text, nullable=True)

    job_type = Column(String(255), nullable=True)  # comma-separated string: "part-time,virtual"
    tags = Column(String(255), nullable=True)      # comma-separated string

    location_street = Column(String(255), nullable=True)
    location_city = Column(String(100), nullable=True)
    location_state = Column(String(50), nullable=True)
    location_zip = Column(String(20), nullable=True)

    applicants = Column(Integer, default=0)
    posted_date = Column(Date, nullable=True)

    description = Column(Text, nullable=True)
    key_responsibilities = Column(Text, nullable=True)           # JSON string list
    requirements_qualifications = Column(Text, nullable=True)    # JSON string list
    offerings = Column(Text, nullable=True)                      # JSON string list
    job_details = Column(Text, nullable=True)                    # JSON string (dict)
