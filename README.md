# Laytix

**Laytix** is a lightweight visual UI testing tool for Android apps.

It helps QA engineers and developers catch layout regressions before release by comparing Android screenshots against approved baselines.

## Product

Laytix focuses on a simple local workflow:

```text
Android app -> screenshots -> baseline comparison -> visual diff -> HTML report
```

Use:

- product name: **Laytix**
- repository name: `laytix`
- Python package name: `laytix`

## Tech Stack

- Python 3.11+
- Typer
- Pillow
- scikit-image
- FastAPI
- Pytest
- ADB
- Static HTML reports

## Repository Structure

```text
laytix/
├── README.md
├── AGENTS.md
├── pyproject.toml
├── requirements.txt
├── src/
│   └── laytix/
│       ├── __init__.py
│       ├── adb.py
│       ├── cli.py
│       ├── compare.py
│       ├── config.py
│       ├── models.py
│       ├── report.py
│       └── web.py
├── tests/
└── examples/
    └── laytix.yaml
```

## 1. Create a Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 2. Install Dependencies

Install Laytix in editable mode with development dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## 3. Check the Environment

```powershell
laytix doctor
```

This checks:

- Python version;
- required Python packages;
- ADB availability;
- connected Android devices.

## 4. Capture a Screenshot

Start an Android emulator or connect a real device with USB debugging enabled.

```powershell
laytix capture --output screenshots/
```

Laytix saves a PNG screenshot into the selected folder.

You can also provide a specific file path:

```powershell
laytix capture --output screenshots/login.png
```

## 5. Compare Screenshots with CLI

Prepare two folders:

```text
examples/
├── baseline/
│   └── login.png
└── actual/
    └── login.png
```

Run comparison:

```powershell
laytix compare `
  --baseline examples/baseline `
  --actual examples/actual `
  --report examples/reports/report.html `
  --threshold 0.02 `
  --method pixel
```

Laytix compares images by matching file names.

Comparison methods:

- `pixel`: counts changed pixels and is the default behavior.
- `ssim`: uses scikit-image structural similarity for more advanced visual comparison.

Result:

- exit code `0` when all screens pass;
- exit code `1` when differences exceed the threshold;
- exit code `2` when input is invalid.

## 6. Compare Screenshots with a Config File

Generate a starter config:

```powershell
laytix init-config --output laytix.yaml
```

Then edit `laytix.yaml`:

```yaml
project: Demo Android App

paths:
  baseline: examples/baseline
  actual: examples/actual
  report: examples/reports/report.html
  diff_dir: examples/reports/diffs

comparison:
  threshold: 0.02
  method: ssim
```

Run:

```powershell
laytix compare --config laytix.yaml
```

CLI options override config values:

```powershell
laytix compare --config laytix.yaml --threshold 0.01
laytix compare --config laytix.yaml --method pixel
```

If the config file already exists, Laytix will not overwrite it unless you pass `--force`:

```powershell
laytix init-config --output laytix.yaml --force
```

## 7. Use the Web Interface

Start the local interface:

```powershell
laytix web
```

Open:

```text
http://127.0.0.1:8000
```

Then:

1. Enter project name.
2. Set threshold, for example `0.02`.
3. Select comparison method.
4. Upload baseline screenshots.
5. Upload actual screenshots with matching file names.
6. Click **Compare screenshots**.
7. Open the generated HTML report.

Reports and uploaded files are stored locally in:

```text
.laytix-runs/
```

This folder is for local generated artifacts and should not be committed.

## 8. Run Tests

```powershell
python -m pytest
```

## Current Limitations

- The web interface is local only.
- Screenshots are matched by file name.
- Advanced Figma comparison is not implemented yet.

## Product Positioning

Laytix is not a generic testing platform.

It is a focused tool for:

- Android UI regression testing;
- layout validation;
- visual QA automation.

## License

TBD.
