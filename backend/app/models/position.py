"""
Position Model

Represents a judicial position held by a person.
"""
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class Position(Base):
    """
    Position model representing a judicial position.
    
    Links a person to a court with position details and dates.
    """
    __tablename__ = "people_db_position"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    person_id = Column(Integer, ForeignKey("people_db_person.id"), nullable=False, index=True)
    court_id = Column(String(50), ForeignKey("people_db_court.id"), nullable=True, index=True)  # String to match Court.id
    
    # Position details
    position_type = Column(String(100), nullable=True, index=True)  # e.g., "Associate Justice", "Chief Judge"
    job_title = Column(String(100), nullable=True)
    
    # Dates
    date_start = Column(Date, nullable=True, index=True)
    date_termination = Column(Date, nullable=True, index=True)
    date_granularity_start = Column(String(10), nullable=True)  # e.g., "year", "month", "day"
    date_granularity_termination = Column(String(10), nullable=True)
    
    # Selection method
    how_selected = Column(String(50), nullable=True)  # e.g., "Election", "Appointment"
    nomination_process = Column(String(100), nullable=True)
    
    # Termination reason
    termination_reason = Column(String(100), nullable=True)  # e.g., "Retirement", "Death", "Resignation"
    
    # Additional fields
    supervisor_id = Column(Integer, ForeignKey("people_db_person.id"), nullable=True)
    predecessor_id = Column(Integer, ForeignKey("people_db_person.id"), nullable=True)
    successor_id = Column(Integer, ForeignKey("people_db_person.id"), nullable=True)
    
    # Relationships
    person = relationship("Person", foreign_keys=[person_id], back_populates="positions")
    court = relationship("Court", back_populates="positions")
    supervisor = relationship("Person", foreign_keys=[supervisor_id], remote_side="Person.id", post_update=True)
    predecessor = relationship("Person", foreign_keys=[predecessor_id], remote_side="Person.id", post_update=True)
    successor = relationship("Person", foreign_keys=[successor_id], remote_side="Person.id", post_update=True)
    
    def __repr__(self):
        return f"<Position(id={self.id}, person_id={self.person_id}, court_id={self.court_id})>"
    
    @property
    def is_current(self):
        """Check if position is currently active."""
        if self.date_termination is None:
            return True
        return False

