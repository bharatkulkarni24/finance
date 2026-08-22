# Release 2 Deployment Steps (version_2.0.1)

Purpose: record exactly what we do to move from the old test setup on PythonAnywhere
to the finished Release 2 app — so we always know what was done, when, and why.

---

## Background — why PythonAnywhere looks the way it does

- The repo's `.gitignore` excludes `*.db`, so the real laptop database was never pushed.
- When the app first ran on PythonAnywhere (old `release/0.0.1` code), it found no
  database, created one, and seeded it with just 2 starter users
  (Govindrao 1001, Bharat 1002). That is why PA shows only those two.
- That PA database contains **no real data** — it is disposable.
- Release 2 changes that make deploy special:
  - Flask upgraded 2.2.5 → 3.1.3 (`requirements.txt`) → the PA virtualenv must be rebuilt.
  - `seed_db()` now plants the full **12-member founding roster**
    (IDs 1001–1012, joined 2025-04-01, ₹25,000 entry deposit each,
    admins Govindrao & Bharat with PIN 1000, everyone else locked until
    Reset Password).
  - Seeding only fires on an EMPTY members table — so the old 2-user PA database
    must be removed first, otherwise the roster would never appear.
  - Backups feature active (daily snapshots kept 14 days, 30 manual max).

---

## STEP 1 — Deal with the EXISTING PythonAnywhere setup

Goal: clear the way without losing anything, and prepare for the new Flask.

- [ ] 1. Note: free-tier PythonAnywhere has **no Stop button** — only **Reload**.
       That's fine: nobody uses the app yet, so just leave it as-is while we swap
       files (worst case a request mid-swap shows an error page), and we hit
       **Reload** at the end of Step 2 to go live.
- [ ] 2. ~~Safety copy of old database~~ — SKIPPED by decision: the old DB held
       only dummy starter data, nothing worth keeping.
- [ ] 3. Remove the old database from the app folder:
       DELETED `finance.db` via Files tab (PA has no rename option; content was
       disposable starter data). Seeding will now fire fresh on next startup.
- [ ] 4. Note current settings before touching anything:
       **Web** tab → write down: Python version, source directory, WSGI file path,
       virtualenv path. Screenshot or copy into this file below.

       > Recorded settings (read off Web tab):
       > - Account/project: slvfinance → https://slvfinance.pythonanywhere.com
       > - Working directory: /home/slvfinance/finance
       > - WSGI file: /var/www/slvfinance_pythonanywhere_com_wsgi.py
       >   (imports `from run import app as application`)
       > - Virtualenv: /home/slvfinance/finance/venv (inside project — same path
       >   reused in Step 2 so no Web-tab changes needed)
       > - Python version: **3.11** — already ≥3.10, nothing to bump ✓

- [ ] ~~5. Bump Python~~ — not needed: 3.11 already selected.
- [ ] 6. Virtualenv rebuild: deferred into Step 2 — the existing `venv/` inside
       the project gets deleted and rebuilt fresh AFTER new code is uploaded,
       because `pip install -r requirements.txt` must read the NEW requirements
       (Flask 3.1.3). Old app is already inert (DB deleted), so no downside.
- [ ] 7. Leave the web app un-reloaded for now (it may show errors if visited —
       expected, since its database is renamed away). Code upload and the final
       **Reload** happen in Step 2.

Checkpoint for Step 1: old DB renamed+copied ✓ · settings recorded ✓ ·
Python ≥3.10 selected ✓ · fresh venv built with new requirements ✓ · app stopped ✓

---

## STEP 2 — Deploy Release 2 code

1. **Laptop:** commit all Release 2 work and `git push` to
   `origin/feature/version_2.0.1`.
2. **PA Bash console** (Consoles tab → Bash):
   ```bash
   cd ~/finance
   git fetch origin
   git checkout feature/version_2.0.1
   git pull origin feature/version_2.0.1
   ```
3. **Rebuild venv in place** (same path the Web tab already points to):
   ```bash
   rm -rf venv
   python3.11 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **Boot test — this also creates finance.db and seeds all 12 members:**
   ```bash
   python -c "from core import create_app; app = create_app(); print('BOOT OK')"
   python -c "import sqlite3; print(sqlite3.connect('finance.db').execute('SELECT COUNT(*) FROM members').fetchone()[0], 'members')"
   ```
   Expect: `BOOT OK` then `12 members`.
5. **Web tab check:** Virtualenv path `/home/slvfinance/finance/venv`,
   static mapping `/static/ → /home/slvfinance/finance/static` still present.
6. Click green **Reload** → open https://slvfinance.pythonanywhere.com

---

## Verification checklist (after Step 2)

- [ ] Login page loads over https
- [ ] Admin login with PIN 1000 works (both admins)
- [ ] All Members shows 12 members with Kannada names rendered correctly
- [ ] Reset Password flow sets a member PIN and that member can log in
- [ ] Passbook filters (date/type/member/amount) work incl. calendar dropdowns
- [ ] Add-to-Home-Screen installs fullscreen (PWA manifest + service worker)
- [ ] backups/ folder appears after first request; Download Backup works
