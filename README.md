# Family Finance Local App

Local-first app for tracking deposits, monthly shares, loans, payments, interest, and late fees.

## Run

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Open http://localhost:5000

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
