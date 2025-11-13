"""
Database Models

SQLAlchemy ORM models representing database tables.
"""
from app.core.database import Base

# Import all models so Alembic can detect them
from app.models.court import Court
from app.models.person import Person
from app.models.position import Position
from app.models.school import School
from app.models.education import Education
from app.models.political_affiliation import PoliticalAffiliation
from app.models.race import Race
from app.models.source import Source
from app.models.docket import Docket
from app.models.opinion_cluster import OpinionCluster
from app.models.citation import Citation
from app.models.parenthetical import Parenthetical

__all__ = [
    "Base",
    "Court",
    "Person",
    "Position",
    "School",
    "Education",
    "PoliticalAffiliation",
    "Race",
    "Source",
    "Docket",
    "OpinionCluster",
    "Citation",
    "Parenthetical",
]

