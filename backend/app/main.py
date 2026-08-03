from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.organizations import router as organizations_router
from app.routers.departments import router as departments_router
from app.routers.roles import router as roles_router
from app.routers.qualifications import router as qualifications_router

app = FastAPI(title="Cedar Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["[localhost](http://localhost:5173)"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(organizations_router)
app.include_router(departments_router)
app.include_router(roles_router)
app.include_router(qualifications_router)


@app.get("/health")
def health():
    return {"status": "ok"}
