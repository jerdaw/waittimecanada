# Getting Started

This section provides the fastest path to run Wait Time Canada locally.

It is a local-development entrypoint, not the live production deployment
baseline. Current production remains split: the frontend runs on the shared VPS
at `https://wait-time.ca`, while backend scheduling and heartbeat checks remain
on GitHub Actions because the Ontario source is not reliably reachable from the
VPS.

## Recommended Path

1. Follow the root quick start in `README.md`.
2. Review backend specifics in `backend/README.md`.
3. Review frontend specifics in `frontend/README.md`.
4. Review live runtime docs in `docs/operations/direct-vps-frontend.md`,
   `docs/operations/direct-vps-backend.md`, and
   `docs/operations/scraper-scheduling.md` if you need production truth.
5. Validate roadmap context in `docs/planning/roadmap.md`.

## Quick Links

- One-page quick start: `docs/getting-started/quick-start.md`
- Development setup reference: `docs/development/setup.md`
- Live split-runtime baseline: `docs/operations/direct-vps-frontend.md`,
  `docs/operations/direct-vps-backend.md`, `docs/operations/scraper-scheduling.md`
- Architecture overview: `docs/architecture/index.md`
- API contracts: `docs/API.md`
