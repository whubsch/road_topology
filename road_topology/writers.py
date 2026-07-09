"""Output writers.

Supported formats:
  - Report JSON  Machine-readable table data consumed by the React frontend
  - HTML         Interactive table with object details and links to editors
                 (legacy/standalone format, kept for offline viewing)
  - CSV          Simple tabular format for spreadsheet review
  - GeoJSON      Point features for each flagged way (centroid of both termini)
                 with full properties; load directly in QGIS / geojson.io
  - OSM Note XML Placeholder note markers compatible with JOSM's TODO plugin
"""

from __future__ import annotations

import csv
import json
import logging
import os
from datetime import datetime, timezone

from .checker import FlaggedWay

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Report JSON (consumed by the React frontend)
# ---------------------------------------------------------------------------


def write_report_json(
    flagged: list[FlaggedWay], path: str, state_name: str | None = None
) -> None:
    """Write flagged ways to a JSON report consumed by the React frontend.

    This replaces the standalone per-state HTML page: instead of a fully
    rendered document, we emit structured data (metadata + a row per
    flagged way) so the site's React app can fetch and render it directly.
    """
    rows = []
    for fw in sorted(flagged, key=lambda x: (x.rank, -x.version)):
        row = fw.to_dict()
        row["start_connecting_highways"] = row["start_connecting_highways"] or None
        row["end_connecting_highways"] = row["end_connecting_highways"] or None
        rows.append(row)

    report = {
        "state_name": state_name,
        "generated": datetime.now(timezone.utc).isoformat(),
        "total_issues": len(flagged),
        "flagged": rows,
    }

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    logger.info("Report JSON written: %s (%d rows)", path, len(flagged))


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------


def write_html(
    flagged: list[FlaggedWay], path: str, state_name: str | None = None
) -> None:
    """Write flagged ways to an interactive HTML table.

    Each row includes:
      - Way ID
      - Highway classification
      - Version number
      - Last edit timestamp
      - Issue description
      - Links to OSM, iD, JOSM, and Level0 editors
    """
    from datetime import datetime as dt

    html_lines = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "  <meta charset='UTF-8'>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        "  <title>OSM Highway Topology Errors</title>",
        "  <link rel='icon' href='/road_topology/favicon.svg' type='image/svg+xml'>",
        "  <style>",
        "    * { font-family: sans-serif; }",
        "    body { background: #f5f5f5; padding: 20px; }",
        "    .container { max-width: 1400px; margin: 0 auto; }",
        "    h1 { color: #333; margin-bottom: 10px; }",
        "    .metadata { background: #fff; padding: 15px; border-radius: 5px; margin-bottom: 20px; color: #666; font-size: 14px; }",
        "    table { width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
        "    th { background: #2c3e50; color: white; padding: 12px; text-align: left; font-weight: bold; }",
        "    td { padding: 10px 12px; border-bottom: 1px solid #ddd; }",
        "    tr:hover { background: #f9f9f9; }",
        "    .way-id { font-family: monospace; font-weight: bold; color: #0066cc; }",
        "    .highway { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 13px; }",
        "    .timestamp { color: #666; font-size: 13px; }",
        "    .editors { white-space: nowrap; }",
        "    .editor-btn { display: inline-block; padding: 5px 10px; margin: 2px; border-radius: 3px; text-decoration: none; font-size: 12px; font-weight: bold; transition: opacity 0.2s; border: none; cursor: pointer; }",
        "    .editor-btn:hover { opacity: 0.9; }",
        "    .osm-link { background: #0066cc; color: white; }",
        "    .osm-link:visited { background: #999999; color: white; }",
        "    .id-link { background: #1c4995; color: white; }",
        "    .id-link:visited { background: #999999; color: white; }",
        "    .josm-link { background: #5a5a5a; color: white; }",
        "    .josm-link:visited { background: #999999; color: white; }",
        "    .level0-link { background: #4caf50; color: white; }",
        "    .level0-link:visited { background: #999999; color: white; }",
        "    .issue { color: #d32f2f; font-size: 13px; }",
        "    .header { font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: 0.5px; }",
        "  </style>",
        "</head>",
        "<body>",
        "<div class='container'>",
        f"  <h1>🚗 OSM Highway Topology Errors{' — ' + state_name if state_name else ''}</h1>",
        "  <div class='metadata'>",
        f"    <strong>Generated:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}<br>",
        f"    <strong>Total Issues:</strong> {len(flagged):,}<br>  </div>",
        "  <table>",
        "    <thead>",
        "      <tr>",
        "        <th class='header'>Way ID</th>",
        "        <th class='header'>Name</th>",
        "        <th class='header'>Highway</th>",
        "        <th class='header'>Version</th>",
        "        <th class='header'>Last Edited</th>",
        "        <th class='header'>Issue</th>",
        "        <th class='header'>Edit</th>",
        "      </tr>",
        "    </thead>",
        "    <tbody>",
    ]

    # Sort by highway class (rank), then by version (descending)
    for fw in sorted(flagged, key=lambda x: (x.rank, -x.version)):
        # Build issue description
        issue = (
            f"Start: {fw.start.connecting_highways or 'none'}; "
            f"End: {fw.end.connecting_highways or 'none'}"
        )

        # Parse and format timestamp in a user-friendly way
        try:
            ts = dt.fromisoformat(fw.timestamp.replace("Z", "+00:00"))
            formatted_timestamp = ts.strftime("%-d %b '%y")
        except (ValueError, AttributeError):
            formatted_timestamp = fw.timestamp

        # Escape HTML characters in issue
        issue_escaped = (
            issue.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

        html_lines.extend(
            [
                "      <tr>",
                f"        <td class='way-id'><a href='{fw.osm_url()}' target='_blank'>{fw.way_id}</a></td>",
                f"        <td>{fw.name or ''}</td>",
                f"        <td><span class='highway'>{fw.highway}</span></td>",
                f"        <td>{fw.version}</td>",
                f"        <td class='timestamp'>{formatted_timestamp}</td>",
                f"        <td class='issue'>{issue_escaped}</td>",
                "        <td class='editors'>",
                f"          <a href='{fw.osm_url()}' target='_blank' class='editor-btn osm-link'>OSM</a>",
                f"          <a href='{fw.id_url()}' target='_blank' class='editor-btn id-link'>iD</a>",
                f"          <a href='{fw.josm_url()}' target='_blank' class='editor-btn josm-link'>JOSM</a>",
                f"          <a href='{fw.level0_url()}' target='_blank' class='editor-btn level0-link'>L0</a>"
                f"        </td>",
                "      </tr>",
            ]
        )

    html_lines.extend(
        [
            "    </tbody>",
            "  </table>",
            "</div>",
            "</body>",
            "</html>",
        ]
    )

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(html_lines))
    logger.info("HTML written: %s (%d rows)", path, len(flagged))


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

CSV_FIELDS = [
    "way_id",
    "name",
    "highway",
    "rank",
    "start_node_id",
    "start_lat",
    "start_lon",
    "start_connecting_highways",
    "start_min_rank",
    "end_node_id",
    "end_lat",
    "end_lon",
    "end_connecting_highways",
    "end_min_rank",
    "josm_url",
]


def write_csv(flagged: list[FlaggedWay], path: str) -> None:
    """Write flagged ways to a CSV file."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for fw in flagged:
            writer.writerow(fw.to_dict())
    logger.info("CSV written: %s (%d rows)", path, len(flagged))


# ---------------------------------------------------------------------------
# GeoJSON
# ---------------------------------------------------------------------------


def write_geojson(flagged: list[FlaggedWay], path: str) -> None:
    """
    Write flagged ways as a GeoJSON FeatureCollection.

    Each feature is a LineString connecting the two terminus points.
    If only one terminus has coordinates, a Point is used instead.
    If neither has coordinates, the feature is skipped.
    """
    features = []
    skipped = 0

    for fw in flagged:
        start_coords = (
            [fw.start.lon, fw.start.lat]
            if fw.start.lon is not None and fw.start.lat is not None
            else None
        )
        end_coords = (
            [fw.end.lon, fw.end.lat]
            if fw.end.lon is not None and fw.end.lat is not None
            else None
        )

        if start_coords and end_coords:
            geometry = {
                "type": "LineString",
                "coordinates": [start_coords, end_coords],
            }
        elif start_coords:
            geometry = {"type": "Point", "coordinates": start_coords}
        elif end_coords:
            geometry = {"type": "Point", "coordinates": end_coords}
        else:
            skipped += 1
            continue

        props = fw.to_dict()
        # Add human-readable descriptions for the map popup
        props["description"] = (
            f"{fw.highway} (rank {fw.rank}) — both ends connect only to "
            f"lower-class roads. Start neighbours: "
            f"{props['start_connecting_highways'] or 'none'}; "
            f"End neighbours: {props['end_connecting_highways'] or 'none'}"
        )

        features.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": props,
            }
        )

    collection = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "total_flagged": len(flagged),
            "features_written": len(features),
            "skipped_no_coords": skipped,
        },
    }

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(collection, fh, indent=2)

    logger.info(
        "GeoJSON written: %s (%d features, %d skipped)", path, len(features), skipped
    )


# ---------------------------------------------------------------------------
# Summary report (plain text)
# ---------------------------------------------------------------------------


def write_summary(
    flagged: list[FlaggedWay],
    path: str,
    pbf_path: str,
    elapsed_seconds: float,
) -> None:
    """Write a human-readable summary of the analysis run."""
    from collections import Counter

    counts_by_class = Counter(fw.highway for fw in flagged)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "=" * 60,
        "OSM Highway Topology Error Report",
        "=" * 60,
        f"Generated:   {timestamp}",
        f"Source PBF:  {pbf_path}",
        f"Elapsed:     {elapsed_seconds:.1f}s",
        "",
        f"Total flagged ways: {len(flagged):,}",
        "",
        "Breakdown by highway class:",
    ]

    for hw_class in [
        "motorway",
        "motorway_link",
        "trunk",
        "trunk_link",
        "primary",
        "primary_link",
        "secondary",
        "secondary_link",
        "tertiary",
        "tertiary_link",
    ]:
        count = counts_by_class.get(hw_class, 0)
        if count:
            lines.append(f"  {hw_class:<20} {count:>6,}")

    lines += [
        "",
        "Detection rule:",
        "  A way is flagged when both termini connect only to roads of",
        "  lower classification (higher rank number), meaning the way",
        "  cannot be reached from or continue to an equal/higher-class road.",
        "  Dead-ends and boundary termini are excluded.",
        "=" * 60,
    ]

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    # Also print to stdout
    print("\n".join(lines))
    logger.info("Summary written: %s", path)


# ---------------------------------------------------------------------------
# Convenience: write all formats at once
# ---------------------------------------------------------------------------


def write_all(
    flagged: list[FlaggedWay],
    output_dir: str,
    pbf_path: str,
    elapsed_seconds: float,
    prefix: str = "osm_highway_errors",
    html_only: bool = False,
    json_only: bool = False,
    write_html_report: bool = False,
    state_name: str | None = None,
) -> dict[str, str]:
    """
    Write output files to output_dir.

    By default, writes a JSON report (consumed by the React frontend), CSV,
    GeoJSON, and a plain-text summary.

    - If json_only=True, writes only the JSON report.
    - If html_only=True, writes only the (legacy) standalone HTML file.
    - If write_html_report=True, also writes the legacy standalone HTML file
      alongside the other formats.

    Returns a dict of {format: filepath}.
    """
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"{prefix}_{date_str}"

    if html_only:
        paths = {"html": os.path.join(output_dir, f"{stem}.html")}
        write_html(flagged, paths["html"], state_name=state_name)
        return paths

    paths = {
        "json": os.path.join(output_dir, f"{stem}.json"),
    }
    write_report_json(flagged, paths["json"], state_name=state_name)

    if not json_only:
        paths["csv"] = os.path.join(output_dir, f"{stem}.csv")
        paths["geojson"] = os.path.join(output_dir, f"{stem}.geojson")
        paths["summary"] = os.path.join(output_dir, f"{stem}_summary.txt")

        write_csv(flagged, paths["csv"])
        write_geojson(flagged, paths["geojson"])
        write_summary(flagged, paths["summary"], pbf_path, elapsed_seconds)

        if write_html_report:
            paths["html"] = os.path.join(output_dir, f"{stem}.html")
            write_html(flagged, paths["html"], state_name=state_name)

    return paths
