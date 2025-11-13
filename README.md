# CourtListener Database Browser

A web application for downloading, importing, and visualizing CourtListener's bulk legal data, focusing on the People/Judges database.

## Features

- 📥 **Download Management**: Download bulk data files from CourtListener's public S3 bucket
- 💾 **Data Import**: Import CSV data into PostgreSQL with proper relationship handling
- 🔍 **Search & Browse**: Search and filter judges, positions, schools, and courts
- 📊 **Visualizations**: View timelines, relationships, and statistics
- 🔄 **Data Updates**: Manage monthly data updates

## Quick Start

### Prerequisites

- Docker Desktop
- Git

### Setup

1. **Clone the repository**:
   ```bash
   git clone [repository-url]
   cd courtlistener-browser
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env if needed (defaults should work for development)
   ```

3. **Start services**:
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001
   - API Documentation: http://localhost:8001/docs

## Project Structure

```
courtlistener-browser/
├── backend/          # FastAPI backend
├── frontend/         # React frontend
├── data/             # Downloaded CSV files
└── docker-compose.yml
```

## Development

### Backend Development

```bash
# Enter backend container
docker-compose exec backend bash

# Run migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Run tests
pytest
```

### Frontend Development

```bash
# Enter frontend container
docker-compose exec frontend bash

# Install dependencies
npm install

# Run tests
npm test
```

## Documentation

- **AI Instructions**: See `AI_INSTRUCTIONS.md` for complete application documentation
- **System Prompt**: See `AI_System_Prompt.md` for AI agent instructions
- **Project Plan**: See `courtlistener-db-browser-project-plan.md` for development roadmap

## Data Source

- **S3 Bucket**: `com-courtlistener-storage/bulk-data/`
- **Update Frequency**: Monthly (last day of each month)
- **Format**: PostgreSQL CSV dumps with UTF-8 encoding

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React, TypeScript, Shadcn/ui, TanStack Table
- **Infrastructure**: Docker Compose, Redis, Celery

## License

[Add license information]

## Contributing

[Add contributing guidelines]

