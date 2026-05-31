"""Minimal local web interface for Laytix."""

from pathlib import Path, PurePosixPath
from typing import cast
from urllib.parse import quote
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from laytix.compare import ComparisonMethod, SUPPORTED_COMPARISON_METHODS, compare_folders
from laytix.report import generate_html_report

RUNS_DIR = Path(".laytix-runs")

app = FastAPI(title="Laytix")
RUNS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/runs", StaticFiles(directory=RUNS_DIR), name="runs")


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> str:
    """Render the upload form."""

    error = request.query_params.get("error")
    return _page(
        title="Laytix",
        body=f"""
        <section class="toolbar">
          <div>
            <h1>Laytix</h1>
            <p>Local visual UI testing for Android screenshots.</p>
          </div>
        </section>

        {_render_error(error)}

        <form action="/compare" method="post" enctype="multipart/form-data" class="panel">
          <div class="grid">
            <label>
              <span>Project name</span>
              <input name="project" type="text" value="Demo Android App" autocomplete="off">
            </label>
            <label>
              <span>Threshold</span>
              <input name="threshold" type="number" min="0" max="1" step="0.001" value="0.02">
            </label>
            <label>
              <span>Method</span>
              <select name="method">
                <option value="pixel" selected>Pixel</option>
                <option value="ssim">SSIM</option>
              </select>
            </label>
          </div>

          <div class="upload-grid">
            <label class="drop">
              <strong>Baseline screenshots</strong>
              <span>Approved PNG, JPG, JPEG, or WEBP files</span>
              <input name="baseline_files" type="file" multiple accept="image/png,image/jpeg,image/webp">
            </label>
            <label class="drop">
              <strong>Actual screenshots</strong>
              <span>New screenshots with matching file names</span>
              <input name="actual_files" type="file" multiple accept="image/png,image/jpeg,image/webp">
            </label>
          </div>

          <button type="submit">Compare screenshots</button>
        </form>

        <section class="notes">
          <h2>Expected file matching</h2>
          <p>Laytix compares images by file name. For example, <code>login.png</code> in baseline is compared with <code>login.png</code> in actual.</p>
        </section>
        """,
    )


@app.post("/compare")
async def compare_uploads(
    project: str = Form("Laytix project"),
    threshold: float = Form(0.02),
    method: str = Form("pixel"),
    baseline_files: list[UploadFile] = File(...),
    actual_files: list[UploadFile] = File(...),
) -> RedirectResponse:
    """Save uploaded screenshots, compare them, and redirect to the report."""

    if threshold < 0 or threshold > 1:
        return _redirect_with_error("Threshold must be between 0 and 1.")

    if method not in SUPPORTED_COMPARISON_METHODS:
        return _redirect_with_error("Comparison method must be pixel or ssim.")

    if not baseline_files or not actual_files:
        return _redirect_with_error("Upload baseline and actual screenshots.")

    run_id = uuid4().hex
    run_dir = RUNS_DIR / run_id
    baseline_dir = run_dir / "baseline"
    actual_dir = run_dir / "actual"
    report_path = run_dir / "reports" / "report.html"
    diff_dir = run_dir / "reports" / "diffs"

    try:
        await _save_uploads(baseline_files, baseline_dir)
        await _save_uploads(actual_files, actual_dir)
        summary = compare_folders(
            baseline_dir,
            actual_dir,
            diff_dir,
            threshold=threshold,
            method=cast(ComparisonMethod, method),
            project_name=project.strip() or "Laytix project",
        )
        generate_html_report(summary, report_path)
    except (ValueError, FileNotFoundError, HTTPException) as error:
        return _redirect_with_error(str(error))

    return RedirectResponse(f"/runs/{run_id}/reports/report.html", status_code=303)


async def _save_uploads(files: list[UploadFile], target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)

    for upload in files:
        relative_path = _safe_relative_path(upload.filename)
        output_path = target_dir / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        content = await upload.read()

        if not content:
            raise ValueError(f"Uploaded file is empty: {upload.filename}")

        output_path.write_bytes(content)


def _safe_relative_path(filename: str | None) -> Path:
    if not filename:
        raise ValueError("Uploaded file has no name.")

    normalized = filename.replace("\\", "/")
    path = PurePosixPath(normalized)

    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe upload file path: {filename}")

    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise ValueError(f"Unsupported image type: {filename}")

    return Path(*path.parts)


def _redirect_with_error(message: str) -> RedirectResponse:
    return RedirectResponse(f"/?error={quote(message)}", status_code=303)


def _render_error(error: str | None) -> str:
    if not error:
        return ""
    return f'<div class="alert">{_escape(error)}</div>'


def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_escape(title)}</title>
  <style>
    :root {{
      --bg: #f4f6f8;
      --panel: #ffffff;
      --text: #17202a;
      --muted: #667085;
      --border: #d7dee8;
      --accent: #1264a3;
      --accent-hover: #0d5286;
      --danger-bg: #fff1f0;
      --danger-border: #f1a7a0;
      --danger-text: #9f1f14;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.5;
    }}
    main {{
      max-width: 940px;
      margin: 0 auto;
      padding: 32px 20px 56px;
    }}
    .toolbar {{
      align-items: end;
      display: flex;
      justify-content: space-between;
      margin-bottom: 20px;
    }}
    h1 {{
      font-size: 32px;
      line-height: 1.1;
      margin: 0 0 6px;
    }}
    h2 {{
      font-size: 18px;
      margin: 0 0 6px;
    }}
    p {{
      color: var(--muted);
      margin: 0;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 20px;
    }}
    .grid {{
      display: grid;
      gap: 16px;
      grid-template-columns: 1fr 180px 160px;
      margin-bottom: 18px;
    }}
    label span {{
      color: var(--muted);
      display: block;
      font-size: 13px;
      margin-bottom: 6px;
    }}
    input[type="text"],
    input[type="number"],
    select {{
      border: 1px solid var(--border);
      border-radius: 6px;
      color: var(--text);
      font: inherit;
      height: 42px;
      padding: 8px 10px;
      width: 100%;
    }}
    .upload-grid {{
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      margin-bottom: 18px;
    }}
    .drop {{
      border: 1px dashed #9aa8ba;
      border-radius: 8px;
      display: block;
      min-height: 148px;
      padding: 18px;
    }}
    .drop strong {{
      display: block;
      font-size: 16px;
      margin-bottom: 4px;
    }}
    .drop input {{
      margin-top: 18px;
      max-width: 100%;
    }}
    button {{
      background: var(--accent);
      border: 0;
      border-radius: 6px;
      color: #ffffff;
      cursor: pointer;
      font: inherit;
      font-weight: 700;
      min-height: 44px;
      padding: 10px 16px;
    }}
    button:hover {{
      background: var(--accent-hover);
    }}
    .notes {{
      margin-top: 20px;
    }}
    code {{
      background: #e9eef5;
      border-radius: 4px;
      padding: 2px 5px;
    }}
    .alert {{
      background: var(--danger-bg);
      border: 1px solid var(--danger-border);
      border-radius: 8px;
      color: var(--danger-text);
      margin-bottom: 16px;
      padding: 12px 14px;
    }}
    @media (max-width: 720px) {{
      main {{
        padding-top: 20px;
      }}
      .grid,
      .upload-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main>
    {body}
  </main>
</body>
</html>"""


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
