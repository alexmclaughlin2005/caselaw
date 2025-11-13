# Components - Documentation

## Purpose
The `components` directory contains reusable React components organized by category.

## Directory Structure

### `tables/`
**Purpose**: Data table components using TanStack Table.

**Planned Components**:
- `DataTable.tsx`: Reusable table component with sorting, filtering, pagination
- `PeopleTable.tsx`: Specialized table for people/judges
- `PositionsTable.tsx`: Specialized table for positions

### `forms/`
**Purpose**: Form input components.

**Planned Components**:
- `SearchInput.tsx`: Search input with autocomplete
- `DateRangePicker.tsx`: Date range selection
- `FilterPanel.tsx`: Filter controls for tables

### `common/`
**Purpose**: Shared UI components.

**Planned Components**:
- `Button.tsx`: Button component
- `Card.tsx`: Card container component
- `LoadingSpinner.tsx`: Loading indicator
- `ErrorBoundary.tsx`: Error boundary component

## Dependencies
- **Depends on**: 
  - `@tanstack/react-table` for table components
  - `shadcn/ui` components (to be installed)
  - `tailwindcss` for styling
- **Used by**: Page components

## Integration
- Pages import and compose components from this directory
- Components follow a consistent design system
- Shared styling through Tailwind CSS

## Reference
See [AI_INSTRUCTIONS.md](../../AI_INSTRUCTIONS.md) for complete application overview.

