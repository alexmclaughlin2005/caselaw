# Models - Documentation

## Purpose
The `models` directory contains SQLAlchemy ORM models representing database tables. These models define the database schema and relationships.

## Planned Models

### `person.py` ✅ Implemented
**Purpose**: Person/Judge model.

**Table**: `people_db_person`

**Key Fields**:
- `id`: Primary key
- `name_first`, `name_middle`, `name_last`, `name_suffix`: Name components (indexed)
- `date_dob`, `date_dod`: Dates of birth and death (indexed)
- `gender`: Gender information
- `fjc_id`: Federal Judicial Center ID (indexed)
- `is_alias_of_id`: Self-referential for aliases

**Relationships**:
- One-to-many with `Position` (cascade delete)
- One-to-many with `Education` (cascade delete)
- One-to-many with `PoliticalAffiliation` (cascade delete)
- One-to-many with `Race` (cascade delete)
- One-to-many with `Source` (cascade delete)
- Self-referential for aliases

**Properties**:
- `name_full`: Constructs full name from components

### `position.py` ✅ Implemented
**Purpose**: Judicial position model.

**Table**: `people_db_position`

**Key Fields**:
- `id`: Primary key
- `person_id`: Foreign key to Person (indexed)
- `court_id`: Foreign key to Court (indexed)
- `position_type`: Type of position (indexed)
- `job_title`: Job title
- `date_start`, `date_termination`: Position dates (indexed)
- `date_granularity_start`, `date_granularity_termination`: Date precision
- `how_selected`: Selection method (e.g., "Election", "Appointment")
- `termination_reason`: Reason for termination
- `supervisor_id`, `predecessor_id`, `successor_id`: Related person references

**Relationships**:
- Many-to-one with `Person`
- Many-to-one with `Court`
- Many-to-one with supervisor, predecessor, successor (Person)

**Properties**:
- `is_current`: Checks if position is currently active

### `school.py`
**Purpose**: Educational institution model.

**Table**: `people_db_school`

**Key Fields**:
- `id`: Primary key
- `name`: School name
- `is_alias_of`: Reference to another school (if alias)

**Relationships**:
- One-to-many with `Education`

### `education.py`
**Purpose**: Education record linking people to schools.

**Table**: `people_db_education`

**Key Fields**:
- `id`: Primary key
- `person_id`: Foreign key to Person
- `school_id`: Foreign key to School
- `degree_level`: Level of degree
- `degree_year`: Year degree was awarded

**Relationships**:
- Many-to-one with `Person`
- Many-to-one with `School`

### Additional Models ✅ All Implemented

- `court.py`: Court information with parent court relationships
- `school.py`: Educational institutions with alias support
- `education.py`: Links people to schools with degree information
- `political_affiliation.py`: Political party affiliations over time
- `race.py`: Race/ethnicity information
- `source.py`: Source references with URLs and notes

## Dependencies
- **Depends on**: 
  - `Base` from `app.core.database`
  - Other models (for relationships)
- **Used by**: 
  - API routes (for queries)
  - Services (for data operations)
  - Alembic (for migrations)

## Integration
- Models inherit from `Base` (declarative base)
- Relationships are defined using SQLAlchemy's `relationship()`
- Foreign keys use `ForeignKey()` constraint
- Models are imported in `alembic/env.py` for migrations

## Example Model Structure
```python
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Person(Base):
    __tablename__ = "people_db_person"
    
    id = Column(Integer, primary_key=True)
    name_first = Column(String(50))
    name_last = Column(String(50))
    
    positions = relationship("Position", back_populates="person")
```

## Import Order
Models must be imported in dependency order for Alembic migrations:
1. Courts (no dependencies)
2. People (no dependencies)
3. Schools (no dependencies)
4. Positions (depends on people, courts)
5. Education (depends on people, schools)
6. Other dependent models

## Reference
See [AI_INSTRUCTIONS.md](../../AI_INSTRUCTIONS.md) for complete application overview.

