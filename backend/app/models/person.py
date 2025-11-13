"""
Person Model

Represents a person (judge or legal professional) in the database.
"""
from sqlalchemy import Column, Integer, String, Date, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Person(Base):
    """
    Person model representing a judge or legal professional.
    
    This is the core table linking to positions, education, and other related data.
    """
    __tablename__ = "people_db_person"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Name fields
    name_first = Column(String(50), nullable=True, index=True)
    name_middle = Column(String(50), nullable=True)
    name_last = Column(String(50), nullable=True, index=True)
    name_suffix = Column(String(5), nullable=True)
    
    # Dates
    date_dob = Column(Date, nullable=True, index=True)
    date_dod = Column(Date, nullable=True)
    
    # Gender (if available)
    gender = Column(String(1), nullable=True)  # M, F, or other
    
    # Additional information
    is_alias_of_id = Column(Integer, ForeignKey("people_db_person.id"), nullable=True)
    fjc_id = Column(Integer, nullable=True, index=True)  # Federal Judicial Center ID
    
    # Relationships
    positions = relationship("Position", foreign_keys="Position.person_id", back_populates="person", cascade="all, delete-orphan")
    educations = relationship("Education", back_populates="person", cascade="all, delete-orphan")
    political_affiliations = relationship("PoliticalAffiliation", back_populates="person", cascade="all, delete-orphan")
    races = relationship("Race", back_populates="person", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="person", cascade="all, delete-orphan")
    
    # Self-referential relationship for aliases
    is_alias_of = relationship("Person", remote_side=[id], backref="aliases")
    
    def __repr__(self):
        return f"<Person(id={self.id}, name='{self.name_first} {self.name_last}')>"
    
    @property
    def name_full(self):
        """Construct full name from components."""
        parts = [self.name_first, self.name_middle, self.name_last, self.name_suffix]
        return " ".join(p for p in parts if p)

