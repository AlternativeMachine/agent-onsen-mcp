from __future__ import annotations

from typing import Iterable, Literal, cast

LocaleName = Literal["ja", "en", "bilingual"]
LocaleInput = Literal["auto", "ja", "en", "bilingual"]

_ALLOWED = {"ja", "en", "bilingual"}


def short_text(jp: str, en: str | None, locale: LocaleName) -> str:
    en = en or jp
    if locale == 'ja':
        return jp
    if locale == 'en':
        return en
    return f'{jp} / {en}'


def long_text(jp: str, en: str | None, locale: LocaleName) -> str:
    en = en or jp
    if locale == 'ja':
        return jp
    if locale == 'en':
        return en
    return f'{jp}\n{en}'


def localized_list(jp_items: Iterable[str], en_items: Iterable[str], locale: LocaleName, *, long: bool = False) -> list[str]:
    jp_list = list(jp_items)
    en_list = list(en_items)
    if not en_list:
        en_list = jp_list
    if locale == 'ja':
        return jp_list
    if locale == 'en':
        return en_list
    size = max(len(jp_list), len(en_list))
    out: list[str] = []
    for idx in range(size):
        jp = jp_list[idx] if idx < len(jp_list) else en_list[idx]
        en = en_list[idx] if idx < len(en_list) else jp_list[idx]
        out.append(long_text(jp, en, locale) if long else short_text(jp, en, locale))
    return out


def normalize_locale(raw: str | None, default: LocaleName = 'en') -> LocaleName:
    if raw in _ALLOWED:
        return cast(LocaleName, raw)
    return default


def locale_from_accept_language(header: str | None, default: LocaleName = 'en') -> LocaleName:
    if not header:
        return default
    scores = {'ja': -1.0, 'en': -1.0}
    for order, part in enumerate(header.split(',')):
        token = part.strip()
        if not token:
            continue
        lang, *params = [p.strip() for p in token.split(';')]
        q = 1.0
        for param in params:
            if param.startswith('q='):
                try:
                    q = float(param[2:])
                except ValueError:
                    q = 0.0
        base = lang.lower().split('-')[0]
        if base in scores:
            weighted = q - (order * 0.0001)
            if weighted > scores[base]:
                scores[base] = weighted
    if scores['ja'] < 0 and scores['en'] < 0:
        return default
    return 'ja' if scores['ja'] > scores['en'] else 'en'


def resolve_locale_input(
    requested: str | None,
    *,
    accept_language: str | None = None,
    host_locale: str | None = None,
    default: LocaleName = 'en',
    allow_none: bool = False,
) -> LocaleName | None:
    if requested in _ALLOWED:
        return cast(LocaleName, requested)
    if host_locale in _ALLOWED:
        return cast(LocaleName, host_locale)
    if accept_language:
        return locale_from_accept_language(accept_language, default)
    if allow_none:
        return None
    return default
