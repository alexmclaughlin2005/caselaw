# AI Instructions - CourtListener Database Browser

## Table of Contents
1. [Application Overview](#application-overview)
2. [Project Structure](#project-structure)
3. [Service Architecture](#service-architecture)
4. [Data Schema](#data-schema)
5. [Service Documentation Map](#service-documentation-map)
6. [Dependencies & Libraries](#dependencies--libraries)
7. [Service Interactions](#service-interactions)
8. [Development Workflow](#development-workflow)

---

## Application Overview

The CourtListener Database Browser is a full-stack web application designed to download, import, and visualize legal data from CourtListener's bulk data repository. The application focuses on the People/Judges database, providing a comprehensive interface for browsing judges, their positions, education, and related information.

### Core Functionality
1. **Data Download**: Downloads bulk data files from CourtListener's public S3 bucket (`com-courtlistener-storage/bulk-data/`)
2. **Data Import**: Imports CSV data into PostgreSQL database with proper relationship handling
3. **Data Visualization**: Provides web-based interface for browsing, searching, and filtering legal data
4. **Data Management**: Tools for managing downloads, imports, and database updates
5. **Citation Analysis**: Interactive exploration of citation networks between legal opinions

### Technology Stack
- **Backend**: FastAPI (Python), SQLAlchemy (ORM), PostgreSQL 15+
- **Frontend**: React 18+ with TypeScript, Shadcn/ui, TanStack Table, TanStack Query
- **Infrastructure**: Docker Compose, Redis (Celery), PostgreSQL
- **Data Processing**: boto3 (S3), Celery (background tasks)

### Key Features Implemented
1. **Dockets Browser**: Search and browse 34.9M court cases with filtering and pagination
2. **Opinions Browser**: Search and browse 7.2K legal opinions with citation statistics
3. **Citation Network**: Interactive drill-down into citation relationships (48.3M citations)
   - View all cases citing an opinion (up to 500 results)
   - View all cases cited by an opinion (up to 500 results)
   - Lazy loading and caching for performance
   - See [CITATION_FEATURES.md](CITATION_FEATURES.md) for detailed documentation
4. **Detail Drawers**: Slide-out panels with full case/opinion information
5. **Data Management**: Download and import bulk data from CourtListener
6. **People Database**: Browse 16K judges with positions, education, and affiliations

---

## Project Structure

```
courtlistener-browser/
├── AI_INSTRUCTIONS.md          # Master documentation (this file)
├── AI_System_Prompt.md          # High-level system instructions
├── courtlistener-db-browser-project-plan.md  # Project plan with progress tracking
├── README.md                    # User-facing documentation
├── docker-compose.yml           # Docker orchestration
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
│
├── backend/                     # FastAPI backend application
│   ├── app/
│   │   ├── main.py             # FastAPI application entry point
│   │   ├── core/               # Core configuration and database setup
│   │   │   ├── config.py      # Application configuration
│   │   │   └── database.py    # Database connection and session management
│   │   ├── models/             # SQLAlchemy database models
│   │   │   ├── __init__.py
│   │   │   ├── person.py      # Person/Judge model
│   │   │   ├── position.py    # Position model
│   │   │   ├── school.py      # School model
│   │   │   ├── education.py   # Education model
│   │   │   └── [other models]
│   │   ├── schemas/            # Pydantic schemas for API validation
│   │   │   ├── __init__.py
│   │   │   ├── person.py
│   │   │   ├── position.py
│   │   │   └── [other schemas]
│   │   ├── api/                # API routes
│   │   │   ├── routes/
│   │   │   │   ├── people.py  # People endpoints
│   │   │   │   ├── positions.py
│   │   │   │   ├── schools.py
│   │   │   │   └── data_management.py
│   │   │   └── deps.py        # Dependency injection
│   │   └── services/           # Business logic services
│   │       ├── s3_downloader.py    # S3 file download service
│   │       ├── data_importer.py    # CSV import service
│   │       └── data_validator.py   # Data validation service
│   ├── alembic/                # Database migrations
│   ├── tests/                  # Backend tests
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile             # Backend container definition
│
├── frontend/                    # React frontend application
│   ├── src/
│   │   ├── App.tsx             # Main application component
│   │   ├── main.tsx            # Application entry point
│   │   ├── components/         # React components
│   │   │   ├── tables/         # Table components
│   │   │   ├── forms/          # Form components
│   │   │   └── common/         # Common/shared components
│   │   ├── pages/              # Page components
│   │   │   ├── People.tsx
│   │   │   ├── Positions.tsx
│   │   │   ├── Schools.tsx
│   │   │   └── DataManagement.tsx
│   │   ├── services/           # API client services
│   │   │   └── api.ts          # API client configuration
│   │   ├── hooks/              # Custom React hooks
│   │   ├── types/              # TypeScript type definitions
│   │   └── lib/                # Utility libraries
│   ├── package.json            # Node.js dependencies
│   └── Dockerfile              # Frontend container definition
│
└── data/                       # Volume mount for downloaded CSV files
```

---

## Service Architecture

### Backend Services

#### 1. Core Service (`backend/app/core/`)
**Purpose**: Application configuration and database connection management

**Files**:
- `config.py`: Loads environment variables, defines application settings
- `database.py`: SQLAlchemy engine, session factory, database dependency injection

**Documentation**: See `backend/app/core/README.md`

#### 2. Models (`backend/app/models/`)
**Purpose**: SQLAlchemy ORM models representing database tables

**Key Models**:
- `Person`: Judges and legal professionals
- `Position`: Judicial positions held by people
- `School`: Educational institutions
- `Education`: Education records linking people to schools
- `Court`: Court information
- `PoliticalAffiliation`: Political party affiliations
- `Race`: Race/ethnicity information
- `Source`: Source references for data

**Documentation**: See `backend/app/models/README.md`

#### 3. API Routes (`backend/app/api/routes/`)
**Purpose**: HTTP endpoints for frontend consumption

**Route Modules**:
- `people.py`: `/api/people/*` endpoints
- `positions.py`: `/api/positions/*` endpoints
- `schools.py`: `/api/schools/*` endpoints
- `data_management.py`: `/api/data/*` endpoints for downloads/imports

**Documentation**: See `backend/app/api/README.md`

#### 4. Services (`backend/app/services/`)
**Purpose**: Business logic and external integrations

**Services**:
- `s3_downloader.py`: Downloads files from CourtListener S3 bucket (✅ Implemented)
  - Handles `.csv.bz2` compressed files with automatic decompression
  - Maps S3 filenames to database table names (e.g., `people-db-people` → `people_db_person`)
  - Includes `people_db_court` table support
- `data_importer.py`: Imports CSV files into PostgreSQL using pandas (✅ Implemented)
  - Uses pandas `to_sql()` for robust CSV handling (handles malformed CSV with unquoted carriage returns)
  - Automatically filters CSV columns to match database schema
  - Column mapping and validation
- `data_validator.py`: Validates data integrity (✅ Implemented)

**Documentation**: See `backend/app/services/README.md`

#### 5. Tasks (`backend/app/tasks/`)
**Purpose**: Celery background tasks for long-running operations

**Task Modules**:
- `download_tasks.py`: Background tasks for S3 downloads (✅ Implemented)
- `import_tasks.py`: Background tasks for data imports (⏳ Phase 3)

**Documentation**: See `backend/app/tasks/README.md`

### Frontend Services

#### 1. API Client (`frontend/src/services/api.ts`)
**Purpose**: Centralized API communication layer

**Features**:
- Axios instance with base URL configuration
- Request/response interceptors
- Error handling
- Type-safe API calls

**Documentation**: See `frontend/src/services/README.md`

#### 2. Components (`frontend/src/components/`)
**Purpose**: Reusable UI components

**Component Categories**:
- `tables/`: Data table components using TanStack Table
- `forms/`: Form input components
- `common/`: Shared UI components (buttons, cards, etc.)

**Documentation**: See `frontend/src/components/README.md`

#### 3. Pages (`frontend/src/pages/`)
**Purpose**: Main application pages/routes

**Pages**:
- `People.tsx`: Browse and search people/judges
- `Positions.tsx`: Browse judicial positions
- `Schools.tsx`: Browse educational institutions
- `DataManagement.tsx`: Manage downloads and imports

**Documentation**: See `frontend/src/pages/README.md`

---

## Data Schema

### Database: PostgreSQL 15+

The database schema mirrors CourtListener's People database structure. Key tables and relationships:

#### Core Tables

**people_db_person**
- Primary table for judges and legal professionals
- Fields: id, name_first, name_middle, name_last, name_suffix, date_dob, date_dod, etc.
- Relationships: One-to-many with positions, education, political_affiliations, races, sources

**people_db_position**
- Judicial positions held by people
- Fields: id, person_id, court_id, position_type, date_start, date_termination, etc.
- Relationships: Many-to-one with person, many-to-one with court

**people_db_school**
- Educational institutions
- Fields: id, name, is_alias_of, etc.
- Relationships: One-to-many with education records

**people_db_education**
- Links people to schools
- Fields: id, person_id, school_id, degree_level, degree_year, etc.
- Relationships: Many-to-one with person, many-to-one with school

**people_db_court**
- Court information (matches CourtListener's structure)
- Fields: id (String, e.g., 'nc', 'ag'), short_name, full_name, citation_string, url, jurisdiction, start_date, end_date, parent_court_id (String), position (Float), pacer_court_id, pacer_has_rss_feed, pacer_rss_entry_types, date_last_pacer_contact, fjc_court_id, date_modified, in_use, has_opinion_scraper, has_oral_argument_scraper, notes
- Relationships: One-to-many with positions, self-referential (parent courts)
- Note: Uses string IDs (not integer) matching CourtListener's schema

**people_db_politicalaffiliation**
- Political party affiliations
- Fields: id, person_id, political_party, date_start, date_end
- Relationships: Many-to-one with person

**people_db_race**
- Race/ethnicity information
- Fields: id, person_id, race
- Relationships: Many-to-one with person

**people_db_source**
- Source references
- Fields: id, person_id, url, notes
- Relationships: Many-to-one with person

### Import Order (Foreign Key Dependencies)
1. Courts (no dependencies)
2. People (no dependencies)
3. Schools (no dependencies)
4. Positions (depends on people, courts)
5. Education (depends on people, schools)
6. Political Affiliations (depends on people)
7. Races (depends on people)
8. Sources (depends on people)

**Documentation**: See `backend/app/models/README.md` for detailed schema documentation

---

## Service Documentation Map

Each service and major directory has its own README.md file that describes:
- Purpose and responsibilities
- Key functions/classes
- Dependencies
- Usage examples
- How it integrates with other services

### Documentation Files

1. **Master Documentation** (this file)
   - `AI_INSTRUCTIONS.md` - Complete application overview

2. **System Instructions**
   - `AI_System_Prompt.md` - High-level instructions for AI agents

3. **Feature Documentation**
   - `CITATION_FEATURES.md` - Citation network drill-down feature (detailed implementation guide)
   - `DATA_MANAGEMENT.md` - Data download and import features

4. **Backend Documentation**
   - `backend/app/core/README.md` - Configuration and database setup
   - `backend/app/models/README.md` - Database models and schema
   - `backend/app/api/README.md` - API routes and endpoints
   - `backend/app/services/README.md` - Business logic services
   - `backend/app/schemas/README.md` - Pydantic validation schemas
   - `backend/app/tasks/README.md` - Celery background tasks

5. **Frontend Documentation**
   - `frontend/src/services/README.md` - API client service
   - `frontend/src/components/README.md` - React components
   - `frontend/src/pages/README.md` - Page components

6. **Infrastructure Documentation**
   - `docker-compose.yml` - Container orchestration (comments)
   - `README.md` - User-facing setup and usage guide

---

## Dependencies & Libraries

### Backend Dependencies

**Core Framework**:
- `fastapi`: Web framework for building APIs
- `uvicorn`: ASGI server for FastAPI
- `pydantic`: Data validation using Python type annotations

**Database**:
- `sqlalchemy`: ORM for database interactions
- `alembic`: Database migration tool
- `psycopg2-binary`: PostgreSQL adapter
- `asyncpg`: Async PostgreSQL driver (optional, for async operations)

**Data Processing**:
- `boto3`: AWS SDK for S3 downloads (✅ Used)
- `pandas`: Data manipulation and CSV import (✅ Used - handles malformed CSV files)
- `celery`: Distributed task queue (✅ Configured - uses `--pool=solo` to avoid forking issues)
- `redis`: Celery broker and caching (✅ Configured)

**Utilities**:
- `python-dotenv`: Environment variable management
- `python-multipart`: File upload support

### Frontend Dependencies

**Core Framework**:
- `react`: UI library
- `react-dom`: React DOM renderer
- `typescript`: Type-safe JavaScript
- `vite`: Build tool and dev server

**UI Libraries**:
- `shadcn/ui`: Component library
- `tailwindcss`: Utility-first CSS framework
- `@radix-ui/*`: Headless UI primitives (used by shadcn)

**Data Management**:
- `@tanstack/react-table`: Powerful table component
- `@tanstack/react-query`: Server state management with polling
  - Download status: Polls every 2 seconds when downloading/pending
  - Import status: Polls every 2 seconds when importing/pending
  - Database status: Polls every 10 seconds
  - Datasets list: Polls every 30 seconds
- `axios`: HTTP client

**Routing**:
- `react-router-dom`: Client-side routing

**Visualization** (optional):
- `recharts`: Chart library
- `react-vis`: Timeline/visualization components

### Infrastructure
- `docker`: Containerization
- `docker-compose`: Multi-container orchestration
- `postgresql`: Database server
- `redis`: Cache and task queue broker

---

## Service Interactions

### Data Flow

1. **Download Flow**:
   ```
   Frontend → API Route (data_management.py) → S3 Downloader Service → S3 Bucket
                                                      ↓
                                              Local File Storage (data/)
   ```

2. **Import Flow**:
   ```
   Frontend → API Route (data_management.py) → Celery Task → Data Importer Service
                                                                     ↓
                                                           Pandas CSV Reader
                                                                     ↓
                                                           PostgreSQL Database (via to_sql)
   ```
   
   **Import Process**:
   - CSV files are read using pandas (handles malformed CSV with unquoted carriage returns)
   - Columns are filtered to match database schema (CSV may have extra columns)
   - Data is inserted using pandas `to_sql()` with standard INSERT statements (not COPY)
   - Import order respects foreign key dependencies

3. **Query Flow**:
   ```
   Frontend → API Route (people.py/positions.py/etc.) → SQLAlchemy Models → PostgreSQL
                                                              ↓
                                                         JSON Response → Frontend
   ```

### Service Dependencies

- **API Routes** depend on:
  - Models (for database queries)
  - Schemas (for request/response validation)
  - Services (for business logic)
  - Database session (from core/database.py)

- **Services** depend on:
  - Database session (for data operations)
  - Configuration (from core/config.py)
  - External APIs (S3, etc.)

- **Models** depend on:
  - SQLAlchemy Base (from core/database.py)
  - Other models (for relationships)

- **Frontend** depends on:
  - API Client (for backend communication)
  - Components (for UI)
  - Types (for TypeScript type safety)

---

## Development Workflow

### Setting Up Development Environment

1. **Clone and Setup**:
   ```bash
   git clone [repository]
   cd courtlistener-browser
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start Services**:
   ```bash
   docker-compose up -d
   ```

3. **Run Migrations**:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

4. **Access Services**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001 (changed from 8000 due to port conflict)
   - API Docs: http://localhost:8001/docs
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379
   - Celery Worker: Runs in background (check logs with `tail -f celery.log`)

### Adding New Features

1. **Backend API Endpoint**:
   - Add route in `backend/app/api/routes/`
   - Add schema in `backend/app/schemas/`
   - Update service if needed in `backend/app/services/`
   - Update `backend/app/api/README.md`

2. **Database Model**:
   - Add model in `backend/app/models/`
   - Create Alembic migration: `alembic revision --autogenerate -m "description"`
   - Update `backend/app/models/README.md`

3. **Frontend Page/Component**:
   - Add component in `frontend/src/components/` or `frontend/src/pages/`
   - Add API call in `frontend/src/services/api.ts` if needed
   - Update relevant README.md files

4. **Documentation**:
   - Update `AI_INSTRUCTIONS.md` if adding new service
   - Update service-specific README.md
   - Update project plan with completed tasks

### Testing

- Backend tests: `docker-compose exec backend pytest`
- Frontend tests: `docker-compose exec frontend npm test`
- Integration tests: See `tests/` directories

---

## Key Design Principles

1. **Separation of Concerns**: Clear boundaries between API routes, services, and models
2. **Type Safety**: TypeScript on frontend, Pydantic schemas on backend
3. **Documentation**: Every service has its own README.md
4. **Dependency Injection**: Use FastAPI's dependency system for database sessions
5. **Error Handling**: Consistent error responses across all endpoints
6. **Performance**: Use connection pooling, caching, and efficient queries
7. **Scalability**: Background tasks for long-running operations (downloads/imports)

---

## Notes for AI Agents

- Always check `AI_INSTRUCTIONS.md` first to understand the application structure
- When modifying a service, update its README.md file
- Follow the project plan in `courtlistener-db-browser-project-plan.md`
- Update the project plan checklist as tasks are completed
- Maintain consistency with existing code patterns
- All new services/directories should have their own README.md
- README.md files should reference back to `AI_INSTRUCTIONS.md`

---

## Known Issues & Solutions

### Import Issues
1. **Segmentation Fault (SIGSEGV)**: Fixed by:
   - Removing `inspect(engine)` calls (causes crashes in Celery workers)
   - Using `--pool=solo` for Celery (avoids forking issues)
   - Using pandas instead of direct COPY command

2. **CSV Format Issues**: Fixed by:
   - Using pandas `read_csv()` with `on_bad_lines='skip'` and `engine='python'`
   - Filtering CSV columns to match database schema
   - Using pandas `to_sql()` instead of PostgreSQL COPY (more forgiving)

3. **Column Mismatches**: Fixed by:
   - Automatically detecting database columns
   - Filtering DataFrame to only include columns that exist in database
   - Warning about missing columns

### Frontend Polling
- Status endpoints are polled frequently for real-time updates
- This creates recurring network requests visible in browser DevTools
- Polling intervals:
  - Active downloads/imports: 2 seconds
  - Database status: 10 seconds
  - Datasets list: 30 seconds
- Polling stops when operations complete

### Port Configuration
- Backend port changed from 8000 to 8001 (due to port conflict)
- All configuration files updated accordingly

---

## Recent Updates

### Version 1.2.0 (January 12, 2025)
- Added citation network drill-down feature in OpinionDetailDrawer
- Implemented lazy loading for citing/cited opinions lists
- Added ChevronUp and ChevronDown icons for expand/collapse UI
- Created comprehensive citation features documentation (CITATION_FEATURES.md)
- Enhanced OpinionDetailDrawer with clickable citation cards
- Added support for up to 500 citing/cited cases per opinion

### Version 1.1.0 (November 11, 2025)
- Initial implementation of Dockets and Opinions browsers
- Added detail drawers for dockets and opinions
- Implemented citation statistics API endpoints
- Fixed text alignment and visibility issues

---

**Last Updated**: January 12, 2025
**Version**: 1.2.0

