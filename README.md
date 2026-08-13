# OSM Highway Topology Checker

Detects topological errors in OpenStreetMap's hierarchical road tagging system.

A highway way segment is flagged as a **potential error** when:

1. Its classification is `motorway` → `tertiary` (inclusive of `_link` variants)
2. **Both** of its terminus nodes connect to at least one other road
3. Neither terminus connects to a road of **equal or higher** classification

This pattern indicates a road that is "stranded" — it cannot be reached from or
continue to a road of appropriate importance, suggesting a missing link, a
misclassified segment, or a connectivity error in the map.

Dead-ends (one terminus with no connecting roads) and map boundary termini are
**excluded** automatically, avoiding false positives for cul-de-sacs and
extract edges.

---

## Installation

```bash
pip install osmium          # core dependency
pip install -e ".[dev]"     # + pytest for development
```

`osmium` requires `libosmium` system libraries. On Debian/Ubuntu:

```bash
sudo apt install libosmium-dev libprotozero-dev
pip install osmium
```

On macOS with Homebrew:

```bash
brew install libosmium
pip install osmium
```

---

## Usage

```bash
# Analyse a regional extract
python -m road_topology path/to/region.osm.pbf

# With a custom output directory
python -m road_topology region.osm.pbf --output-dir results/

# Only emit the JSON report consumed by the frontend
python -m road_topology region.osm.pbf --json-only

# Verbose logging
python -m road_topology region.osm.pbf -v
```

### Output files

By default, four files are written per run, timestamped:

| File                                             | Description                                |
| ------------------------------------------------ | ------------------------------------------ |
| `osm_highway_errors_YYYYMMDD_HHMMSS.json`        | Structured report consumed by the frontend |
| `osm_highway_errors_YYYYMMDD_HHMMSS.csv`         | Tabular data for spreadsheet review        |
| `osm_highway_errors_YYYYMMDD_HHMMSS.geojson`     | Line features for QGIS / geojson.io        |
| `osm_highway_errors_YYYYMMDD_HHMMSS_summary.txt` | Human-readable run summary                 |

Use `--json-only` to write just the JSON report, or `--html-only` /
`--with-html-report` to also produce a legacy standalone HTML table (kept
for offline viewing outside of the frontend app).

The GeoJSON draws a line between the two terminus points of each flagged way.
Load in QGIS or drag into [geojson.io](https://geojson.io) for immediate visual review.

Each flagged way includes a direct OSM link for quick editing:

```
https://www.openstreetmap.org/way/<ID>
```

---

## Highway class hierarchy

| Class                      | Rank | Analysed?      |
| -------------------------- | ---- | -------------- |
| motorway / motorway_link   | 1    | ✅             |
| trunk / trunk_link         | 2    | ✅             |
| primary / primary_link     | 3    | ✅             |
| secondary / secondary_link | 4    | ✅             |
| tertiary / tertiary_link   | 5    | ✅             |
| unclassified               | 6    | neighbour only |
| residential                | 6    | neighbour only |
| service                    | 7    | neighbour only |
| track / path / footway     | 8–9  | neighbour only |

`unclassified` and `residential` are treated as equivalent (rank 6) and are
valid lower-class neighbours for tertiary roads, but are never checked
themselves.

---

## Architecture

```
parse_pbf_with_locations()          parser.py
  │
  │  Single pass, osmium location store
  │  Output: ways dict + node_coords dict
  ▼
build_terminus_index()              checker.py
  │
  │  node_id → [WayRecord, ...]
  ▼
check_topology()                    checker.py
  │
  │  For each analysed way:
  │    evaluate_terminus(start) → TerminusInfo
  │    evaluate_terminus(end)   → TerminusInfo
  │    if both connected + neither qualifies → FlaggedWay
  ▼
write_all()                         writers.py
     JSON report (frontend) + CSV + GeoJSON + summary
```

### Memory and performance

For regional extracts (e.g. a US state, ~100 MB–2 GB PBF):

- Peak RAM: ~1–4 GB (osmium location store holds all node coords in memory
  during the single pass; only the relevant ways and terminus coords are
  retained afterwards)
- Runtime: typically 1–10 minutes

For **planet-scale** processing, consider:

- Using a regional extract from [Geofabrik](https://download.geofabrik.de/)
- Or replacing the single-pass approach with osmium's `NodeLocationsForWays`
  index backed by a disk-based store (e.g. `DiskBasedNodeLocationsForWays`)
  which trades speed for lower peak RAM.

### Daily diff workflow

To track changes day-over-day:

1. Run the checker on each daily PBF, saving output with datestamped filenames.
2. Compare `way_id` sets between consecutive CSV outputs to find:
   - **Newly introduced errors** (in today's output, not yesterday's)
   - **Fixed errors** (in yesterday's output, not today's)

This can be scripted with a simple `pandas` join or a shell `comm` on sorted
way ID columns.

---

## GitHub Actions: Automated Nightly Analysis

The repository includes a GitHub Actions workflow that:

1. **Downloads** the latest PBF extracts from Geofabrik for all US states
2. **Analyzes** each extract for topology errors
3. **Generates** a per-state JSON report (rendered client-side by the static frontend)
4. **Copies** the static HTML/CSS/JS frontend, which lists all states and links to each report
5. **Deploys** everything to GitHub Pages

### Workflow Configuration

The workflow is defined in `.github/workflows/nightly-analysis.yml`:

- **Schedule**: Runs every Friday at 7:34 AM UTC via cron
- **Manual trigger**: Can be triggered on-demand via "Run workflow" button
- **Duration**: Typically 30–60 minutes for all 50 US states

### Output Structure

Published to GitHub Pages:

```
gh-pages/
├── index.html              # Static homepage with all state links
├── app.js                  # Vanilla JS app logic (fetching, routing, rendering)
├── style.css               # Compiled, purged Tailwind CSS (built via frontend/build.sh)
├── results.json            # Machine-readable summary for each state
└── reports/                # Per-state JSON reports, rendered by app.js
    ├── vermont.json
    ├── maine.json
    ├── new-york.json
    └── ... (one per state)
```

Each state's detail view is served client-side by `app.js` at
`#/state/<slug>`, which fetches `reports/<slug>.json` and renders the flagged
ways as an interactive table — no separate static HTML page per state, and no
build step.

### Local Testing

To test the workflow locally before pushing:

```bash
# Backend: Download a single state and analyze
python scripts/download_and_analyze.py

# This generates gh-pages/results.json (summary) and
# gh-pages/reports/<state>.json (per-state detail, consumed by the frontend)

# Frontend: no build step needed — serve the static files directly
cd frontend
python -m http.server 8000  # Preview at http://localhost:8000/
```

Outputs go to `gh-pages/` directory by default, which is `.gitignore`'d.

### Deployment Architecture

The GitHub Pages deployment consists of:

1. **Python Backend** (`road_topology/`)
   - Analyzes OSM data for topology errors
   - Generates `results.json` with analysis metadata and per-state summaries
   - Produces per-state JSON reports (`reports/<state>.json`) with the flagged
     ways and their properties, for the frontend to render

2. **Static Frontend** (`frontend/`)
   - Plain HTML, CSS, and vanilla JavaScript — no framework, no Node.js/npm
   - Tailwind CSS is precompiled with the standalone Tailwind CLI (`frontend/build.sh`) into a purged `style.css`
   - Consumes `results.json` for the interactive dashboard
   - Provides search, filtering, and sorting of state results
   - Renders each state's detail report client-side (via `#/state/<slug>`) by
     fetching and displaying `reports/<slug>.json` — no separate HTML pages

3. **GitHub Pages Output** (`gh-pages/`)
   - The frontend's static files are copied as-is to `gh-pages/`
   - Static analysis results (`results.json`, `reports/*.json`) also stored there
   - Single source of truth at root domain

### GitHub Pages Setup

To use this workflow:

1. **Enable GitHub Pages** in repository settings
   - Source: Deploy from a branch
   - Branch: `gh-pages`
   - Folder: `/ (root)`

2. **Check Actions permissions**
   - Settings → Actions → General
   - Allow GitHub Actions to create and approve pull requests
   - Allow read and write permissions

3. **First deployment** (after first workflow run)
   - Go to Actions tab and wait for the workflow to complete
   - Pages should then be available at: `https://your-username.github.io/road_topology/`

---

## Running tests

```bash
pytest tests/ -v
```

The test suite covers:

- Hierarchy rank ordering and link road equivalence
- Terminus index construction
- Topology flag/no-flag decisions for all key cases
- Output dict structure and coordinate attachment
