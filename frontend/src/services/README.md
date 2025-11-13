# Services - Documentation

## Purpose
The `services` directory contains API client and external service integrations for the frontend.

## Key Files

### `api.ts`
**Purpose**: Centralized API communication layer using Axios.

**Key Components**:
- `apiClient`: Axios instance with base URL and default headers
- Request/response interceptors for error handling
- Type-safe API calls

**Usage**:
```typescript
import apiClient from '@/services/api'

// GET request
const response = await apiClient.get('/api/people')
const people = response.data

// POST request
await apiClient.post('/api/data/import', { dataset: '2024-10-31' })
```

**Configuration**:
- Base URL from `VITE_API_URL` environment variable
- Default: `http://localhost:8001`
- Headers configured for JSON content

## Dependencies
- **Depends on**: `axios` for HTTP requests
- **Used by**: All page components and hooks that need to communicate with the backend

## Integration
- Pages import `apiClient` to make API calls
- React Query hooks can wrap `apiClient` calls for caching and state management
- Error handling is centralized in interceptors

## Future Enhancements
- Add authentication token handling
- Add request/response logging
- Add retry logic for failed requests
- Add request cancellation support

## Reference
See [AI_INSTRUCTIONS.md](../../AI_INSTRUCTIONS.md) for complete application overview.

