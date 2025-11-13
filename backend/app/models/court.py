"""
Court Model

Represents a court in the legal system.
Matches the structure from CourtListener's people_db_court table.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, Date, DateTime, Float, SmallInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Court(Base):
    """
    Court model representing a court in the legal system.
    
    Courts can have parent courts (e.g., Circuit Courts under Supreme Court).
    Matches CourtListener's people_db_court table structure.
    """
    __tablename__ = "people_db_court"
    
    # Primary key - CourtListener uses string IDs (e.g., 'nc', 'ag')
    id = Column(String(15), primary_key=True, index=True)
    
    # Basic court information
    short_name = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=True)
    citation_string = Column(String(100), nullable=True)
    url = Column(String(500), nullable=True)
    jurisdiction = Column(String(3), nullable=True)
    
    # Dates
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # Hierarchy
    parent_court_id = Column(String(15), ForeignKey("people_db_court.id"), nullable=True)
    position = Column(Float, nullable=True)  # Display order
    
    # PACER integration fields
    pacer_court_id = Column(SmallInteger, nullable=True)
    pacer_has_rss_feed = Column(Boolean, nullable=True)
    pacer_rss_entry_types = Column(Text, nullable=True)
    date_last_pacer_contact = Column(DateTime(timezone=True), nullable=True)
    
    # FJC (Federal Judicial Center) ID
    fjc_court_id = Column(String(3), nullable=True)
    
    # Metadata
    date_modified = Column(DateTime(timezone=True), nullable=True)
    in_use = Column(Boolean, nullable=True)
    has_opinion_scraper = Column(Boolean, nullable=True)
    has_oral_argument_scraper = Column(Boolean, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    parent_court = relationship("Court", remote_side=[id], backref="child_courts")
    positions = relationship("Position", back_populates="court")
    dockets = relationship("Docket", back_populates="court", foreign_keys="[Docket.court_id]")
    
    # Backward compatibility properties
    @property
    def name(self):
        """Return short_name or full_name for backward compatibility."""
        return self.short_name or self.full_name or ""
    
    @property
    def name_abbreviation(self):
        """Return citation_string for backward compatibility."""
        return self.citation_string or ""

