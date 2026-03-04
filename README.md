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

## Usage

1. **Bestellungen CSV** – upload the orders export (comma-separated, UTF-8).  
2. **Kontakte CSV** – upload the contacts export (comma-separated, UTF-8).  
3. **Beiträge PDF** – upload the fee-schedule PDF.  
4. Click **▶ Run**.  
5. Preview the generated new-members table and download the three masterlists:

| File | Encoding |
|------|----------|
| `IPNA Masterliste.csv` | windows-1252 |
| `Masterliste neue Mitglieder.csv` | windows-1250 |
| `Masterliste_full.csv` | windows-1252 |

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
