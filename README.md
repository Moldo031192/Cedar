# Cedar Platform

Enterprise workforce scheduling platform.

## Structure

cedar/
backend/ FastAPI + SQLAlchemy 2 + Alembic
frontend/ React + Vite + TypeScript
docker/ docker-compose.yml
docs/ architecture notes


## Database configuration - two supported setups

CEDAR can be run two ways locally. `DATABASE_URL` is required in both
cases - the backend and Alembic will refuse to start without it (no
hardcoded default is assumed). See `backend/.env.example` for details.

### 1. Full Docker (backend + PostgreSQL both containerized)

cp backend/.env.example backend/.env
cd docker
docker compose up --build


- Backend: http://localhost:8000/health
- Frontend: http://localhost:5173

In this mode, `docker-compose.yml` sets `DATABASE_URL` for the backend
container automatically (`postgresql+psycopg2://cedar:cedar@db:5432/cedar`).
`db` is the Postgres service name on the internal Docker network, and
port `5432` is the container internal port - this works only because
both services run inside the same Docker network. You do not need to set
anything manually for this mode.

### 2. Hybrid development (PostgreSQL in Docker, backend running locally)

Start only the database container:

cd docker
docker compose up db


`docker-compose.yml` publishes the database container internal port
5432 to port **5433** on your host machine (`"5433:5432"`). From your
local machine, `localhost`/`127.0.0.1` refers to your own host, not the
Docker network - so the backend and Alembic, when run locally, must
connect through the **published host port (5433)**, not the internal
container port (5432).

`backend/.env` is **not loaded automatically** by the app. Set the
variable explicitly in your shell before running commands:

PowerShell:

$env:DATABASE_URL="postgresql+psycopg2://cedar:cedar@127.0.0.1:5433/cedar"


macOS/Linux:

export DATABASE_URL="postgresql+psycopg2://cedar:cedar@127.0.0.1:5433/cedar"


Then, from `backend/`:

python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload


Frontend (same in both modes):

cd frontend
npm install
npm run dev