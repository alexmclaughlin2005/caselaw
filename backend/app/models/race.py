"""
Race Model

Represents race/ethnicity information for people.
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Race(Base):
    """
    Race model linking a person to race/ethnicity information.
    
    People can have multiple race entries.
    """
    __tablename__ = "people_db_race"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    person_id = Column(Integer, ForeignKey("people_db_person.id"), nullable=False, index=True)
    
    # Race information
    race = Column(String(100), nullable=True, index=True)  # e.g., "White", "Black", "Hispanic", "Asian"
    
    # Relationships
    person = relationship("Person", back_populates="races")
    
    def __repr__(self):
        return f"<Race(id={self.id}, person_id={self.person_id}, race='{self.race}')>"

