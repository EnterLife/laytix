# Project Instructions

## Project

This repository contains **Laytix**, a lightweight developer tool for Android visual UI testing.

Laytix provides a local workflow for:

- capturing Android screenshots through ADB;
- comparing screenshots against approved baselines;
- generating visual diff images;
- generating static HTML reports;
- returning CI-friendly exit codes when differences exceed a configured threshold;
- optionally using a minimal local FastAPI web interface for uploads and reports.

Keep the product local-first, simple and focused. Do not introduce cloud, billing, authentication, organization management, hosted dashboards or AI analysis unless the user explicitly asks for that direction.

## Tech Stack

- Python 3.11+
- Typer for CLI commands
- Pillow for image loading and pixel diffs
- scikit-image and NumPy for SSIM comparison
- PyYAML for config loading
- FastAPI and Uvicorn for the local web interface
- Pytest for automated tests
- ADB for Android screenshot capture
- Static HTML reports

Avoid unless explicitly needed:

- Django
- Celery
- Kubernetes
- database layers
- microservices
- heavy frontend frameworks

## Repository Structure

- `src/laytix/cli.py` - Typer CLI commands.
- `src/laytix/adb.py` - Android Debug Bridge helpers.
- `src/laytix/compare.py` - image comparison logic.
- `src/laytix/config.py` - YAML config loading and validation.
- `src/laytix/models.py` - shared dataclasses and result models.
- `src/laytix/report.py` - static HTML report generation.
- `src/laytix/web.py` - minimal local FastAPI web interface.
- `tests/` - pytest coverage for CLI, config, compare, report and web behavior.
- `examples/laytix.yaml` - sample Laytix config.
- `README.md` - setup and usage documentation.
- `pyproject.toml` - package metadata, dependencies and pytest config.
- `requirements.txt` - runtime dependencies.

## Generated and Runtime Folders

Do not edit generated or runtime folders unless the task explicitly requires it:

- `.laytix-runs/`
- `.pytest_cache/`
- `__pycache__/`
- virtual environments such as `.venv/`

If a generated artifact is created during verification, leave it alone unless it is part of the requested output or cleanup is clearly needed.

## Coding Rules

- Follow the existing project style and keep code readable for a small early-stage team.
- Keep edits focused on the requested behavior.
- Prefer working CLI functionality over architecture abstractions.
- Do not refactor unrelated code while fixing a local issue.
- Preserve user changes already present in the working tree.
- Use type hints.
- Use dataclasses for simple shared data models.
- Keep functions small and explicit.
- Avoid hidden global state.
- Avoid broad `except Exception` blocks.
- Error messages should be clear and actionable.
- Do not leave unused constants, helpers, imports, parameters or dead code after changing files.
- Do not introduce unnecessary frameworks or services.

## CLI Rules

- CLI output should be readable and concise.
- Use actionable messages when input is invalid or local tools are missing.
- Prefer examples like:

```text
Checking screenshots...
Compared: 12
Passed: 10
Failed: 2
Report: reports/laytix-report.html
```

- Avoid vague output like:

```text
Done.
```

## Comparison Rules

- Keep `pixel` comparison deterministic and simple: count changed pixels and compare the ratio with the threshold.
- Keep `ssim` comparison based on scikit-image structural similarity and return `1 - score` as the difference ratio.
- Always validate that baseline and actual image dimensions match before comparing.
- If image sizes differ, mark the result failed and include a clear reason.
- Missing baseline or actual files should produce failed comparison results with clear reasons.
- Diff images should be generated when a diff path is provided.
- Supported image extensions should stay explicit and easy to understand.

## Config Rules

- Config files are YAML.
- Relative paths in config should resolve from the config file directory.
- CLI options should override config values.
- Validate thresholds as numbers between `0` and `1`.
- Validate comparison methods explicitly, currently `pixel` and `ssim`.
- Keep starter config output aligned with `README.md` and `examples/laytix.yaml`.

## Report Rules

- Reports should remain static HTML files.
- Include project name, comparison date, total screens, passed count, failed count, status, baseline image, actual image, diff image, difference percentage and failure reason.
- Prefer relative image paths in the generated report.
- Escape user-provided text before putting it into HTML.

## Web Interface Rules

- Keep the web interface local-only and minimal.
- Do not add accounts, cloud storage, billing, dashboards or hosted reports.
- Validate uploads before saving them.
- Preserve safe path handling for uploaded filenames.
- Store local web artifacts under `.laytix-runs/`.
- Reuse the same comparison and report functions as the CLI instead of duplicating behavior.

## Testing Rules

Every core function should have focused tests.

Prioritize tests for:

- identical image comparison;
- different image comparison;
- SSIM comparison behavior;
- image size mismatch;
- missing baseline file;
- missing actual file;
- threshold behavior;
- invalid comparison method;
- config path resolution and validation;
- CLI option overrides;
- report generation;
- web upload flow.

Use small generated test images instead of large binary fixtures where possible.

When behavior changes, update related tests in the same focused edit.

## Useful Commands

Always run project commands through the local virtual environment when feasible. On Windows, prefer `.venv\Scripts\python.exe -m ...` so pytest and dependencies resolve from the project `.venv`.

Install dependencies:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Run all tests:

```powershell
.venv\Scripts\python.exe -m pytest
```

Run one test file:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_compare.py
```

Run one test by name:

```powershell
.venv\Scripts\python.exe -m pytest -k "test_name_part"
```

Run the CLI locally:

```powershell
.venv\Scripts\python.exe -m laytix.cli --help
```

Check the environment:

```powershell
.venv\Scripts\python.exe -m laytix.cli doctor
```

Compare screenshots:

```powershell
.venv\Scripts\python.exe -m laytix.cli compare `
  --baseline examples/baseline `
  --actual examples/actual `
  --report examples/reports/report.html `
  --threshold 0.02 `
  --method pixel
```

Start the local web interface:

```powershell
.venv\Scripts\python.exe -m laytix.cli web
```

## Commit Message Suggestions

After each completed work chunk, include a suggested commit message in the final response.

Use a lowercase prefix and a short lowercase summary. Keep the message in one line without a period.

Choose the prefix by intent:

- `add:` for new commands, features or user-visible behavior.
- `fix:` for bug fixes or broken behavior.
- `upd:` for updates to existing code, docs, configs or expected behavior.
- `refactor:` for internal restructuring without behavior changes.
- `docs:` for documentation-only changes.
- `test:` for test-only maintenance that does not add new feature coverage.
- `chore:` for tooling, cleanup or repository maintenance.

Examples:

- `add: ssim comparison method`
- `fix: report missing actual screenshot reason`
- `docs: consolidate usage guide in readme`

## Before Finishing Work

- Review the changed files.
- Run the most focused relevant pytest command when feasible.
- For comparison, config, CLI, report or web changes, run tests that cover the touched behavior.
- For documentation-only changes, tests are optional; mention when they were not run.
- If ADB, an emulator, a real device or another local dependency is unavailable, say so explicitly in the final response and mention the remaining verification risk.
- Mention any remaining risk or follow-up that matters for the user.

## Product Naming

Use the product name:

```text
Laytix
```

Use the repository name:

```text
laytix
```

Use lowercase package/module names:

```text
laytix
```

Do not rename the product without explicit instruction.
