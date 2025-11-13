# AI System Prompt - CourtListener Database Browser

## Purpose
This document provides high-level instructions for AI coding assistants working on the CourtListener Database Browser project. It explains the application's purpose, architecture, and how to maintain documentation.

---

## Application Overview

The CourtListener Database Browser is a full-stack web application that:
1. Downloads bulk legal data from CourtListener's public S3 bucket
2. Imports the data into a PostgreSQL database with chunked processing for large datasets (70M+ records)
3. Provides real-time progress monitoring for data imports
4. Offers a web interface for browsing, searching, and visualizing the data

**Supported Databases**:
- **People/Judges Database**: Judges, their positions, education, and related data
- **Case Law Database**: Dockets, opinion clusters, citations, and parentheticals (70M+ records, 50+ GB)

**Key Features**:
- Chunked pandas import processing (50k rows per chunk) for memory efficiency
- Real-time import progress tracking with visual progress bars
- Database status dashboard showing record counts across all tables
- Manual progress refresh for on-demand updates

---

## High-Level Architecture

### Technology Stack
- **Backend**: FastAPI (Python) + SQLAlchemy + PostgreSQL
- **Frontend**: React + TypeScript + Shadcn/ui + TanStack Table
- **Infrastructure**: Docker Compose (PostgreSQL, Redis, Backend, Frontend)
- **Background Tasks**: Celery + Redis

### Application Structure
```
courtlistener-browser/
├── backend/          # FastAPI application
├── frontend/         # React application
├── data/             # Downloaded CSV files (volume mount)
└── docker-compose.yml
```

### Key Services
1. **S3 Downloader**: Downloads files from CourtListener's S3 bucket
2. **Data Importer**: Imports CSV files into PostgreSQL
3. **API Routes**: REST endpoints for frontend consumption
4. **Database Models**: SQLAlchemy models representing database tables
5. **Frontend Pages**: React pages for browsing data

---

## Documentation Requirements

### Master Documentation File
**File**: `AI_INSTRUCTIONS.md`

This is the central documentation file that:
- Provides complete application overview
- Maps all services and their purposes
- Documents data schema and relationships
- Lists all dependencies
- Explains service interactions
- Contains links to all service-specific documentation

**When to Update**: 
- When adding new services or major features
- When changing architecture or dependencies
- When adding new documentation files

### Service-Specific Documentation
**Location**: Each service/directory should have its own `README.md`

**Required Content**:
1. **Purpose**: What the service/directory does
2. **Key Files**: List of important files and their purposes
3. **Dependencies**: What other services it depends on
4. **Usage Examples**: How to use the service
5. **Integration**: How it connects with other services
6. **Reference**: Link back to `AI_INSTRUCTIONS.md`

**When to Create/Update**:
- When creating a new service or directory
- When adding significant functionality
- When changing how a service works

### Project Plan
**File**: `courtlistener-db-browser-project-plan.md`

This file tracks:
- Project phases and tasks
- Completed items (checkboxes)
- Technical considerations
- Progress milestones

**When to Update**:
- Mark tasks as complete when finished
- Add notes about implementation decisions
- Update progress milestones

---

## How to Create Documentation Files

### For New Services/Directories

1. **Create README.md** in the service directory:
   ```markdown
   # [Service Name] - Documentation
   
   ## Purpose
   [What this service does]
   
   ## Key Files
   - `file1.py`: [Purpose]
   - `file2.py`: [Purpose]
   
   ## Dependencies
   - Depends on: [Other services]
   - Used by: [Other services]
   
   ## Usage
   [Code examples]
   
   ## Integration
   [How it connects with other services]
   
   ## Reference
   See [AI_INSTRUCTIONS.md](../../AI_INSTRUCTIONS.md) for complete application overview.
   ```

2. **Update AI_INSTRUCTIONS.md**:
   - Add service to "Service Architecture" section
   - Add to "Service Documentation Map"
   - Update "Service Interactions" if needed
   - Add to "Dependencies & Libraries" if new dependencies

3. **Update Project Plan**:
   - Mark relevant tasks as complete
   - Add implementation notes if significant

### Documentation Standards

- **Be Specific**: Explain what, why, and how
- **Include Examples**: Show code examples when helpful
- **Link References**: Link to related documentation
- **Keep Updated**: Update docs when code changes
- **Use Clear Structure**: Use headers, lists, and code blocks

---

## File and Folder Purposes

### Backend (`backend/`)

**`app/core/`**: Application configuration and database setup
- `config.py`: Environment variables and settings
- `database.py`: Database connection and session management

**`app/models/`**: SQLAlchemy ORM models
- Each model file represents a database table
- Defines relationships between tables

**`app/schemas/`**: Pydantic validation schemas
- Request/response validation for API endpoints
- Type definitions for API contracts

**`app/api/routes/`**: HTTP endpoint definitions
- REST API routes for frontend consumption
- Handles HTTP requests and responses

**`app/services/`**: Business logic and external integrations
- S3 downloader, data importer, validators
- Contains reusable business logic

**`alembic/`**: Database migrations
- Version control for database schema changes

**`tests/`**: Backend test files

### Frontend (`frontend/`)

**`src/components/`**: Reusable React components
- `tables/`: Data table components
- `forms/`: Form input components
- `common/`: Shared UI components

**`src/pages/`**: Main application pages
- Each page represents a route/feature

**`src/services/`**: API client and external services
- Centralized API communication

**`src/hooks/`**: Custom React hooks
- Reusable stateful logic

**`src/types/`**: TypeScript type definitions
- Type definitions for data structures

### Infrastructure

**`docker-compose.yml`**: Container orchestration
- Defines all services (PostgreSQL, Redis, Backend, Frontend)
- Volume mounts and networking

**`data/`**: Volume mount for downloaded CSV files
- Persists downloaded data between container restarts

**`.env`**: Environment variables (not in git)
- Database credentials, API keys, configuration

---

## Development Guidelines

### Code Organization
- Follow existing patterns and structure
- Keep services focused on single responsibilities
- Use dependency injection (FastAPI's Depends)
- Type hints in Python, TypeScript types in frontend

### Error Handling
- Consistent error responses across API
- Proper error boundaries in React
- Log errors appropriately

### Testing
- Write tests for new features
- Test API endpoints
- Test React components

### Git Workflow
- Commit frequently with clear messages
- Update documentation with code changes
- Keep project plan updated

---

## Key Principles

1. **Documentation First**: Create/update docs when adding features
2. **Consistency**: Follow existing patterns and conventions
3. **Type Safety**: Use types everywhere (TypeScript, Pydantic)
4. **Separation of Concerns**: Clear boundaries between layers
5. **User Experience**: Build intuitive, performant interfaces
6. **Maintainability**: Write clear, documented, testable code

---

## Quick Reference

- **Master Documentation**: `AI_INSTRUCTIONS.md`
- **Data Management Guide**: `DATA_MANAGEMENT.md` (comprehensive import/download documentation)
- **Project Plan**: `courtlistener-db-browser-project-plan.md`
- **Backend Entry**: `backend/app/main.py`
- **Frontend Entry**: `frontend/src/main.tsx`
- **Database Config**: `backend/app/core/database.py`
- **API Routes**: `backend/app/api/routes/`
- **Services**: `backend/app/services/`
- **Data Importer**: `backend/app/services/data_importer.py` (chunked processing)

---

## Recent Enhancements (2025)

### Import Progress Monitoring
Added real-time import progress tracking for case law data:

**Backend** (`backend/app/api/routes/data_management.py`):
- New endpoint: `GET /api/data/import-progress`
- Returns current vs. expected row counts for all 4 case law tables
- Calculates progress percentages based on CSV file sizes
- Expected totals: Dockets (70M), OpinionClusters (75M), Citations (76M), Parentheticals (6M)

**Frontend** (`frontend/src/pages/DataManagement.tsx`):
- "Case Law Import Progress" card with visual progress bars
- Manual refresh button for on-demand updates
- Color-coded status badges (pending/importing/completed)
- Progress display: current_count / expected_count with percentage

**Schemas** (`backend/app/schemas/data_management.py`, `frontend/src/types/dataManagement.ts`):
- `TableImportProgress`: Includes expected_count and progress_percent fields
- `ImportProgressResponse`: Structured response for all 4 tables

**Hooks** (`frontend/src/hooks/useDataManagement.ts`):
- `useImportProgress()`: React Query hook with manual refresh only
- Config: `staleTime: Infinity`, `refetchOnWindowFocus: false`

### Chunked Import Processing
Enhanced data importer for large datasets (backend/app/services/data_importer.py):
- Method: `import_csv_with_postgres_copy()` for case law tables
- Chunk size: 50,000 rows per iteration
- Periodic commits: Every 1,000,000 rows (20 chunks)
- Error handling: Skip malformed lines with `on_bad_lines='skip'`
- Memory efficient: Suitable for 25+ GB CSV files

---

**For AI Agents**: Always read `AI_INSTRUCTIONS.md` first to understand the complete application structure before making changes. Update relevant documentation files when modifying code. See `DATA_MANAGEMENT.md` for detailed information about data import features.

