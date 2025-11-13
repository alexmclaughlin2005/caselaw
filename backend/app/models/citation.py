"""
Citation Model

Maps citations between opinions (who cited whom).
"""
from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Citation(Base):
    """
    Citation model representing citation relationships between opinions.

    Links which opinion cited which other opinion and how deeply
    (depth indicates how many times cited).
    """
    __tablename__ = "search_opinionscited"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys - both reference opinions table
    citing_opinion_id = Column(Integer, nullable=False, index=True)
    cited_opinion_id = Column(Integer, nullable=False, index=True)

    # Citation metadata
    depth = Column(Integer, default=1)  # How many times cited
    score = Column(Float, nullable=True)  # Citation importance score

    def __repr__(self):
        return f"<Citation(citing={self.citing_opinion_id}, cited={self.cited_opinion_id}, depth={self.depth})>"
