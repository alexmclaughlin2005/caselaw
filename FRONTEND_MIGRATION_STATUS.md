# Frontend Migration Status - Visual Overview

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                     SINGLE UNIFIED FRONTEND                        │
│                    /frontend directory                             │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              React 18 + TypeScript + Vite                    │ │
│  │                                                              │ │
│  │  Same codebase for BOTH:                                    │ │
│  │  ✅ Local Development (http://localhost:3000)              │ │
│  │  ✅ Vercel Production (https://your-app.vercel.app)        │ │
│  │                                                              │ │
│  │  ONLY DIFFERENCE: Environment variable for API URL          │ │
│  │  - Local: VITE_API_URL=http://localhost:8000              │ │
│  │  - Prod:  VITE_API_URL=https://railway-backend.app        │ │
│  │                                                              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  Development Mode (npm run dev)                                   │
│  ├─ Vite Dev Server: localhost:3000                             │
│  ├─ Hot Module Replacement (HMR)                                │
│  ├─ TypeScript compilation                                      │
│  └─ Source maps for debugging                                   │
│                                                                    │
│  Production Mode (npm run build)                                 │
│  ├─ TypeScript → JavaScript                                     │
│  ├─ Vite bundling                                               │
│  ├─ Minification & tree-shaking                                 │
│  ├─ Output: dist/ folder                                        │
│  └─ Deployed to Vercel CDN                                      │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure Overview

```
Court Listener Project Root
│
├── backend/              ← FastAPI backend (runs on Railway)
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/             ← React SPA (runs on Vercel locally)
│   ├── src/
│   │   ├── pages/        → 4 main pages (Home, Dockets, Opinions, Data)
│   │   ├── components/   → UI components & detail drawers
│   │   ├── services/     → API integration
│   │   ├── hooks/        → Custom React hooks
│   │   ├── types/        → TypeScript definitions
│   │   ├── lib/          → Utilities
│   │   ├── App.tsx       → Main router
│   │   └── main.tsx      → Entry point
│   ├── vite.config.ts    → Build configuration
│   ├── package.json      → Dependencies
│   ├── index.html        → HTML template
│   └── Dockerfile        → Container image
│
└── [other files & docs]
```

---

## Feature Implementation Status Map

```
┌─────────────────────────────────────────────────────────────────┐
│                    FEATURES IMPLEMENTED                         │
│                        100% COMPLETE                            │
└─────────────────────────────────────────────────────────────────┘

SEARCH & BROWSE          DETAIL VIEWS           CITATIONS
├─ ✅ Dockets Search    ├─ ✅ Docket Detail    ├─ ✅ Stats Display
├─ ✅ Opinions Search   ├─ ✅ Opinion Detail   ├─ ✅ Citing List
├─ ✅ Full-text search  └─ ✅ Slide drawers    ├─ ✅ Cited List
├─ ✅ Sorting options                         ├─ ✅ Lazy Loading
├─ ✅ Pagination                              ├─ ✅ TanStack Query
└─ ✅ 50 results/page                         └─ ✅ Caching

UI COMPONENTS            DATA MANAGEMENT        VERCEL READY
├─ ✅ Navigation         ├─ ✅ DB Status        ├─ ✅ Env variables
├─ ✅ Tables             ├─ ✅ Download S3      ├─ ✅ Build config
├─ ✅ Cards              ├─ ✅ Import tracking  ├─ ✅ TypeScript
├─ ✅ Buttons            ├─ ✅ Progress bars    ├─ ✅ Dockerfile
├─ ✅ Badges             └─ ✅ Statistics       ├─ ✅ ESLint
├─ ✅ Drawers                                  ├─ ✅ Responsive
├─ ✅ Inputs                                   └─ ✅ Mobile-ready
├─ ✅ Icons
└─ ✅ Loading states
```

---

## What Was NOT Needed (No "Old" Frontend)

```
Traditional Migration Pattern (what DIDN'T happen):
┌──────────────┐      Migration      ┌────────────┐
│  Old Frontend │ ─────────────────> │ New Frontend│
│ (HTML/CSS/JS)│      (Manual)       │  (React)   │
└──────────────┘                     └────────────┘

What ACTUALLY exists:
┌──────────────────────────────────────┐
│    NEW Frontend (All-in-One)         │
│                                      │
│  - Started as modern from day 1      │
│  - Uses Vite (modern tooling)        │
│  - React 18 with TypeScript          │
│  - Production-ready architecture     │
│  - Works locally AND on Vercel       │
│  - No legacy code to port            │
│  - No migration needed               │
└──────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      USER INTERACTIONS                           │
│              (in browser on localhost:3000 or Vercel)            │
└──────────────────────────────────────────────────────────────────┘
                            │
                            ▼
                ┌────────────────────────┐
                │   Frontend (React)     │
                │   ├─ Dockets page     │
                │   ├─ Opinions page    │
                │   ├─ Detail drawers   │
                │   └─ Data Mgmt page   │
                └────────────────────────┘
                            │
                            │ (API Calls via fetch)
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼ (Local Dev)                           ▼ (Production)
┌──────────────────┐                     ┌──────────────────┐
│ http://localhost │                     │  Railway Backend │
│      :8000       │                     │   (Production)   │
└──────────────────┘                     └──────────────────┘
        │                                       │
        ▼                                       ▼
┌──────────────────────────────────────────────────────────┐
│            PostgreSQL Database                          │
│   (Both dev and prod use same schema)                   │
│   - search_docket (millions of rows)                    │
│   - search_opinion (millions of rows)                   │
│   - search_opinionscited (citations)                    │
│   - And more...                                         │
└──────────────────────────────────────────────────────────┘
```

---

## Deployment Pipeline

```
Developer commits to GitHub
        │
        ▼
    git push
        │
        ▼
┌─────────────────────────────────────┐
│  GitHub Repository                  │
│  (alexmclaughlin2005/caselaw)       │
└─────────────────────────────────────┘
        │
        ├─────────────────────────────────────────┐
        │                                         │
        ▼ (Automatic on push to main)            ▼ (Manual setup)
┌──────────────────────┐         ┌────────────────────────┐
│  Railway CI/CD       │         │  Vercel CI/CD          │
│  ├─ Clone repo       │         │  ├─ Clone repo         │
│  ├─ Build backend    │         │  ├─ Install deps       │
│  ├─ Run migrations   │         │  ├─ npm run build      │
│  └─ Deploy to edge   │         │  ├─ Type checking      │
└──────────────────────┘         │  └─ Deploy to CDN      │
        │                        └────────────────────────┘
        │                                 │
        ▼                                 ▼
┌──────────────────────┐         ┌────────────────────────┐
│  Railway Production  │         │  Vercel Production     │
│  caselaw-*.up.      │         │  your-app.vercel.app  │
│  railway.app        │         │                        │
└──────────────────────┘         └────────────────────────┘
        ▲                                 │
        │                                 │
        └─────────────────┬───────────────┘
                          │
                          │ (User accesses app)
                          │
                    Frontend calls Backend API
```

---

## Pages & Routes

```
App.tsx (Main Router)
│
├─ / (Home)
│  └─ Welcome page
│     ├─ "Browse Dockets" button
│     ├─ "Browse Opinions" button
│     └─ "Data Management" button
│
├─ /dockets (Dockets Page)
│  ├─ Search bar
│  ├─ Sorting/filtering options
│  ├─ Results table (paginated, 50 per page)
│  └─ OnClick → DocketDetailDrawer
│     └─ Full docket information
│
├─ /opinions (Opinions Page)
│  ├─ Search bar
│  ├─ Sorting/filtering options
│  ├─ Results table (paginated, 50 per page)
│  └─ OnClick → OpinionDetailDrawer
│     ├─ Full opinion information
│     ├─ Citation Statistics (blue cards)
│     │  └─ Click "Times Cited" → Lazy load citing opinions
│     ├─ Citation Statistics (green cards)
│     │  └─ Click "Times Citing" → Lazy load cited opinions
│     └─ Document text
│
└─ /data (Data Management)
   ├─ Database Status Cards
   │  ├─ Row counts for each table
   │  ├─ Last import dates
   │  └─ Import statistics
   ├─ Dataset Browser
   │  └─ Available files from S3
   ├─ Download Controls
   │  ├─ Select dataset
   │  └─ Download button with progress
   └─ Import Controls
      ├─ Select downloaded files
      ├─ Import button
      └─ Progress tracking
```

---

## Components Dependency Tree

```
App (Router)
│
├── Navigation
│   ├── Home link
│   ├── Dockets link
│   ├── Opinions link
│   └── Data Management link
│
├── Dockets (Page)
│   ├── Input (Search bar)
│   ├── Button (Search)
│   ├── Table
│   │   ├── Badge (status)
│   │   └── OnClick rows
│   └── DocketDetailDrawer
│       ├── Card
│       ├── Badge
│       └── Drawer
│
├── Opinions (Page)
│   ├── Input (Search bar)
│   ├── Button (Search)
│   ├── Table
│   │   ├── Badge (status)
│   │   └── OnClick rows
│   └── OpinionDetailDrawer
│       ├── Card
│       ├── Badge
│       ├── Drawer
│       ├── Citation Cards (blue/green)
│       │   └── ChevronUp/ChevronDown icons
│       └── Lazy-loaded Lists
│
└── DataManagement (Page)
    ├── Card (DB Status)
    │   ├── ProgressBar
    │   └── Stats
    ├── Card (Dataset Browser)
    │   ├── Button (Download)
    │   └── ProgressBar
    ├── Card (Import)
    │   ├── Button (Import)
    │   └── ProgressBar
    └── LoadingSpinner
```

---

## State Management Flow

```
┌────────────────────────────────────────────────────────────┐
│              LOCAL STATE (useState)                         │
│  - searchInput, selectedDocketId, drawerOpen, etc.         │
│  - Managed per-component                                   │
│  - Triggers re-renders locally                             │
└────────────────────────────────────────────────────────────┘

                            ▲
                            │
                ┌───────────┴────────────┐
                │                        │
                ▼                        ▼
        ┌──────────────┐        ┌──────────────┐
        │ React Hooks  │        │TanStack Query│
        │              │        │              │
        │ useState     │        │ useQuery     │
        │ useEffect    │        │ useMutation  │
        │ useContext   │        │              │
        └──────────────┘        │ Features:    │
                                │ - Caching   │
                                │ - Fetching  │
                                │ - Sync      │
                                │ - State     │
                                └──────────────┘

                            ▲
                            │
                ┌───────────┘
                │
                ▼
        ┌──────────────────┐
        │  API Services    │
        │                  │
        │ dockets.ts       │
        │ opinions.ts      │
        │ citations.ts     │
        │ dataManagementApi│
        └──────────────────┘

                            ▲
                            │
                ┌───────────┘
                │
                ▼
        ┌──────────────────────────┐
        │   REST API Backend       │
        │   (Railway)              │
        └──────────────────────────┘
```

---

## Build Pipeline

```
Source Code (TypeScript + TSX)
    │
    ├─ pages/*.tsx
    ├─ components/*.tsx
    ├─ services/*.ts
    ├─ App.tsx
    ├─ main.tsx
    └─ index.css
    │
    ▼
TypeScript Compiler (tsc)
    │
    ├─ Type checking
    ├─ Compilation to JavaScript
    └─ Error reporting
    │
    ▼
Vite Build Tool
    │
    ├─ Module bundling
    ├─ Code splitting
    ├─ Tree shaking
    ├─ CSS processing (Tailwind)
    └─ Asset optimization
    │
    ▼
Output: dist/ folder
    │
    ├─ index.html
    ├─ assets/
    │   ├─ js bundles
    │   ├─ css bundles
    │   └─ images/fonts
    │
    ▼
Vercel CDN
    │
    └─ Global edge caching & distribution
```

---

## Environment Configuration

```
┌────────────────────────────────────────────────────────────┐
│              ENVIRONMENT VARIABLES                         │
└────────────────────────────────────────────────────────────┘

LOCAL DEVELOPMENT
├─ File: .env.local (not in git)
├─ VITE_API_URL=http://localhost:8000
└─ Accessible at: http://localhost:3000

VERCEL PRODUCTION
├─ Configured in: Vercel Dashboard
├─ Environment: Production
├─ VITE_API_URL=https://caselaw-*.railway.app
└─ Accessible at: https://your-app.vercel.app

VERCEL PREVIEW (for PRs)
├─ Configured in: Vercel Dashboard
├─ Environment: Preview
├─ VITE_API_URL=https://caselaw-staging.railway.app
└─ Auto-created for each PR

VERCEL DEVELOPMENT
├─ Configured in: Vercel Dashboard (optional)
├─ Environment: Development
└─ Used for local testing with Vercel CLI

Note: Both build locally and on Vercel use the
      same source code - only env vars differ
```

---

## No Migration Needed - Summary

```
┌────────────────────────────────────────────────────────────┐
│           KEY INSIGHT                                      │
│                                                            │
│  There is NO separate "old" vs "new" frontend             │
│  to worry about.                                           │
│                                                            │
│  The current frontend is ALREADY:                         │
│  ✅ Modern (Vite + React 18)                              │
│  ✅ Type-safe (TypeScript strict mode)                    │
│  ✅ Production-ready (Vercel compatible)                  │
│  ✅ Scalable (React Router + TanStack Query)              │
│  ✅ Accessible (ARIA labels, keyboard nav)                │
│  ✅ Responsive (Mobile/tablet/desktop)                    │
│  ✅ Performant (Lazy loading, caching)                    │
│                                                            │
│  To deploy to Vercel right now:                           │
│  1. Backend must be ready (Railway)                       │
│  2. Set environment variables in Vercel                   │
│  3. Connect GitHub repo to Vercel                         │
│  4. Click Deploy                                          │
│  5. Done!                                                 │
│                                                            │
│  The frontend code doesn't need ANY changes for          │
│  Vercel deployment.                                       │
└────────────────────────────────────────────────────────────┘
```

---

## File Organization Summary

```
frontend/
├── Configuration (Build & Dev)
│   ├── vite.config.ts          (Bundler config)
│   ├── tsconfig.json           (TypeScript config)
│   ├── tailwind.config.js      (CSS framework config)
│   ├── postcss.config.js       (CSS processor config)
│   ├── .eslintrc.cjs           (Code quality config)
│   └── package.json            (Dependencies)
│
├── Static (HTML & Assets)
│   ├── index.html              (Template for both local & Vercel)
│   └── public/                 (Static assets)
│
├── Source Code (React App)
│   └── src/
│       ├── App.tsx             (Main router & layout)
│       ├── main.tsx            (App entry point)
│       ├── index.css           (Global styles)
│       │
│       ├── pages/              (Page components - 4 pages)
│       │   ├── Dockets.tsx
│       │   ├── Opinions.tsx
│       │   └── DataManagement.tsx
│       │
│       ├── components/         (Reusable UI components)
│       │   ├── common/         (Custom components)
│       │   ├── ui/             (shadcn/ui library)
│       │   ├── DocketDetailDrawer.tsx
│       │   ├── OpinionDetailDrawer.tsx
│       │   └── icons.tsx
│       │
│       ├── services/           (API integration)
│       │   ├── api.ts          (Base HTTP client)
│       │   ├── dockets.ts
│       │   ├── opinions.ts
│       │   ├── citations.ts
│       │   └── dataManagementApi.ts
│       │
│       ├── hooks/              (Custom React hooks)
│       │   └── useDataManagement.ts
│       │
│       ├── types/              (TypeScript types)
│       │   ├── index.ts
│       │   └── dataManagement.ts
│       │
│       └── lib/                (Utilities)
│           └── utils.ts
│
├── Containerization
│   └── Dockerfile              (For container deployment)
│
└── Documentation
    └── README.md               (Frontend docs)
```

