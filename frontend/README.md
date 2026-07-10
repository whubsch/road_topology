# Road Topology Frontend

A plain HTML/CSS/JavaScript dashboard for viewing OSM highway topology error
analysis results. No framework, and no Node.js/npm required — Tailwind CSS is
compiled ahead of time with the standalone Tailwind CLI into a small, purged
`style.css` file.

## Features

- **Interactive Dashboard**: View all state analysis results with real-time search and filtering
- **Smart Sorting**: Sort by state name or issue count (ascending/descending)
- **Status Filtering**: Filter by successful analyses or failed runs
- **Live Statistics**: Dashboard displays total states, total issues, and success rate
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **State Reports**: Detailed, per-state issue tables with links to iD, JOSM, and Level0 editors

## Development

`style.css` is a generated file, compiled from `input.css`. If you change
`input.css` or add/remove Tailwind classes in `index.html`/`app.js`, rebuild it:

```bash
cd frontend
./build.sh
```

This downloads the standalone Tailwind CLI binary for your platform (cached as
`.tailwindcss-cli`, gitignored) — no Node.js or npm required — and regenerates
`style.css`.

To preview locally, serve this directory with any static file server, for example:

```bash
cd frontend
python -m http.server 8000
```

Then open `http://localhost:8000/`.

## Deployment

The GitHub Actions workflow copies the contents of this directory directly
into `gh-pages/`, then the analysis script overwrites `results.json` and
`reports/*.json` with fresh data.

## Data Format

The frontend expects a `results.json` file with the following structure:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "total_states": 50,
  "total_issues": 1234,
  "successful_analyses": 48,
  "results": [
    {
      "state": "vermont",
      "name": "Vermont",
      "issues": 42,
      "success": true
    }
  ]
}
```

Each state also has a `reports/<state>.json` file with the detailed,
per-way issue list rendered on the state report page.

## File Structure

- `index.html` — page shell
- `app.js` — all application logic: data fetching, hash-based routing, and rendering
- `input.css` — Tailwind entry point plus custom styles not covered by utility classes
- `style.css` — **generated** by `build.sh`; the compiled, purged CSS actually served to the browser
- `build.sh` — downloads the standalone Tailwind CLI and compiles `input.css` → `style.css`
- `results.json` / `reports/*.json` — sample data for local development (overwritten in CI)
