# Pages - Documentation

## Purpose
The `pages` directory contains main application pages/routes. Each page represents a major feature or section of the application.

## Implemented Pages

### `DataManagement.tsx` ✅ Implemented
**Purpose**: Manage data downloads and imports.

**Features**:
- ✅ Available datasets browser (lists all datasets from S3)
- ✅ Download manager with progress tracking
- ✅ Import controls with status display
- ✅ Database statistics dashboard
- ✅ Real-time status updates via polling:
  - Download status: Polls every 2 seconds when downloading/pending
  - Import status: Polls every 2 seconds when importing/pending
  - Database status: Polls every 10 seconds
  - Datasets list: Polls every 30 seconds
  - Note: This creates recurring network requests visible in browser DevTools

**Components Used**:
- `Button` - For actions
- `Card` - For sections
- `LoadingSpinner` - For loading states
- `ProgressBar` - For progress display

**Hooks Used**:
- `useDatasets` - Fetch available datasets
- `useStartDownload` - Start download
- `useDownloadStatus` - Track download progress
- `useStartImport` - Start import
- `useImportStatus` - Track import progress
- `useDatabaseStatus` - Get database statistics

## Planned Pages

### `People.tsx`
**Purpose**: Browse and search people/judges.

**Features** (to be implemented):
- Table view of all people
- Name search (first, middle, last)
- Date of birth range filter
- Currently serving filter
- Court affiliation filter
- Quick view panel
- Navigation to detailed person view

### `Positions.tsx`
**Purpose**: Browse judicial positions.

### `Schools.tsx`
**Purpose**: Browse educational institutions.

## Reference
See [AI_INSTRUCTIONS.md](../../AI_INSTRUCTIONS.md) for complete application overview.
