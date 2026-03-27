from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .a2a import router as a2a_router
from .config import get_settings
from .db import create_db_and_tables
from .routers.health import router as health_router
from .routers.internal import router as internal_router
from .security import OnsenSecurityMiddleware, build_cors_kwargs

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.state.settings = settings

cors_kwargs = build_cors_kwargs(settings)
if cors_kwargs:
    app.add_middleware(CORSMiddleware, **cors_kwargs)
app.add_middleware(
    OnsenSecurityMiddleware,
    settings=settings,
    protected_prefixes=('/v1',),
    exempt_paths=('/healthz', '/.well-known/agent-card.json'),
)


@app.on_event('startup')
def on_startup() -> None:
    create_db_and_tables()


_static_dir = Path(__file__).resolve().parent / 'static'


@app.get('/')
def index():
    return FileResponse(_static_dir / 'index.html')


app.include_router(health_router)
app.include_router(internal_router)
app.include_router(a2a_router)
