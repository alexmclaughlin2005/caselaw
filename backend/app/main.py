"""
CourtListener Database Browser - FastAPI Application Entry Point

This module initializes the FastAPI application and includes all API routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# Initialize FastAPI application
app = FastAPI(
    title="CourtListener Database Browser API",
    description="API for browsing and querying CourtListener's People/Judges database",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "courtlistener-api"}

# Include API routes
from app.api.routes import data_management, dockets, opinions, citations, monitoring, database, chunk_management, migration, file_upload, simple_download
# from app.api.routes import people, positions, schools

app.include_router(data_management.router, prefix="/api/data", tags=["data"])
app.include_router(chunk_management.router, prefix="/api/chunks", tags=["chunks"])
app.include_router(migration.router, prefix="/api/migration", tags=["migration"])
app.include_router(file_upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(simple_download.router, prefix="/api/download", tags=["download"])
app.include_router(dockets.router, prefix="/api/dockets", tags=["dockets"])
app.include_router(opinions.router, prefix="/api/opinions", tags=["opinions"])
app.include_router(citations.router, prefix="/api/citations", tags=["citations"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])
app.include_router(database.router, prefix="/api/database", tags=["database"])
# app.include_router(people.router, prefix="/api/people", tags=["people"])
# app.include_router(positions.router, prefix="/api/positions", tags=["positions"])
# app.include_router(schools.router, prefix="/api/schools", tags=["schools"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

