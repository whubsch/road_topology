#!/usr/bin/env python3
"""
Download OSM PBF files from Geofabrik and analyze them for topology errors.

Processes all US state extracts, generates HTML reports, and stores them for
GitHub Pages deployment.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# State name mapping for display
STATE_NAMES = {
    "alabama": "Alabama",
    "alaska": "Alaska",
    "arizona": "Arizona",
    "arkansas": "Arkansas",
    "california": "California",
    "colorado": "Colorado",
    "connecticut": "Connecticut",
    "delaware": "Delaware",
    "district-of-columbia": "District of Columbia",
    "florida": "Florida",
    "georgia": "Georgia",
    "hawaii": "Hawaii",
    "idaho": "Idaho",
    "illinois": "Illinois",
    "indiana": "Indiana",
    "iowa": "Iowa",
    "kansas": "Kansas",
    "kentucky": "Kentucky",
    "louisiana": "Louisiana",
    "maine": "Maine",
    "maryland": "Maryland",
    "massachusetts": "Massachusetts",
    "michigan": "Michigan",
    "minnesota": "Minnesota",
    "mississippi": "Mississippi",
    "missouri": "Missouri",
    "montana": "Montana",
    "nebraska": "Nebraska",
    "nevada": "Nevada",
    "new-hampshire": "New Hampshire",
    "new-jersey": "New Jersey",
    "new-mexico": "New Mexico",
    "new-york": "New York",
    "north-carolina": "North Carolina",
    "north-dakota": "North Dakota",
    "ohio": "Ohio",
    "oklahoma": "Oklahoma",
    "oregon": "Oregon",
    "pennsylvania": "Pennsylvania",
    "rhode-island": "Rhode Island",
    "south-carolina": "South Carolina",
    "south-dakota": "South Dakota",
    "tennessee": "Tennessee",
    "texas": "Texas",
    "utah": "Utah",
    "vermont": "Vermont",
    "virginia": "Virginia",
    "washington": "Washington",
    "west-virginia": "West Virginia",
    "wisconsin": "Wisconsin",
    "wyoming": "Wyoming",
}


def download_pbf(state: str, output_dir: Path) -> Path | None:
    """Download a state PBF file from Geofabrik."""
    url = f"https://download.geofabrik.de/north-america/us/{state}-latest.osm.pbf"
    output_path = output_dir / f"{state}-latest.osm.pbf"

    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info("File already exists: %s", output_path)
        return output_path

    logger.info("Downloading %s from Geofabrik...", state)
    try:
        result = subprocess.run(
            ["curl", "-L", "-o", str(output_path), url],
            check=True,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout per file
        )

        # Verify file was actually downloaded and has content
        if not output_path.exists() or output_path.stat().st_size == 0:
            logger.error("Download produced empty or missing file for %s", state)
            return None

        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info("Downloaded %s (%.1f MB): %s", state, file_size_mb, output_path)
        return output_path
    except subprocess.TimeoutExpired:
        logger.error("Download timeout for %s (exceeded 10 minutes)", state)
        return None
    except subprocess.CalledProcessError as e:
        logger.error("Failed to download %s: %s", state, e)
        return None


def analyze_pbf(pbf_path: Path, state: str, output_dir: Path) -> dict:
    """Analyze a PBF file for topology errors."""
    state_name = STATE_NAMES.get(state, state.replace("-", " ").title())
    output_file = output_dir / f"{state}.html"

    logger.info("Analyzing %s...", state)
    try:
        # Run the osm-highway-checker
        subprocess.run(
            [
                sys.executable,
                "-m",
                "road_topology",
                str(pbf_path),
                "--html-only",
                "-o",
                str(output_dir / ".tmp"),
                "--prefix",
                state,
                "--state-name",
                state_name,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        # Find the generated HTML file and rename it
        tmp_dir = output_dir / ".tmp"
        html_files = list(tmp_dir.glob(f"{state}_*.html"))

        if html_files:
            # Use the first (and should be only) HTML file
            tmp_html = html_files[0]
            tmp_html.rename(output_file)
            logger.info("Generated report: %s", output_file)

            # Clean up temporary directory
            import shutil

            try:
                shutil.rmtree(tmp_dir)
            except Exception as e:
                logger.warning("Failed to remove temp directory: %s", e)

            # Extract issue count from the HTML
            import re

            with open(output_file, "r") as f:
                content = f.read()
                # Look for "Total Issues: X,XXX" in the metadata
                match = re.search(r"Total Issues:</strong> ([\d,]+)", content)
                issue_count = int(match.group(1).replace(",", "")) if match else 0

            return {
                "state": state,
                "name": state_name,
                "issues": issue_count,
                "success": True,
            }
        else:
            logger.error("No HTML file generated for %s", state)
            return {"state": state, "name": state_name, "issues": 0, "success": False}

    except subprocess.CalledProcessError as e:
        logger.error("Failed to analyze %s: %s", state, e)
        logger.error("stdout: %s", e.stdout)
        logger.error("stderr: %s", e.stderr)
        return {"state": state, "name": state_name, "issues": 0, "success": False}


def main():
    """Main entry point."""
    # Get list of states from environment
    states_str = os.environ.get(
        "STATES",
        "vermont maine new-hampshire massachusetts rhode-island connecticut",
    )
    states = states_str.split()

    # Create output directories
    work_dir = Path("work")
    work_dir.mkdir(exist_ok=True)

    pages_dir = Path("gh-pages")
    pages_dir.mkdir(exist_ok=True)

    results = []

    for state in states:
        logger.info("=" * 60)
        logger.info("Processing %s", state)
        logger.info("=" * 60)

        # Download
        pbf_path = download_pbf(state, work_dir)
        if not pbf_path or not pbf_path.exists():
            logger.error("Failed to download PBF for %s", state)
            results.append(
                {
                    "state": state,
                    "name": STATE_NAMES.get(state, state),
                    "issues": 0,
                    "success": False,
                }
            )
            continue

        # Analyze
        result = analyze_pbf(pbf_path, state, pages_dir)
        results.append(result)

        # Clean up PBF to save space
        try:
            pbf_path.unlink()
            logger.info("Cleaned up: %s", pbf_path)
        except Exception as e:
            logger.warning("Failed to delete %s: %s", pbf_path, e)

    # Save results for homepage generation
    import json

    results_file = pages_dir / "results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info("=" * 60)
    logger.info("Analysis complete!")
    logger.info("=" * 60)
    for result in results:
        status = "✓" if result["success"] else "✗"
        logger.info(
            "%s %s: %d issues",
            status,
            result["name"],
            result["issues"],
        )


if __name__ == "__main__":
    main()
