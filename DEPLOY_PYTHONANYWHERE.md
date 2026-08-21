# Deployment Guide — PythonAnywhere (Free)

Living document. We update it step by step as we deploy. Tick each step when done.

## What we are deploying

- **App:** Sri Lakshmi Venkateshwara Finance (Flask + SQLite)
- **Repo/branch:** `https://github.com/bharatkulkarni24/finance.git` → branch `release/0.0.1`
- **Runtime:** Python 3.10+ · `requirements.txt` (Flask 2.2.5, Werkzeug 2.3.8, fpdf2 2.8.7)
- **Data:** SQLite file `finance.db` (auto-created) + `static/uploads/` (member photos/screenshots)
- **Stack notes:** single-process app; login sessions signed by `.secret_key` (auto-generated); admin access via bearer token; login rate-limited in-memory; CORS off; HTTPS via `FORCE_HTTPS=1`.

## Status tracker

| # | Step | Status |
|---|------|--------|
| 0 | Code committed & pushed to GitHub | ✅ done (branch `release/0.0.1`) |
| 1 | Create PythonAnywhere free account | ✅ done (username `slvfinance`) |
| 2 | Open PythonAnywhere Bash console | ✅ done |
| 3 | Clone repo into `~/finance` | ✅ done |
| 4 | Create virtualenv + install requirements | ✅ done (Python 3.11, deps installed) |
| 5 | First app start (creates the DB) | ✅ done (`BOOT OK`) |
| 6 | Set admin passwords (bootstrap) | ✅ done (Govindrao + Bharat) |
| 7 | Create the Web App (WSGI + static files) | ✅ done (site live) |
| 8 | Reload web app & open the URL | ✅ done — https://slvfinance.pythonanywhere.com loads |
| 9 | Validation round (logins, member, loan, PDF) | ⬜ pending |
| 10 | Reset DB for real data (April 2025 start) | ⬜ pending |

---

## Step-by-step

### Step 1 — PythonAnywhere account
1. Go to https://www.pythonanywhere.com and click **Start running Python online in 5 minutes** (free "Beginner" account).
2. Choose the free plan (no payment needed).
3. Remember your **username** — your site URL will be `https://<username>.pythonanywhere.com`.

### Step 2 — Bash console
1. Log in to PythonAnywhere → top menu **Consoles** → **Bash**.

### Step 3 — Clone the code
Run in the Bash console:
```bash
git clone -b release/0.0.1 https://github.com/bharatkulkarni24/finance.git ~/finance
cd ~/finance
```
If the repo is **private**, GitHub will ask for a username/password here. In that case
the repo must be made public, or you must clone with a personal access token
(we will handle it at this step if it fails).

### Step 4 — Virtualenv + dependencies
```bash
cd ~/finance
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
Use `python3.10` or `python3.12` if `python3.11` is not available (must be 3.10+).

### Step 5 — First app start (creates the DB)
The database file (`finance.db`) and schema are created the first time the app starts.
Run this boot test, which creates them:
```bash
cd ~/finance
source venv/bin/activate
python -c "from core import create_app; app = create_app(); print('BOOT OK')"
```
Expected output: `BOOT OK` (also creates `finance.db`, `.secret_key`, `logs/`).
The tables must exist before Step 6 (`set_password.py`).

### Step 6 — Set admin passwords (bootstrap)
Fresh DBs have the two seed admins with **no password**. Set them:
```bash
cd ~/finance
source venv/bin/activate
python scripts/set_password.py "Govindrao Kulkarni" "YourRealPassword"
python scripts/set_password.py "Bharat Kulkarni" "YourRealPassword"
```
Use strong, private passwords (4-digit pins are easy to guess — not recommended for production).

### Step 7 — Create the Web App
1. Top menu **Web** → **Add a new web app** → Next → **Manual configuration** → Python **3.11** → Next.
2. **Code** → Working directory: `/home/<username>/finance`
3. **Virtualenv**: `/home/<username>/finance/venv`
4. Click **WSGI configuration file** → replace contents with:
   ```python
   import os, sys
   project_home = os.path.expanduser('~/finance')
   if project_home not in sys.path:
       sys.path.insert(0, project_home)
   os.chdir(project_home)
   from run import app as application
   ```
   Save.
5. **Static files**: add
   - URL: `/static/` → Directory: `/home/<username>/finance/static`
6. (Optional hardening, do AFTER Step 9 works) Under **Environment variables** add `FORCE_HTTPS = 1`.

### Step 8 — Reload
Click the green **Reload** button (top of the Web tab).
Open `https://<username>.pythonanywhere.com` → you should see the login page.

### Step 9 — Validation round
On the live site:
- [ ] Login page loads (English/Kannada toggle works)
- [ ] Admin login with a password set in Step 5 works
- [ ] Admin can create a member (with password)
- [ ] That member can log in
- [ ] Member can submit a payment request with a screenshot
- [ ] Admin sees and approves the request
- [ ] Admin can apply/approve a loan for a member
- [ ] Member statement CSV downloads
- [ ] Admin PDF report exports (`from`/`to` dates given)
- [ ] Upload a profile photo → shows in member card
- [ ] Reload page → still logged in (session cookie works)

### Step 10 — Reset DB for real data (April 2025 onwards)
Only after Step 9 validation passes. Two options:

**Option A — enter real data here locally, then upload the DB to PythonAnywhere**
1. Local: clean the DB (delete test members/requests/ledger/loans/FD entries — or start a fresh DB).
2. Enter real data from April 2025.
3. Backup PROD: Web tab → Files → download `finance.db` and `static/uploads/` first.
4. Upload the cleaned local `finance.db` via **Files** tab, replacing the server copy.
5. Reload web app. Keep `.secret_key` as-is (do NOT copy it) so existing sessions stay valid.

**Option B — enter data directly in PROD**
1. Clean the server DB (delete test data via UI, or run a cleanup script).
2. Do all data entry on the live site.
3. Always keep a downloaded backup of `finance.db` + `static/uploads/`.

Recommended: **Option A** — entering data locally is faster and safer (no risk of the live
site breaking mid-entry), and you already do entry locally today.

> Note: real data starts **April 2025**. Decide before cleaning whether you also want
> profile photos / screenshots carried over, since those live in `static/uploads/`.

---

## Maintenance / future updates

- **Change code later (keep DB):** update files (PythonAnywhere file editor, `git pull`,
  or upload), then **Reload** the web app. The app auto-creates missing tables and
  auto-adds missing columns at startup, so your data is kept. Always back up first.
- **Data fixes:** run a small Python script in the Bash console (e.g. `set_password.py`).
- **Backup:** download `finance.db` and `static/uploads/` from the **Files** tab regularly.
- **DB edit while app runs:** avoid it; stop/reload the app before uploading a replaced DB.

## Golden rules

1. Back up `finance.db` + `static/uploads/` before every change.
2. One change at a time, then test.
3. Never copy `.secret_key` between machines.

## Backups (added Aug 2026)

- **Automatic:** the app saves a full copy of `finance.db` once a day into
  `backups/finance-YYYY-MM-DD.db` (first request after midnight triggers it).
  Keeps the newest **14** dated copies, older ones are removed automatically.
- **Manual download:** Admin Panel → "Download Backup" button gives you the
  file to keep on your phone/PC. Keep at least one copy outside PythonAnywhere.
- **View on PythonAnywhere:** Files tab → open your project folder → `backups/`.
- **Restore:** Files tab → rename current `finance.db` to `finance-broken.db`,
  then upload/rename the chosen `finance-YYYY-MM-DD.db` back to `finance.db`
  and reload the web app.
