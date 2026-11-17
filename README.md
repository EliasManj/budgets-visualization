# Finance Dashboard

Interactive Finance Dashboard project for personal use, developed using Python, Pandas, FastAPI, and Panel.

* Parses `.csv` and `.xlsx` files from bank transaction history (BBVA, Amex, Banamex, Cetes)
* Filters expenses by month, year, day range, tags, and cards
* Tracks budgets and savings goals

![Dashboard Video](img/recording.gif)

---

## Requirements

* Python 3.8+
* `sqlite3` CLI (for database initialization)

Install Python dependencies:

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate.bat
pip install -r requirements.txt
```

---

## Running the web dashboard (FastAPI + static frontend)

The primary way to run the dashboard is via [`budgets.sh`](budgets.sh) (Linux/macOS) or [`budgets.bat`](budgets.bat) (Windows).

### First run (reset & import all data)

```bash
./budgets.sh --reset
```

This will:
1. Delete and recreate the SQLite database from [`schema.sql`](schema.sql)
2. Import all bank CSV/Excel files into the database
3. Apply any manual DB modifications from [`db/modifications.sql`](db/modifications.sql)
4. Start the API server at **http://localhost:8000**

### Subsequent runs (data already imported)

```bash
./budgets.sh
```

### Update data without resetting the database

```bash
./budgets.sh --update
```

### Windows

```bat
budgets.bat --reset
budgets.bat
budgets.bat --update
```

### Available flags

| Flag | Short | Description |
|------|-------|-------------|
| `--reset` | `-r` | Drop and recreate the DB, then reimport all data |
| `--update` | `-u` | Reimport all data without resetting the DB |
| `--month=N` | `-m=N` | Override the default month (1–12) |
| `--year=N` | `-y=N` | Override the default year |

The frontend is served as static files under [`static/`](static/) and is accessible at **http://localhost:8000** once the server is running.

---

## Running the Panel dashboard (Visualize.py)

`Visualize.py` is a standalone [Panel](https://panel.holoviz.org/) dashboard. Run it directly with:

```bash
source venv/bin/activate
panel serve Visualize.py --show
```

The `--show` flag automatically opens the dashboard in your browser (default port **5006**).

> **Note:** The database must already be populated before running `Visualize.py`. Run `./budgets.sh --reset` or `./budgets.sh --update` first, or run the import scripts manually:
> ```bash
> python amex.py && python bbva.py && python banamex.py && python cetes.py
> ```

---

## Installing as a systemd service (Linux)

To run the API server automatically on boot:

```bash
./install.sh
```

This creates and enables a `budgets-visualization` systemd service. Manage it with:

```bash
sudo systemctl start budgets-visualization
sudo systemctl stop budgets-visualization
sudo systemctl status budgets-visualization
```

---

## Configuration

### `budgets.yaml` — spending budgets per tag

```yaml
budgets:
  - tag: Food
    category: Expense
    amount: 100
  - tag: Gas
    category: Expense
    amount: 100
  - tag: Shopping
    category: Expense
    amount: 100
  - tag: Home
    category: Expense
    amount: 100
```

### `keywords.yaml` — keyword-to-tag mapping

Transaction descriptions are matched against these keywords to assign a tag automatically:

```yaml
food:
  - soriana
  - walmart
  - oxxo

entertainment:
  - youtube
  - netflix
  - spotify

gas:
  - gaxco
  - gasol
  - bp

productivity:
  - chatgpt
  - github
  - copilot
  - udemy
```

