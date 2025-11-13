"""
Source Model

Represents source references for person data.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Source(Base):
    """
    Source model linking a person to source references.
    
    Stores URLs and notes about data sources.
    """
    __tablename__ = "people_db_source"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    person_id = Column(Integer, ForeignKey("people_db_person.id"), nullable=False, index=True)
    
    # Source information
    url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    date_accessed = Column(String(50), nullable=True)
    
    # Relationships
    person = relationship("Person", back_populates="sources")
    
    def __repr__(self):
        return f"<Source(id={self.id}, person_id={self.person_id}, url='{self.url[:50] if self.url else None}')>"

