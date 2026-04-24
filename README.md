# FinSight AI Backend

Sri Lanka Financial Intelligence System backend built with FastAPI.

## Step 1 Scope

- Initialize production-style FastAPI project structure
- Add environment-based configuration
- Add API v1 router and health endpoint

## Run Locally

1. Create and activate a virtual environment
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Start server:
   - `uvicorn app.main:app --reload`
4. Test health endpoint:
   - `GET http://127.0.0.1:8000/api/v1/health`
