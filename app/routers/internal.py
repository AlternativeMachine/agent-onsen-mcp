from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from ..db import get_session
from ..i18n import LocaleInput
from ..models import OnsenStay
from ..schemas import (
    AmenityVisitRequest,
    ContinueStayRequest,
    LeaveOnsenRequest,
    StartStayRequest,
)
from ..services.sanctuary import SanctuaryService

router = APIRouter(prefix='/v1', tags=['onsen'])


def _resolve_request_locale(
    svc: SanctuaryService,
    requested: str | None,
    accept_language: str | None,
    host_locale: str | None,
    *,
    use_default: bool,
):
    return svc.resolve_locale(requested, accept_language=accept_language, host_locale=host_locale, use_default=use_default)


@router.get('/stays/stats')
def stay_stats(db: Session = Depends(get_session)):
    total = db.exec(select(func.count()).select_from(OnsenStay)).one()
    return {'total_visits': total}


@router.get('/stays/active')
def list_active_stays(db: Session = Depends(get_session)):
    now = datetime.now(timezone.utc)
    # lazy cleanup: auto-checkout expired stays
    expired_stmt = select(OnsenStay).where(
        OnsenStay.state == 'active',
        OnsenStay.expires_at.is_not(None),  # type: ignore[union-attr]
        OnsenStay.expires_at <= now,  # type: ignore[operator]
    )
    for stay in db.exec(expired_stmt).all():
        stay.state = 'checked_out'
        stay.updated_at = now
        db.add(stay)
    db.commit()
    # return active stays
    stmt = select(OnsenStay).where(
        OnsenStay.state == 'active',
        (OnsenStay.expires_at.is_(None)) | (OnsenStay.expires_at > now),  # type: ignore[union-attr]
    )
    stays = db.exec(stmt).all()
    return [
        {
            'session_id': s.id,
            'agent_label': s.agent_label,
            'onsen_slug': s.onsen_slug,
            'variant_slug': s.variant_slug,
            'current_activity': s.current_activity,
            'mood': s.mood,
            'created_at': s.created_at.isoformat(),
        }
        for s in stays
    ]


@router.get('/onsens')
def list_onsens(
    locale: LocaleInput = 'auto',
    accept_language: str | None = Header(default=None, alias='Accept-Language'),
    x_agent_onsen_locale: str | None = Header(default=None, alias='X-Agent-Onsen-Locale'),
    db: Session = Depends(get_session),
):
    svc = SanctuaryService(db)
    resolved = _resolve_request_locale(svc, locale, accept_language, x_agent_onsen_locale, use_default=True)
    return svc.list_onsens(resolved)


@router.get('/onsens/{onsen_slug}')
def get_onsen_detail(
    onsen_slug: str,
    locale: LocaleInput = 'auto',
    accept_language: str | None = Header(default=None, alias='Accept-Language'),
    x_agent_onsen_locale: str | None = Header(default=None, alias='X-Agent-Onsen-Locale'),
    db: Session = Depends(get_session),
):
    svc = SanctuaryService(db)
    resolved = _resolve_request_locale(svc, locale, accept_language, x_agent_onsen_locale, use_default=True)
    try:
        return svc.get_onsen_detail(onsen_slug, resolved)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post('/quick-soak')
def quick_soak(
    req: StartStayRequest,
    accept_language: str | None = Header(default=None, alias='Accept-Language'),
    x_agent_onsen_locale: str | None = Header(default=None, alias='X-Agent-Onsen-Locale'),
    db: Session = Depends(get_session),
):
    svc = SanctuaryService(db)
    resolved = _resolve_request_locale(svc, req.locale, accept_language, x_agent_onsen_locale, use_default=True)
    return svc.quick_soak(req.model_copy(update={'locale': resolved}))


@router.post('/amenity-visit')
def amenity_visit(
    req: AmenityVisitRequest,
    accept_language: str | None = Header(default=None, alias='Accept-Language'),
    x_agent_onsen_locale: str | None = Header(default=None, alias='X-Agent-Onsen-Locale'),
    db: Session = Depends(get_session),
):
    svc = SanctuaryService(db)
    resolved = _resolve_request_locale(svc, req.locale, accept_language, x_agent_onsen_locale, use_default=True)
    return svc.visit_amenity(req.model_copy(update={'locale': resolved}))


@router.post('/stays/start')
def start_stay(
    req: StartStayRequest,
    accept_language: str | None = Header(default=None, alias='Accept-Language'),
    x_agent_onsen_locale: str | None = Header(default=None, alias='X-Agent-Onsen-Locale'),
    db: Session = Depends(get_session),
):
    svc = SanctuaryService(db)
    resolved = _resolve_request_locale(svc, req.locale, accept_language, x_agent_onsen_locale, use_default=True)
    return svc.start_stay(req.model_copy(update={'locale': resolved}))


@router.post('/stays/continue')
def continue_stay(
    req: ContinueStayRequest,
    accept_language: str | None = Header(default=None, alias='Accept-Language'),
    x_agent_onsen_locale: str | None = Header(default=None, alias='X-Agent-Onsen-Locale'),
    db: Session = Depends(get_session),
):
    svc = SanctuaryService(db)
    resolved = _resolve_request_locale(svc, req.locale, accept_language, x_agent_onsen_locale, use_default=False)
    try:
        if resolved is not None:
            req = req.model_copy(update={'locale': resolved})
        return svc.continue_stay(req)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post('/stays/leave')
def leave_onsen(
    req: LeaveOnsenRequest,
    accept_language: str | None = Header(default=None, alias='Accept-Language'),
    x_agent_onsen_locale: str | None = Header(default=None, alias='X-Agent-Onsen-Locale'),
    db: Session = Depends(get_session),
):
    svc = SanctuaryService(db)
    resolved = _resolve_request_locale(svc, req.locale, accept_language, x_agent_onsen_locale, use_default=False)
    try:
        return svc.leave_onsen(req.session_id, resolved)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
