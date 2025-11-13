#!/bin/bash
# Railway worker script for long-running import
# This script runs directly as a Railway service (not via API endpoint)

echo "Railway Worker Starting..."
echo "Working directory: $(pwd)"
echo "Python version: $(python3 --version)"

# Run the import script directly
python3 /app/import_directly.py

echo "Import complete. Worker will now exit."
