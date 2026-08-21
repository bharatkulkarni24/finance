# Improvement Backlog

Working list of agreed improvement ideas for the Finance app.
We discuss and implement these ONE BY ONE. Update Status after each decision.

Status legend: `Pending` → `Approved` → `Done` / `Declined`

---

## Tier 1 — Important

### 1. Automatic database backups ✅
- **Problem:** `finance.db` is the only copy of all financial records. Disk failure = total loss.
- **Fix:** Auto-copy DB to `backups/finance-YYYYMMDD-HHMM.db` once per day (on first request/start of a new day), keep last 14. Add "Download Backup" button in Admin Panel.
- **Implemented Aug 2026:** `core/backup.py` (daily snapshot on first request after midnight, keeps 14 dated + 30 manual), `/api/admin/backup/download` (admin-only), "⬇️ Download Backup" button under the Admin hub with bilingual toasts, `backups/` gitignored, restore steps added to DEPLOY_PYTHONANYWHERE.md, 5 unit tests.
- **Status:** Done

### 2. Debug mode ON in production
- **Problem:** `run.py` runs `debug=True`. Family members on the LAN get detailed error pages / debugger console access when errors happen.
- **Fix:** Read `FLASK_DEBUG` env or add two launchers: `run_dev.bat` (debug on, auto-reload, for development) and `start.bat` (debug off, for daily family use).
- **Status:** Declined Aug 2026 — only 12 trusted members, app can be stopped for days, not urgent

### 3. Sessions stay valid too long ✅ Already implemented
- **Found during audit:** core/__init__.py already enforces 30-min inactivity + 12-hour absolute re-login, HttpOnly + SameSite cookies.
- **Status:** Done (no work needed)

## Tier 2 — Quality of life

### 4. PWA (installable app on phone) ✅
- **Problem:** Site opens in browser tab with address bars; elders find tabs confusing.
- **Fix:** `manifest.json` + icons (favicon.ico already exists) + service worker lite → "Add to Home Screen" opens fullscreen like a real app.
- **Implemented Aug 2026:** manifest.json (standalone, portrait, dark theme #081124), generated emerald ₹ icons (192/512/maskable/apple-touch), conservative service worker (static cache-first, pages network-first, API never cached) served from root `/sw.js` route, head tags added, SW registered in app.js v73. Install: Chrome ⋮ → Add to Home screen / iOS Safari Share → Add to Home Screen.
- **Status:** Done

### 5. CSV export
- **Problem:** Export Report produces PDF only; no easy way to analyze data in Excel.
- **Fix:** "Export CSV" button in Edit Entries / Export view producing entries table as CSV (opens in Excel).
- **Status:** Declined Aug 2026 — user wants to plan/redo export later

### 6. Admin password reset for members ✅
- **Problem:** If a member forgets password, unclear if admin can reset it anywhere except scripts/set_password.py on the laptop.
- **Fix:** Verify current capability; if missing, add "Reset Password" action in All Members → member profile (admin only).
- **Implemented Aug 2026:** `POST /api/members/<id>/reset_password` (admin token only, min 4 chars, logged server-side); "🔑 Reset Password" lives in the **Admin Panel menu** (second-last card; Add New Member moved to last per user request) — pick member from dropdown + new/confirm password with show/hide toggles; bilingual toasts; 5 unit tests incl. login-with-new-password verification.
- **Status:** Done

## Tier 3 — Later / optional

### 7. GitHub Actions CI
- Run unit+integration tests automatically on every push.
- **Status:** Postponed Aug 2026 — tests already run manually before every change; revisit if more developers join

### 8. Upgrade Flask 2.2.5 → current
- Works today; do it some day with full test run. Also bump Werkzeug accordingly.
- **Status:** Pending

## Small cleanups

### 9. Remove duplicate I18N keys
- 'Entry Deposit', 'From', 'To', 'Password', 'Share' exist twice in en/kn blocks (identical values, harmless today).
- **Status:** Pending

### 10. Replace deprecated `datetime.utcnow()`
- Python 3.13 deprecation warnings across models (loan.py, transaction.py etc.). Use timezone-aware datetimes. Purely future-proofing.
- **Status:** Pending

### 11. Tests for Entry Deposit & Loan Disbursed editing
- The two new Edit Entries kinds (added Aug 2026) have no dedicated unit/integration tests yet.
- **Status:** Pending
