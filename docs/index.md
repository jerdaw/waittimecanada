# Wait Time Canada Documentation

Wait Time Canada is a clinically defensible Health Systems Observatory for auditing Canadian emergency department wait time data and methodology differences across provinces.

## Start Here

- Project overview: `README.md` (repo root)
- Roadmap (source of truth): `docs/planning/roadmap.md`
- API reference: `docs/API.md`
- Architecture overview: `docs/architecture/index.md`

## Deployment Status

As of **2026-03-12**, the frontend is deployed on Netlify and the application is reachable at `https://earnest-pavlova-73674e.netlify.app`. The canonical domain `https://wait-time.ca` is serving content but is not launch-ready yet because HTTPS hostname validation is still presenting the default Netlify certificate instead of a certificate valid for `wait-time.ca`. See `docs/planning/roadmap.md`.

## Safety

This project does **not** provide medical advice. For emergencies, call **911**.
