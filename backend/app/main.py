from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import engine, Base
from app.api.routes import auth, projects, updates, dashboard, autonomy

app = FastAPI(
    title=settings.APP_NAME,
    description="Autonomous AI Project Manager",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(updates.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(autonomy.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"status": "running", "app": settings.APP_NAME}


@app.get("/health")
async def health():
    return {"status": "healthy"}