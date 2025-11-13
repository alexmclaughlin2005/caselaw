# Hooks - Documentation

## Purpose
The `hooks` directory contains custom React hooks for reusable stateful logic.

## Planned Hooks

### `usePeople.ts`
**Purpose**: Hook for fetching and managing people data.

**Features**:
- Fetch people with pagination
- Search functionality
- Filter management
- Caching with React Query

### `usePositions.ts`
**Purpose**: Hook for fetching and managing positions data.

### `useDataManagement.ts`
**Purpose**: Hook for managing downloads and imports.

**Features**:
- Download status tracking
- Import progress monitoring
- Dataset listing

## Dependencies
- **Depends on**: 
  - `@tanstack/react-query` for data fetching
  - API client from `services/api.ts`
- **Used by**: Page components

## Integration
- Pages use hooks to fetch and manage data
- Hooks encapsulate API calls and state management
- Hooks provide consistent data fetching patterns

## Reference
See [AI_INSTRUCTIONS.md](../../AI_INSTRUCTIONS.md) for complete application overview.

