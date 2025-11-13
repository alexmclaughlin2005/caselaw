"""
Parenthetical Model

Represents short summaries of opinions written by courts.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship
from app.core.database import Base


class Parenthetical(Base):
    """
    Parenthetical model representing short summaries of opinions.

    Parentheticals are brief descriptions of how a case was used
    in another opinion, typically in the format "(holding that...)".
    """
    __tablename__ = "search_parenthetical"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys - references opinions table
    described_opinion_id = Column(Integer, nullable=False, index=True)  # The opinion being described
    describing_opinion_id = Column(Integer, nullable=False, index=True)  # The opinion doing the describing

    # Parenthetical content
    text = Column(Text, nullable=False)  # The actual parenthetical text

    # Metadata
    score = Column(Float, nullable=True)  # Relevance/importance score
    group_id = Column(BigInteger, nullable=True, index=True)  # Groups related parentheticals

    def __repr__(self):
        return f"<Parenthetical(id={self.id}, described={self.described_opinion_id}, text={self.text[:50]}...)>"
