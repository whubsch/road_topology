#!/usr/bin/env python3
"""
Generate a homepage index for all state topology error reports.

Reads results.json and creates an index page with links to each state's report.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


def generate_homepage():
    """Generate the homepage index."""
    pages_dir = Path("gh-pages")
    results_file = pages_dir / "results.json"

    if not results_file.exists():
        print("Error: results.json not found")
        return

    # Load results
    with open(results_file, "r") as f:
        results = json.load(f)

    # Sort by name
    results = sorted(results, key=lambda x: x["name"])

    # Calculate totals
    total_states = len(results)
    total_issues = sum(r["issues"] for r in results)
    successful = sum(1 for r in results if r["success"])

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSM Highway Topology Error Reports</title>
    <link rel="icon" href="/road_topology/favicon.svg" type="image/svg+xml">
    <style>
        * {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}

        body {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}

        header {{
            background: white;
            border-radius: 8px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        h1 {{
            margin: 0 0 10px 0;
            color: #333;
            font-size: 2em;
        }}

        .subtitle {{
            color: #666;
            margin: 0 0 20px 0;
            font-size: 14px;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}

        .stat {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}

        .stat-value {{
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
        }}

        .stat-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            margin-top: 5px;
            letter-spacing: 0.5px;
        }}

        .reports {{
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .reports-header {{
            background: #2c3e50;
            color: white;
            padding: 20px 30px;
            font-weight: bold;
        }}

        .report-list {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 0;
        }}

        .report-item {{
            padding: 20px 30px;
            border-bottom: 1px solid #eee;
            border-right: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s;
        }}

        .report-item:hover {{
            background: #f9f9f9;
        }}

        .report-item:last-child {{
            border-bottom: none;
        }}

        .report-item:nth-child(even) {{
            border-right: none;
        }}

        .report-name {{
            font-weight: 500;
            color: #333;
        }}

        .report-link {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            margin-left: 10px;
        }}

        .report-link:hover {{
            text-decoration: underline;
        }}

        .report-count {{
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }}

        .report-count.zero {{
            background: #4caf50;
        }}

        .report-status {{
            font-size: 18px;
            margin-right: 10px;
        }}

        .report-status.error {{
            color: #d32f2f;
        }}

        .report-status.success {{
            color: #4caf50;
        }}

        a {{
            color: #667eea;
        }}

        a:visited {{
            color: #667eea;
        }}

        footer {{
            text-align: center;
            color: white;
            margin-top: 40px;
            font-size: 12px;
        }}

        @media (max-width: 768px) {{
            h1 {{
                font-size: 1.5em;
            }}

            .report-list {{
                grid-template-columns: 1fr;
            }}

            .report-item {{
                border-right: none;
                flex-direction: column;
                text-align: left;
            }}

            .report-link {{
                margin-left: 0;
                display: block;
                margin-top: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🗺️ OSM Highway Topology Error Reports</h1>
            <p class="subtitle">Automated analysis of OpenStreetMap highway topology across US states</p>

            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{total_states}</div>
                    <div class="stat-label">States Analyzed</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{total_issues:,}</div>
                    <div class="stat-label">Total Issues Found</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{successful}/{total_states}</div>
                    <div class="stat-label">Reports Generated</div>
                </div>
            </div>
        </header>

        <div class="reports">
            <div class="reports-header">State Reports</div>
            <div class="report-list">
"""

    # Add report items
    for result in results:
        status_icon = "✓" if result["success"] else "✗"
        status_class = "success" if result["success"] else "error"
        count_class = "zero" if result["issues"] == 0 else ""

        if result["success"]:
            link = f'<a href="{result["state"]}.html" class="report-link">View Report →</a>'
            # For clean analyses, show descriptive label
            if result["issues"] == 0:
                issues_text = "0 issues ✨"
                count_style = 'style="background: #4caf50;"'
            else:
                issues_text = f"{result['issues']:,} issues"
                count_style = ""
            issues_label = f'<span class="report-count {count_class}" {count_style}>{issues_text}</span>'
        else:
            link = (
                '<span class="report-link" style="color: #999;">Analysis Failed</span>'
            )
            issues_label = (
                '<span class="report-count" style="background: #d32f2f;">Error</span>'
            )

        html += f"""                <div class="report-item">
                    <div>
                        <span class="report-status {status_class}">{status_icon}</span>
                        <span class="report-name">{result["name"]}</span>
                    </div>
                    <div style="display: flex; align-items: center;">
                        {issues_label}
                        {link}
                    </div>
                </div>
"""

    html += """            </div>
        </div>

        <footer>
            <p>Reports generated at {timestamp}</p>
            <p><a href="https://github.com/whubsch/road_topology" style="color: white;">road_topology on GitHub</a></p>
        </footer>
    </div>
</body>
</html>
""".format(
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    )

    # Write homepage
    homepage_path = pages_dir / "index.html"
    with open(homepage_path, "w") as f:
        f.write(html)

    print(f"Homepage generated: {homepage_path}")


if __name__ == "__main__":
    generate_homepage()
