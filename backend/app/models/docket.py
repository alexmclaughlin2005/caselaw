"""
Docket Model

Represents a legal case docket with metadata.
"""
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, Boolean, SmallInteger, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class Docket(Base):
    """
    Docket model representing a legal case.

    A docket contains high-level case information and can have multiple
    opinion clusters associated with it.
    """
    __tablename__ = "search_docket"

    id = Column(Integer, primary_key=True, index=True)

    # Timestamp columns (from migration bc02f0ddd58f)
    date_created = Column(DateTime(timezone=True), nullable=True)
    date_modified = Column(DateTime(timezone=True), nullable=True)

    # Foreign keys
    court_id = Column(String(50), ForeignKey("people_db_court.id"), nullable=False, index=True)
    assigned_to_id = Column(Integer, ForeignKey("people_db_person.id"), nullable=True, index=True)
    referred_to_id = Column(Integer, ForeignKey("people_db_person.id"), nullable=True, index=True)
    appeal_from_id = Column(String(50), ForeignKey("people_db_court.id"), nullable=True)

    # Case identification
    docket_number = Column(Text, nullable=True, index=True)
    case_name = Column(Text, nullable=True)
    case_name_short = Column(Text, nullable=True)
    case_name_full = Column(Text, nullable=True)

    # Case details (from migration bc02f0ddd58f)
    cause = Column(String(2000), nullable=True)
    nature_of_suit = Column(String(1000), nullable=True)
    jury_demand = Column(String(500), nullable=True)
    jurisdiction_type = Column(String(100), nullable=True)

    # Dates
    date_filed = Column(Date, nullable=True, index=True)
    date_terminated = Column(Date, nullable=True)
    date_argued = Column(Date, nullable=True)
    date_reargued = Column(Date, nullable=True)
    date_reargument_denied = Column(Date, nullable=True)
    date_cert_granted = Column(Date, nullable=True)
    date_cert_denied = Column(Date, nullable=True)
    date_blocked = Column(Date, nullable=True)  # from migration cf47bd255dfb
    date_last_index = Column(DateTime(timezone=True), nullable=True)
    date_last_filing = Column(Date, nullable=True)

    # Source and metadata
    source = Column(SmallInteger, nullable=True)
    pacer_case_id = Column(String(100), nullable=True, index=True)
    slug = Column(String(75), nullable=True, index=True)

    # File paths (from migration bc02f0ddd58f)
    filepath_local = Column(String(1000), nullable=True)
    filepath_ia = Column(String(1000), nullable=True)
    filepath_ia_json = Column(String(1000), nullable=True)

    # String representations (from migration bc02f0ddd58f)
    assigned_to_str = Column(Text, nullable=True)
    referred_to_str = Column(Text, nullable=True)
    appeal_from_str = Column(Text, nullable=True)
    panel_str = Column(Text, nullable=True)

    # Appellate information (from migration bc02f0ddd58f)
    appellate_fee_status = Column(Text, nullable=True)
    appellate_case_type_information = Column(Text, nullable=True)

    # MDL and view tracking (from migration bc02f0ddd58f)
    mdl_status = Column(String(100), nullable=True)
    view_count = Column(Integer, nullable=True)

    # Internet Archive (from migration bc02f0ddd58f)
    ia_needs_upload = Column(Boolean, nullable=True)
    ia_upload_failure_count = Column(SmallInteger, nullable=True)
    ia_date_first_change = Column(DateTime(timezone=True), nullable=True)

    # Federal docket numbers (from migration bc02f0ddd58f)
    docket_number_core = Column(String(20), nullable=True)
    federal_dn_case_type = Column(String(6), nullable=True)
    federal_dn_judge_initials_assigned = Column(String(5), nullable=True)
    federal_dn_judge_initials_referred = Column(String(5), nullable=True)
    federal_dn_office_code = Column(String(3), nullable=True)

    # Additional fields (from migration bc02f0ddd58f)
    federal_defendant_number = Column(SmallInteger, nullable=True)
    parent_docket_id = Column(Integer, nullable=True)
    originating_court_information_id = Column(Integer, nullable=True)
    idb_data_id = Column(Integer, nullable=True)
    docket_number_raw = Column(String, nullable=True)

    # Status
    blocked = Column(Boolean, default=False, index=True)

    # Relationships
    court = relationship("Court", foreign_keys=[court_id], back_populates="dockets")
    assigned_to = relationship("Person", foreign_keys=[assigned_to_id])
    referred_to = relationship("Person", foreign_keys=[referred_to_id])
    appeal_from = relationship("Court", foreign_keys=[appeal_from_id])
    opinion_clusters = relationship("OpinionCluster", back_populates="docket", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Docket(id={self.id}, docket_number={self.docket_number}, case_name={self.case_name})>"
