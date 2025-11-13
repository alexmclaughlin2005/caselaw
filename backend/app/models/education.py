"""
Education Model

Links people to schools with education details.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.core.database import Base


class Education(Base):
    """
    Education model linking a person to a school.
    
    Represents an educational record (degree, attendance, etc.).
    """
    __tablename__ = "people_db_education"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    person_id = Column(Integer, ForeignKey("people_db_person.id"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("people_db_school.id"), nullable=False, index=True)
    
    # Education details
    degree_level = Column(String(50), nullable=True)  # e.g., "JD", "LLM", "BA", "MA", "PhD"
    degree_detail = Column(String(100), nullable=True)  # e.g., "Juris Doctor", "Bachelor of Arts"
    degree_year = Column(Integer, nullable=True, index=True)
    
    # Additional information
    date_start = Column(Date, nullable=True)
    date_end = Column(Date, nullable=True)
    
    # Relationships
    person = relationship("Person", back_populates="educations")
    school = relationship("School", back_populates="educations")
    
    def __repr__(self):
        return f"<Education(id={self.id}, person_id={self.person_id}, school_id={self.school_id})>"

