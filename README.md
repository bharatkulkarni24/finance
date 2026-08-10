# Sri Lakshmi Venkateshwara Finance

A local-first finance tracker for a family savings society. Members make monthly
share deposits, take loans, repay with interest, and the admin approves payments,
tracks fixed deposits, and exports a PDF financial report.

## Features

- Member accounts with passwords, profile photos, and deposit tracking
- Monthly share collections with late-fee support
- Loans with interest accrual and repayment tracking
- Payment requests submitted by members, approved/rejected by admin
- Fixed deposits with interest on closure
- Member passbook and CSV statement export
- Monthly PDF report export (English; Kannada headings)
- English / Kannada UI toggle

## Requirements

- Python 3.10+ (tested on 3.13)
- Dependencies are pinned in `requirements.txt`

## Setup (Windows)

```powershell
cd "C:\My projects\Finance"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Open http://localhost:5000

## First-time login

The database is created automatically on first run with two seeded admin
accounts (both with **no password yet**):

- `Govindrao Kulkarni`
- `Bharat Kulkarni`

Set a password before logging in:

```powershell
python scripts/set_password.py "Govindrao Kulkarni" "YourPassword123"
python scripts/set_password.py "Bharat Kulkarni" "YourPassword123"
```

Use the same script to reset a forgotten password anytime.

New members are created by an admin from the **Admin Panel**; the admin sets
each member's initial password there. Members can change their own password
from their profile.

## Running tests

```powershell
.venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```

## Production notes

- Run behind a reverse proxy with HTTPS (nginx/caddy) and start the app with
  `FORCE_HTTPS=1`. This redirects all HTTP traffic to HTTPS and marks session
  cookies as secure.
- `FORCE_HTTPS=1` env var is read at startup:
  ```powershell
  $env:FORCE_HTTPS = "1"
  python run.py
  ```
- Keep `.secret_key` (auto-generated, git-ignored) secret — it signs login
  sessions. Set `SECRET_KEY` env var to override it.
- Back up regularly:
  - `finance.db` (SQLite database)
  - `static/uploads/` (member profile photos and payment screenshots)
- `static/uploads/` and `logs/` are git-ignored and are created automatically.

## Project structure

```
run.py               # Entry point (starts the Flask server)
core/
  __init__.py        # create_app() factory, HTTPS enforcement, error handlers
  config.py          # Settings (DB path, secret key)
  database.py        # DB init, schema, seed data
  rate_limit.py      # Login brute-force protection
  session.py         # Login sessions and admin tokens
  routes/            # API endpoint blueprints (auth, members, loans, admin)
  models/            # Database access layer (member, payment, loan, report)
  fonts/             # Fonts for the PDF report
scripts/
  set_password.py    # Set/reset a member's login password
static/              # CSS, JS, images (uploads/ is git-ignored)
templates/           # HTML templates
tests/               # Pytest suite (unit + integration)
```

## API security overview

- All member-data endpoints require a logged-in session (or admin token)
- All admin endpoints require an admin token
- Login is rate-limited (5 attempts per 5 minutes per IP and per account)
- Member creation is admin-only; the `is_admin` flag is never client-settable
- Uploads are restricted to image types (`.jpg .jpeg .png .gif .webp`, max 2 MB)
