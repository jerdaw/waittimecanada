# Security Policy

## Supported Versions

We currently support the latest version on the `main` branch. Security updates are applied to the current release only.

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |
| < main  | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in Wait Time Canada, please report it responsibly.

### How to Report

**Preferred:** Use [GitHub Security Advisories](https://github.com/jerdaw/waittimecanada/security/advisories/new) for private disclosure.

**Alternative:** Email the repository owner (contact available in GitHub profile).

### What to Include

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Suggested fix (if you have one)

### Response Timeline

- **Acknowledgment:** Within 72 hours
- **Initial Assessment:** Within 1 week
- **Resolution:** Depends on severity and complexity

## Scope

### What This Project Handles

- **Public health data only:** All data is scraped from publicly available provincial health authority websites
- **Aggregate wait times:** We collect hospital-level statistics, not individual patient information
- **Metadata:** Hospital locations, names, and contact information (all publicly available)

### What This Project Does NOT Handle

- **No Protected Health Information (PHI):** We do not access, store, or process any individual patient data
- **No Personal Identifiable Information (PII):** No user accounts, no login credentials, no personal data collection
- **No PHIPA-regulated data:** This project is outside the scope of Ontario's Personal Health Information Protection Act

### Security Safeguards

Our architecture includes several layers of security:

1. **SHA256 payload hashing:** Raw scraper responses are hashed (not stored in full) to detect silent data corruption
2. **30-day retention policy:** Raw measurement data older than 30 days is deleted; only aggregates are retained
3. **No full HTML storage:** Only the first 200 characters of raw payloads are stored for debugging purposes
4. **Read-only scrapers:** Our scrapers only read publicly available data; they do not authenticate or submit forms
5. **No cookies or tracking:** The frontend does not use analytics or tracking services
6. **IP geolocation is ephemeral:** Server-side geolocation processing returns results with `Cache-Control: no-store`

## Security Best Practices

If you're deploying this project:

- **Never commit secrets:** Use `.env.local` for sensitive configuration (already in `.gitignore`)
- **Rotate database credentials:** If you suspect credential exposure, rotate Neon PostgreSQL credentials immediately
- **Review dependencies:** Run `npm audit` and `pip-audit` regularly
- **Enable Dependabot:** Automated dependency updates are configured in `.github/dependabot.yml`

## Out of Scope

The following are explicitly **not** security issues for this project:

- **Scraped data inaccuracies:** Report data quality issues via [GitHub Issues](https://github.com/jerdaw/waittimecanada/issues) instead
- **Provincial source downtime:** We are not responsible for upstream data availability
- **Rate limiting or abuse prevention:** This is a portfolio project, not a production service; DoS concerns are out of scope

## Contact

For non-security issues, please use [GitHub Issues](https://github.com/jerdaw/waittimecanada/issues).

For general questions, see our [Contributing Guidelines](CONTRIBUTING.md).
