# Direct VPS Frontend Deployment

**Status:** Live production frontend path
**Last Updated:** 2026-03-13

This document defines the app-local deployment path for the Wait Time Canada
frontend now running on the shared VPS.

Shared-VPS ownership note:

1. Shared host topology, ingress ownership, release-root conventions, and live
   cross-project inventory are canonical in `/home/jer/repos/platform-ops`.
2. Use `/home/jer/repos/platform-ops/docs/standards/PLAT-009-shared-vps-documentation-boundary.md`
   for the documentation boundary.
3. This repo remains canonical for Wait Time Canada's frontend packaging,
   deploy, verify, and rollback steps.
4. The backend scheduler/runtime path now has its own companion runbook in
   `docs/operations/direct-vps-backend.md`.

## Current State

As of 2026-03-13:

1. `https://wait-time.ca` is live on the shared VPS through host Caddy.
2. `https://www.wait-time.ca` redirects to the apex host through the same VPS route.
3. `platform-ops` inventory now records `waittime-frontend` as a live Docker web service.
4. Netlify should be treated as rollback-only for the frontend path.

## Target Runtime Shape

The VPS target mirrors the other direct-VPS web apps:

1. Docker container for the Next.js frontend
2. Host-managed Caddy for public ingress
3. Loopback-only upstream bind: `127.0.0.1:3400 -> container:3000`
4. Release root: `/srv/apps/waittime-frontend`
5. Env file: `/etc/projects-merge/env/waittime-frontend.env`
6. Public health endpoint: `https://wait-time.ca/api/health`
7. Private health endpoint: `http://127.0.0.1:3400/api/health`

## Required Env Contract

Required:

1. `DATABASE_URL`
2. `NEXT_PUBLIC_MAPBOX_TOKEN`

Recommended:

1. `NEXT_PUBLIC_BASE_URL=https://wait-time.ca`
2. `HEARTBEAT_STALE_THRESHOLD_MINUTES=120` to match the hourly GitHub Actions backend cadence

Deployment note:

1. `NEXT_PUBLIC_MAPBOX_TOKEN` and `NEXT_PUBLIC_BASE_URL` must be present at
   image build time because they are embedded into the Next.js frontend bundle.
2. `APP_VERSION` is injected by the deploy script so `/api/health` can expose
   the deployed revision.

## Packaging Files

The direct-VPS path uses:

1. `frontend/Dockerfile`
2. `scripts/deploy-vps-frontend.sh`
3. `scripts/release-vps-frontend.sh`

## Local Preflight

Before preparing a release:

```bash
cd /home/jer/repos/waittimecanada/frontend
npm run lint
npm run type-check
npm run test:unit
npm run build
```

## Deploy On The VPS

From the checked-out release on the VPS:

```bash
cd /srv/apps/waittime-frontend/current
./scripts/deploy-vps-frontend.sh /etc/projects-merge/env/waittime-frontend.env
```

The deploy script:

1. builds the frontend image from `frontend/`
2. tags it with the git revision when available
3. replaces any existing `waittime-frontend` container
4. runs the container with `--restart unless-stopped`
5. binds it privately at `127.0.0.1:3400:3000`
6. sets `APP_VERSION` for health visibility

## Stage And Release From A Workstation

```bash
cd /home/jer/repos/waittimecanada
./scripts/release-vps-frontend.sh user@your-vps --deploy
```

Defaults:

1. app root: `/srv/apps/waittime-frontend`
2. env file: `/etc/projects-merge/env/waittime-frontend.env`

## Verification

After deploy, verify:

```bash
curl -fsS http://127.0.0.1:3400/api/health
curl -fsS https://wait-time.ca/api/health
PRODUCTION_BASE_URL=https://wait-time.ca ./scripts/production-smoke.sh
```

Expected outcome:

1. private and public health return HTTP `200`
2. page smoke checks pass for `/`, `/methods`, `/data-quality`, and `/analytics`
3. `/api/health` reflects the current backend freshness state in the database, so `healthy` may be `false` even when the frontend cutover itself is correct

Suggested Caddy shape after cutover:

```caddy
www.wait-time.ca {
    redir https://wait-time.ca{uri} 308
}

wait-time.ca {
    encode zstd gzip
    reverse_proxy 127.0.0.1:3400
}
```

## Rollback

Rollback is release-based:

1. identify the previous release in `/srv/apps/waittime-frontend/releases`
2. repoint `/srv/apps/waittime-frontend/current`
3. rerun `./scripts/deploy-vps-frontend.sh /etc/projects-merge/env/waittime-frontend.env`
4. repeat the health and smoke verification

## Current Production Rule

Treat this as the live production path. If a rollback is required, document the
reason and flip shared status surfaces in `platform-ops` back to rollback mode
instead of treating Netlify as silently active.
