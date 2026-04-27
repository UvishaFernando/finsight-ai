# FinSight AI (Backend)

Backend for **FinSight AI – Sri Lanka Financial Intelligence System**.

## Run locally (Windows PowerShell)

Create a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

Check health:
- `http://127.0.0.1:8000/health`
