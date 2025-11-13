"""
Political Affiliation Model

Represents political party affiliations of people.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.core.database import Base


class PoliticalAffiliation(Base):
    """
    Political Affiliation model linking a person to a political party.
    
    People can have multiple political affiliations over time.
    """
    __tablename__ = "people_db_politicalaffiliation"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    person_id = Column(Integer, ForeignKey("people_db_person.id"), nullable=False, index=True)
    
    # Affiliation details
    political_party = Column(String(100), nullable=True, index=True)  # e.g., "Democratic", "Republican", "Independent"
    date_start = Column(Date, nullable=True, index=True)
    date_end = Column(Date, nullable=True)
    
    # Relationships
    person = relationship("Person", back_populates="political_affiliations")
    
    def __repr__(self):
        return f"<PoliticalAffiliation(id={self.id}, person_id={self.person_id}, party='{self.political_party}')>"

