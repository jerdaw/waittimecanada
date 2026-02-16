# Deployment: Migration to Vercel

Due to Netlify credit exhaustion on the free tier, the project has been migrated to Vercel (Hobby Tier). This document outlines the configuration changes and deployment steps.

## Configuration Changes
- **Added:** `vercel.json` (Vercel build config)
- **Removed:** `netlify.toml`, `frontend/scripts/netlify-ignore.sh`
- **Reverted:** `next.config.js` image optimization (Vercel supports this on free tier)

## Required Environment Variables (Vercel)

When deploying to Vercel, ensuring the following environment variables are set in the Vercel Project Settings:

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_MAPBOX_TOKEN` | Required for map rendering. |
| `DATABASE_URL` | Required for build-time static generation (if applicable) or API routes. |

## Build Settings
- **Framework Preset:** Next.js
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `.next`
- **Install Command:** `npm install`
