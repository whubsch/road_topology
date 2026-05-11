"""
OSM Highway Hierarchy Checker — CLI entry point.

Usage:
    python -m osm_highway_checker path/to/region.osm.pbf [options]

or after pip install:
    osm-highway-checker path/to/region.osm.pbf [options]
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

from .checker import check_topology
from .parser import parse_pbf_with_locations
from .writers import write_all


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="osm-highway-checker",
        description=(
            "Detect OSM highway topology errors: road segments whose both "
            "termini connect only to roads of lower classification."
        ),
    )
    p.add_argument(
        "pbf",
        metavar="FILE.osm.pbf",
        help="Path to an OSM PBF file (planet, country, or regional extract).",
    )
    p.add_argument(
        "-o",
        "--output-dir",
        default="output",
        metavar="DIR",
        help="Directory for output files (default: ./output).",
    )
    p.add_argument(
        "--prefix",
        default="osm_highway_errors",
        metavar="PREFIX",
        help="Filename prefix for output files (default: osm_highway_errors).",
    )
    p.add_argument(
        "--no-csv",
        action="store_true",
        help="Skip CSV output.",
    )
    p.add_argument(
        "--no-geojson",
        action="store_true",
        help="Skip GeoJSON output.",
    )
    p.add_argument(
        "--html-only",
        action="store_true",
        help="Output only HTML file (skip CSV and GeoJSON).",
    )
    p.add_argument(
        "--state-name",
        default=None,
        metavar="NAME",
        help="Name of state/region to display in the report title.",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger(__name__)

    t0 = time.perf_counter()

    # ── Parse ──────────────────────────────────────────────────────────────
    try:
        ways, node_coords = parse_pbf_with_locations(args.pbf)
    except FileNotFoundError:
        logger.error("PBF file not found: %s", args.pbf)
        return 1
    except Exception as exc:
        logger.exception("Failed to parse PBF: %s", exc)
        return 1

    # ── Analyse ────────────────────────────────────────────────────────────
    flagged = check_topology(ways, node_coords)

    elapsed = time.perf_counter() - t0
    logger.info("Total elapsed: %.1fs", elapsed)

    if not flagged:
        logger.info("No topology errors detected.")
        return 0

    # ── Write output ───────────────────────────────────────────────────────
    # ── Write output ──────────────────────────────────────
    written = write_all(
        flagged,
        output_dir=args.output_dir,
        pbf_path=args.pbf,
        elapsed_seconds=elapsed,
        prefix=args.prefix,
        html_only=args.html_only,
        state_name=args.state_name,
    )

    logger.info("Output files:")
    for fmt, path in written.items():
        logger.info("  %-10s %s", fmt, path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
