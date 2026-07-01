# Family Finance Local App

Local-first app for tracking deposits, monthly shares, loans, payments, interest, and late fees.

## Run

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Open http://localhost:5000

Notes:
- Admin PIN: `1234`
- First run creates the DB and one admin member: **Govindrao Kulkarni**
- Create additional members manually via the UI after logging in as admin

## Test

```powershell
.venv\Scripts\activate
python -m pytest tests/
```

## Project structure

```
core/           # Flask app package
  routes/       # API endpoint blueprints
  models/       # Database access layer
  database.py   # DB init, migrations, seed
  config.py     # Settings (DB path, admin PIN)
  __init__.py   # create_app() factory
run.py          # Entry point
static/         # CSS, JS, images
templates/      # HTML templates
tests/          # Pytest suite
```
