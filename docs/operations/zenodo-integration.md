# Zenodo DOI Integration Guide

> **Status: Repo Prepared, External Activation Parked**
>
> The repository and release side are prepared, but the real DOI does **not** exist yet. The remaining Zenodo activation and publication steps are intentionally parked until explicit maintainer approval.

## Overview

This guide documents how to link the GitHub repository to Zenodo to generate a permanent Digital Object Identifier (DOI) for academic citations.

**Current Status:**
- Repository prepared with `.zenodo.json` metadata
- `CITATION.cff` updated for the current public release
- Current public release prepared on GitHub
- Zenodo activation and publication still require human account access

**Remaining work:** Human action is required in Zenodo after this track is explicitly activated.

---

## Benefits of Zenodo Integration

- **Permanent Citation:** DOI provides a stable, citable reference for your work
- **Academic Credibility:** Zenodo is recognized by academic institutions worldwide
- **Archival:** Automatic archival of each GitHub release
- **Discoverability:** Listed in academic databases and search engines
- **Version Tracking:** Each release gets its own DOI (with concept DOI for all versions)
- **Metadata Preservation:** `.zenodo.json` ensures proper attribution and keywords

---

## Prerequisites

- GitHub repository with releases
- `.zenodo.json` metadata file
- `CITATION.cff` file
- README DOI badge will be added only after a real DOI exists
- Zenodo account access

---

## Step-by-Step Integration

### Step 1: Create Zenodo Account (2 minutes)

1. Go to **[https://zenodo.org](https://zenodo.org)**
2. Click **"Log in"** in the top-right corner
3. Click **"Log in with GitHub"**
4. Authorize Zenodo to access the GitHub account
5. Zenodo redirects to the Zenodo dashboard

**Why GitHub login?** This links the GitHub account for repository syncing.

---

### Step 2: Enable GitHub Integration (3 minutes)

1. In Zenodo, click your **username** (top-right) → **"GitHub"**
2. Zenodo shows the GitHub integration page with a list of repositories
3. Find **"jerdaw/waittimecanada"** in the list
4. Click the **"On"** toggle switch to enable syncing
5. The switch should turn green, indicating the repository is now linked

**What happens now?** Zenodo will automatically create a DOI for:
- The latest release
- Future releases you create

---

### Step 3: Trigger First DOI Generation (2 minutes)

**Option A: Use Existing Release (Recommended)**

Since the current public release already exists on GitHub:
1. On the Zenodo GitHub page, click **"Sync now"** button
2. Zenodo will fetch your latest release
3. Wait 30-60 seconds for processing
4. You'll see a new entry on your [Zenodo Uploads page](https://zenodo.org/me/uploads)

**Option B: Create New Release (If Needed)**

If you prefer a fresh release:
```bash
# Tag the current commit
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin vX.Y.Z

# Create GitHub release
gh release create vX.Y.Z --title "Release vX.Y.Z" --notes "Release for Zenodo archival."
```

Zenodo will automatically detect the new release within minutes.

---

### Step 4: Publish on Zenodo (2 minutes)

1. Go to [https://zenodo.org/me/uploads](https://zenodo.org/me/uploads)
2. Confirm the repository is listed (it may say "In progress")
3. Click on the repository entry
4. Review the metadata (pre-filled from `.zenodo.json`):
   - Title
   - Authors
   - Description
   - Keywords
   - License (MIT)
   - Related identifiers
5. Click **"Publish"** button
6. The DOI is live after publication.

---

### Step 5: Verify DOI Badge (1 minute)

1. Go to the GitHub repository: https://github.com/jerdaw/waittimecanada
2. Check the README after the badge is added in a follow-up commit
3. Click the badge to verify it links to your Zenodo record

**Badge URL Format:** Zenodo will provide both the badge image URL and the latest DOI link after publication.

The badge automatically updates when new releases are created.

---

## Understanding Your DOIs

Zenodo creates **two types of DOIs**:

### 1. Concept DOI (Permanent)
- Example: `10.5281/zenodo.1234567`
- Points to **all versions** of the repository
- Use this in your CV, applications, and general citations
- Never changes, even with new releases

### 2. Version DOI (Specific)
- Example: `10.5281/zenodo.1234568` (for v1.0.0)
- Points to a **specific release**
- Use this when citing a particular version in research
- Each release gets its own version DOI

**Best Practice:** Use the **concept DOI** in the README badge and general citations.

---

## Updating CITATION.cff (Optional)

After a DOI exists, add it to `CITATION.cff`:

```yaml
cff-version: 1.2.0
title: "Wait Time Canada"
message: "If you use this software, please cite it as below."
type: software
authors:
  - family-names: "Dawson"
    given-names: "Jeremy"
repository-code: "https://github.com/jerdaw/waittimecanada"
url: "https://github.com/jerdaw/waittimecanada"
abstract: "A clinically defensible Health Systems Observatory for Canadian emergency department wait-time methodology and data quality."
keywords:
  - health systems
  - emergency medicine
  - wait times
  - methodology audit
  - open data
  - Canada
  - healthcare analytics
license: MIT
version: "1.0.0"
date-released: "2026-02-11"
doi: 10.5281/zenodo.XXXXXXX  # ← Add your concept DOI here
```

---

## Troubleshooting

### Badge Shows "DOI Not Found"
- **Cause:** Repository not yet published on Zenodo
- **Fix:** Complete Step 4 (Publish on Zenodo)

### Repository Not Visible in Zenodo GitHub Page
- **Cause:** GitHub integration not authorized
- **Fix:** Re-authorize Zenodo in [GitHub Settings → Applications](https://github.com/settings/applications)

### Metadata Incorrect on Zenodo
- **Cause:** `.zenodo.json` malformed or not detected
- **Fix:** Validate `.zenodo.json` syntax, ensure it's in repository root, create new release

### Zenodo Not Detecting New Releases
- **Cause:** Webhook delay or sync issue
- **Fix:** Use "Sync now" button on Zenodo GitHub page

---

## For Future Releases

Once Zenodo is linked, routine releases require no additional manual Zenodo action.

Every time you create a GitHub release:
1. Zenodo automatically detects it
2. Creates a new version DOI
3. Updates the concept DOI to point to latest
4. Archives the release files
5. Updates the README badge

---

## Citation Examples

### APA Format
```
Dawson, J. (2026). Wait Time Canada (Version 1.3.0) [Computer software].
https://doi.org/10.5281/zenodo.XXXXXXX
```

### IEEE Format
```
J. Dawson, "Wait Time Canada," Version 1.3.0, 2026. [Online].
Available: https://doi.org/10.5281/zenodo.XXXXXXX
```

### BibTeX Format
```bibtex
@software{dawson2026waittimecanada,
  author = {Dawson, Jeremy},
  title = {Wait Time Canada},
  version = {1.3.0},
  year = {2026},
  doi = {10.5281/zenodo.XXXXXXX},
  url = {https://github.com/jerdaw/waittimecanada}
}
```

---

## Resources

- **Zenodo Documentation:** https://help.zenodo.org/
- **GitHub-Zenodo Integration:** https://guides.github.com/activities/citable-code/
- **DOI System:** https://www.doi.org/
- **Zenodo Communities:** https://zenodo.org/communities/ (consider joining relevant health/Canada communities)

---

## Checklist

- [ ] Create Zenodo account via GitHub login
- [ ] Enable waittimecanada repository in Zenodo GitHub settings
- [ ] Sync or create release to trigger DOI generation
- [ ] Publish on Zenodo
- [ ] Verify DOI badge displays correctly on GitHub
- [ ] (Optional) Add DOI to CITATION.cff
- [ ] (Optional) Add DOI to public citation and project materials

**Estimated Time:** 10 minutes

**Once complete:** The repository will have a permanent, citable DOI recognized by academic institutions worldwide.
