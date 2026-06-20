# Family Finance Local App

This is a simple local-first demo app for tracking one-time deposits, monthly shares, loans, payments, interest (1%/month), and late fees (₹50/day after 10th).

Run locally (Windows):

1. Create a Python virtual env and install:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

2. Initialize DB with sample data:

```powershell
python db_init.py
```

3. Run the server:

```powershell
python app.py
```

4. Open http://localhost:5000 in your browser or on your Android device (use your PC IP address if accessing from phone).

Notes:
- Admin PIN: `1234` (used in the demo to approve loans)
- This is an MVP local demo. We can extend to a proper Android APK using Flutter or add sync later.
