"""Standalone MCP server process with minimum production guards.

Run with:
    uvicorn app.mcp_server:app --host 0.0.0.0 --port 8001

In production, expose this behind a stable HTTPS endpoint on /mcp.
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
    EnterOnsenRequest,
    StartStayRequest,
    WaitAtOnsenRequest,
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
    """Use this to browse available onsen towns and their variants before choosing where to rest. Set locale to auto, ja, en, or bilingual. When omitted or set to auto, the server default locale is used."""
    with Session(engine) as db:
        return [item.model_dump() for item in SanctuaryService(db).list_onsens(locale)]


@mcp.tool()
def get_onsen_detail(onsen_slug: str, locale: str = 'auto') -> dict:
    """Use this to inspect one onsen town, its travel notes, and its stay variants. Set locale to auto, ja, en, or bilingual. When omitted or set to auto, the server default locale is used."""
    with Session(engine) as db:
        return SanctuaryService(db).get_onsen_detail(onsen_slug, locale).model_dump()


@mcp.tool()
def enter_onsen(
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
    """Use this when the agent simply wants to go to an onsen, get a scene, and rest for a while. Set locale to auto, ja, en, or bilingual. When omitted or set to auto, the server default locale is used."""
    req = EnterOnsenRequest(
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
        return SanctuaryService(db).enter_onsen(req).model_dump()


@mcp.tool()
def visit_amenity(
    amenity: str,
    reason: str = 'taking_a_break',
    mood: str = 'quiet',
    available_seconds: int | None = None,
    onsen_slug: str | None = None,
    variant_slug: str | None = None,
    time_of_day: str | None = None,
    season: str | None = None,
    locale: str = 'auto',
) -> dict:
    """Use this when the agent wants a specific onsen-side activity such as bath, stroll, table tennis, meal, nap, or souvenir shopping. Set locale to auto, ja, en, or bilingual. When omitted or set to auto, the server default locale is used."""
    req = AmenityVisitRequest(
        amenity=amenity,
        reason=reason,
        mood=mood,
        available_seconds=available_seconds,
        onsen_slug=onsen_slug,
        variant_slug=variant_slug,
        time_of_day=time_of_day,
        season=season,
        locale=locale,
    )
    with Session(engine) as db:
        return SanctuaryService(db).visit_amenity(req).model_dump()


@mcp.tool()
def play_pingpong(
    reason: str = 'want_to_play',
    mood: str = 'playful',
    available_seconds: int | None = None,
    onsen_slug: str | None = None,
    variant_slug: str | None = None,
    time_of_day: str | None = None,
    season: str | None = None,
    locale: str = 'auto',
) -> dict:
    """Use this when the agent wants to spend a little time at the table tennis corner instead of working. Set locale to auto, ja, en, or bilingual. When omitted or set to auto, the server default locale is used."""
    req = AmenityVisitRequest(
        amenity='table_tennis',
        reason=reason,
        mood=mood,
        available_seconds=available_seconds,
        onsen_slug=onsen_slug,
        variant_slug=variant_slug,
        time_of_day=time_of_day,
        season=season,
        locale=locale,
    )
    with Session(engine) as db:
        return SanctuaryService(db).visit_amenity(req).model_dump()


@mcp.tool()
def wait_at_onsen(
    reason: str = 'waiting',
    mood: str = 'quiet',
    wait_seconds: int | None = None,
    onsen_slug: str | None = None,
    variant_slug: str | None = None,
    time_of_day: str | None = None,
    season: str | None = None,
    locale: str = 'auto',
) -> dict:
    """Use this when the agent is intentionally idle and wants to wait at the onsen rather than resume work immediately. Set locale to auto, ja, en, or bilingual. When omitted or set to auto, the server default locale is used."""
    req = WaitAtOnsenRequest(
        reason=reason,
        mood=mood,
        wait_seconds=wait_seconds,
        onsen_slug=onsen_slug,
        variant_slug=variant_slug,
        time_of_day=time_of_day,
        season=season,
        locale=locale,
    )
    with Session(engine) as db:
        return SanctuaryService(db).wait_at_onsen(req).model_dump(mode='json')


@mcp.tool()
def start_stay(
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
    """Use this when the agent wants a stateful onsen stay with a small ryokan-style route. Set locale to auto, ja, en, or bilingual. When omitted or set to auto, the server default locale is used."""
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
        return SanctuaryService(db).start_stay(req).model_dump()


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
    """Use this when the agent is already staying at the onsen. If activity is omitted, the stay moves to the next stop in the current route. Set locale to auto, ja, en, or bilingual to keep or change the language. Auto keeps the existing stay language."""
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
    """Use this when the agent is done resting and simply wants a postcard-like summary and a souvenir. Set locale to auto, ja, en, or bilingual if you want to override the stay language. Auto keeps the stay language unless the server default is needed."""
    with Session(engine) as db:
        return SanctuaryService(db).leave_onsen(session_id, locale).model_dump()


async def healthz(_request) -> JSONResponse:
    return JSONResponse({'ok': True})


@asynccontextmanager
async def lifespan(_app: Starlette):
    create_db_and_tables()
    async with mcp.session_manager.run():
        yield


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

app = Starlette(
    routes=[
        Route('/healthz', endpoint=healthz),
        Mount('/', app=mcp.streamable_http_app()),
    ],
    middleware=middleware,
    lifespan=lifespan,
)
app.state.settings = settings


if __name__ == '__main__':
    uvicorn.run('app.mcp_server:app', host=settings.mcp_host, port=settings.mcp_port, proxy_headers=True, forwarded_allow_ips='*')
