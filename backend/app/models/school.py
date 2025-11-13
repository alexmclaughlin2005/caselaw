"""
School Model

Represents an educational institution.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class School(Base):
    """
    School model representing an educational institution.
    
    Schools can have aliases (e.g., "Harvard Law School" vs "Harvard University Law School").
    """
    __tablename__ = "people_db_school"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    
    # Alias handling
    is_alias_of_id = Column(Integer, ForeignKey("people_db_school.id"), nullable=True)
    
    # Additional fields
    ein = Column(String(20), nullable=True)  # Employer Identification Number
    location_city = Column(String(100), nullable=True)
    location_state = Column(String(50), nullable=True)
    
    # Relationships
    is_alias_of = relationship("School", remote_side=[id], backref="aliases")
    educations = relationship("Education", back_populates="school")
    
    def __repr__(self):
        return f"<School(id={self.id}, name='{self.name}')>"

