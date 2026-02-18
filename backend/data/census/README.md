# Census Data Staging (Local Only)

This directory is used for local, temporary staging of raw Statistics Canada inputs for M28 equity-layer processing.

## Local layout

```text
backend/data/census/
├── boundaries/
│   └── on/
│       ├── lct_000a21a_e.dbf
│       ├── lct_000a21a_e.prj
│       ├── lct_000a21a_e.shp
│       ├── lct_000a21a_e.shx
│       ├── lct_000a21a_e.xml
│       └── lct_000a21a_e.zip
└── income/
    └── on/
        ├── 98-401-X2021007_English_CSV_data.csv
        ├── 98-401-X2021007_English_meta.txt
        ├── 98-401-X2021007_Geo_starting_row.CSV
        ├── 98-401-X2021007_eng_CSV.zip
        └── README_meta.txt
```

## Processing environments (M29 hardening)

Use project extras so local setup is reproducible:

```bash
cd backend
uv sync --extra dev --extra equity
```

Extras intent:

- `dev`: pytest/mypy/ruff and test tooling
- `equity`: geospatial processing stack used by `prepare_equity_layer.py`

Current `equity` stack in `backend/pyproject.toml`:

- `geopandas`
- `pyogrio`
- `pyproj`
- `shapely`

### Troubleshooting geospatial installs

- If `uv sync --extra equity` fails due platform wheel issues, try:
  - `cd backend && .venv/bin/pip install --upgrade geopandas pyogrio pyproj shapely`
- If shapefile loading fails, verify the Python environment is the backend venv:
  - `cd backend && .venv/bin/python -c "import geopandas, pyogrio, shapely; print('ok')"`
- Keep `uv.lock` updated after dependency changes:
  - `cd backend && uv lock`

## Provenance log (Ontario acquisition on 2026-02-18)

### 1) Boundary file source

- Page: `https://www12.statcan.gc.ca/census-recensement/2021/geo/sip-pis/boundary-limites/index2021-eng.cfm?year=21`
- Selections used:
  - `Language`: English
  - `Type`: Digital Boundary Files (DBF)
  - `Boundary`: Census tracts
  - `Format`: Shapefile (.shp)
- Downloaded archive: `lct_000a21a_e.zip`
- Extracted shapefile set: `lct_000a21a_e.shp/.shx/.dbf/.prj` plus metadata XML

### 2) Income file source

- Page: `https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/prof/details/download-telecharger.cfm?Lang=E`
- Section used: `Comprehensive download files` (not the confidence interval section)
- Selections used:
  - `Geographic level`: Census metropolitan areas (CMAs), tracted census agglomerations (CAs) and census tracts (CTs)
  - `File format`: CSV
- Downloaded archive: `98-401-X2021007_eng_CSV.zip`
- Extracted files: `98-401-X2021007_English_CSV_data.csv`, metadata files, and geographic row index file

### 3) How files were placed

```bash
mkdir -p backend/data/census/boundaries/on backend/data/census/income/on
# Place downloaded zip files into the matching folders, then extract:
unzip backend/data/census/boundaries/on/lct_000a21a_e.zip -d backend/data/census/boundaries/on
unzip backend/data/census/income/on/98-401-X2021007_eng_CSV.zip -d backend/data/census/income/on
```

## Verification snapshots

Use these commands to verify local copies:

```bash
ls -la backend/data/census/boundaries/on
ls -la backend/data/census/income/on
sha256sum backend/data/census/boundaries/on/* backend/data/census/income/on/*
```

Current hashes (captured 2026-02-18):

- `lct_000a21a_e.dbf`: `cc00b2bfc2f7d21c67d8fc29c1944bc60514af1687f5b0f8627848a2ec1bddb9`
- `lct_000a21a_e.prj`: `ab73d71a919003b760582daea9d1653b857b98c0a66efecb65d7d3c30911908b`
- `lct_000a21a_e.shp`: `2377029813ac123e36f46c782ebfa51e828a60e9746003ac0c7d0256e63dd2f9`
- `lct_000a21a_e.shx`: `4cec718708592b3d3bec2e7a57eb80c503cfa8437af685df6879b494b04765dd`
- `lct_000a21a_e.xml`: `3718714300cdda2672fd0569490d12a935c16472e761e69e64e158350d05066d`
- `lct_000a21a_e.zip`: `6546216274f1f4979c7692aa55e3130961878340f7170a9461051e417013920b`
- `98-401-X2021007_English_CSV_data.csv`: `4ac6bb9c6a363d0a7b54537e2ffcbf5a789da28f80ded95e0805b11f8e99b4fb`
- `98-401-X2021007_English_meta.txt`: `04125d2f09de389de7c5c7df87c4eccbb3d05978dbae50f36403737c9be38ae0`
- `98-401-X2021007_Geo_starting_row.CSV`: `e4317b43e649e1002111b468bd00523a7207d8b4188266ae87856c18f8f9f740`
- `98-401-X2021007_eng_CSV.zip`: `5d29811e5c3171cb16c9564bfbce0a08da45d1584810be2bd74764cbd2329ffc`
- `README_meta.txt`: `174972ad50565083d515a09ead8fd5972f7592957481419af3a60edbfebfbc42`

## Important rules

- Raw census files are intentionally ignored by git via `backend/.gitignore`.
- Keeping `.zip` files locally is acceptable for reproducibility; deleting them is also acceptable after extraction.
- Do not commit raw downloads.
- Commit only processed outputs under `backend/data/layers/`:
  - `ontario-equity-layer.geojson`
  - `equity-manifest-on.json`

## Processing command (for this local dataset)

```bash
cd backend
.venv/bin/python scripts/prepare_equity_layer.py \
  --province ON \
  --census-shp data/census/boundaries/on/lct_000a21a_e.shp \
  --income data/census/income/on/98-401-X2021007_English_CSV_data.csv \
  --output data/layers/ontario-equity-layer.geojson \
  --optimized-output data/layers/ontario-equity-layer.optimized.geojson \
  --manifest-output data/layers/equity-manifest-on.json \
  --include-no-data \
  --tolerance 0 \
  --optimized-tolerance 0.001 \
  --source-boundary-url "https://www12.statcan.gc.ca/census-recensement/2021/geo/sip-pis/boundary-limites/index2021-eng.cfm?year=21" \
  --source-income-url "https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/prof/details/download-telecharger.cfm?Lang=E"
```
