# API Routes - Documentation

## Purpose
The `api` directory contains all HTTP endpoint definitions for the FastAPI backend. Routes are organized by resource type.

## Directory Structure

### `routes/`
**Purpose**: Individual route modules for different resources.

**Route Modules**:
- `people.py`: `/api/people/*` endpoints for people/judges
- `positions.py`: `/api/positions/*` endpoints for positions
- `schools.py`: `/api/schools/*` endpoints for schools
- `data_management.py`: `/api/data/*` endpoints for downloads and imports

### `deps.py`
**Purpose**: Common dependencies used across routes (e.g., database session).

## Planned Endpoints

### People Endpoints (`/api/people`)
- `GET /api/people` - List people (paginated, searchable)
- `GET /api/people/{id}` - Get person details
- `GET /api/people/search` - Full-text search
- `GET /api/people/{id}/positions` - Get person's positions
- `GET /api/people/{id}/education` - Get person's education
- `GET /api/people/stats` - Statistics

### Positions Endpoints (`/api/positions`)
- `GET /api/positions` - List positions (with filters)
- `GET /api/positions/{id}` - Get position details
- `GET /api/positions/by-court/{court_id}` - Positions by court

### Schools Endpoints (`/api/schools`)
- `GET /api/schools` - List schools
- `GET /api/schools/{id}` - Get school details
- `GET /api/schools/{id}/alumni` - Get people who attended

### Data Management Endpoints (`/api/data`)
- `GET /api/data/status` - Current database status
- `POST /api/data/import` - Start import process
- `GET /api/data/import/status` - Check import progress
- `POST /api/data/validate` - Run validation checks
- `GET /api/data/datasets` - List available datasets
- `POST /api/data/download` - Start download

## Dependencies
- **Depends on**: 
  - Models (for database queries)
  - Schemas (for request/response validation)
  - Services (for business logic)
  - Database session (from `deps.py`)
- **Used by**: Frontend application

## Integration
- Routes are registered in `app/main.py`
- Routes use dependency injection for database sessions
- Routes validate requests/responses using Pydantic schemas
- Routes call services for business logic

## Example Route Structure
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.person import PersonResponse
from app.models.person import Person

router = APIRouter()

@router.get("/", response_model=list[PersonResponse])
def get_people(db: Session = Depends(get_db)):
    return db.query(Person).all()
```

## Reference
See [AI_INSTRUCTIONS.md](../../AI_INSTRUCTIONS.md) for complete application overview.

