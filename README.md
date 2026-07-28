# Cedar Platform

Enterprise workforce scheduling platform.

## Structure

```
cedar/
  backend/   FastAPI + SQLAlchemy 2 + Alembic
  frontend/  React + Vite + TypeScript
  docker/    docker-compose.yml
  docs/      architecture notes
```

## Run with Docker (recommended)

```
cp backend/.env.example backend/.env
cd docker
docker compose up --build
```

- Backend: http://localhost:8000/health
- Frontend: http://localhost:5173

## Run without Docker

Backend:
```
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:
```
cd frontend
npm install
npm run dev
```

PostgreSQL must be running separately (see docker/docker-compose.yml
for the expected user/password/db, or run "docker compose up db" alone).
