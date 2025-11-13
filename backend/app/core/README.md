# Core Service - Documentation

## Purpose
The `core` service provides application-wide configuration and database connection management. It's the foundation that all other services depend on.

## Key Files

### `config.py`
**Purpose**: Loads and manages application configuration from environment variables.

**Key Components**:
- `Settings` class: Pydantic settings model that loads from `.env` file
- `settings` instance: Singleton instance used throughout the application

**Configuration Options**:
- Database connection string
- Redis connection URL
- CORS origins
- AWS S3 bucket configuration
- Data directory paths
- Logging levels

**Usage**:
```python
from app.core.config import settings

database_url = settings.DATABASE_URL
```

### `database.py`
**Purpose**: SQLAlchemy database engine, session factory, and dependency injection.

**Key Components**:
- `engine`: SQLAlchemy engine for database connections
- `SessionLocal`: Session factory for creating database sessions
- `Base`: Declarative base class for all models
- `get_db()`: FastAPI dependency function for database sessions

**Usage**:
```python
from app.core.database import Base, get_db
from fastapi import Depends
from sqlalchemy.orm import Session

@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    # Use db session here
    pass
```

## Dependencies
- **Depends on**: None (foundational service)
- **Used by**: All other services (models, API routes, services)

## Integration
- Models import `Base` from `database.py` to define tables
- API routes use `get_db()` dependency for database access
- Services import `settings` for configuration values

## Reference
See [AI_INSTRUCTIONS.md](../../AI_INSTRUCTIONS.md) for complete application overview.

