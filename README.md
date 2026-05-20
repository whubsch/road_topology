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
python -m osm_highway_checker path/to/region.osm.pbf

# With a custom output directory
python -m osm_highway_checker region.osm.pbf --output-dir results/

# Verbose logging
python -m osm_highway_checker region.osm.pbf -v
```

### Output files

Three files are written per run, timestamped:

| File                                             | Description                         |
| ------------------------------------------------ | ----------------------------------- |
| `osm_highway_errors_YYYYMMDD_HHMMSS.csv`         | Tabular data for spreadsheet review |
| `osm_highway_errors_YYYYMMDD_HHMMSS.geojson`     | Line features for QGIS / geojson.io |
| `osm_highway_errors_YYYYMMDD_HHMMSS_summary.txt` | Human-readable run summary          |

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
     CSV + GeoJSON + summary
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
3. **Generates** individual HTML reports for each state
4. **Creates** a homepage index with links to all reports
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
├── index.html              # Homepage with all state links and issue counts
├── results.json            # Machine-readable results for each state
├── vermont.html            # Individual state report (no timestamp)
├── maine.html
├── new-york.html
└── ... (one per state)
```

### Local Testing

To test the workflow locally before pushing:

```bash
# Download a single state and analyze
python scripts/download_and_analyze.py

# Or run directly
python -m road_topology path/to/extract.osm.pbf --html-only --state-name "Vermont"

# Generate the homepage
python scripts/generate_homepage.py
```

Outputs go to `gh-pages/` directory by default, which is `.gitignore`'d.

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
