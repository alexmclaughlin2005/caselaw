#!/bin/bash
set -e

# Railway PostgreSQL connection
RAILWAY_DB="postgresql://postgres:tChJPFTgQuKBuBHenTtAqRsWMSnIOWhj@crossover.proxy.rlwy.net:40848/railway"

# Local PostgreSQL connection
LOCAL_DB="postgresql://alexmclaughlin@localhost:5432/courtlistener"

echo "==============================================="
echo "PARALLEL DATA IMPORT TO RAILWAY"
echo "==============================================="
echo ""

# Function to export and import a table in parallel
import_table() {
    local table=$1
    local job_num=$2

    echo "[Job $job_num] Starting import of $table..."

    # Use pg_dump to export data and pipe directly to Railway
    docker exec courtlistener-postgres pg_dump \
        -U courtlistener \
        -d courtlistener \
        --table=$table \
        --data-only \
        --no-owner \
        --no-privileges \
        | PGPASSWORD="tChJPFTgQuKBuBHenTtAqRsWMSnIOWhj" psql \
        -h crossover.proxy.rlwy.net \
        -p 40848 \
        -U postgres \
        -d railway \
        2>&1 | tee "/tmp/import_${table}.log"

    echo "[Job $job_num] ✓ Completed $table"
}

# Export function so it's available to parallel
export -f import_table
export RAILWAY_DB
export LOCAL_DB

# List of tables to import (ordered by size - smallest first for quick wins)
TABLES=(
    "search_docket"
    "search_opinioncluster"
    "search_opinionscited"
    "search_parenthetical"
)

echo "Starting parallel import of ${#TABLES[@]} tables..."
echo ""

# Import tables in parallel (4 jobs at a time - adjust based on Railway limits)
printf '%s\n' "${TABLES[@]}" | parallel -j 4 --progress import_table {} {#}

echo ""
echo "==============================================="
echo "✓ ALL IMPORTS COMPLETED"
echo "==============================================="
echo ""
echo "Checking record counts..."
echo ""

# Verify record counts
for table in "${TABLES[@]}"; do
    count=$(PGPASSWORD="tChJPFTgQuKBuBHenTtAqRsWMSnIOWhj" psql \
        -h crossover.proxy.rlwy.net \
        -p 40848 \
        -U postgres \
        -d railway \
        -t -c "SELECT COUNT(*) FROM $table;")
    echo "$table: $count records"
done
