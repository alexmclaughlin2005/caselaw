# Vercel Frontend Deployment Plan - Court Listener

## Executive Summary

**Objective**: Deploy Next.js frontend to Vercel with Railway backend integration.

**Architecture**:
```
┌─────────────┐     API Requests      ┌──────────────┐
│   Vercel    │ ──────────────────► │   Railway    │
│  (Frontend) │                      │  (Backend)   │
└─────────────┘                      └──────────────┘
      │                                      │
      │                                      │
   HTTPS                                PostgreSQL
 (Auto SSL)                            (Railway DB)
```

**Benefits**:
- ✅ Global CDN with edge caching
- ✅ Automatic HTTPS/SSL
- ✅ GitHub integration with preview deployments
- ✅ Serverless functions for API routes
- ✅ Zero configuration deployment
- ✅ Free hobby tier (generous limits)

**Timeline**: 2-3 hours
**Cost**: Free (Hobby tier sufficient for most use cases)

---

## Phase 1: Vercel Account Setup (15 mins)

### Task 1.1: Create Vercel Account
- [ ] Go to [vercel.com](https://vercel.com)
- [ ] Sign up with GitHub account (recommended)
- [ ] Verify email

### Task 1.2: Connect GitHub Repository
- [ ] Vercel dashboard → "Add New Project"
- [ ] Import Git Repository → Select "Court Listener" repo
- [ ] Grant Vercel access to repository

### Task 1.3: Team/Organization Setup (Optional)
- [ ] Create team if working with others
- [ ] Invite collaborators
- [ ] Set up billing (if needed beyond free tier)

---

## Phase 2: Frontend Configuration (30 mins)

### Task 2.1: Verify Project Structure

**Expected structure**:
```
Court Listener/
├── backend/          # Railway
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/         # Vercel
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── next.config.js
│   ├── tsconfig.json
│   └── .env.local
└── README.md
```

**Verify frontend setup**:
```bash
cd frontend
npm install  # Ensure dependencies installed
npm run build  # Test build locally
```

### Task 2.2: Create/Update next.config.js

**frontend/next.config.js**:
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },

  // API rewrites for production
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
      },
    ];
  },

  // Security headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin'
          },
        ],
      },
    ];
  },

  // Image optimization
  images: {
    domains: ['your-railway-app.railway.app'],
    formats: ['image/avif', 'image/webp'],
  },

  // Enable React strict mode
  reactStrictMode: true,

  // Output standalone for optimized builds
  output: 'standalone',

  // Experimental features (if needed)
  experimental: {
    // serverActions: true,
  },
};

module.exports = nextConfig;
```

### Task 2.3: Environment Variables Setup

**Create `.env.example`**:
```env
# Backend API URL
NEXT_PUBLIC_API_URL=https://your-app.railway.app

# Analytics (optional)
NEXT_PUBLIC_GA_ID=
NEXT_PUBLIC_VERCEL_ANALYTICS_ID=

# Feature flags (optional)
NEXT_PUBLIC_ENABLE_SEARCH=true
NEXT_PUBLIC_ENABLE_ADVANCED_FILTERS=true
```

**Create `.env.local`** (for local development):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Add to `.gitignore`**:
```
.env.local
.env*.local
.vercel
```

### Task 2.4: Create Vercel Configuration

**Create `vercel.json`**:
```json
{
  "version": 2,
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "regions": ["iad1"],
  "env": {
    "NEXT_PUBLIC_API_URL": "@api-url"
  },
  "build": {
    "env": {
      "NEXT_PUBLIC_API_URL": "@api-url"
    }
  },
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "s-maxage=1, stale-while-revalidate"
        }
      ]
    }
  ]
}
```

### Task 2.5: Update API Client Configuration

**frontend/src/lib/api.ts** (or similar):
```typescript
// API configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// API client with retry logic
export class APIClient {
  private baseURL: string;
  private timeout: number;

  constructor(baseURL: string = API_BASE_URL, timeout: number = 30000) {
    this.baseURL = baseURL;
    this.timeout = timeout;
  }

  async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      throw error;
    }
  }

  // Helper methods
  async get<T>(endpoint: string): Promise<T> {
    return this.fetch<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data: any): Promise<T> {
    return this.fetch<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

// Export singleton instance
export const apiClient = new APIClient();
```

---

## Phase 3: Vercel Deployment (30 mins)

### Task 3.1: Configure Project in Vercel

**Vercel dashboard**:
1. Select imported repository
2. Configure project settings:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend` (if monorepo)
   - **Build Command**: `npm run build` (or `cd frontend && npm run build`)
   - **Output Directory**: `.next` (auto-detected)
   - **Install Command**: `npm install`

### Task 3.2: Set Environment Variables

**In Vercel project settings → Environment Variables**:

**Production**:
```
NEXT_PUBLIC_API_URL = https://your-app.railway.app
```

**Preview** (for PR previews):
```
NEXT_PUBLIC_API_URL = https://your-staging-app.railway.app
```

**Development** (optional):
```
NEXT_PUBLIC_API_URL = http://localhost:8000
```

**Notes**:
- Variables prefixed with `NEXT_PUBLIC_` are exposed to browser
- Use Vercel's secret feature for sensitive values
- Can override per environment (production/preview/development)

### Task 3.3: Deploy

**First deployment**:
1. Click "Deploy" in Vercel dashboard
2. Vercel will:
   - Clone repository
   - Install dependencies
   - Build Next.js app
   - Deploy to global CDN
   - Generate preview URL

**Expected output**:
```
✓ Built in 45s
✓ Deployed to https://court-listener-xyz.vercel.app
```

### Task 3.4: Configure Custom Domain (Optional)

**If you have a custom domain**:
1. Vercel → Project → Settings → Domains
2. Add domain (e.g., `courtlistener.com`)
3. Configure DNS records:
   ```
   Type: A
   Name: @
   Value: 76.76.21.21

   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   ```
4. Wait for DNS propagation (5-30 mins)
5. Vercel auto-provisions SSL certificate

---

## Phase 4: Railway + Vercel Integration (30 mins)

### Task 4.1: Configure CORS on Railway Backend

**backend/app/main.py**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS configuration for Vercel
origins = [
    "http://localhost:3000",  # Local development
    "https://court-listener-xyz.vercel.app",  # Vercel production
    "https://*.vercel.app",  # Vercel preview deployments
]

# In production, you may want to be more restrictive
if settings.RAILWAY_ENVIRONMENT == "production":
    origins = [
        "https://courtlistener.com",  # Your custom domain
        "https://www.courtlistener.com",
        "https://court-listener-xyz.vercel.app",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Update Railway environment variables**:
```env
ALLOWED_ORIGINS=https://court-listener-xyz.vercel.app,https://courtlistener.com
```

### Task 4.2: Update API URLs in Vercel

**After Railway backend is deployed**:
1. Get Railway public URL (e.g., `https://court-listener-backend.railway.app`)
2. Update Vercel environment variable:
   ```
   NEXT_PUBLIC_API_URL = https://court-listener-backend.railway.app
   ```
3. Redeploy frontend (automatic if env var changed)

### Task 4.3: Test Integration

**Test API connectivity**:
```bash
# From your browser console on Vercel deployment
fetch(process.env.NEXT_PUBLIC_API_URL + '/health')
  .then(r => r.json())
  .then(console.log)
```

**Expected response**:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

## Phase 5: CI/CD Setup (30 mins)

### Task 5.1: Automatic Deployments

**Vercel automatically deploys on**:
- ✅ Push to `main` branch → Production deployment
- ✅ Pull request opened → Preview deployment
- ✅ Commit to PR → Updated preview deployment

**Configure in Vercel**:
1. Settings → Git → Production Branch: `main`
2. Settings → Git → Enable preview deployments: ✓
3. Settings → Git → Deploy hooks (optional)

### Task 5.2: GitHub Integration

**Vercel bot will**:
- Comment on PRs with preview URL
- Report deployment status
- Show deployment logs

**Enable GitHub checks**:
1. Vercel → Project → Settings → Git
2. Enable "Vercel for GitHub" integration
3. Status checks will appear on PRs

### Task 5.3: Preview Deployments for Feature Branches

**Workflow**:
```bash
# Create feature branch
git checkout -b feature/advanced-search

# Make changes
git add .
git commit -m "Add advanced search UI"
git push origin feature/advanced-search

# Create PR on GitHub
# Vercel automatically creates preview deployment
# Preview URL: https://court-listener-git-feature-advanced-search-username.vercel.app
```

**Benefits**:
- Test features before merging
- Share with stakeholders
- Isolated environments per PR

---

## Phase 6: Optimization (30 mins)

### Task 6.1: Performance Optimization

**Enable Vercel Analytics**:
```bash
npm install @vercel/analytics
```

**frontend/src/app/layout.tsx**:
```typescript
import { Analytics } from '@vercel/analytics/react';

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
```

**Enable Vercel Speed Insights**:
```bash
npm install @vercel/speed-insights
```

```typescript
import { SpeedInsights } from '@vercel/speed-insights/next';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <SpeedInsights />
      </body>
    </html>
  );
}
```

### Task 6.2: Caching Strategy

**API route caching** (if using Next.js API routes):
```typescript
// app/api/dockets/route.ts
export const revalidate = 60; // Revalidate every 60 seconds

export async function GET(request: Request) {
  // Fetch from Railway backend
  const data = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/dockets`);
  return Response.json(data);
}
```

**Static page generation**:
```typescript
// app/about/page.tsx
export const dynamic = 'force-static'; // Generate at build time
```

### Task 6.3: Image Optimization

**next.config.js** (already configured):
```javascript
images: {
  domains: ['your-railway-app.railway.app'],
  formats: ['image/avif', 'image/webp'],
}
```

**Usage**:
```tsx
import Image from 'next/image';

<Image
  src="/logo.png"
  alt="Court Listener"
  width={200}
  height={50}
  priority
/>
```

---

## Phase 7: Monitoring & Analytics (15 mins)

### Task 7.1: Set Up Vercel Analytics

**Included in free tier**:
- Web Vitals (CLS, FID, LCP)
- Page views
- Top pages
- Visitor insights

**Access**: Vercel dashboard → Project → Analytics

### Task 7.2: Error Tracking (Optional)

**Integrate Sentry**:
```bash
npm install @sentry/nextjs
```

**sentry.client.config.js**:
```javascript
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.VERCEL_ENV || 'development',
  tracesSampleRate: 1.0,
});
```

**Add to Vercel env vars**:
```
NEXT_PUBLIC_SENTRY_DSN = your_sentry_dsn
```

### Task 7.3: Uptime Monitoring

**Use Vercel's built-in monitoring** or:
- UptimeRobot (free tier)
- Better Uptime
- Pingdom

---

## Phase 8: Testing & Verification (30 mins)

### Task 8.1: Functional Testing

**Test checklist**:
- [ ] Homepage loads correctly
- [ ] Search functionality works
- [ ] API calls to Railway backend succeed
- [ ] Pagination works
- [ ] Detail pages load
- [ ] Forms submit correctly
- [ ] Error handling displays properly

**Test URLs**:
```
Production: https://court-listener-xyz.vercel.app
Preview: https://court-listener-git-branch-name.vercel.app
```

### Task 8.2: Performance Testing

**Lighthouse audit**:
```bash
# Chrome DevTools → Lighthouse
# Run audit on Vercel production URL
```

**Target scores**:
- Performance: 90+
- Accessibility: 90+
- Best Practices: 90+
- SEO: 90+

**Vercel Speed Insights**:
- Check Core Web Vitals
- Identify slow pages
- Optimize as needed

### Task 8.3: Cross-Browser Testing

**Test on**:
- [ ] Chrome (desktop & mobile)
- [ ] Firefox
- [ ] Safari (desktop & mobile)
- [ ] Edge

**Tools**:
- BrowserStack (if needed)
- Vercel preview deployments (test on real devices)

---

## Phase 9: Documentation (15 mins)

### Task 9.1: Update README.md

**Add deployment section**:
```markdown
## Deployment

### Frontend (Vercel)

**Production**: https://court-listener-xyz.vercel.app
**GitHub**: Automatic deployments from `main` branch

**Environment Variables**:
- `NEXT_PUBLIC_API_URL`: Railway backend URL

**Deploy manually**:
```bash
vercel --prod
```

### Backend (Railway)

**Production**: https://court-listener-backend.railway.app
**Database**: PostgreSQL on Railway

See [RAILWAY_MIGRATION_PLAN.md](./RAILWAY_MIGRATION_PLAN.md) for details.
```

### Task 9.2: Create DEPLOYMENT_GUIDE.md

**Document**:
- How to deploy frontend
- How to set environment variables
- How to roll back deployments
- How to access logs
- Common issues and solutions

### Task 9.3: Update CONTRIBUTING.md

**Add sections for**:
- Preview deployments
- Testing on Vercel previews
- Environment variable management

---

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────┐
│                         VERCEL                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Next.js Frontend                     │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │  │
│  │  │   Pages    │  │    API     │  │   Static   │    │  │
│  │  │  (React)   │  │   Routes   │  │   Assets   │    │  │
│  │  └────────────┘  └────────────┘  └────────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                 │
│                    Global CDN                                │
└────────────────────────────┼───────────────────────────────┘
                             │
                    API Requests
                             │
┌────────────────────────────▼───────────────────────────────┐
│                       RAILWAY                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              FastAPI Backend                         │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │  │
│  │  │   REST     │  │  Business  │  │   Data     │    │  │
│  │  │    API     │  │   Logic    │  │  Import    │    │  │
│  │  └────────────┘  └────────────┘  └────────────┘    │  │
│  └──────────────────────────┬───────────────────────────┘  │
│                              │                               │
│                              ▼                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              PostgreSQL Database                     │  │
│  │   - search_docket (70M rows)                        │  │
│  │   - search_opinionscited (76M rows)                 │  │
│  │   - search_opinioncluster (75M rows)                │  │
│  │   - search_parenthetical (6M rows)                  │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

---

## Environment Variables Summary

### Vercel (Frontend)

| Variable | Environment | Value |
|----------|-------------|-------|
| `NEXT_PUBLIC_API_URL` | Production | `https://court-listener-backend.railway.app` |
| `NEXT_PUBLIC_API_URL` | Preview | `https://court-listener-staging.railway.app` |
| `NEXT_PUBLIC_API_URL` | Development | `http://localhost:8000` |

### Railway (Backend)

| Variable | Value |
|----------|-------|
| `ALLOWED_ORIGINS` | `https://court-listener-xyz.vercel.app,https://*.vercel.app` |
| `DATABASE_URL` | (Railway provides) |
| `PORT` | `8000` |

---

## Cost Breakdown

### Vercel Pricing

**Hobby (Free)**:
- ✅ Unlimited deployments
- ✅ 100GB bandwidth/month
- ✅ Automatic HTTPS
- ✅ Preview deployments
- ✅ Analytics included
- **Cost**: $0/month

**Pro** (if needed):
- Everything in Hobby +
- 1TB bandwidth/month
- Password protection
- Advanced analytics
- **Cost**: $20/month

**Recommendation**: Start with Hobby, upgrade if needed

### Total Infrastructure Cost

| Service | Purpose | Cost |
|---------|---------|------|
| Railway (Backend + DB) | API + PostgreSQL | $20-50/month |
| Vercel (Frontend) | Next.js hosting | $0/month (Hobby) |
| **Total** | | **$20-50/month** |

---

## Rollback Procedures

### Vercel Rollback

**Via Dashboard**:
1. Vercel → Project → Deployments
2. Find previous successful deployment
3. Click "..." → "Promote to Production"

**Via CLI**:
```bash
vercel rollback
```

### Railway Rollback

See [RAILWAY_MIGRATION_PLAN.md](./RAILWAY_MIGRATION_PLAN.md) for backend rollback procedures.

---

## Common Issues & Solutions

### Issue 1: CORS Errors

**Symptom**: API calls fail with CORS error in browser console

**Solution**:
1. Check Railway CORS configuration in `backend/app/main.py`
2. Verify Vercel domain in `allow_origins` list
3. Redeploy Railway backend

### Issue 2: Environment Variable Not Loading

**Symptom**: `process.env.NEXT_PUBLIC_API_URL` is undefined

**Solution**:
1. Check variable is prefixed with `NEXT_PUBLIC_`
2. Verify set in Vercel dashboard
3. Redeploy Vercel app (env vars require redeploy)

### Issue 3: API Timeout

**Symptom**: API requests timeout after 30s

**Solution**:
1. Increase timeout in API client
2. Optimize backend query performance
3. Implement caching strategy

### Issue 4: Build Fails on Vercel

**Symptom**: TypeScript errors or build failures

**Solution**:
```bash
# Test build locally first
cd frontend
npm run build

# Check logs in Vercel dashboard
# Fix errors and push again
```

---

## Success Criteria

- [ ] Vercel account created and GitHub connected
- [ ] Frontend deploys successfully to Vercel
- [ ] Production URL accessible and functional
- [ ] API calls to Railway backend work
- [ ] Preview deployments work for PRs
- [ ] Environment variables configured correctly
- [ ] CORS configured on backend
- [ ] Analytics and monitoring set up
- [ ] Performance scores > 90
- [ ] Documentation updated
- [ ] Custom domain configured (optional)

---

## Timeline Summary

| Phase | Duration | Can Run in Parallel? |
|-------|----------|---------------------|
| 1. Vercel Setup | 15 mins | No |
| 2. Frontend Config | 30 mins | Yes (with Railway) |
| 3. Deployment | 30 mins | Yes (with Railway) |
| 4. Integration | 30 mins | After Railway deployed |
| 5. CI/CD | 30 mins | Yes |
| 6. Optimization | 30 mins | Yes |
| 7. Monitoring | 15 mins | Yes |
| 8. Testing | 30 mins | After deployment |
| 9. Documentation | 15 mins | Yes |

**Total**: 2-3 hours (can parallelize with Railway migration)

---

## Combined Timeline (Railway + Vercel)

### Day 1 (3-4 hours)
- Morning: Railway setup + Vercel setup (parallel)
- Afternoon: Railway schema migration + Frontend deployment (parallel)

### Day 2 (8-10 hours)
- Railway data imports (can run overnight)
- Frontend optimization and testing

### Day 3 (2-3 hours)
- Testing and verification
- Documentation
- Cleanup

**Total**: 13-17 hours over 3 days

---

**Last Updated**: 2025-11-13
**Status**: Ready for execution
**Dependencies**: Railway backend deployment (RAILWAY_MIGRATION_PLAN.md)
