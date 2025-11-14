# CSV Chunking - Quick Reference Card

## 🚀 Quick Start

```bash
# 1. Chunk a CSV (splits into numbered files)
python chunk_and_import.py chunk --table TABLE_NAME --date YYYY-MM-DD --chunk-size 1000000

# 2. Import all chunks sequentially
python chunk_and_import.py import --table TABLE_NAME --date YYYY-MM-DD --method standard

# 3. Check progress
python chunk_and_import.py progress --table TABLE_NAME --date YYYY-MM-DD
```

## 📋 All Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `chunk` | Split CSV into chunks | `python chunk_and_import.py chunk --table search_docket --date 2025-10-31 --chunk-size 1000000` |
| `import` | Import chunks sequentially | `python chunk_and_import.py import --table search_docket --date 2025-10-31 --method standard` |
| `progress` | Check import status | `python chunk_and_import.py progress --table search_docket --date 2025-10-31` |
| `reset` | Reset to pending | `python chunk_and_import.py reset --table search_docket --date 2025-10-31` |
| `delete` | Remove chunks | `python chunk_and_import.py delete --table search_docket --date 2025-10-31 --delete-files --yes` |

## ⚙️ Import Methods

| Method | Speed | Best For |
|--------|-------|----------|
| `standard` | Fast (50-100K rows/min) | Clean CSV data (default) |
| `pandas` | Medium (30-80K rows/min) | Malformed CSVs, encoding issues |
| `copy` | Very Fast (200-500K rows/min) | Perfect CSV format only |

## 📊 Recommended Chunk Sizes

| Table | Rows | Chunk Size |
|-------|------|------------|
| search_docket (small rows) | ~35M | 1,000,000 |
| search_opinioncluster | ~7M | 500,000 |
| search_opinionscited | ~48M | 2,000,000 |
| search_parenthetical (large text) | ~5M | 250,000 |

## 🔧 Common Tasks

### Resume Failed Import
```bash
# Check what failed
python chunk_and_import.py progress --table search_docket --date 2025-10-31 --detailed

# Resume (skips completed chunks automatically)
python chunk_and_import.py import --table search_docket --date 2025-10-31
```

### Monitor Long-Running Import
```bash
# In separate terminal, refresh every 30 seconds
watch -n 30 'python chunk_and_import.py progress --table search_docket --date 2025-10-31'
```

### Clean Up After Import
```bash
# Remove chunks to save disk space
python chunk_and_import.py delete --table search_docket --date 2025-10-31 --delete-files --yes
```

## 🌐 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chunks/chunk` | POST | Create chunks |
| `/api/chunks/{table}/{date}` | GET | List chunks |
| `/api/chunks/{table}/{date}/progress` | GET | Progress summary |
| `/api/chunks/import` | POST | Import chunks |
| `/api/chunks/reset` | POST | Reset chunks |
| `/api/chunks` | DELETE | Delete chunks |

## 📈 Progress Output Example

```
================================================================================
IMPORT PROGRESS
================================================================================
Table: search_docket
Date: 2025-10-31
Status: in_progress

Chunks:
  Total: 35
  Completed: 18
  Failed: 1
  Processing: 0
  Pending: 16

Rows:
  Total: 34,900,000
  Imported: 18,000,000
  Skipped: 1,234

Progress: 51.4%
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No chunks found" | Run `chunk` command first |
| "Chunk file not found" | Re-run `chunk` command |
| Slow import | Try `copy` method or increase chunk size |
| Memory errors | Reduce chunk size |
| Data type errors (COPY) | Use `standard` or `pandas` method |

## 📁 Files Created

```
backend/data/chunks/
└── search_docket-2025-10-31/
    ├── search_docket-2025-10-31.chunk_0001.csv
    ├── search_docket-2025-10-31.chunk_0002.csv
    └── ...
```

## 🗄️ Database Table

Chunk progress tracked in: `csv_chunk_progress`

Query directly:
```sql
SELECT chunk_number, status, rows_imported, duration_seconds
FROM csv_chunk_progress
WHERE table_name = 'search_docket' AND dataset_date = '2025-10-31'
ORDER BY chunk_number;
```

## ⏱️ Time Estimates

**35M row table (search_docket):**
- Chunking: ~5-10 minutes
- Import (standard): ~5.8-11.6 hours
- Import (copy): ~1.2-2.9 hours

**7M row table (search_opinioncluster):**
- Chunking: ~2-5 minutes
- Import (standard): ~1.2-2.3 hours
- Import (copy): ~14-35 minutes

## 🎯 Best Practices

1. ✅ Always chunk before import
2. ✅ Use resume mode for reliability
3. ✅ Monitor progress regularly
4. ✅ Keep original CSVs until import verified
5. ✅ Clean up chunks after successful import
6. ✅ Test with small chunk size first
7. ✅ Document chunk size and method used

## 📚 Documentation

- **Complete Guide**: [CSV_CHUNKING_GUIDE.md](CSV_CHUNKING_GUIDE.md)
- **Implementation Details**: [CSV_CHUNKING_IMPLEMENTATION_SUMMARY.md](CSV_CHUNKING_IMPLEMENTATION_SUMMARY.md)
- **Test Script**: [test_chunking_system.py](test_chunking_system.py)

## 🚦 Setup

```bash
# 1. Run migration
docker compose exec backend alembic upgrade head

# 2. Test the system
python test_chunking_system.py

# 3. Start using it!
python chunk_and_import.py chunk --table YOUR_TABLE --date YYYY-MM-DD
```

## 💡 Tips

- **Parallel monitoring**: Open two terminals - one for import, one for progress
- **Chunk size tuning**: Smaller = more frequent commits, larger = faster overall
- **Resume is default**: Failed imports automatically resume from last success
- **Disk space**: Chunks use ~same space as original CSV
- **Safety first**: Use `standard` method unless you need speed
