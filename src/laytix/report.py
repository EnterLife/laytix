"""HTML report generation for Laytix."""

import os
from datetime import UTC, datetime
from html import escape
from pathlib import Path

from laytix.models import ComparisonResult, ComparisonSummary


def generate_html_report(summary: ComparisonSummary, report_path: Path | str) -> Path:
    """Generate a static HTML report for comparison results."""

    output_path = Path(report_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    rows = "\n".join(_render_result_row(result, output_path.parent) for result in summary.results)
    status = "failed" if summary.has_failures else "passed"

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Laytix Report</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f8fb;
      --panel: #ffffff;
      --text: #17202a;
      --muted: #637083;
      --border: #d9e0ea;
      --pass: #0b7a4b;
      --fail: #b42318;
      --accent: #244b8f;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.5;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    header {{
      margin-bottom: 24px;
    }}
    h1 {{
      margin: 0 0 6px;
      font-size: 30px;
    }}
    .meta {{
      color: var(--muted);
      margin: 0;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 12px;
      margin-bottom: 24px;
    }}
    .metric {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px 16px;
    }}
    .metric span {{
      color: var(--muted);
      display: block;
      font-size: 13px;
    }}
    .metric strong {{
      display: block;
      font-size: 26px;
      margin-top: 2px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
    }}
    th, td {{
      border-bottom: 1px solid var(--border);
      padding: 12px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
    }}
    tr:last-child td {{
      border-bottom: 0;
    }}
    .status {{
      font-weight: 700;
      text-transform: uppercase;
      font-size: 12px;
    }}
    .status.passed {{
      color: var(--pass);
    }}
    .status.failed {{
      color: var(--fail);
    }}
    .reason {{
      color: var(--muted);
      max-width: 260px;
    }}
    .shots {{
      display: grid;
      grid-template-columns: repeat(3, minmax(120px, 1fr));
      gap: 8px;
      min-width: 380px;
    }}
    figure {{
      margin: 0;
    }}
    figcaption {{
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 4px;
    }}
    img {{
      width: 100%;
      max-height: 240px;
      object-fit: contain;
      border: 1px solid var(--border);
      background: #f1f4f8;
    }}
    .missing {{
      align-items: center;
      background: #f1f4f8;
      border: 1px solid var(--border);
      color: var(--muted);
      display: flex;
      height: 120px;
      justify-content: center;
      font-size: 13px;
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Laytix Report</h1>
      <p class="meta">{escape(summary.project_name)} · {generated_at} · status: {status}</p>
    </header>

    <section class="summary" aria-label="Comparison summary">
      <div class="metric"><span>Total screens</span><strong>{summary.total}</strong></div>
      <div class="metric"><span>Passed</span><strong>{summary.passed}</strong></div>
      <div class="metric"><span>Failed</span><strong>{summary.failed}</strong></div>
    </section>

    <table>
      <thead>
        <tr>
          <th>Screen</th>
          <th>Status</th>
          <th>Difference</th>
          <th>Reason</th>
          <th>Images</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </main>
</body>
</html>
"""

    output_path.write_text(html, encoding="utf-8")
    return output_path


def _render_result_row(result: ComparisonResult, report_dir: Path) -> str:
    status = "passed" if result.passed else "failed"
    reason = result.reason or ""
    difference = f"{result.difference_ratio:.2%}"

    return f"""<tr>
  <td>{escape(result.screen_name)}</td>
  <td><span class="status {status}">{status}</span></td>
  <td>{difference}</td>
  <td class="reason">{escape(reason)}</td>
  <td class="shots">
    {_render_image("Baseline", result.baseline_path, report_dir)}
    {_render_image("Actual", result.actual_path, report_dir)}
    {_render_image("Diff", result.diff_path, report_dir)}
  </td>
</tr>"""


def _render_image(label: str, image_path: Path | None, report_dir: Path) -> str:
    if image_path is None or not image_path.exists():
        return f"""<figure>
  <figcaption>{escape(label)}</figcaption>
  <div class="missing">Missing</div>
</figure>"""

    relative_path = Path(os.path.relpath(image_path.resolve(), report_dir.resolve()))
    return f"""<figure>
  <figcaption>{escape(label)}</figcaption>
  <img src="{escape(relative_path.as_posix())}" alt="{escape(label)}">
</figure>"""
