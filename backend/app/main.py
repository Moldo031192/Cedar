from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.organizations import router as organizations_router

app = FastAPI(title="Cedar Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["[localhost](http://localhost:5173)"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(organizations_router)


@app.get("/health")
def health():
    return {"status": "ok"}
