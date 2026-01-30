# WaitTime Canada - Frontend

Next.js 14 frontend with interactive hospital wait time map.

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment Variables

Copy the example file and add your credentials:

```bash
cp .env.local.example .env.local
```

Edit `.env.local` and add:

- **DATABASE_URL**: Copy from `backend/.env.local` (same Neon PostgreSQL connection string)
- **NEXT_PUBLIC_MAPBOX_TOKEN**: Get from https://account.mapbox.com/access-tokens/

Example `.env.local`:

```env
DATABASE_URL=postgresql://user:pass@ep-xxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
NEXT_PUBLIC_MAPBOX_TOKEN=pk.eyJ1IjoiZXhhbXBsZSIsImEiOiJjbHh4eHh4eHgifQ.xxxxx
```

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Features

### Interactive Map

- **Color-coded markers** by wait time:
  - 🟢 Green: < 60 minutes
  - 🟡 Yellow: 60-120 minutes
  - 🔴 Red: > 120 minutes

- **Click markers** to view hospital details:
  - Hospital name and location
  - Current wait time
  - Last updated timestamp

- **Pan and zoom** to explore different regions

### API Routes

#### GET `/api/hospitals`

Returns all verified, visible hospitals with their latest wait times.

Query parameters:
- `province` (optional): Filter by province code (e.g., "ON", "QC")

Response:
```json
{
  "success": true,
  "count": 10,
  "data": [
    {
      "id": "ca-on-cheo",
      "name": "CHEO",
      "province": "ON",
      "city": "Ottawa",
      "latitude": 45.4215,
      "longitude": -75.6972,
      "current_wait_time": 108,
      "last_updated": "2026-01-30T16:01:30Z"
    }
  ]
}
```

## Architecture

- **Next.js 14** with App Router
- **React Map GL** for Mapbox integration
- **TailwindCSS** for styling
- **TypeScript** for type safety
- **Direct PostgreSQL connection** to Neon (no ORM)

## Development

```bash
# Run dev server
npm run dev

# Type check
npm run type-check

# Lint
npm run lint

# Format code
npm run format

# Run tests
npm run test:unit
npm run test:e2e
```

## Deployment

### Vercel (Recommended)

1. Push to GitHub
2. Import project to Vercel
3. Add environment variables in Vercel dashboard
4. Deploy

### Environment Variables for Production

- `DATABASE_URL`: Neon PostgreSQL connection string
- `NEXT_PUBLIC_MAPBOX_TOKEN`: Mapbox public token
- `NEXT_PUBLIC_VERCEL_ANALYTICS_ID` (optional): Analytics tracking

## Notes

- Only **verified and visible** hospitals appear on the map
- Wait times are fetched from the latest measurement in the database
- Map requires valid Mapbox token to render
