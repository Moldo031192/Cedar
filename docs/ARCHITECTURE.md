# Cedar Platform - Architecture

Enterprise workforce scheduling platform.

## Stack

- Backend: FastAPI + SQLAlchemy 2 + Alembic
- Database: PostgreSQL (Docker)
- Frontend: React + Vite + TypeScript
- Orchestration: Docker Compose

## Status

As of 2026-08-15 (end of day):

- Data foundation exists: Organization, Department, Role, Qualification,
  Employee, EmployeeQualification, DemandTask, Shift, EmployeeShift
  (models, schemas, routers, and migrations for all of the above).
- demand_calculator and workforce_coverage services exist.
- Migration history is stabilized: a fresh database can be built from
  migration history alone (validated twice).
- Database environment configuration is stabilized for both Full Docker
  and Hybrid (local backend + Dockerized PostgreSQL) development.
- Authentication is not yet implemented.
- Automated testing is not yet implemented (next planned milestone:
  Testing Baseline).
- Frontend is still only the application scaffold; no functional UI yet.