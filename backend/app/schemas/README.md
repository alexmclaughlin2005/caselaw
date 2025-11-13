# Schemas - Documentation

## Purpose
The `schemas` directory contains Pydantic models for API request/response validation. These schemas define the structure of data sent to and received from the API.

## Planned Schemas

### `person.py`
**Purpose**: Person-related request/response schemas.

**Schemas**:
- `PersonBase`: Base fields shared across person schemas
- `PersonCreate`: Schema for creating a person (if needed)
- `PersonUpdate`: Schema for updating a person (if needed)
- `PersonResponse`: Schema for API responses with person data
- `PersonListResponse`: Schema for paginated person list responses

### `position.py`
**Purpose**: Position-related request/response schemas.

**Schemas**:
- `PositionBase`: Base fields
- `PositionResponse`: Response schema
- `PositionListResponse`: Paginated list response

### `school.py`
**Purpose**: School-related request/response schemas.

### `data_management.py`
**Purpose**: Data management request/response schemas.

**Schemas**:
- `DatasetInfo`: Information about available datasets
- `DownloadRequest`: Request to start a download
- `DownloadStatus`: Status of a download
- `ImportRequest`: Request to start an import
- `ImportStatus`: Status of an import
- `DatabaseStatus`: Current database status

### Common Schemas
- `PaginationParams`: Query parameters for pagination
- `FilterParams`: Query parameters for filtering
- `SortParams`: Query parameters for sorting

## Dependencies
- **Depends on**: 
  - `pydantic` for validation
  - Type definitions from models (for reference)
- **Used by**: 
  - API routes (for request/response validation)
  - Frontend (for type definitions, if shared)

## Integration
- Routes use schemas as `response_model` parameter
- Routes use schemas for request body validation
- Schemas are automatically documented in FastAPI's OpenAPI docs
- Schemas provide type hints for better IDE support

## Example Schema Structure
```python
from pydantic import BaseModel
from datetime import date
from typing import Optional

class PersonBase(BaseModel):
    name_first: Optional[str] = None
    name_last: Optional[str] = None

class PersonResponse(PersonBase):
    id: int
    date_dob: Optional[date] = None
    
    class Config:
        from_attributes = True
```

## Best Practices
- Use `BaseModel` for all schemas
- Use `Optional` for nullable fields
- Use `from_attributes = True` in Config for ORM model conversion
- Keep schemas focused and avoid deep nesting
- Use descriptive names (Response, Create, Update)

## Reference
See [AI_INSTRUCTIONS.md](../../AI_INSTRUCTIONS.md) for complete application overview.

