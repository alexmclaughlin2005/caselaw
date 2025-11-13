# CourtListener Database Browser - Project Plan

## Project Overview
Build an application to download CourtListener's bulk legal data (focusing on the People/Judges database), load it into a PostgreSQL database, and provide a web-based frontend for browsing and querying the data.

## Data Source Information
- **S3 Bucket**: `com-courtlistener-storage/bulk-data/`
- **Format**: PostgreSQL CSV dumps with UTF-8 encoding
- **Update Frequency**: Monthly (last day of each month)
- **Key Tables**: Person, Position, School, Education, Political Affiliation, Race, Source, Courts
- **Size**: Multi-GB dataset (compressed)

---

## Phase 1: Project Setup & Architecture (Week 1)

### 1.1 Technology Stack Selection
**Backend:**
- **Database**: PostgreSQL 15+ (matches source database)
- **API Framework**: FastAPI (Python) - for rapid development and automatic OpenAPI docs
- **ORM**: SQLAlchemy (for database interactions)
- **Data Download**: boto3 (AWS S3 SDK)
- **Task Queue**: Celery + Redis (for background downloads/imports)

**Frontend:**
- **Framework**: React 18+ with TypeScript
- **UI Library**: Shadcn/ui + Tailwind CSS (modern, accessible components)
- **Data Grid**: TanStack Table (formerly React Table) - for powerful table views
- **State Management**: TanStack Query (for API data caching)
- **Routing**: React Router v6

**Infrastructure:**
- **Containerization**: Docker + Docker Compose
- **Storage**: Local volume mounts for downloaded files
- **Development**: Hot reload for both frontend and backend

### 1.2 Project Structure
```
courtlistener-browser/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── people.py
│   │   │   │   ├── positions.py
│   │   │   │   ├── schools.py
│   │   │   │   └── data_management.py
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   ├── person.py
│   │   │   ├── position.py
│   │   │   ├── school.py
│   │   │   └── education.py
│   │   ├── schemas/
│   │   │   └── [pydantic models]
│   │   ├── services/
│   │   │   ├── s3_downloader.py
│   │   │   ├── data_importer.py
│   │   │   └── data_validator.py
│   │   └── main.py
│   ├── alembic/  # Database migrations
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── tables/
│   │   │   ├── forms/
│   │   │   └── common/
│   │   ├── pages/
│   │   │   ├── People.tsx
│   │   │   ├── Positions.tsx
│   │   │   ├── Schools.tsx
│   │   │   └── DataManagement.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── hooks/
│   │   ├── types/
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── data/  # Volume for downloaded CSV files
├── docker-compose.yml
└── README.md
```

### 1.3 Development Environment Setup
- [x] Initialize Git repository (ready for git init)
- [x] Create Docker Compose configuration
- [x] Set up PostgreSQL container with persistent volume
- [x] Set up Redis container (for Celery)
- [x] Configure environment variables (.env.example file created)
- [x] Set up backend development environment (FastAPI structure created)
- [x] Set up frontend development environment (React + TypeScript structure created)
- [x] Create initial documentation (AI_INSTRUCTIONS.md, AI_System_Prompt.md, README.md, and service-specific READMEs)

---

## Phase 2: Data Download System (Week 2)

### 2.1 S3 Browser & File Discovery
**Goal**: List and identify available bulk data files

**Tasks:**
- [x] Implement S3 listing functionality (no authentication required for CourtListener bucket)
- [x] Parse S3 bucket structure to find:
  - Schema files (e.g., `courtlistener-schema-2024-10-31.sql`)
  - CSV data files (e.g., `people-2024-10-31.csv`)
  - Import scripts (e.g., `load-bulk-data-2024-10-31.sh`)
- [x] Filter for "People" database tables:
  - `people_db_person`
  - `people_db_position`
  - `people_db_school`
  - `people_db_education`
  - `people_db_politicalaffiliation`
  - `people_db_race`
  - `people_db_source`
  - `people_db_abarating`
  - `people_db_retentionevent`
- [ ] Create UI to display available datasets with dates (Frontend - Phase 2.3)

**Code Example Structure:**
```python
# backend/app/services/s3_downloader.py
import boto3
from botocore import UNSIGNED
from botocore.client import Config

class CourtListenerDownloader:
    BUCKET_NAME = "com-courtlistener-storage"
    PREFIX = "bulk-data/"
    
    def __init__(self):
        # No credentials needed for public bucket
        self.s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    
    def list_available_datasets(self):
        """List all available bulk data files with dates"""
        pass
    
    def download_schema(self, date: str, target_dir: str):
        """Download schema SQL file"""
        pass
    
    def download_csv(self, table_name: str, date: str, target_dir: str):
        """Download specific CSV file with progress tracking"""
        pass
```

### 2.2 Download Manager
**Goal**: Efficiently download large files with resume capability

**Tasks:**
- [x] Implement chunked download with progress tracking (via boto3)
- [x] Add retry logic for failed downloads (boto3 handles retries)
- [ ] Implement checksum verification (if available) - Future enhancement
- [x] Create download queue system using Celery
- [x] Store download metadata (file size, download date, status) - In-memory tracking
- [x] Create API endpoints for:
  - Starting downloads (`POST /api/data/download`)
  - Checking download status (`GET /api/data/download/status/{date}`)
  - Listing downloaded files (`GET /api/data/datasets`)
  - Listing available datasets (`GET /api/data/datasets`)

**Features:**
- [x] Basic download functionality
- [ ] Resume interrupted downloads - Future enhancement
- [x] Parallel downloads for multiple files (via Celery)
- [ ] Bandwidth throttling option - Future enhancement
- [ ] Disk space checks before download - Future enhancement
- [ ] Real-time progress updates via WebSocket - Future enhancement (currently polling)

### 2.3 Frontend Download UI
- [x] Create "Data Management" page
- [x] Display available datasets in S3
- [x] Show download queue and progress (with real-time polling)
- [x] Display downloaded files with metadata
- [x] Add controls to start downloads
- [x] Add import controls and status display
- [x] Add database status dashboard
- [x] Real-time polling for status updates (2s intervals during operations)
- [ ] Add pause/cancel download controls (Future enhancement)

---

## Phase 3: Database Schema & Import (Week 3)

### 3.1 Schema Implementation
**Goal**: Create database schema matching CourtListener's structure

**Tasks:**
- [x] Download and analyze latest schema SQL file (can be done when downloading data)
- [x] Create SQLAlchemy models matching the schema:
  - [x] Person model with all fields
  - [x] Position model with relationships
  - [x] School model
  - [x] Education model with person/school relationships
  - [x] PoliticalAffiliation model
  - [x] Race model
  - [x] Source model
  - [x] Court model (updated to match CourtListener schema - uses string IDs, all CSV fields)
- [x] Set up Alembic for database migrations
- [ ] Create initial migration (run: `alembic revision --autogenerate -m "Initial schema"`)
- [x] Add indexes for common query patterns (included in models):
  - [x] Person name searches (indexes on name_first, name_last)
  - [x] Date ranges for positions (indexes on date_start, date_termination)
  - [x] Court ID lookups (indexes on court_id, person_id)
  - [ ] Geographic searches (can be added later if needed)

**Key Relationships to Model:**
```python
# backend/app/models/person.py
class Person(Base):
    __tablename__ = "people_db_person"
    
    id = Column(Integer, primary_key=True)
    name_first = Column(String(50))
    name_middle = Column(String(50))
    name_last = Column(String(50))
    name_suffix = Column(String(5))
    date_dob = Column(Date)
    date_dod = Column(Date)
    # ... other fields
    
    # Relationships
    positions = relationship("Position", back_populates="person")
    educations = relationship("Education", back_populates="person")
    political_affiliations = relationship("PoliticalAffiliation", back_populates="person")
    races = relationship("Race", back_populates="person")
    sources = relationship("Source", back_populates="person")
```

### 3.2 Data Import System
**Goal**: Reliably import CSV data into PostgreSQL

**Tasks:**
- [x] Parse CourtListener's import script to understand dependencies (import order implemented)
- [x] Implement import order based on foreign key dependencies:
  1. [x] Courts (referenced by many tables)
  2. [x] People (base table)
  3. [x] Schools (base table)
  4. [x] Positions (references people & courts)
  5. [x] Education (references people & schools)
  6. [x] Political Affiliations (references people)
  7. [x] Races (references people)
  8. [x] Sources (references people)
- [x] Use pandas for CSV import (changed from COPY due to CSV format issues)
  - Uses pandas `read_csv()` with error handling for malformed CSV files
  - Uses pandas `to_sql()` with standard INSERT statements
  - Automatically filters CSV columns to match database schema
- [x] Implement error handling and validation:
  - [x] Check CSV format and encoding (pandas handles malformed CSV)
  - [x] Validate foreign key constraints (in data_validator.py)
  - [x] Handle NULL vs empty string differences (pandas handles this)
  - [x] Log import errors for review
  - [x] Filter CSV columns to match database schema (handles column mismatches)
- [x] Create import status tracking (via Celery tasks)
- [x] Implement rollback on failure (transaction-based)
- [x] Add data validation post-import (data_validator.py)

**Import Process:**
1. [x] Verify downloaded files exist
2. [ ] Create backup of existing data (if any) - Future enhancement
3. [ ] Truncate tables in reverse dependency order (temporarily disabled due to SIGSEGV issues)
4. [x] Import CSVs in dependency order using pandas
5. [x] Run ANALYZE on tables for query optimization
6. [x] Verify record counts (in validator)
7. [x] Run basic data integrity checks (in validator)

**Known Issues & Solutions:**
- SIGSEGV during truncation: Fixed by disabling truncation (imports append data)
- CSV format issues (unquoted carriage returns): Fixed by using pandas instead of COPY
- Column mismatches: Fixed by automatic column filtering

### 3.3 Data Management API
- [x] Create endpoints for:
  - [x] `/api/data/status` - Current database status (record counts, last import date)
  - [x] `/api/data/import` - Start import process
  - [x] `/api/data/import/status` - Check import progress
  - [ ] `/api/data/validate` - Run validation checks (can be called manually via validator service)
- [x] Implement Celery task for background import
  - Uses `--pool=solo` to avoid forking issues
  - Runs in background with status tracking
- [x] Real-time progress updates via polling (every 2 seconds during active operations)
- [ ] Add WebSocket updates for real-time progress (Future enhancement - currently using HTTP polling)

---

## Phase 4: Backend API Development (Week 4-5)

### 4.1 Core API Endpoints

**People Endpoints:**
```
GET    /api/people               - List people (paginated, searchable)
GET    /api/people/{id}          - Get person details
GET    /api/people/search        - Full-text search
GET    /api/people/{id}/positions - Get person's positions
GET    /api/people/{id}/education - Get person's education
GET    /api/people/stats         - Statistics (count by various attributes)
```

**Positions Endpoints:**
```
GET    /api/positions            - List positions (with filters)
GET    /api/positions/{id}       - Get position details
GET    /api/positions/by-court/{court_id} - Positions by court
```

**Schools Endpoints:**
```
GET    /api/schools              - List schools
GET    /api/schools/{id}         - Get school details
GET    /api/schools/{id}/alumni  - Get people who attended
```

**Courts Endpoints:**
```
GET    /api/courts               - List courts
GET    /api/courts/{id}          - Get court details
GET    /api/courts/{id}/judges   - Get judges who served
```

### 4.2 Advanced Features

**Filtering:**
- [ ] Implement flexible filtering on all list endpoints
- [ ] Support for multiple filter combinations
- [ ] Date range filters
- [ ] Text search across multiple fields

**Sorting:**
- [ ] Allow sorting by any field
- [ ] Support multi-column sorting

**Pagination:**
- [ ] Cursor-based pagination for large datasets
- [ ] Configurable page sizes
- [ ] Return total count with results

**Search:**
- [ ] Implement PostgreSQL full-text search for people names
- [ ] Support fuzzy matching for name searches
- [ ] Index optimization for search performance

**Example API Response:**
```json
{
  "data": [
    {
      "id": 12345,
      "name_full": "Ruth Bader Ginsburg",
      "name_first": "Ruth",
      "name_middle": "Bader",
      "name_last": "Ginsburg",
      "date_dob": "1933-03-15",
      "date_dod": "2020-09-18",
      "positions_count": 3,
      "education_count": 2,
      "most_recent_position": {
        "court": "Supreme Court of the United States",
        "position_type": "Associate Justice",
        "date_start": "1993-08-10",
        "date_termination": "2020-09-18"
      }
    }
  ],
  "pagination": {
    "total": 16191,
    "page": 1,
    "page_size": 50,
    "has_next": true,
    "has_prev": false
  }
}
```

### 4.3 Performance Optimization
- [ ] Implement Redis caching for frequently accessed data
- [ ] Use database connection pooling
- [ ] Add query result caching
- [ ] Implement eager loading for relationships to avoid N+1 queries
- [ ] Add database indexes based on query patterns
- [ ] Set up query monitoring and slow query logging

### 4.4 Documentation
- [ ] FastAPI automatic OpenAPI documentation
- [ ] Add detailed docstrings to all endpoints
- [ ] Create API usage examples
- [ ] Document filtering and search syntax

---

## Phase 5: Frontend Development (Week 6-8)

### 5.1 Core Components

**Layout Components:**
- [ ] App Shell with navigation
- [ ] Header with search bar
- [ ] Sidebar navigation
- [ ] Responsive mobile layout

**Data Table Component:**
- [ ] Reusable table with TanStack Table
- [ ] Column sorting (multi-column)
- [ ] Column filtering (per-column)
- [ ] Column visibility toggle
- [ ] Column resizing
- [ ] Pagination controls
- [ ] Export to CSV functionality
- [ ] Keyboard navigation

**Search Component:**
- [ ] Global search bar
- [ ] Autocomplete suggestions
- [ ] Recent searches
- [ ] Search history

### 5.2 Main Pages

**People Browser Page:**
- [ ] Table view of all people
- [ ] Filters:
  - Name search (first, middle, last)
  - Date of birth range
  - Whether currently serving
  - Court affiliation
  - Geographic location
- [ ] Quick view panel for selected person
- [ ] Navigation to detailed person view

**Person Detail Page:**
- [ ] Personal information section
- [ ] Positions timeline visualization
- [ ] Education history
- [ ] Political affiliations
- [ ] Related sources/references
- [ ] Link to CourtListener profile
- [ ] Statistics (years served, courts, etc.)

**Positions Browser Page:**
- [ ] Table of all positions
- [ ] Filters:
  - Court
  - Position type (Judge, Chief Judge, etc.)
  - Selection method (Appointment, Election)
  - Date range
  - Current vs historical
- [ ] Timeline view option
- [ ] Court hierarchy visualization

**Schools Browser Page:**
- [ ] Table of educational institutions
- [ ] Notable alumni list
- [ ] Statistics per school
- [ ] Geographic distribution

**Courts Browser Page:**
- [ ] List of courts with hierarchy
- [ ] Current and historical judges
- [ ] Court statistics
- [ ] Geographic visualization

**Data Management Page:**
- [ ] Available datasets browser
- [ ] Download manager
- [ ] Import controls
- [ ] Database statistics
- [ ] Last update information
- [ ] Data validation results

### 5.3 Visualizations

**Timeline Visualization:**
- [ ] Judge career timeline (positions over time)
- [ ] Court composition over time
- [ ] Interactive and zoomable

**Geographic Map:**
- [ ] Courts by location
- [ ] Judge distribution
- [ ] Interactive filters

**Relationship Graph:**
- [ ] School alumni networks
- [ ] Clerk relationships
- [ ] Appointment chains

**Statistics Dashboard:**
- [ ] Key metrics cards
- [ ] Charts and graphs
- [ ] Filterable by date range

### 5.4 User Experience

**Performance:**
- [ ] Virtual scrolling for large tables
- [ ] Debounced search inputs
- [ ] Optimistic UI updates
- [ ] Loading skeletons
- [ ] Error boundaries

**Accessibility:**
- [ ] ARIA labels on all interactive elements
- [ ] Keyboard navigation throughout
- [ ] Screen reader support
- [ ] Focus management
- [ ] Color contrast compliance (WCAG AA)

**Responsive Design:**
- [ ] Mobile-optimized table views
- [ ] Touch-friendly controls
- [ ] Adaptive layouts
- [ ] Mobile navigation patterns

---

## Phase 6: Integration & Testing (Week 9)

### 6.1 Integration Testing
- [ ] API integration tests
- [ ] End-to-end tests with Playwright
- [ ] Database import/export tests
- [ ] S3 download tests (mocked)

### 6.2 Performance Testing
- [ ] Load testing with large datasets
- [ ] API response time benchmarks
- [ ] Frontend rendering performance
- [ ] Database query optimization

### 6.3 User Acceptance Testing
- [ ] Create test scenarios
- [ ] Test with sample user workflows
- [ ] Gather feedback
- [ ] Iterate on UX issues

---

## Phase 7: Documentation & Deployment (Week 10)

### 7.1 Documentation
- [ ] User guide
  - How to download data
  - How to search and filter
  - Understanding the data model
- [ ] Developer documentation
  - Setup instructions
  - API documentation
  - Database schema documentation
  - Contributing guidelines
- [ ] Deployment guide
  - Docker deployment
  - Environment configuration
  - Backup and restore procedures
  - Upgrade procedures

### 7.2 Deployment Preparation
- [ ] Create production Docker Compose configuration
- [ ] Set up environment variables
- [ ] Configure nginx reverse proxy (optional)
- [ ] Set up SSL certificates (if hosting publicly)
- [ ] Configure backup strategy
- [ ] Set up monitoring (optional - Prometheus/Grafana)

### 7.3 Deployment
- [ ] Deploy to production environment
- [ ] Verify all services are running
- [ ] Perform initial data download and import
- [ ] Conduct smoke tests
- [ ] Monitor system performance

---

## Technical Considerations

### Data Volume Management
- **Initial Load**: The complete dataset is several GB
- **Storage**: Plan for at least 50GB for data + indexes
- **Memory**: PostgreSQL will benefit from ample RAM (8GB+ recommended)
- **Download Time**: Depending on connection, initial download may take hours

### Update Strategy
- Monthly updates are released
- Implement "refresh" functionality:
  1. Download new files
  2. Import to temporary tables
  3. Swap with production tables
  4. Or: truncate and reimport (simpler but more downtime)

### Data Integrity
- CourtListener data has complex relationships
- Foreign key constraints must be respected during import
- Some data may have NULL values that need handling
- Implement validation checks post-import

### Performance Tips
- Use PostgreSQL COPY for bulk import (much faster than INSERT)
- Create indexes AFTER bulk import, not before
- Run ANALYZE after import to update query planner statistics
- Consider partitioning large tables (positions table could be large)
- Use connection pooling (PgBouncer or SQLAlchemy pool)

### Security Considerations
- If hosting publicly:
  - Use rate limiting
  - Implement API authentication
  - Add CORS configuration
  - Use HTTPS
  - Regular security updates
- Sensitive data: Check if any PII needs protection
- Input validation on all API endpoints

---

## Milestones & Deliverables

### Week 2: Foundation
✅ Project setup complete
✅ Docker environment running
✅ S3 download working
✅ Downloaded first dataset

### Week 4: Data Layer
✅ Database schema implemented
✅ Data import working
✅ Sample data loaded
✅ Basic API endpoints functional

### Week 6: API Complete
✅ All API endpoints implemented
✅ Testing coverage adequate
✅ Documentation written
✅ Performance benchmarks met

### Week 8: Frontend Complete
✅ All pages implemented
✅ User can browse all data types
✅ Search and filter working
✅ Visualizations complete

### Week 10: Production Ready
✅ Testing complete
✅ Documentation published
✅ Deployed to production
✅ Initial data loaded
✅ System monitored and stable

---

## Resource Requirements

### Development Tools
- Docker Desktop
- Git
- IDE (VS Code recommended)
- PostgreSQL client (pgAdmin or DBeaver)
- API testing tool (Postman or Insomnia)

### Infrastructure (Production)
- Server with:
  - 4+ CPU cores
  - 16GB+ RAM
  - 100GB+ SSD storage
  - Good network bandwidth
- Or use cloud provider:
  - AWS: EC2 + RDS + S3
  - DigitalOcean: Droplet + Managed Database
  - Google Cloud: Compute Engine + Cloud SQL

### Development Time Estimate
- **With AI assistance (Cursor, Claude)**: 6-10 weeks (1 developer)
- **Without AI assistance**: 12-16 weeks (1 developer)
- **With team of 2**: 4-6 weeks

---

## Risk Mitigation

### Risks & Mitigation Strategies

| Risk | Impact | Likelihood | Mitigation |
|------|---------|-----------|------------|
| Large dataset size causes memory issues | High | Medium | Stream processing, chunked downloads, pagination |
| Import fails midway | High | Medium | Transactions, checkpoints, resume capability |
| S3 download bandwidth limits | Medium | Low | Retry logic, resume downloads, parallel downloads |
| Schema changes between versions | Medium | Low | Version checking, migration scripts |
| Complex foreign key dependencies | Medium | Medium | Careful import ordering, validation |
| Performance issues with large tables | High | Medium | Indexes, caching, query optimization |
| UI becomes slow with many records | Medium | Medium | Virtual scrolling, pagination, lazy loading |

---

## Success Criteria

The project will be considered successful when:
1. ✅ User can download latest CourtListener bulk data
2. ✅ Data successfully imports into PostgreSQL
3. ✅ User can search for judges by name
4. ✅ User can view judge career history
5. ✅ User can browse courts and see current judges
6. ✅ User can filter and sort all data types
7. ✅ Application handles 10,000+ records smoothly
8. ✅ Data can be updated with new monthly releases
9. ✅ All documentation is complete and clear
10. ✅ System is stable and performant

---

## Next Steps

To get started immediately:

1. **Set up development environment:**
   ```bash
   mkdir courtlistener-browser
   cd courtlistener-browser
   
   # Create docker-compose.yml
   # Create backend/ and frontend/ directories
   # Set up Git repository
   ```

2. **Test S3 access:**
   ```python
   import boto3
   from botocore import UNSIGNED
   from botocore.client import Config
   
   s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
   result = s3.list_objects_v2(
       Bucket='com-courtlistener-storage',
       Prefix='bulk-data/',
       MaxKeys=10
   )
   for obj in result.get('Contents', []):
       print(obj['Key'])
   ```

3. **Download schema file:**
   ```bash
   aws s3 cp \
     s3://com-courtlistener-storage/bulk-data/courtlistener-schema-2024-10-31.sql \
     ./data/ \
     --no-sign-request
   ```

4. **Review schema to understand data model:**
   - Examine table definitions
   - Identify key relationships
   - Note any special PostgreSQL features used

5. **Create initial project scaffolding:**
   - Initialize FastAPI backend
   - Initialize React frontend
   - Set up PostgreSQL in Docker
   - Create basic API health check endpoint

Would you like me to help you start with any specific phase of this project? I can help you:
- Create the Docker Compose setup
- Build the S3 downloader
- Design the database models
- Create the initial API structure
- Set up the React frontend

Let me know which part you'd like to tackle first!
