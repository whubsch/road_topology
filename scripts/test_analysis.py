#!/usr/bin/env python3
"""
Simple test script to generate results.json for frontend testing.
Does NOT generate HTML files - just creates the JSON data structure.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

# State name mapping
STATE_NAMES = {
    "vermont": "Vermont",
    "maine": "Maine",
    "new-hampshire": "New Hampshire",
}


def main():
    """Generate test results.json for frontend."""
    pages_dir = Path("gh-pages")
    pages_dir.mkdir(exist_ok=True)

    # Create test results
    results = [
        {"state": "vermont", "name": "Vermont", "issues": 42, "success": True},
        {"state": "maine", "name": "Maine", "issues": 87, "success": True},
        {
            "state": "new-hampshire",
            "name": "New Hampshire",
            "issues": 23,
            "success": True,
        },
    ]

    # Create comprehensive results object with metadata
    results_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_states": len(results),
        "total_issues": sum(r["issues"] for r in results),
        "successful_analyses": sum(1 for r in results if r["success"]),
        "results": results,
    }

    results_file = pages_dir / "results.json"
    with open(results_file, "w") as f:
        json.dump(results_data, f, indent=2)

    print(f"✅ Created test results.json: {results_file}")
    print(json.dumps(results_data, indent=2))


if __name__ == "__main__":
    main()
