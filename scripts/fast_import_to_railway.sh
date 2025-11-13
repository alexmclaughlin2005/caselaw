#!/bin/bash
set -e

# Railway PostgreSQL connection details
RAILWAY_HOST="crossover.proxy.rlwy.net"
RAILWAY_PORT="40848"
RAILWAY_USER="postgres"
RAILWAY_PASS="tChJPFTgQuKBuBHenTtAqRsWMSnIOWhj"
RAILWAY_DB="railway"

echo "==============================================="
echo "FAST PARALLEL IMPORT TO RAILWAY"
echo "==============================================="
echo ""
echo "This will import data from local Docker to Railway in parallel"
echo "Estimated time: 2-4 hours for ~150M records"
echo ""

# Function to import a single table
import_table() {
    local table=$1
    local log_file="/tmp/import_${table}.log"

    echo "[$(date '+%H:%M:%S')] Starting $table..." | tee -a "$log_file"

    # Stream dump directly to Railway (fastest method)
    docker exec courtlistener-postgres pg_dump \
        -U courtlistener \
        -d courtlistener \
        --table=$table \
        --data-only \
        --no-owner \
        --no-privileges \
        --no-tablespaces \
        | PGPASSWORD="$RAILWAY_PASS" psql \
        -h "$RAILWAY_HOST" \
        -p "$RAILWAY_PORT" \
        -U "$RAILWAY_USER" \
        -d "$RAILWAY_DB" \
        >> "$log_file" 2>&1

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        # Get record count
        local count=$(PGPASSWORD="$RAILWAY_PASS" psql \
            -h "$RAILWAY_HOST" \
            -p "$RAILWAY_PORT" \
            -U "$RAILWAY_USER" \
            -d "$RAILWAY_DB" \
            -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null | tr -d ' ')

        echo "[$(date '+%H:%M:%S')] ✓ Completed $table ($count records)" | tee -a "$log_file"
        return 0
    else
        echo "[$(date '+%H:%M:%S')] ✗ Failed $table (exit code: $exit_code)" | tee -a "$log_file"
        return 1
    fi
}

# Export function for background jobs
export -f import_table
export RAILWAY_HOST RAILWAY_PORT RAILWAY_USER RAILWAY_PASS RAILWAY_DB

# Tables to import (in order of priority/size)
echo "Step 1: Importing core tables in parallel..."
echo ""

# Start all imports in background
import_table "search_docket" &
PID_DOCKET=$!

import_table "search_opinioncluster" &
PID_OPINION=$!

import_table "search_opinionscited" &
PID_CITED=$!

import_table "search_parenthetical" &
PID_PARENS=$!

# Monitor progress
echo "Background jobs started:"
echo "  - search_docket (PID: $PID_DOCKET)"
echo "  - search_opinioncluster (PID: $PID_OPINION)"
echo "  - search_opinionscited (PID: $PID_CITED)"
echo "  - search_parenthetical (PID: $PID_PARENS)"
echo ""
echo "Monitoring progress... (logs in /tmp/import_*.log)"
echo ""

# Wait for all jobs and collect exit codes
wait $PID_DOCKET
RESULT_DOCKET=$?

wait $PID_OPINION
RESULT_OPINION=$?

wait $PID_CITED
RESULT_CITED=$?

wait $PID_PARENS
RESULT_PARENS=$?

# Summary
echo ""
echo "==============================================="
echo "IMPORT SUMMARY"
echo "==============================================="
echo ""

if [ $RESULT_DOCKET -eq 0 ]; then
    echo "✓ search_docket: SUCCESS"
else
    echo "✗ search_docket: FAILED (check /tmp/import_search_docket.log)"
fi

if [ $RESULT_OPINION -eq 0 ]; then
    echo "✓ search_opinioncluster: SUCCESS"
else
    echo "✗ search_opinioncluster: FAILED (check /tmp/import_search_opinioncluster.log)"
fi

if [ $RESULT_CITED -eq 0 ]; then
    echo "✓ search_opinionscited: SUCCESS"
else
    echo "✗ search_opinionscited: FAILED (check /tmp/import_search_opinionscited.log)"
fi

if [ $RESULT_PARENS -eq 0 ]; then
    echo "✓ search_parenthetical: SUCCESS"
else
    echo "✗ search_parenthetical: FAILED (check /tmp/import_search_parenthetical.log)"
fi

echo ""

# Check if all succeeded
if [ $RESULT_DOCKET -eq 0 ] && [ $RESULT_OPINION -eq 0 ] && [ $RESULT_CITED -eq 0 ] && [ $RESULT_PARENS -eq 0 ]; then
    echo "🎉 ALL IMPORTS COMPLETED SUCCESSFULLY!"
    echo ""
    echo "Verifying Railway database..."
    PGPASSWORD="$RAILWAY_PASS" psql \
        -h "$RAILWAY_HOST" \
        -p "$RAILWAY_PORT" \
        -U "$RAILWAY_USER" \
        -d "$RAILWAY_DB" \
        -c "SELECT
            'search_docket' as table_name, COUNT(*) as records FROM search_docket
            UNION ALL
            SELECT 'search_opinioncluster', COUNT(*) FROM search_opinioncluster
            UNION ALL
            SELECT 'search_opinionscited', COUNT(*) FROM search_opinionscited
            UNION ALL
            SELECT 'search_parenthetical', COUNT(*) FROM search_parenthetical;"
    exit 0
else
    echo "⚠️  Some imports failed. Check logs in /tmp/"
    exit 1
fi
