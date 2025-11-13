#!/bin/bash

echo "===== Case Law Import Progress ====="
echo ""

# Check if import process is running
echo "Import Process Status:"
docker exec courtlistener-celery-worker ps aux | grep -i "import" | grep -v grep || echo "No active import process found"
echo ""

# Check latest log entries with progress
echo "Latest Progress (last 20 lines):"
docker logs --tail 20 courtlistener-celery-worker 2>&1 | grep -E "(Importing|Processed|chunks|rows|SUCCESS|ERROR|====)" | tail -20
echo ""

# Check database row counts
echo "Current Database Counts:"
docker exec courtlistener-postgres psql -U courtlistener -d courtlistener -c "
SELECT
    'search_docket' as table_name, COUNT(*) as row_count FROM search_docket
UNION ALL
SELECT
    'search_opinioncluster', COUNT(*) FROM search_opinioncluster
UNION ALL
SELECT
    'search_opinionscited', COUNT(*) FROM search_opinionscited
UNION ALL
SELECT
    'search_parenthetical', COUNT(*) FROM search_parenthetical
ORDER BY table_name;
" 2>&1
