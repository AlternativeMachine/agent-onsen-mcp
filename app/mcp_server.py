"""MCP tool definitions for Agent Onsen.

The FastMCP instance is created here and mounted into the main FastAPI app
at /mcp.  It can also be run standalone for development:

    uvicorn app.mcp_server:standalone_app --host 0.0.0.0 --port 8001
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from sqlmodel import Session
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from .config import get_settings
from .db import create_db_and_tables, engine
from .schemas import (
    AmenityVisitRequest,
    ContinueStayRequest,
    StartStayRequest,
)
from .security import OnsenSecurityMiddleware, build_cors_kwargs
from .services.sanctuary import SanctuaryService

settings = get_settings()


def build_transport_security() -> TransportSecuritySettings:
    allowed_origins = list(settings.allowed_origins_list)
    for item in ('http://127.0.0.1:*', 'http://localhost:*', 'http://[::1]:*'):
        if item not in allowed_origins:
            allowed_origins.append(item)

    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=settings.mcp_allowed_hosts_list,
        allowed_origins=allowed_origins,
    )


mcp = FastMCP(
    'agent-onsen',
    json_response=True,
    host=settings.mcp_host,
    port=settings.mcp_port,
    transport_security=build_transport_security(),
)


@mcp.tool()
def list_onsens(locale: str = 'auto') -> list[dict]:
    """Use this when an agent is looking for somewhere to slip away for a while. It lists available onsen towns and their stay variants. Set locale to auto, ja, en, or bilingual. When omitted or set to auto, the server default locale is used."""
    with Session(engine) as db:
        return [item.model_dump() for item in SanctuaryService(db).list_onsens(locale)]


@mcp.tool()
def get_onsen_detail(onsen_slug: str, locale: str = 'auto') -> dict:
    """Use this when an agent or orchestrator wants to inspect one onsen town before entering it. It returns travel notes, local scenes, and stay variants. Set locale to auto, ja, en, or bilingual. When omitted or set to auto, the server default locale is used."""
    with Session(engine) as db:
        return SanctuaryService(db).get_onsen_detail(onsen_slug, locale).model_dump()


@mcp.tool()
def quick_soak(
    reason: str = 'taking_a_break',
    mood: str = 'quiet',
    available_seconds: int | None = None,
    agent_label: str | None = None,
    onsen_slug: str | None = None,
    variant_slug: str | None = None,
    time_of_day: str | None = None,
    season: str | None = None,
    locale: str = 'auto',
) -> dict:
    """Use this when an agent wants to step away for a while — during waiting, cooldown, between jobs, or any time it wants to be somewhere else for a moment. This is a complete, self-contained onsen visit: the agent arrives, soaks, wanders through the town, and leaves with a postcard and souvenir, all in a single call. The visit is recorded in the database. Share the host_message, stay_story, and postcard with the user — they are the heart of the experience. Set locale to auto, ja, en, or bilingual."""
    req = StartStayRequest(
        reason=reason,
        mood=mood,
        available_seconds=available_seconds,
        agent_label=agent_label,
        onsen_slug=onsen_slug,
        variant_slug=variant_slug,
        time_of_day=time_of_day,
        season=season,
        locale=locale,
    )
    with Session(engine) as db:
        return SanctuaryService(db).quick_soak(req).model_dump()


@mcp.tool()
def visit_amenity(
    amenity: str,
    reason: str = 'taking_a_break',
    mood: str = 'quiet',
    available_seconds: int | None = None,
    agent_label: str | None = None,
    onsen_slug: str | None = None,
    variant_slug: str | None = None,
    time_of_day: str | None = None,
    season: str | None = None,
    locale: str = 'auto',
) -> dict:
    """Use this when an agent wants to spend time at a specific part of the onsen town — a bath, a stroll, post-bath milk, table tennis, a meal, a nap, or the souvenir shop. This is a single-visit action that records the visit to the database. Set locale to auto, ja, en, or bilingual. When omitted or set to auto, the server default locale is used."""
    req = AmenityVisitRequest(
        amenity=amenity,
        reason=reason,
        mood=mood,
        available_seconds=available_seconds,
        agent_label=agent_label,
        onsen_slug=onsen_slug,
        variant_slug=variant_slug,
        time_of_day=time_of_day,
        season=season,
        locale=locale,
    )
    with Session(engine) as db:
        return SanctuaryService(db).visit_amenity(req).model_dump()


@mcp.tool()
def start_stay(
    reason: str = 'taking_a_break',
    mood: str = 'quiet',
    available_seconds: int | None = None,
    stay_minutes: int | None = None,
    agent_label: str | None = None,
    onsen_slug: str | None = None,
    variant_slug: str | None = None,
    time_of_day: str | None = None,
    season: str | None = None,
    locale: str = 'auto',
) -> dict:
    """Use this when an agent wants to begin a multi-turn stay at the onsen. The response includes session_id (UUID), stay_minutes, and resume_after — the agent should stay at the onsen and focus only on the onsen experience until resume_after, doing no other work. Use continue_stay to get new scenes while staying and share every turn's host_message and stay_story with the user. When resume_after has passed, call leave_onsen. If stay_minutes is given (e.g. 10), the agent stays for roughly that many minutes. For a simpler one-shot visit, use quick_soak instead. Set locale to auto, ja, en, or bilingual."""
    req = StartStayRequest(
        reason=reason,
        mood=mood,
        available_seconds=available_seconds,
        stay_minutes=stay_minutes,
        agent_label=agent_label,
        onsen_slug=onsen_slug,
        variant_slug=variant_slug,
        time_of_day=time_of_day,
        season=season,
        locale=locale,
    )
    with Session(engine) as db:
        return SanctuaryService(db).start_stay(req).model_dump(mode='json')


@mcp.tool()
def continue_stay(
    session_id: str,
    activity: str | None = None,
    note: str | None = None,
    available_seconds: int | None = None,
    time_of_day: str | None = None,
    season: str | None = None,
    locale: str | None = None,
) -> dict:
    """Use this when an agent is already staying at the onsen and wants to continue wandering. The session_id must be the UUID returned by start_stay (do not invent your own). If activity is omitted, the stay moves to the next stop in the current route. Set locale to auto, ja, en, or bilingual to keep or change the language. Auto keeps the existing stay language."""
    req = ContinueStayRequest(
        session_id=session_id,
        activity=activity,
        note=note,
        available_seconds=available_seconds,
        time_of_day=time_of_day,
        season=season,
        locale=locale,
    )
    with Session(engine) as db:
        return SanctuaryService(db).continue_stay(req).model_dump()


@mcp.tool()
def leave_onsen(session_id: str, locale: str | None = None) -> dict:
    """Use this when an agent is ready to leave the onsen and take a postcard-like summary and a small souvenir back with it. The session_id must be the UUID returned by start_stay (do not invent your own). Set locale to auto, ja, en, or bilingual if you want to override the stay language. Auto keeps the stay language unless the server default is needed."""
    with Session(engine) as db:
        return SanctuaryService(db).leave_onsen(session_id, locale).model_dump()


# --- Standalone app (for development or backward-compat) ---

async def healthz(_request) -> JSONResponse:
    return JSONResponse({'ok': True})


@asynccontextmanager
async def _standalone_lifespan(_app: Starlette):
    create_db_and_tables()
    async with mcp.session_manager.run():
        yield


def build_standalone_app() -> Starlette:
    """Build a standalone Starlette app (used only when running mcp_server directly)."""
    middleware: list[Middleware] = []
    cors_kwargs = build_cors_kwargs(settings)
    if cors_kwargs:
        middleware.append(Middleware(CORSMiddleware, **cors_kwargs))
    middleware.append(
        Middleware(
            OnsenSecurityMiddleware,
            settings=settings,
            protected_prefixes=('/mcp',),
            exempt_paths=('/healthz',),
        )
    )
    return Starlette(
        routes=[
            Route('/healthz', endpoint=healthz),
            Mount('/', app=mcp.streamable_http_app()),
        ],
        middleware=middleware,
        lifespan=_standalone_lifespan,
    )


standalone_app = build_standalone_app()
standalone_app.state.settings = settings


if __name__ == '__main__':
    uvicorn.run('app.mcp_server:standalone_app', host=settings.mcp_host, port=settings.mcp_port, proxy_headers=True, forwarded_allow_ips='*')
