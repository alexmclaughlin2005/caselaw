"""
Opinion Cluster Model

Groups related opinions together (majority, dissent, concurrence).
"""
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, Boolean, SmallInteger
from sqlalchemy.orm import relationship
from app.core.database import Base


class OpinionCluster(Base):
    """
    Opinion Cluster model grouping related opinions.

    Serves the purpose of grouping dissenting and concurring opinions together.
    Contains metadata about the opinion(s) that it groups together.
    """
    __tablename__ = "search_opinioncluster"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    docket_id = Column(Integer, ForeignKey("search_docket.id"), nullable=False, index=True)

    # Case information
    case_name = Column(Text, nullable=True)
    case_name_short = Column(Text, nullable=True)
    case_name_full = Column(Text, nullable=True)

    # Dates
    date_filed = Column(Date, nullable=True, index=True)
    date_argued = Column(Date, nullable=True)
    date_reargued = Column(Date, nullable=True)
    date_reargument_denied = Column(Date, nullable=True)
    date_created = Column(Date, nullable=True)
    date_modified = Column(Date, nullable=True)
    date_filed_is_approximate = Column(Boolean, nullable=True)
    date_blocked = Column(Date, nullable=True)

    # Opinion metadata
    judges = Column(Text, nullable=True)  # Text representation of judges
    attorneys = Column(Text, nullable=True)
    nature_of_suit = Column(Text, nullable=True)
    posture = Column(Text, nullable=True)
    syllabus = Column(Text, nullable=True)
    headnotes = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    headmatter = Column(Text, nullable=True)
    procedural_history = Column(Text, nullable=True)
    disposition = Column(Text, nullable=True)
    history = Column(Text, nullable=True)
    other_dates = Column(Text, nullable=True)
    cross_reference = Column(Text, nullable=True)
    correction = Column(Text, nullable=True)
    arguments = Column(Text, nullable=True)

    # Source and identifiers
    source = Column(String(10), nullable=True)
    scdb_id = Column(String(10), nullable=True, index=True)  # Supreme Court Database ID
    scdb_decision_direction = Column(String(50), nullable=True)
    scdb_votes_majority = Column(Integer, nullable=True)
    scdb_votes_minority = Column(Integer, nullable=True)

    # Status
    precedential_status = Column(String(50), nullable=True, index=True)
    blocked = Column(Boolean, default=False, index=True)
    citation_count = Column(Integer, default=0, index=True)

    # Slugs and URLs
    slug = Column(String(75), nullable=True, index=True)

    # Harvard file paths
    filepath_json_harvard = Column(Text, nullable=True)
    filepath_pdf_harvard = Column(Text, nullable=True)

    # Relationships
    docket = relationship("Docket", back_populates="opinion_clusters")
    # Note: Opinion model not implemented (Option 1: metadata only)

    def __repr__(self):
        return f"<OpinionCluster(id={self.id}, case_name={self.case_name}, date_filed={self.date_filed})>"
