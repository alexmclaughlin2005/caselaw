# Changelog

All notable changes to the CourtListener Database Browser project.

## [1.2.0] - 2025-01-12

### Added - Citation Network Drill-Down Feature

#### Frontend Changes
- **OpinionDetailDrawer.tsx**: Enhanced with interactive citation drill-down
  - Added state management for expand/collapse (`showCitingCases`, `showCitedCases`)
  - Implemented lazy loading queries for citing and cited opinions
  - Created clickable citation cards with hover effects
  - Added expandable sections with scrollable lists (max 384px height)
  - Blue theme for "Times Cited" (cases citing this opinion)
  - Green theme for "Times Citing" (cases cited by this opinion)

- **icons.tsx**: Added new icons
  - `ChevronDown`: Indicates collapsed state
  - `ChevronUp`: Indicates expanded state

#### Features
- Click citation count cards to expand/collapse detailed case lists
- Lazy loading: Data fetched only when expanded (enabled flag in TanStack Query)
- Caching: Results cached by TanStack Query for instant re-expansion
- Rich case details: Name, filing date, citation count, depth badges
- Supports up to 500 citing cases and 500 cited cases per opinion
- Loading states and empty states for better UX
- Smooth transitions and visual feedback

#### Documentation
- Created `CITATION_FEATURES.md`: Comprehensive 400+ line documentation
  - Architecture overview
  - Backend API details
  - Frontend implementation guide
  - UI/UX specifications
  - Performance considerations
  - Future enhancement roadmap
  - Testing recommendations
  - Troubleshooting guide

- Updated `ai_instructions.md`:
  - Added citation analysis to core functionality
  - Added TanStack Query to technology stack
  - Listed key features implemented
  - Added reference to CITATION_FEATURES.md
  - Created version history section

#### Backend (No Changes)
- Citation API endpoints already existed (`/api/citations/{id}/citing`, `/api/citations/{id}/cited`)
- Backend fully supports the new frontend features

#### Technical Details
- Uses TanStack Query for data fetching and caching
- Implements React hooks pattern (useState, useQuery)
- Conditional rendering based on expand/collapse state
- Query enabled flag: `enabled: !!opinionId && open && showCitingCases`
- Maximum 500 results per category to prevent performance issues
- Responsive design with proper spacing and borders

#### Data Requirements
- Citation table: 48.3M citations (✅ Loaded)
- Opinion cluster table: 7.2K entries (⏳ Still importing)
- Full functionality available once opinion cluster import completes

---

## [1.1.0] - 2025-01-11

### Added - Text Alignment and Visibility Fixes

#### UI Improvements
- Removed centered text alignment from table cells and empty states
- Fixed text visibility issues (white text on white background)
- Added explicit text colors throughout UI components:
  - Input: `text-gray-900`, `bg-white`, `placeholder-gray-500`
  - Button: `text-gray-700` (outline), `text-gray-900` (secondary)
  - Card: `text-gray-900` for titles
  - Table: `text-gray-900` for cells
- Replaced `text-muted-foreground` with `text-gray-600`

#### Files Modified
- `frontend/src/components/ui/input.tsx`
- `frontend/src/components/ui/button.tsx`
- `frontend/src/components/ui/card.tsx`
- `frontend/src/components/ui/table.tsx`
- `frontend/src/pages/Dockets.tsx`
- `frontend/src/pages/Opinions.tsx`
- `frontend/src/components/DocketDetailDrawer.tsx`
- `frontend/src/components/OpinionDetailDrawer.tsx`

---

## [1.0.0] - 2025-01-10

### Added - Initial Implementation

#### Backend API
- Created API routes for dockets, opinions, and citations
- Implemented search and filtering for dockets
- Implemented search and filtering for opinions
- Added citation statistics endpoints
- Created Pydantic schemas for validation
- Added database indexes for performance

#### Frontend Pages
- **Dockets Page**: Search and browse 34.9M court cases
  - Full-text search by case name or docket number
  - Pagination (50 items per page)
  - Sorting by date filed
  - Clickable case names open detail drawer

- **Opinions Page**: Search and browse 7.2K legal opinions
  - Full-text search by case name or judge name
  - Sort by most cited option
  - Pagination (50 items per page)
  - Clickable case names open detail drawer

#### Detail Drawers
- **DocketDetailDrawer**: Full docket information
  - Case information section
  - Important dates section
  - Judges and panel section
  - Federal docket information
  - Associated opinions list
  - System metadata

- **OpinionDetailDrawer**: Full opinion information
  - Opinion information with precedential status
  - Important dates
  - Judges and attorneys
  - Opinion content (syllabus, headnotes, summary)
  - Supreme Court Database (SCDB) information
  - Associated docket
  - Citation statistics (basic counts)

#### UI Components
- Created reusable UI components:
  - `Input`: Text input with consistent styling
  - `Button`: Multiple variants (default, outline, secondary, destructive)
  - `Card`: Container with header, title, description, content
  - `Table`: Data table with header, body, rows, cells
  - `Badge`: Status badges with color variants
  - `Drawer`: Slide-out panel with backdrop
  - Icons: Search, ChevronLeft, ChevronRight, TrendingUp, ExternalLink

#### Infrastructure
- Set up Docker Compose with backend, frontend, postgres, redis, celery
- Configured backend port 8001 (changed from 8000)
- Implemented TanStack Query for data fetching
- Added routing with React Router

---

## Database Status

### Current Data (as of 2025-01-12)
- **Dockets**: 34,926,768 entries (✅ Complete)
- **Citations**: 48,364,101 entries (✅ Complete)
- **Opinion Clusters**: 7,216 entries (⏳ Still importing)
- **Parentheticals**: 6,130,000+ entries (⏳ Still importing)
- **People**: 16,000+ entries (✅ Complete)
- **Positions**: 51,000+ entries (✅ Complete)
- **Schools**: 6,000+ entries (✅ Complete)
- **Education**: 12,000+ entries (✅ Complete)

### Import Timeline
- Phase 1 (People DB): ✅ Complete
- Phase 2 (Dockets & Citations): ⏳ In Progress (7.2K / ~10M opinions)
- Phase 3 (Remaining data): ⏳ Pending

---

## Future Enhancements

### Citation Features
- [ ] Make case names in citation lists clickable
- [ ] Add pagination for large citation lists (>500 cases)
- [ ] Add search/filter within citation lists
- [ ] Add sort options (by date, citation count, case name)
- [ ] Implement citation network graph visualization
- [ ] Add export functionality (CSV, JSON)
- [ ] Show citation context/snippets
- [ ] Add citation timeline and statistics

### Search & Browse
- [ ] Advanced search with multiple filters
- [ ] Save search queries
- [ ] Export search results
- [ ] Bulk operations on search results

### Data Visualization
- [ ] Timeline visualization for case filings
- [ ] Court distribution charts
- [ ] Citation network graphs
- [ ] Judge statistics and visualizations

### Performance
- [ ] Add pagination to opinion cluster import
- [ ] Implement ElasticSearch for full-text search
- [ ] Add Redis caching for frequent queries
- [ ] Optimize database indexes

---

## Technical Debt

### Known Issues
1. Opinion cluster import is very slow (7.2K out of ~10M entries)
2. Citation relationships only work when both opinions exist in cluster table
3. Frontend container has ARM architecture build issues (workaround: run locally)

### Improvements Needed
1. Add error boundaries to React components
2. Add loading skeletons for better perceived performance
3. Add unit tests for frontend components
4. Add integration tests for API endpoints
5. Add E2E tests for critical user flows

---

## Contributors

- Development: Claude (Anthropic)
- User: Alex McLaughlin
- Project: CourtListener Database Browser

---

## License

This project uses data from [CourtListener](https://www.courtlistener.com/), which is provided under the CC0 1.0 Universal license.
