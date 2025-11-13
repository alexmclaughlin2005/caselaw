# Citation Network Features

## Overview

The CourtListener Database Browser includes comprehensive citation analysis features that allow users to explore relationships between legal opinions through citation networks. This document describes the implementation of the citation drill-down functionality.

**Last Updated**: January 12, 2025

---

## Table of Contents

1. [Feature Summary](#feature-summary)
2. [Architecture](#architecture)
3. [Backend Implementation](#backend-implementation)
4. [Frontend Implementation](#frontend-implementation)
5. [User Interface](#user-interface)
6. [Data Flow](#data-flow)
7. [Performance Considerations](#performance-considerations)
8. [Future Enhancements](#future-enhancements)

---

## Feature Summary

### Core Functionality

The citation network features provide:

1. **Citation Statistics**: Display counts of how many times an opinion has been cited and how many opinions it cites
2. **Interactive Drill-Down**: Click on citation counts to expand and view detailed lists of all related cases
3. **Lazy Loading**: Citation details are fetched on-demand only when expanded by the user
4. **Rich Case Details**: Each related case shows name, filing date, citation count, and depth information
5. **Scrollable Lists**: Large citation lists are scrollable with a maximum height for usability

### Key Capabilities

- View up to 500 citing cases per opinion
- View up to 500 cited cases per opinion
- Real-time data loading with loading states
- Visual distinction between citing (blue) and cited (green) cases
- Expandable/collapsible sections with animated chevron icons
- Hover effects and clear visual feedback

---

## Architecture

### Component Structure

```
OpinionDetailDrawer (Main Component)
├── Citation Statistics Section
│   ├── Clickable "Times Cited" Card (Blue theme)
│   │   └── Expandable List of Citing Cases
│   └── Clickable "Times Citing" Card (Green theme)
│       └── Expandable List of Cited Cases
```

### Data Dependencies

```
Citation Stats API (/api/citations/{id}/stats)
├── times_cited: number
├── times_citing: number
├── top_citing_cases: array (not used in drill-down)
└── top_cited_cases: array (not used in drill-down)

Citing Opinions API (/api/citations/{id}/citing)
└── citing_opinions: array
    ├── id: number
    ├── citing_opinion_id: number
    ├── citing_case_name: string
    ├── citing_date_filed: string
    ├── citing_citation_count: number
    └── depth: number

Cited Opinions API (/api/citations/{id}/cited)
└── cited_opinions: array
    ├── id: number
    ├── cited_opinion_id: number
    ├── cited_case_name: string
    ├── cited_date_filed: string
    ├── cited_citation_count: number
    └── depth: number
```

---

## Backend Implementation

### API Endpoints

#### 1. Get Citation Statistics
**Endpoint**: `GET /api/citations/{opinion_id}/stats`

**Purpose**: Retrieve citation statistics for an opinion

**Response**:
```json
{
  "opinion_id": 894639,
  "case_name": "Wheeler v. Green",
  "times_cited": 395,
  "times_citing": 12,
  "top_citing_cases": [],
  "top_cited_cases": []
}
```

**Implementation**: `backend/app/api/routes/citations.py`

---

#### 2. Get Citing Opinions
**Endpoint**: `GET /api/citations/{opinion_id}/citing?limit=500`

**Purpose**: Retrieve all opinions that cite this opinion

**Response**:
```json
{
  "opinion_id": 894639,
  "case_name": "Wheeler v. Green",
  "times_cited": 395,
  "citing_opinions": [
    {
      "id": 123,
      "citing_opinion_id": 456,
      "cited_opinion_id": 894639,
      "depth": 1,
      "citing_case_name": "Smith v. Jones",
      "citing_date_filed": "2023-05-15",
      "citing_citation_count": 42
    }
  ]
}
```

**Query Details**:
- Joins `search_opinionscited` with `search_opinioncluster`
- Filters by `cited_opinion_id == opinion_id`
- Orders by citation count (most cited first)
- Limits to specified number of results (default 100, max 500)

**Implementation**: `backend/app/api/routes/citations.py:26-84`

---

#### 3. Get Cited Opinions
**Endpoint**: `GET /api/citations/{opinion_id}/cited?limit=500`

**Purpose**: Retrieve all opinions cited by this opinion

**Response**:
```json
{
  "opinion_id": 894639,
  "case_name": "Wheeler v. Green",
  "times_citing": 12,
  "cited_opinions": [
    {
      "id": 789,
      "citing_opinion_id": 894639,
      "cited_opinion_id": 101112,
      "depth": 1,
      "cited_case_name": "Brown v. Board of Education",
      "cited_date_filed": "1954-05-17",
      "cited_citation_count": 5000
    }
  ]
}
```

**Query Details**:
- Joins `search_opinionscited` with `search_opinioncluster`
- Filters by `citing_opinion_id == opinion_id`
- Orders by citation count (most cited first)
- Limits to specified number of results (default 100, max 500)

**Implementation**: `backend/app/api/routes/citations.py:87-150`

---

### Database Schema

**Table**: `search_opinionscited`

```sql
CREATE TABLE search_opinionscited (
    id BIGINT PRIMARY KEY,
    citing_opinion_id INTEGER,
    cited_opinion_id INTEGER,
    depth INTEGER,
    score FLOAT
);
```

**Table**: `search_opinioncluster`

```sql
CREATE TABLE search_opinioncluster (
    id INTEGER PRIMARY KEY,
    case_name TEXT,
    date_filed DATE,
    citation_count INTEGER,
    -- ... other fields
);
```

**Indexes**:
- Index on `cited_opinion_id` for fast "citing" lookups
- Index on `citing_opinion_id` for fast "cited" lookups
- Index on `citation_count` for sorting

---

## Frontend Implementation

### Component: OpinionDetailDrawer

**File**: `frontend/src/components/OpinionDetailDrawer.tsx`

### State Management

```typescript
const [showCitingCases, setShowCitingCases] = useState(false)
const [showCitedCases, setShowCitedCases] = useState(false)
```

These boolean states control the expand/collapse behavior of the citation lists.

---

### Data Fetching with TanStack Query

#### Citation Statistics (Always Loaded)
```typescript
const { data: citationStats, isLoading: isLoadingCitations } = useQuery({
  queryKey: ['citation-stats', opinionId],
  queryFn: () => getCitationStats(opinionId!),
  enabled: !!opinionId && open,
})
```

**When Loaded**: Immediately when drawer opens
**Why**: Needed to display citation counts on the clickable cards

---

#### Citing Opinions (Lazy Loaded)
```typescript
const { data: citingOpinions, isLoading: isLoadingCitingOpinions } = useQuery({
  queryKey: ['citing-opinions', opinionId],
  queryFn: () => getCitingOpinions(opinionId!, 500),
  enabled: !!opinionId && open && showCitingCases,
})
```

**When Loaded**: Only when user clicks to expand "Times Cited" section
**Why**: Avoids unnecessary API calls and reduces initial load time
**Caching**: Results are cached by TanStack Query for subsequent views

---

#### Cited Opinions (Lazy Loaded)
```typescript
const { data: citedOpinions, isLoading: isLoadingCitedOpinions } = useQuery({
  queryKey: ['cited-opinions', opinionId],
  queryFn: () => getCitedOpinions(opinionId!, 500),
  enabled: !!opinionId && open && showCitedCases,
})
```

**When Loaded**: Only when user clicks to expand "Times Citing" section
**Why**: Same as above - lazy loading optimization
**Caching**: Results are cached by TanStack Query

---

### API Service Functions

**File**: `frontend/src/services/citations.ts`

```typescript
export const getCitationStats = async (opinionId: number) => {
  const response = await apiClient.get(`/api/citations/${opinionId}/stats`)
  return response.data
}

export const getCitingOpinions = async (opinionId: number, limit: number = 100) => {
  const response = await apiClient.get(`/api/citations/${opinionId}/citing`, { params: { limit } })
  return response.data
}

export const getCitedOpinions = async (opinionId: number, limit: number = 100) => {
  const response = await apiClient.get(`/api/citations/${opinionId}/cited`, { params: { limit } })
  return response.data
}
```

---

## User Interface

### Clickable Citation Cards

The citation statistics are displayed as two clickable cards:

#### "Times Cited" Card (Blue Theme)
```tsx
<button
  onClick={() => setShowCitingCases(!showCitingCases)}
  className="p-3 bg-blue-50 rounded-md hover:bg-blue-100 transition-colors text-left"
>
  <div className="text-2xl font-bold text-blue-900">{citationStats.times_cited}</div>
  <div className="text-xs text-blue-600 flex items-center justify-between">
    <span>Times Cited (Click to view)</span>
    {showCitingCases ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
  </div>
</button>
```

**Visual Design**:
- Light blue background (`bg-blue-50`)
- Darker blue on hover (`hover:bg-blue-100`)
- Large bold number displaying citation count
- Small text with chevron icon indicating expand/collapse state
- Smooth transitions

---

#### "Times Citing" Card (Green Theme)
```tsx
<button
  onClick={() => setShowCitedCases(!showCitedCases)}
  className="p-3 bg-green-50 rounded-md hover:bg-green-100 transition-colors text-left"
>
  <div className="text-2xl font-bold text-green-900">{citationStats.times_citing}</div>
  <div className="text-xs text-green-600 flex items-center justify-between">
    <span>Times Citing (Click to view)</span>
    {showCitedCases ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
  </div>
</button>
```

**Visual Design**:
- Light green background (`bg-green-50`)
- Darker green on hover (`hover:bg-green-100`)
- Large bold number displaying citation count
- Same interaction pattern as citing card
- Smooth transitions

---

### Expanded Citation Lists

When a user clicks a card, an expanded section appears below with detailed case information.

#### Citing Cases List (Blue Theme)
```tsx
{showCitingCases && (
  <div className="border border-blue-200 rounded-md p-4 bg-blue-50/50">
    <div className="text-sm font-medium text-gray-900 mb-3">
      Cases Citing This Opinion ({citationStats.times_cited})
    </div>
    {isLoadingCitingOpinions ? (
      <div className="text-sm text-gray-600">Loading citing cases...</div>
    ) : citingOpinions && citingOpinions.citing_opinions && citingOpinions.citing_opinions.length > 0 ? (
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {citingOpinions.citing_opinions.map((cite: any) => (
          <div key={cite.id} className="p-3 bg-white rounded border border-gray-200">
            <div className="font-medium text-sm text-gray-900 mb-1">
              {cite.citing_case_name || 'Unnamed Case'}
            </div>
            <div className="text-xs text-gray-600 space-y-1">
              {cite.citing_date_filed && (
                <div>Filed: {formatDate(cite.citing_date_filed)}</div>
              )}
              <div className="flex items-center gap-2 mt-1">
                {cite.citing_citation_count > 0 && (
                  <Badge variant="secondary" className="text-xs">
                    {cite.citing_citation_count} citations
                  </Badge>
                )}
                {cite.depth !== null && (
                  <Badge variant="outline" className="text-xs">
                    Depth: {cite.depth}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    ) : (
      <div className="text-sm text-gray-600">No citing cases found</div>
    )}
  </div>
)}
```

**Visual Design**:
- Light blue border and background (`border-blue-200`, `bg-blue-50/50`)
- White cards for individual cases
- Maximum height of 384px with scroll (`max-h-96 overflow-y-auto`)
- Spacing between cases
- Badges for citation count and depth
- Loading state while fetching data
- Empty state if no cases found

---

#### Cited Cases List (Green Theme)
```tsx
{showCitedCases && (
  <div className="border border-green-200 rounded-md p-4 bg-green-50/50">
    <div className="text-sm font-medium text-gray-900 mb-3">
      Cases Cited By This Opinion ({citationStats.times_citing})
    </div>
    {isLoadingCitedOpinions ? (
      <div className="text-sm text-gray-600">Loading cited cases...</div>
    ) : citedOpinions && citedOpinions.cited_opinions && citedOpinions.cited_opinions.length > 0 ? (
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {citedOpinions.cited_opinions.map((cite: any) => (
          <div key={cite.id} className="p-3 bg-white rounded border border-gray-200">
            <div className="font-medium text-sm text-gray-900 mb-1">
              {cite.cited_case_name || 'Unnamed Case'}
            </div>
            <div className="text-xs text-gray-600 space-y-1">
              {cite.cited_date_filed && (
                <div>Filed: {formatDate(cite.cited_date_filed)}</div>
              )}
              <div className="flex items-center gap-2 mt-1">
                {cite.cited_citation_count > 0 && (
                  <Badge variant="secondary" className="text-xs">
                    {cite.cited_citation_count} citations
                  </Badge>
                )}
                {cite.depth !== null && (
                  <Badge variant="outline" className="text-xs">
                    Depth: {cite.depth}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    ) : (
      <div className="text-sm text-gray-600">No cited cases found</div>
    )}
  </div>
)}
```

**Visual Design**:
- Light green border and background (`border-green-200`, `bg-green-50/50`)
- Same card structure as citing cases
- Same maximum height and scrolling behavior
- Consistent badge styling
- Same loading and empty states

---

### Icons

**File**: `frontend/src/components/icons.tsx`

Two new chevron icons were added for expand/collapse indication:

```typescript
export const ChevronDown = (props: React.SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
  </svg>
)

export const ChevronUp = (props: React.SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" {...props}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 15.75l7.5-7.5 7.5 7.5" />
  </svg>
)
```

---

## Data Flow

### User Interaction Flow

```
1. User clicks on opinion in Opinions page
   ↓
2. OpinionDetailDrawer opens
   ↓
3. Citation stats are fetched automatically
   ↓
4. Two clickable cards display citation counts
   ↓
5. User clicks "Times Cited" card
   ↓
6. showCitingCases state set to true
   ↓
7. TanStack Query enabled flag triggers API call
   ↓
8. Loading state displayed
   ↓
9. API returns citing opinions data
   ↓
10. Expanded section renders with list of cases
    ↓
11. User can scroll through cases
    ↓
12. User clicks card again to collapse
    ↓
13. showCitingCases set to false
    ↓
14. Section collapses (data remains in cache)
```

### Caching Behavior

TanStack Query automatically caches the results:

- **Cache Key**: `['citing-opinions', opinionId]` or `['cited-opinions', opinionId]`
- **Cache Duration**: Default TanStack Query settings (5 minutes)
- **Stale Time**: Default TanStack Query settings (0 seconds)
- **Refetch**: On window focus (default behavior)

This means:
1. First expansion fetches from API
2. Subsequent expansions use cached data
3. Cache expires after 5 minutes of inactivity
4. Refetches if user focuses window after data goes stale

---

## Performance Considerations

### Optimizations

1. **Lazy Loading**: Citation details only fetched when user expands sections
   - Reduces initial API calls
   - Faster drawer open time
   - Better for mobile/slow connections

2. **Caching**: TanStack Query caches results
   - Instant re-expansion without API calls
   - Reduces server load
   - Better user experience

3. **Limit Results**: Maximum 500 cases per category
   - Prevents overwhelming UI
   - Reduces API response size
   - Faster data transfer

4. **Scrollable Lists**: Maximum height of 384px
   - Prevents infinite scrolling
   - Maintains drawer usability
   - Clear visual boundary

5. **Conditional Rendering**: Only renders expanded sections when needed
   - Smaller DOM tree
   - Better React performance
   - Faster re-renders

### Database Performance

The backend queries are optimized:

1. **Joins**: Single join between citations and opinion clusters
2. **Indexes**: Proper indexes on `citing_opinion_id` and `cited_opinion_id`
3. **Ordering**: Sort by citation count (indexed field)
4. **Limits**: Query limits prevent full table scans

### Current Limitations

1. **Data Availability**: Citation relationships only work when both opinions exist in the `search_opinioncluster` table
   - Citation table has 48.3M entries
   - Opinion cluster table has only 7.2K entries (still importing)
   - Full functionality will be available once import completes

2. **No Pagination**: All results fetched at once (up to 500)
   - Future enhancement: Add pagination for large result sets

3. **No Search/Filter**: Cannot search within citation lists
   - Future enhancement: Add search box for filtering cases

---

## Future Enhancements

### Planned Features

1. **Clickable Case Names**: Make case names in citation lists clickable to open their details
   ```typescript
   <button
     onClick={() => handleOpinionClick(cite.citing_opinion_id)}
     className="font-medium text-sm text-blue-600 hover:text-blue-800 hover:underline"
   >
     {cite.citing_case_name || 'Unnamed Case'}
   </button>
   ```

2. **Pagination**: Add pagination for large citation lists
   - Load 50 cases at a time
   - "Load more" button or infinite scroll
   - Reduces initial load time

3. **Search/Filter**: Add search box within expanded sections
   - Filter by case name
   - Filter by date range
   - Filter by citation count

4. **Sort Options**: Allow sorting citation lists
   - By date (newest/oldest first)
   - By citation count (most/least cited)
   - By case name (alphabetical)

5. **Citation Network Visualization**: Add graph visualization
   - Use the existing `/api/citations/{id}/network` endpoint
   - Display citation relationships as interactive graph
   - Use D3.js or similar library
   - Show depth levels visually

6. **Export Functionality**: Allow exporting citation lists
   - CSV export
   - JSON export
   - Copy to clipboard

7. **Citation Context**: Show citation context/snippets
   - Display excerpt where citation appears
   - Highlight citation in opinion text
   - Show citation sentence/paragraph

8. **Citation Statistics**: Add more detailed stats
   - Citation timeline (citations over time)
   - Citation by court
   - Citation by jurisdiction
   - Average citation depth

---

## Technical Details

### File Structure

```
frontend/src/
├── components/
│   ├── OpinionDetailDrawer.tsx    # Main component (modified)
│   ├── icons.tsx                   # Chevron icons (modified)
│   └── ui/
│       ├── drawer.tsx             # Drawer component (existing)
│       └── badge.tsx              # Badge component (existing)
├── services/
│   └── citations.ts               # Citation API functions (existing)

backend/app/
├── api/
│   └── routes/
│       └── citations.py           # Citation endpoints (existing)
├── models/
│   ├── opinion.py                 # OpinionCluster model (existing)
│   └── citation.py                # Citation model (existing)
└── schemas/
    └── citation.py                # Citation schemas (existing)
```

### Dependencies

**Frontend**:
- `react` (18+): Core UI library
- `@tanstack/react-query` (4+): Data fetching and caching
- `axios`: HTTP client

**Backend**:
- `fastapi`: Web framework
- `sqlalchemy`: ORM for database queries
- `pydantic`: Data validation

### Environment Requirements

- **Database**: PostgreSQL 15+ with citation data loaded
- **Memory**: Sufficient for large result sets (up to 500 cases × 2)
- **Network**: Fast connection for large API responses

---

## Testing Recommendations

### Manual Testing Checklist

- [ ] Click "Times Cited" card - section expands
- [ ] Click "Times Cited" card again - section collapses
- [ ] Click "Times Citing" card - section expands
- [ ] Click "Times Citing" card again - section collapses
- [ ] Both sections can be open simultaneously
- [ ] Loading states display while fetching
- [ ] Empty states display when no citations found
- [ ] Scroll works within expanded sections
- [ ] Case names, dates, and badges display correctly
- [ ] Chevron icons rotate correctly
- [ ] Hover effects work on cards
- [ ] Data persists when collapsing/expanding (cached)
- [ ] New drawer instance fetches fresh data

### API Testing

```bash
# Test citation stats
curl http://localhost:8001/api/citations/894639/stats

# Test citing opinions
curl http://localhost:8001/api/citations/894639/citing?limit=10

# Test cited opinions
curl http://localhost:8001/api/citations/894639/cited?limit=10
```

### Performance Testing

1. **Large Result Sets**: Test with opinions that have 400+ citations
2. **Network Throttling**: Test with slow 3G to verify loading states
3. **Rapid Clicking**: Test expand/collapse rapidly to check state management
4. **Memory Usage**: Monitor browser memory with large citation lists open

---

## Troubleshooting

### Common Issues

1. **"No citing cases found" when citations exist**
   - **Cause**: Citing opinions don't exist in `search_opinioncluster` table yet
   - **Solution**: Wait for opinion cluster import to complete
   - **Check**: Query database to verify opinion exists

2. **Loading state never completes**
   - **Cause**: API endpoint error or network issue
   - **Solution**: Check browser console for errors
   - **Check**: Verify backend logs for API errors

3. **Slow performance with large lists**
   - **Cause**: Too many results returned
   - **Solution**: Reduce limit parameter
   - **Check**: Monitor network tab for response size

4. **Stale data displayed**
   - **Cause**: TanStack Query cache not invalidated
   - **Solution**: Close and reopen drawer, or refresh page
   - **Check**: Clear cache manually in React DevTools

---

## Summary

The citation drill-down feature provides a comprehensive way for users to explore citation relationships between legal opinions. The implementation uses modern React patterns (hooks, lazy loading) and efficient API design to provide a fast, responsive user experience. The feature is fully functional and ready to use once the opinion cluster data is fully imported into the database.

**Key Benefits**:
- Intuitive user interface with clear visual feedback
- Efficient data loading with lazy queries and caching
- Scalable design that handles large citation networks
- Extensible architecture for future enhancements

**Next Steps**:
- Complete opinion cluster data import
- Add clickable case names for navigation
- Consider pagination for very large result sets
- Add citation network graph visualization
