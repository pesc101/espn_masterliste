# ESPN / IPNA Masterliste Updater

A Streamlit app that merges an orders export (Bestellungen), a contacts export (Kontakte), and a PDF fee schedule to generate the three membership masterlists as downloadable CSVs.

---

## Requirements

- [uv](https://docs.astral.sh/uv/) ≥ 0.4  
- Python ≥ 3.13 (managed automatically by uv)

---

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/pesc101/espn_masterliste.git
cd espn_masterliste

# 2. Install all dependencies into a local virtual environment
uv sync
```

---

## Run the app

```bash
uv run streamlit run app.py
```

The app opens in your default browser at `http://localhost:8501`.

---

## Build a Windows executable (`.exe`)

This project includes a PyInstaller entrypoint and build scripts to produce a standalone Windows app.

### 1. Build on Windows

PyInstaller cannot reliably cross-compile a Windows `.exe` from macOS/Linux, so run the build on a Windows machine:

```powershell
git clone https://github.com/pesc101/espn_masterliste.git
cd espn_masterliste
scripts\build_windows.ps1
```

If you use Command Prompt instead of PowerShell:

```bat
scripts\build_windows.bat
```

### 2. Find the executable

After a successful build, the executable is at:

```text
dist\MasterlisteUpdater.exe
```

### 3. Run the executable

Double-click `MasterlisteUpdater.exe`. It starts a local Streamlit server and opens your browser automatically.

Notes:
- First startup may take a few seconds.
- Windows SmartScreen may show a warning for unsigned executables.

### 3a. If curl works but browser stays blank

If `curl http://127.0.0.1:8501` returns HTML (often starting with `<!DOCTYPE html>`), the server is alive and the EXE is running. A blank browser page is then usually caused by browser/WebSocket restrictions or a stale process.

This project already applies the key mitigations in the packaged launcher:
- `--server.enableCORS=false`
- `--server.enableXsrfProtection=false`
- `--server.port 8501`

Additional checks on Windows:
- Close the EXE and stop old `python.exe` / `MasterlisteUpdater.exe` processes in Task Manager.
- Start the EXE again and force-refresh the browser (`Ctrl` + `F5`).
- Ensure no other tool occupies port `8501`.

Build note:
- The Windows build script includes `--collect-all streamlit`, which is required so bundled Streamlit frontend assets are available in the EXE.

### 4. Download the `.exe` from GitHub Actions

Every run of the workflow `.github/workflows/build-windows-exe.yml` uploads an artifact named `MasterlisteUpdater-windows`.

1. Open the **Actions** tab in this repository.
2. Open a run of **Build Windows EXE**.
3. In the **Artifacts** section, download `MasterlisteUpdater-windows`.
4. Unzip it to get `MasterlisteUpdater.exe`.

If you publish a GitHub Release, the workflow also attaches `MasterlisteUpdater.exe` directly to the release assets.

---

## Usage

1. **Bestellungen CSV** – upload the orders export (comma-separated, UTF-8).  
2. **Kontakte CSV** – upload the contacts export (comma-separated, UTF-8).  
3. **Beiträge PDF** – upload the fee-schedule PDF.  
4. Click **▶ Run**.  
5. Preview the generated new-members table and download the three masterlists (Excel and CSV):

| Excel file | CSV file | CSV encoding |
|------------|----------|--------------|
| `IPNA Masterliste.xlsx` | `IPNA Masterliste.csv` | windows-1252 |
| `Masterliste neue Mitglieder.xlsx` | `Masterliste neue Mitglieder.csv` | windows-1250 |
| `Masterliste_full.xlsx` | `Masterliste_full.csv` | windows-1252 |

---

## Update the live app

The app is deployed at **<https://espn-masterliste.streamlit.app/>**.

Streamlit Community Cloud watches the `main` branch. Every push automatically rebuilds and redeploys the app — no CLI commands needed.

```bash
# 1. Make your changes locally, then stage them
git add .

# 2. Commit with a descriptive message
git commit -m "describe your change"

# 3. Push to main — redeployment starts immediately
git push
```

The live app is updated within ~1 minute. You can watch the build log at [share.streamlit.io](https://share.streamlit.io) if needed.

---

## Project structure

```
app.py              # Streamlit entry point
core/
  config.py         # Column-name map and output schemas
  io.py             # CSV load / serialise helpers
  pdf.py            # PDF fee-schedule parser
  transform.py      # Data transformation and new-member builder
ui/
  sidebar.py        # File-upload sidebar
  results.py        # Summary, preview tables, download buttons
data/               # Example / reference CSV files
```
