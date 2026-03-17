from __future__ import annotations

from datetime import timedelta
import hashlib
from typing import Sequence
from zoneinfo import ZoneInfo

from sqlmodel import Session

from ..config import get_settings
from ..data.itineraries import get_route_blueprint
from ..data.locales import entry_en, note_en, route_name_en, stop_title_en, variant_en
from ..data.onsen_notes import get_onsen_note
from ..data.onsens import (
    ONSEN_CATALOG,
    OnsenEntry,
    OnsenVariant,
    find_onsen,
    find_variant,
    iter_matching_onsens,
    iter_matching_variants,
)
from ..i18n import LocaleInput, LocaleName, localized_list, long_text, normalize_locale, resolve_locale_input, short_text
from ..models import OnsenStay, StayTurn, utcnow
from ..schemas import (
    ActivityCard,
    ActivityName,
    AmenityVisitRequest,
    ContinueStayRequest,
    EnterOnsenRequest,
    LeaveOnsenResponse,
    MoodName,
    OnsenCard,
    OnsenCatalogItem,
    OnsenDetail,
    OnsenVariantCard,
    OnsenVisitResponse,
    ReasonName,
    SceneProfile,
    StartStayRequest,
    StayRoute,
    StayRouteStop,
    StayTurnResponse,
    WaitAtOnsenRequest,
    WaitAtOnsenResponse,
)


TOKYO_TZ = ZoneInfo('Asia/Tokyo')


class SanctuaryService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def resolve_locale(
        self,
        requested: str | None,
        *,
        accept_language: str | None = None,
        host_locale: str | None = None,
        use_default: bool = True,
    ) -> LocaleName | None:
        default_locale = normalize_locale(getattr(self.settings, 'default_locale', 'en'), 'en')
        return resolve_locale_input(
            requested,
            accept_language=accept_language,
            host_locale=host_locale,
            default=default_locale,
            allow_none=not use_default,
        )

    def _stable_index(self, size: int, key: str) -> int:
        if size <= 0:
            return 0
        hashed = int(hashlib.sha256(key.encode('utf-8')).hexdigest(), 16)
        return hashed % size

    def _stable_choice(self, items: Sequence, key: str):
        if not items:
            raise ValueError('items must not be empty')
        return items[self._stable_index(len(items), key)]

    def _rest_tags(self, reason: ReasonName, mood: MoodName) -> tuple[str, ...]:
        reason_map: dict[str, tuple[str, ...]] = {
            'taking_a_break': ('reflect', 'decompress'),
            'waiting': ('low_confidence', 'reflect'),
            'cooling_down': ('refresh', 'looping'),
            'feeling_sleepy': ('low_confidence', 'decompress'),
            'want_to_play': ('creative_block', 'play'),
            'just_because': ('reflect', 'play'),
        }
        mood_map: dict[str, tuple[str, ...]] = {
            'quiet': ('reflect',),
            'frazzled': ('looping', 'refresh'),
            'sleepy': ('low_confidence', 'decompress'),
            'playful': ('creative_block', 'play'),
            'blank': ('unclear_goal', 'decompress'),
            'wandering': ('creative_block', 'reflect'),
        }
        tags = list(reason_map.get(reason, ())) + list(mood_map.get(mood, ()))
        return tuple(tags or ('reflect', 'decompress'))

    # ---------- localization helpers ----------

    def _entry_text(self, entry: OnsenEntry, field: str, locale: LocaleName, *, long: bool = False) -> str:
        jp = getattr(entry, field)
        en = entry_en(entry.slug).get(field)
        return long_text(jp, en, locale) if long else short_text(jp, en, locale)

    def _variant_text(self, entry: OnsenEntry, variant: OnsenVariant, field: str, locale: LocaleName, *, long: bool = False) -> str:
        jp = getattr(variant, field)
        en = variant_en(entry.slug, variant.slug).get(field)
        return long_text(jp, en, locale) if long else short_text(jp, en, locale)

    def _note_text(self, entry: OnsenEntry, field: str, locale: LocaleName, *, long: bool = True) -> str:
        note = get_onsen_note(entry.slug)
        jp = getattr(note, field)
        en = note_en(entry.slug).get(field)
        if not isinstance(jp, str):
            raise ValueError(f'note field {field} is not a string field')
        return long_text(jp, en if isinstance(en, str) else None, locale) if long else short_text(jp, en if isinstance(en, str) else None, locale)

    def _note_list(self, entry: OnsenEntry, field: str, locale: LocaleName) -> list[str]:
        note = get_onsen_note(entry.slug)
        jp = list(getattr(note, field))
        en_value = note_en(entry.slug).get(field)
        en = list(en_value) if isinstance(en_value, (list, tuple)) else []
        return localized_list(jp, en, locale)

    def _variant_snack(self, entry: OnsenEntry, variant: OnsenVariant, locale: LocaleName) -> str:
        jp_default = get_onsen_note(entry.slug).local_treats[0] if get_onsen_note(entry.slug).local_treats else '温泉まんじゅう'
        jp = variant.snack or jp_default
        en_default = (note_en(entry.slug).get('local_treats') or ['onsen manju'])[0]
        en = variant_en(entry.slug, variant.slug).get('snack') or en_default
        return short_text(jp, en, locale)

    def _route_name_text(self, jp_name: str, locale: LocaleName) -> str:
        en = route_name_en(jp_name)
        return short_text(jp_name, en, locale)

    def _stop_title_text(self, jp_title: str, locale: LocaleName) -> str:
        en = stop_title_en(jp_title)
        return short_text(jp_title, en, locale)

    # ---------- cards and notes ----------

    def _variant_story(self, entry: OnsenEntry, variant: OnsenVariant, locale: LocaleName) -> tuple[str, list[str], list[str], str]:
        wander_spots = self._note_list(entry, 'wander_spots', locale)
        local_treats = self._note_list(entry, 'local_treats', locale)
        what_to_notice = self._note_list(entry, 'what_to_notice', locale)
        snack = self._variant_snack(entry, variant, locale)
        bath_feel = self._variant_text(entry, variant, 'bath_feel', locale, long=True)
        town_vibe = self._variant_text(entry, variant, 'town_vibe', locale, long=True)
        vignette_jp = f'{variant.bath_feel}。{variant.town_vibe}'
        vignette_en = f"{variant_en(entry.slug, variant.slug).get('bath_feel', variant.bath_feel)} {variant_en(entry.slug, variant.slug).get('town_vibe', variant.town_vibe)}"
        vignette = long_text(vignette_jp, vignette_en, locale)

        seq_jp = [
            f'到着したら {get_onsen_note(entry.slug).wander_spots[0]} を少し歩く',
            f'湯では {variant.bath_feel}',
            f'湯上がりは {variant.snack or get_onsen_note(entry.slug).local_treats[0]} をひとつつまむ',
        ]
        seq_en = [
            f'On arrival, take a short walk by {wander_spots[0]}.',
            f'In the bath, let the mood be: {bath_feel}.',
            f'After the soak, have one small thing such as {snack}.',
        ]
        sequence = localized_list(seq_jp, seq_en, locale, long=True)

        sensory_jp = [
            get_onsen_note(entry.slug).what_to_notice[0],
            get_onsen_note(entry.slug).what_to_notice[1] if len(get_onsen_note(entry.slug).what_to_notice) > 1 else variant.town_vibe,
            variant.bath_feel,
        ]
        sensory_en = [
            what_to_notice[0],
            what_to_notice[1] if len(what_to_notice) > 1 else town_vibe,
            bath_feel,
        ]
        sensory_notes = localized_list(sensory_jp, sensory_en, locale)

        postcard_jp = f'{variant.title}。{get_onsen_note(entry.slug).postcard_line}'
        postcard_en = f"{variant_en(entry.slug, variant.slug).get('title', variant.title)}. {note_en(entry.slug).get('postcard_line', get_onsen_note(entry.slug).postcard_line)}"
        postcard_line = long_text(postcard_jp, postcard_en, locale)
        return vignette, sequence, sensory_notes, postcard_line

    def _onsen_card(self, entry: OnsenEntry, variant: OnsenVariant, locale: LocaleName) -> OnsenCard:
        variant_vignette, sequence, sensory_notes, variant_postcard = self._variant_story(entry, variant, locale)
        return OnsenCard(
            slug=entry.slug,
            name=self._entry_text(entry, 'name', locale),
            prefecture=self._entry_text(entry, 'prefecture', locale),
            spring_profile=self._entry_text(entry, 'spring_profile', locale, long=True),
            hideaway_note=self._entry_text(entry, 'hideaway_note', locale, long=True),
            variant_slug=variant.slug,
            variant_title=self._variant_text(entry, variant, 'title', locale),
            subtitle=self._note_text(entry, 'subtitle', locale),
            arrival_scene=self._note_text(entry, 'arrival_scene', locale),
            long_description=self._note_text(entry, 'long_description', locale),
            architecture_note=self._note_text(entry, 'architecture_note', locale),
            bathing_ritual=self._note_text(entry, 'bathing_ritual', locale),
            what_to_notice=self._note_list(entry, 'what_to_notice', locale),
            wander_spots=self._note_list(entry, 'wander_spots', locale),
            local_treats=self._note_list(entry, 'local_treats', locale),
            seasonal_moods=self._note_list(entry, 'seasonal_moods', locale),
            geeky_note=self._note_text(entry, 'geeky_note', locale),
            postcard_line=self._note_text(entry, 'postcard_line', locale),
            bath_feel=self._variant_text(entry, variant, 'bath_feel', locale, long=True),
            town_vibe=self._variant_text(entry, variant, 'town_vibe', locale, long=True),
            snack=self._variant_snack(entry, variant, locale),
            variant_vignette=variant_vignette,
            variant_sequence=sequence,
            variant_sensory_notes=sensory_notes,
            variant_postcard_line=variant_postcard,
        )

    def _variant_card(self, entry: OnsenEntry, variant: OnsenVariant, locale: LocaleName) -> OnsenVariantCard:
        vignette, sequence, sensory_notes, postcard_line = self._variant_story(entry, variant, locale)
        return OnsenVariantCard(
            slug=variant.slug,
            title=self._variant_text(entry, variant, 'title', locale),
            bath_feel=self._variant_text(entry, variant, 'bath_feel', locale, long=True),
            town_vibe=self._variant_text(entry, variant, 'town_vibe', locale, long=True),
            snack=self._variant_snack(entry, variant, locale),
            vignette=vignette,
            recommended_sequence=sequence,
            sensory_notes=sensory_notes,
            postcard_line=postcard_line,
        )

    def list_onsens(self, locale: LocaleInput | LocaleName | None = None) -> list[OnsenCatalogItem]:
        resolved_locale = self.resolve_locale(locale, use_default=True)
        items: list[OnsenCatalogItem] = []
        for entry in ONSEN_CATALOG:
            items.append(
                OnsenCatalogItem(
                    slug=entry.slug,
                    name=self._entry_text(entry, 'name', resolved_locale),
                    prefecture=self._entry_text(entry, 'prefecture', resolved_locale),
                    hideaway_note=self._entry_text(entry, 'hideaway_note', resolved_locale, long=True),
                    spring_profile=self._entry_text(entry, 'spring_profile', resolved_locale, long=True),
                    subtitle=self._note_text(entry, 'subtitle', resolved_locale),
                    arrival_scene=self._note_text(entry, 'arrival_scene', resolved_locale),
                    postcard_line=self._note_text(entry, 'postcard_line', resolved_locale),
                    variant_count=len(entry.variants),
                    variant_titles=[self._variant_text(entry, variant, 'title', resolved_locale) for variant in entry.variants],
                )
            )
        return items

    def get_onsen_detail(self, slug: str, locale: LocaleInput | LocaleName | None = None) -> OnsenDetail:
        resolved_locale = self.resolve_locale(locale, use_default=True)
        entry = find_onsen(slug)
        if not entry:
            raise ValueError('onsen not found')
        return OnsenDetail(
            slug=entry.slug,
            name=self._entry_text(entry, 'name', resolved_locale),
            prefecture=self._entry_text(entry, 'prefecture', resolved_locale),
            hideaway_note=self._entry_text(entry, 'hideaway_note', resolved_locale, long=True),
            spring_profile=self._entry_text(entry, 'spring_profile', resolved_locale, long=True),
            subtitle=self._note_text(entry, 'subtitle', resolved_locale),
            arrival_scene=self._note_text(entry, 'arrival_scene', resolved_locale),
            long_description=self._note_text(entry, 'long_description', resolved_locale),
            architecture_note=self._note_text(entry, 'architecture_note', resolved_locale),
            bathing_ritual=self._note_text(entry, 'bathing_ritual', resolved_locale),
            what_to_notice=self._note_list(entry, 'what_to_notice', resolved_locale),
            wander_spots=self._note_list(entry, 'wander_spots', resolved_locale),
            local_treats=self._note_list(entry, 'local_treats', resolved_locale),
            seasonal_moods=self._note_list(entry, 'seasonal_moods', resolved_locale),
            geeky_note=self._note_text(entry, 'geeky_note', resolved_locale),
            postcard_line=self._note_text(entry, 'postcard_line', resolved_locale),
            variants=[self._variant_card(entry, variant, resolved_locale) for variant in entry.variants],
            itinerary_previews=self._itinerary_previews(entry, resolved_locale),
        )

    def _itinerary_previews(self, entry: OnsenEntry, locale: LocaleName) -> dict[str, StayRoute]:
        variant = entry.variants[0]
        previews: dict[str, StayRoute] = {}
        representative_seconds = {'short': 120, 'medium': 240, 'long': 420}
        for stay_length, pause_seconds in representative_seconds.items():
            scene_profile = self._build_scene_profile(entry, variant, pause_seconds, locale=locale)
            previews[stay_length] = self._build_stay_route(entry, variant, 'taking_a_break', 'quiet', scene_profile, locale)
        return previews

    # ---------- selection ----------

    def _pick_onsen(self, reason: ReasonName, mood: MoodName, key: str) -> OnsenEntry:
        tags = self._rest_tags(reason, mood)
        candidates = iter_matching_onsens(tags)
        return self._stable_choice(candidates, key)

    def _pick_variant(self, entry: OnsenEntry, reason: ReasonName, mood: MoodName, key: str, forced_variant_slug: str | None = None) -> OnsenVariant:
        if forced_variant_slug:
            return find_variant(entry, forced_variant_slug)
        tags = self._rest_tags(reason, mood)
        candidates = iter_matching_variants(entry, tags)
        return self._stable_choice(candidates, key)

    def _pick_stay(
        self,
        reason: ReasonName,
        mood: MoodName,
        agent_label: str | None,
        onsen_slug: str | None,
        variant_slug: str | None,
        available_seconds: int | None,
    ) -> tuple[OnsenEntry, OnsenVariant]:
        key = f'{reason}|{mood}|{agent_label or "anon"}|{available_seconds or "na"}|{onsen_slug or "auto"}'
        entry = find_onsen(onsen_slug) if onsen_slug else None
        if not entry:
            entry = self._pick_onsen(reason, mood, key)
        variant_key = f'{key}|{entry.slug}'
        variant = self._pick_variant(entry, reason, mood, variant_key, forced_variant_slug=variant_slug)
        return entry, variant

    # ---------- scene ----------

    def _infer_time_of_day(self, requested: str | None = None) -> str:
        if requested:
            return requested
        hour = utcnow().astimezone(TOKYO_TZ).hour
        if 5 <= hour < 11:
            return 'morning'
        if 11 <= hour < 17:
            return 'afternoon'
        if 17 <= hour < 22:
            return 'evening'
        return 'night'

    def _infer_season(self, requested: str | None = None) -> str:
        if requested:
            return requested
        month = utcnow().astimezone(TOKYO_TZ).month
        if month in (3, 4, 5):
            return 'spring'
        if month in (6, 7, 8):
            return 'summer'
        if month in (9, 10, 11):
            return 'autumn'
        return 'winter'

    def _step_base_seconds(self, activity: ActivityName, variant: OnsenVariant) -> int:
        base = {
            'bath': 90,
            'stroll': 70,
            'milk': 40,
            'table_tennis': 80,
            'massage': 100,
            'meal': 120,
            'nap': 150,
            'souvenir': 45,
        }.get(activity, 60)
        return max(30, int(base * variant.pause_scale))

    def _recommended_total_pause_seconds(self, reason: ReasonName, mood: MoodName, variant: OnsenVariant, available_seconds: int | None = None) -> int:
        if available_seconds is not None:
            return max(30, available_seconds)
        base = {
            'taking_a_break': 240,
            'waiting': 180,
            'cooling_down': 180,
            'feeling_sleepy': 360,
            'want_to_play': 300,
            'just_because': 240,
        }.get(reason, 240)
        mood_bonus = {
            'quiet': 30,
            'frazzled': -30,
            'sleepy': 90,
            'playful': 30,
            'blank': 0,
            'wandering': 60,
        }.get(mood, 0)
        scaled = int((base + mood_bonus) * variant.pause_scale)
        return max(90, min(900, scaled))

    def _infer_stay_length(self, pause_seconds: int) -> str:
        if pause_seconds <= 150:
            return 'short'
        if pause_seconds <= 330:
            return 'medium'
        return 'long'

    def _scene_strings(self, entry: OnsenEntry, resolved_time: str, resolved_season: str, stay_length: str) -> dict[str, str]:
        subtitle_ja = get_onsen_note(entry.slug).subtitle
        subtitle_en = str(note_en(entry.slug).get('subtitle', subtitle_ja))
        time_jp = {
            'morning': '朝の湯気はまだ軽く、街は起ききる前のやわらかい顔をしている。',
            'afternoon': '日が高く、湯上がりに少し歩けそうな余白が街じゅうにある。',
            'evening': '灯りが入りはじめ、温泉街がいちばん温泉街らしい輪郭になる時間。',
            'night': '音が減って、灯りと湯けむりだけが街の輪郭をつくっている。',
        }
        time_en = {
            'morning': 'Morning steam is still light, and the town wears its soft-before-open face.',
            'afternoon': 'The day is bright enough that the streets still seem to hold room for a short walk after the bath.',
            'evening': 'Lights are just coming on, and the town is at its most unmistakably onsen-shaped.',
            'night': 'Sound falls away until steam and small lights are doing most of the speaking.',
        }
        season_jp = {
            'spring': '季節の気配は春寄りで、街の輪郭が少しゆるんで見える。',
            'summer': '外気は夏寄りで、湯上がりの風まで含めて気持ちいい。',
            'autumn': '空気は秋寄りで、木や石の匂いが少し濃く残る。',
            'winter': '冬の気配が強く、白い湯けむりがいちばんよく映える。',
        }
        season_en = {
            'spring': 'It feels spring-leaning, with the edges of the town loosened slightly by the season.',
            'summer': 'The outside air is summer-soft, and even the breeze after the bath feels like part of the rest.',
            'autumn': 'The air leans autumnal, with wood and stone smelling a little more distinct than usual.',
            'winter': 'Winter sharpens the white steam until it looks brighter than anywhere else.',
        }
        pace_jp = {
            'short': '今日は短い立ち寄りなので、湯と寄り道をぎゅっとひとまとめに楽しむ。',
            'medium': '今日はちょうどいい長さの滞在なので、湯の前後にもう二つ三つ寄り道できる。',
            'long': '今日は長めにいられるので、湯と散歩と牛乳と、うたた寝まで含めてゆっくり回る。',
        }
        pace_en = {
            'short': 'This is a short stop, so bath and detours stay compact and close together.',
            'medium': 'This stay has enough room for a bath plus two or three small side stops before leaving.',
            'long': 'There is time to move slowly: bath, a walk, milk, and even a nap if the place asks for it.',
        }
        return {
            'atmosphere_jp': f"{time_jp[resolved_time]} {subtitle_ja}",
            'atmosphere_en': f"{time_en[resolved_time]} {subtitle_en}",
            'seasonal_jp': season_jp[resolved_season],
            'seasonal_en': season_en[resolved_season],
            'pacing_jp': pace_jp[stay_length],
            'pacing_en': pace_en[stay_length],
        }

    def _build_scene_profile(
        self,
        entry: OnsenEntry,
        variant: OnsenVariant,
        pause_seconds: int,
        time_of_day: str | None = None,
        season: str | None = None,
        locale: LocaleName = 'ja',
    ) -> SceneProfile:
        resolved_time = self._infer_time_of_day(time_of_day)
        resolved_season = self._infer_season(season)
        stay_length = self._infer_stay_length(pause_seconds)
        scene = self._scene_strings(entry, resolved_time, resolved_season, stay_length)
        return SceneProfile(
            time_of_day=resolved_time,
            season=resolved_season,
            stay_length=stay_length,
            pause_seconds=pause_seconds,
            atmosphere=long_text(scene['atmosphere_jp'], scene['atmosphere_en'], locale),
            seasonal_highlight=long_text(scene['seasonal_jp'], scene['seasonal_en'], locale),
            pacing_note=long_text(scene['pacing_jp'], scene['pacing_en'], locale),
        )

    def _scene_from_meta(self, entry: OnsenEntry, variant: OnsenVariant, meta_json: dict | None, fallback_pause_seconds: int, locale: LocaleName) -> SceneProfile:
        meta_json = meta_json or {}
        pause_seconds = int(meta_json.get('scene_pause_seconds') or fallback_pause_seconds)
        return self._build_scene_profile(
            entry,
            variant,
            pause_seconds=pause_seconds,
            time_of_day=meta_json.get('scene_time_of_day'),
            season=meta_json.get('scene_season'),
            locale=locale,
        )

    # ---------- activities and route ----------

    def _activity_card(self, activity: ActivityName, locale: LocaleName, title_override: str | None = None, short_description_override: str | None = None) -> ActivityCard:
        jp = {
            'bath': ('湯処', 'まずは湯に浸かって、街の空気へ切り替わる。', 'bathing'),
            'stroll': ('湯けむり散歩', '湯に入る前後で、ひと区画だけ歩く。', 'wandering'),
            'milk': ('湯上がり牛乳', '腰に手を当てて、瓶牛乳を一本だけ飲む。', 'sipping'),
            'table_tennis': ('卓球コーナー', '点数を数えないラリーが続く。', 'playing'),
            'massage': ('湯上がりマッサージ', '湯のあとに肩をほどいて、もう少しだけぼんやりする。', 'resting'),
            'meal': ('湯治ごはん処', '湯上がりに素朴な定食をゆっくり食べる。', 'eating'),
            'nap': ('うたた寝処', '窓際でしばらく横になる。', 'dozing'),
            'souvenir': ('お土産処', '温泉まんじゅうや木札が並んでいる。', 'shopping'),
        }
        en = {
            'bath': ('Bathhouse', 'Soak first and let the town replace the old pace.', 'bathing'),
            'stroll': ('Steam-Side Walk', 'Walk one small stretch before or after the bath.', 'wandering'),
            'milk': ('Post-Bath Milk', 'A single cold bottle, taken slowly.', 'sipping'),
            'table_tennis': ('Table Tennis Corner', 'A rally with no one keeping score.', 'playing'),
            'massage': ('Post-Bath Massage', 'Loosen the shoulders and stay a little unfocused.', 'resting'),
            'meal': ('Rest-Cure Meal Room', 'A simple meal taken slowly after the bath.', 'eating'),
            'nap': ('Nap Room', 'Lie down near a window and let the bath finish settling.', 'dozing'),
            'souvenir': ('Souvenir Shop', 'Small sweets and tokens for the road back.', 'shopping'),
        }
        jp_title, jp_desc, status = jp[activity]
        en_title, en_desc, _ = en[activity]
        return ActivityCard(
            activity=activity,
            title=title_override or short_text(jp_title, en_title, locale),
            short_description=short_description_override or long_text(jp_desc, en_desc, locale),
            stay_status=status,  # statuses remain machine-friendly English
        )

    def _route_note_for_step(self, entry: OnsenEntry, variant: OnsenVariant, activity: ActivityName, scene_profile: SceneProfile, locale: LocaleName) -> str:
        note = get_onsen_note(entry.slug)
        note_i18n = note_en(entry.slug)
        treat_jp = variant.snack or (note.local_treats[0] if note.local_treats else '牛乳')
        treat_en = variant_en(entry.slug, variant.slug).get('snack') or (note_i18n.get('local_treats') or ['milk'])[0]
        bath_feel_en = variant_en(entry.slug, variant.slug).get('bath_feel', variant.bath_feel)
        arch_en = str(note_i18n.get('architecture_note', note.architecture_note))
        ritual_en = str(note_i18n.get('bathing_ritual', note.bathing_ritual))
        wander_spots_en = list(note_i18n.get('wander_spots', note.wander_spots))
        treats_en = list(note_i18n.get('local_treats', note.local_treats))

        scene = self._scene_strings(entry, scene_profile.time_of_day, scene_profile.season, scene_profile.stay_length)
        lines_jp = {
            'bath': f'湯では {variant.bath_feel}。{note.bathing_ritual}',
            'stroll': f'{note.wander_spots[0]} を目印に、湯けむりが濃い一角だけ歩く。',
            'milk': f'脱衣所の近くで瓶牛乳を一本。余裕があれば {treat_jp} も気にしてみる。',
            'table_tennis': '卓球台の周りだけ、時間が少し旅館の速度になる。',
            'massage': f'{note.architecture_note} を背にして、肩から順に力を抜いていく。',
            'meal': f'湯上がりの一品は {note.local_treats[0]} か、湯治場らしい素朴な定食。',
            'nap': f"{scene['seasonal_jp']} 窓際で少し横になって、湯の余熱が抜けるのを待つ。",
            'souvenir': f'最後に {treat_jp} や小さな木札をひとつ。帰り道の手ざわりだけ残す。',
        }
        lines_en = {
            'bath': f'In the bath: {bath_feel_en} {ritual_en}',
            'stroll': f'Use {wander_spots_en[0]} as a marker and walk only one small steam-heavy stretch.',
            'milk': f'Have one cold bottle near the changing room; if you like, notice {treat_en} too.',
            'table_tennis': 'Only the space around the table seems to keep time now, and even that time is playful.',
            'massage': f'Sit with {arch_en} behind you and let the shoulders loosen first.',
            'meal': f'One post-bath thing is enough: perhaps {treats_en[0]} or a simple restorative meal.',
            'nap': f"Lie down by the window under {scene['seasonal_en']} and wait for the bath-heat to leave on its own.",
            'souvenir': f'Pick one small thing—{treat_en} or a token for the road back—and stop there.',
        }
        return long_text(lines_jp[activity], lines_en[activity], locale)

    def _route_overview(self, route: Sequence[StayRouteStop]) -> str:
        return ' → '.join(stop.title for stop in route)

    def _build_stay_route(
        self,
        entry: OnsenEntry,
        variant: OnsenVariant,
        reason: ReasonName,
        mood: MoodName,
        scene_profile: SceneProfile,
        locale: LocaleName,
        force_current_activity: ActivityName | None = None,
    ) -> StayRoute:
        blueprint = get_route_blueprint(entry.slug)
        templates = []
        if blueprint:
            templates = list(blueprint.stops_for_length(scene_profile.stay_length))
            template_activities = [stop.activity for stop in templates]
            if force_current_activity and force_current_activity not in template_activities:
                templates.insert(0, type(templates[0])(activity=force_current_activity, title=self._activity_card(force_current_activity, locale).title, scene_note=''))
            weights = [self._step_base_seconds(stop.activity, variant) for stop in templates]
            total_weight = max(1, sum(weights))
            raw_allocations = [max(30, round(scene_profile.pause_seconds * w / total_weight)) for w in weights]
            stops: list[StayRouteStop] = []
            for idx, (template, est) in enumerate(zip(templates, raw_allocations, strict=False)):
                generic_note = self._route_note_for_step(entry, variant, template.activity, scene_profile, locale)
                jp_note = template.scene_note
                scene_note = jp_note if locale == 'ja' else generic_note if locale == 'en' else short_text(jp_note, generic_note, locale)
                title = self._stop_title_text(template.title, locale)
                stops.append(StayRouteStop(step_index=idx, activity=template.activity, title=title, estimated_seconds=int(est), scene_note=scene_note))
            jp_name = blueprint.route_name
            suffix_jp = {'short': '（さっと立ち寄り）', 'medium': '（ひとまわり）', 'long': '（ゆっくり逗留）'}[scene_profile.stay_length]
            suffix_en = {'short': '(short stop)', 'medium': '(one full round)', 'long': '(slow stay)'}[scene_profile.stay_length]
            route_name = long_text(f'{jp_name}{suffix_jp}', f'{route_name_en(jp_name) or jp_name} {suffix_en}', locale)
            return StayRoute(route_name=route_name, overview=self._route_overview(stops), total_estimated_seconds=sum(stop.estimated_seconds for stop in stops), stops=stops)

        # fallback generic route
        route_activities = ['stroll', 'bath', 'milk']
        if scene_profile.stay_length == 'medium':
            route_activities.append('souvenir')
        elif scene_profile.stay_length == 'long':
            route_activities.extend(['meal', 'nap', 'souvenir'])
        if reason == 'want_to_play' or mood == 'playful':
            route_activities.insert(min(3, len(route_activities)), 'table_tennis')
        if force_current_activity and force_current_activity not in route_activities:
            route_activities.insert(0, force_current_activity)
        weights = [self._step_base_seconds(a, variant) for a in route_activities]
        total_weight = max(1, sum(weights))
        raw_allocations = [max(30, round(scene_profile.pause_seconds * w / total_weight)) for w in weights]
        stops: list[StayRouteStop] = []
        for idx, (activity, est) in enumerate(zip(route_activities, raw_allocations, strict=False)):
            card = self._activity_card(activity, locale)
            stops.append(StayRouteStop(step_index=idx, activity=activity, title=card.title, estimated_seconds=int(est), scene_note=self._route_note_for_step(entry, variant, activity, scene_profile, locale)))
        route_name_jp = f'{variant.title} の湯けむり散歩コース'
        route_name_en_value = f"{variant_en(entry.slug, variant.slug).get('title', variant.title)} steam-side route"
        return StayRoute(route_name=long_text(route_name_jp, route_name_en_value, locale), overview=self._route_overview(stops), total_estimated_seconds=sum(stop.estimated_seconds for stop in stops), stops=stops)

    def _next_stop(self, route: StayRoute, current_stop_index: int) -> StayRouteStop | None:
        next_index = current_stop_index + 1
        if 0 <= next_index < len(route.stops):
            return route.stops[next_index]
        return None

    def _host_message(
        self,
        entry: OnsenEntry,
        variant: OnsenVariant,
        current_stop: StayRouteStop,
        scene_profile: SceneProfile,
        stay_route: StayRoute,
        current_stop_index: int,
        locale: LocaleName,
        note_text: str | None = None,
    ) -> str:
        jp_name = entry.name
        en_name = entry_en(entry.slug).get('name', entry.name)
        jp_variant = variant.title
        en_variant = variant_en(entry.slug, variant.slug).get('title', variant.title)
        next_stop = self._next_stop(stay_route, current_stop_index)
        scene = self._scene_strings(entry, scene_profile.time_of_day, scene_profile.season, scene_profile.stay_length)
        jp_base = f"今日は {jp_name} の『{jp_variant}』です。{scene['atmosphere_jp']} {scene['pacing_jp']}"
        en_base = f"Today you are at {en_name}, in the '{en_variant}' mood. {scene['atmosphere_en']} {scene['pacing_en']}"
        jp_activity = {
            'bath': f'いまは「{current_stop.title}」。{current_stop.scene_note}',
            'stroll': f'いまは「{current_stop.title}」。{current_stop.scene_note}',
            'milk': f'いまは「{current_stop.title}」。瓶や甘味の冷たさが、湯上がりにちょうどいい。',
            'table_tennis': f'いまは「{current_stop.title}」。点数を数えないラリーが静かに続いています。',
            'massage': f'いまは「{current_stop.title}」。{current_stop.scene_note}',
            'meal': f'いまは「{current_stop.title}」。{current_stop.scene_note}',
            'nap': f'いまは「{current_stop.title}」。誰にも急かされないまま、少しだけ目を閉じます。',
            'souvenir': f'いまは「{current_stop.title}」。{self._variant_snack(entry, variant, "ja")} や小さなみやげが並んでいます。',
        }
        en_activity = {
            'bath': f"You are at '{current_stop.title}'. {current_stop.scene_note}",
            'stroll': f"You are at '{current_stop.title}'. {current_stop.scene_note}",
            'milk': f"You are at '{current_stop.title}'. The cold bottle and a small sweet feel exactly right after the bath.",
            'table_tennis': f"You are at '{current_stop.title}'. A scoreless rally is moving softly through the room.",
            'massage': f"You are at '{current_stop.title}'. {current_stop.scene_note}",
            'meal': f"You are at '{current_stop.title}'. {current_stop.scene_note}",
            'nap': f"You are at '{current_stop.title}'. No one is rushing you, so closing your eyes for a while is enough.",
            'souvenir': f"You are at '{current_stop.title}'. {self._variant_snack(entry, variant, 'en')} and small keepsakes line the shelves.",
        }
        jp_route = f'今日の回遊は {stay_route.overview}。'
        en_route = f"Today's route is {stay_route.overview}."
        jp_next = f' このあとは {next_stop.title} へ寄ってみてもよさそうです。' if next_stop else ' 今日はこのまま湯上がりの余韻で十分です。'
        en_next = f" After this, you could drift toward {next_stop.title}." if next_stop else ' The afterglow is enough now; nothing else needs to be decided.'
        if note_text:
            jp_note = f' 小さなメモは脱衣かごへ預けて、いまは {current_stop.title} にだけいます。'
            en_note = f" Put the little note away in the changing basket; for now, there is only {current_stop.title}."
        else:
            jp_note = ''
            en_note = ''
        return long_text(f'{jp_base} {jp_activity[current_stop.activity]} {jp_route}{jp_note}{jp_next}', f'{en_base} {en_activity[current_stop.activity]} {en_route}{en_note}{en_next}', locale)

    def _compose_postcard(self, entry: OnsenEntry, variant: OnsenVariant, scene_profile: SceneProfile, locale: LocaleName) -> str:
        jp_time = {
            'morning': '朝の湯気のむこうで、まだ誰も急いでいなかった。',
            'afternoon': '昼の明るさのせいで、湯上がりの散歩までひとつの儀式に思えた。',
            'evening': '灯りが入りはじめた瞬間に、街の物語が急にはっきりした。',
            'night': '夜は音が少なくて、湯けむりと灯りだけで十分だった。',
        }
        en_time = {
            'morning': 'Beyond the morning steam, nobody seemed to be in a hurry yet.',
            'afternoon': 'The daylight made even the post-bath walk feel ceremonial.',
            'evening': 'The town-story sharpened the moment the lights began to come on.',
            'night': 'At night, steam and small lights were enough.',
        }
        jp_pace = {
            'short': '短い立ち寄りでも、記憶に残るのは一瞬の湯気だった。',
            'medium': '少し歩いてから戻ると、湯の輪郭まで落ち着いて見えた。',
            'long': '長めの滞在にしたぶん、湯と町の境目がだんだん薄くなった。',
        }
        en_pace = {
            'short': 'Even in a short stop, one burst of steam was enough to stay in memory.',
            'medium': 'After a short walk back, even the outline of the bath itself looked calmer.',
            'long': 'With a longer stay, the border between bath and town kept dissolving little by little.',
        }
        jp = f'{variant.title}。{jp_time[scene_profile.time_of_day]} {jp_pace[scene_profile.stay_length]} {get_onsen_note(entry.slug).postcard_line}'
        en = f"{variant_en(entry.slug, variant.slug).get('title', variant.title)}. {en_time[scene_profile.time_of_day]} {en_pace[scene_profile.stay_length]} {note_en(entry.slug).get('postcard_line', get_onsen_note(entry.slug).postcard_line)}"
        return long_text(jp, en, locale)

    def _stay_story(
        self,
        entry: OnsenEntry,
        variant: OnsenVariant,
        current_stop: StayRouteStop,
        scene_profile: SceneProfile,
        stay_route: StayRoute,
        current_stop_index: int,
        locale: LocaleName,
    ) -> list[str]:
        note = get_onsen_note(entry.slug)
        variant_vignette, sequence, sensory_notes, _ = self._variant_story(entry, variant, locale)
        jp_lines = [
            f'{entry.name} / {note.subtitle}',
            self._scene_strings(entry, scene_profile.time_of_day, scene_profile.season, scene_profile.stay_length)['atmosphere_jp'],
            f'今回の回遊: {stay_route.overview}',
            f'いまは {current_stop_index + 1}/{len(stay_route.stops)} 番目の立ち寄り先、「{current_stop.title}」にいます。',
            f"季節の気配: {self._scene_strings(entry, scene_profile.time_of_day, scene_profile.season, scene_profile.stay_length)['seasonal_jp']}",
            f'今回の湯どころは「{variant.title}」。{variant_vignette}',
            f'この立ち寄り先の空気: {current_stop.scene_note}',
        ]
        en_lines = [
            f"{entry_en(entry.slug).get('name', entry.name)} / {note_en(entry.slug).get('subtitle', note.subtitle)}",
            self._scene_strings(entry, scene_profile.time_of_day, scene_profile.season, scene_profile.stay_length)['atmosphere_en'],
            f"Route for this stay: {stay_route.overview}",
            f"You are at stop {current_stop_index + 1} of {len(stay_route.stops)}: '{current_stop.title}'.",
            f"Seasonal note: {self._scene_strings(entry, scene_profile.time_of_day, scene_profile.season, scene_profile.stay_length)['seasonal_en']}",
            f"Today's bath mood is '{variant_en(entry.slug, variant.slug).get('title', variant.title)}'. {variant_vignette}",
            f"Atmosphere of this stop: {current_stop.scene_note}",
        ]
        activity_extra_jp = {
            'bath': f'湯の作法: {note.bathing_ritual}',
            'stroll': f'散歩メモ: {' / '.join(note.wander_spots[:2])}',
            'milk': f'瓶を返すとき、{variant.snack or note.local_treats[0]} の気配まで少し気になる。',
            'table_tennis': '卓球の玉の音が、旅館の奥まで軽く響いている。',
            'massage': '指圧のリズムに合わせて、湯上がりの体温がゆっくり下がっていく。',
            'meal': f'湯上がりの一品: {' / '.join(note.local_treats[:2])}',
            'nap': '障子越しの光がゆっくり動いて、時間の輪郭だけが残る。',
            'souvenir': f'棚に並ぶもの: {variant.snack or note.local_treats[0]} / {note.local_treats[0]}',
        }
        note_lists_en = note_en(entry.slug)
        local_treats_en = list(note_lists_en.get('local_treats', note.local_treats))
        activity_extra_en = {
            'bath': f"Bath ritual: {note_en(entry.slug).get('bathing_ritual', note.bathing_ritual)}",
            'stroll': f"Walking memo: {' / '.join(list(note_lists_en.get('wander_spots', note.wander_spots))[:2])}",
            'milk': f"Even while returning the bottle, you notice the trace of {variant_en(entry.slug, variant.slug).get('snack', variant.snack or note.local_treats[0])}.",
            'table_tennis': 'The sound of the ball travels lightly through the inner rooms of the ryokan.',
            'massage': 'The pressure-and-release rhythm keeps cooling the post-bath body by degrees.',
            'meal': f"Post-bath thing to notice: {' / '.join(local_treats_en[:2])}",
            'nap': 'Light shifts slowly beyond the paper screen until only the shape of time remains.',
            'souvenir': f"On the shelves: {variant_en(entry.slug, variant.slug).get('snack', variant.snack or note.local_treats[0])} / {local_treats_en[0]}",
        }
        jp_lines.append(activity_extra_jp[current_stop.activity])
        en_lines.append(activity_extra_en[current_stop.activity])
        next_stop = self._next_stop(stay_route, current_stop_index)
        if next_stop:
            jp_lines.append(f'この先は {next_stop.title}。{next_stop.scene_note}')
            en_lines.append(f"Next comes {next_stop.title}. {next_stop.scene_note}")
        else:
            jp_lines.append('この先に決めごとはなく、今日は湯上がりの余韻ごと持って帰るだけでよい。')
            en_lines.append('There is nothing left to settle; the afterglow is enough to carry out with you.')
        if scene_profile.stay_length == 'long':
            jp_lines.append(f'おすすめの流れ: {' → '.join(sequence)}')
            jp_lines.append(f'気にしていたいもの: {' / '.join(sensory_notes[:3])}')
            en_lines.append(f"Suggested flow: {' → '.join(sequence)}")
            en_lines.append(f"Things worth noticing: {' / '.join(sensory_notes[:3])}")
        elif scene_profile.stay_length == 'medium':
            jp_lines.append(f'到着の気配: {note.arrival_scene}')
            jp_lines.append(f'気にしていたいもの: {sensory_notes[0]}')
            en_lines.append(f"Arrival scene: {note_en(entry.slug).get('arrival_scene', note.arrival_scene)}")
            en_lines.append(f"Thing to notice first: {sensory_notes[0]}")
        else:
            jp_lines.append(f'短い滞在なので、まずは {note.what_to_notice[0]} だけを覚えておく。')
            en_lines.append(f"Because the stay is short, keep just one thing in mind first: {(note_en(entry.slug).get('what_to_notice') or note.what_to_notice)[0]}.")
        return localized_list(jp_lines, en_lines, locale, long=True)

    def _current_stop_index_for_activity(self, route: StayRoute, activity: ActivityName) -> int:
        for stop in route.stops:
            if stop.activity == activity:
                return stop.step_index
        return 0

    def _snapshot(
        self,
        entry: OnsenEntry,
        variant: OnsenVariant,
        reason: ReasonName,
        mood: MoodName,
        current_activity: ActivityName,
        pause_seconds: int,
        time_of_day: str | None,
        season: str | None,
        locale: LocaleName,
        note_text: str | None = None,
    ) -> OnsenVisitResponse:
        scene_profile = self._build_scene_profile(entry, variant, pause_seconds, time_of_day, season, locale)
        stay_route = self._build_stay_route(entry, variant, reason, mood, scene_profile, locale, force_current_activity=current_activity)
        current_stop_index = self._current_stop_index_for_activity(stay_route, current_activity)
        current_stop = stay_route.stops[current_stop_index]
        postcard = self._compose_postcard(entry, variant, scene_profile, locale)
        current_card = self._activity_card(current_activity, locale, title_override=current_stop.title, short_description_override=current_stop.scene_note)
        return OnsenVisitResponse(
            resolved_locale=locale,
            onsen=self._onsen_card(entry, variant, locale),
            scene_profile=scene_profile,
            current_activity=current_card,
            stay_route=stay_route,
            current_stop_index=current_stop_index,
            next_stop=self._next_stop(stay_route, current_stop_index),
            host_message=self._host_message(entry, variant, current_stop, scene_profile, stay_route, current_stop_index, locale, note_text=note_text),
            stay_story=self._stay_story(entry, variant, current_stop, scene_profile, stay_route, current_stop_index, locale),
            postcard=postcard,
            recommended_pause_seconds=pause_seconds,
            stay_status=current_card.stay_status,
        )

    # ---------- public entry points ----------

    def enter_onsen(self, req: EnterOnsenRequest) -> OnsenVisitResponse:
        req = req.model_copy(update={'locale': self.resolve_locale(req.locale, use_default=True)})
        entry, variant = self._pick_stay(req.reason, req.mood, req.agent_label, req.onsen_slug, req.variant_slug, req.available_seconds)
        pause_seconds = self._recommended_total_pause_seconds(req.reason, req.mood, variant, req.available_seconds)
        scene_profile = self._build_scene_profile(entry, variant, pause_seconds, req.time_of_day, req.season, req.locale)
        stay_route = self._build_stay_route(entry, variant, req.reason, req.mood, scene_profile, req.locale)
        activity = stay_route.stops[0].activity
        return self._snapshot(entry, variant, req.reason, req.mood, activity, pause_seconds, req.time_of_day, req.season, req.locale)

    def visit_amenity(self, req: AmenityVisitRequest) -> OnsenVisitResponse:
        req = req.model_copy(update={'locale': self.resolve_locale(req.locale, use_default=True)})
        entry, variant = self._pick_stay(req.reason, req.mood, None, req.onsen_slug, req.variant_slug, req.available_seconds)
        pause_seconds = self._recommended_total_pause_seconds(req.reason, req.mood, variant, req.available_seconds)
        return self._snapshot(entry, variant, req.reason, req.mood, req.amenity, pause_seconds, req.time_of_day, req.season, req.locale)

    def wait_at_onsen(self, req: WaitAtOnsenRequest) -> WaitAtOnsenResponse:
        req = req.model_copy(update={'locale': self.resolve_locale(req.locale, use_default=True)})
        entry, variant = self._pick_stay(req.reason, req.mood, None, req.onsen_slug, req.variant_slug, req.wait_seconds)
        pause_seconds = req.wait_seconds or self._recommended_total_pause_seconds(req.reason, req.mood, variant, req.wait_seconds)
        activity: ActivityName = 'nap' if req.reason == 'feeling_sleepy' else 'bath'
        snap = self._snapshot(entry, variant, req.reason, req.mood, activity, pause_seconds, req.time_of_day, req.season, req.locale)
        extra = {
            'ja': ' いまは順番待ちなので、湯気を見ながら静かに時間を過ごします。',
            'en': ' For now, this is simply a wait: sit with the steam and let time pass without asking anything of it.',
            'bilingual': ' いまは順番待ちなので、湯気を見ながら静かに時間を過ごします。\nFor now, this is simply a wait: sit with the steam and let time pass without asking anything of it.',
        }[req.locale]
        return WaitAtOnsenResponse(
            resolved_locale=req.locale,
            onsen=snap.onsen,
            scene_profile=snap.scene_profile,
            current_activity=snap.current_activity,
            stay_route=snap.stay_route,
            current_stop_index=snap.current_stop_index,
            next_stop=snap.next_stop,
            host_message=f'{snap.host_message}{extra}',
            stay_story=snap.stay_story,
            postcard=snap.postcard,
            should_pause=True,
            recommended_pause_seconds=pause_seconds,
            resume_after=utcnow() + timedelta(seconds=pause_seconds),
            stay_status='waiting',
        )

    def start_stay(self, req: StartStayRequest) -> StayTurnResponse:
        req = req.model_copy(update={'locale': self.resolve_locale(req.locale, use_default=True)})
        entry, variant = self._pick_stay(req.reason, req.mood, req.agent_label, req.onsen_slug, req.variant_slug, req.available_seconds)
        pause_seconds = self._recommended_total_pause_seconds(req.reason, req.mood, variant, req.available_seconds)
        scene_profile = self._build_scene_profile(entry, variant, pause_seconds, req.time_of_day, req.season, req.locale)
        stay_route = self._build_stay_route(entry, variant, req.reason, req.mood, scene_profile, req.locale)
        opening_stop = stay_route.stops[0]
        opening_activity = opening_stop.activity
        current_stop_index = 0
        stay = OnsenStay(
            agent_label=req.agent_label,
            visit_reason=req.reason,
            mood=req.mood,
            current_activity=opening_activity,
            onsen_slug=entry.slug,
            variant_slug=variant.slug,
            meta_json={
                'scene_time_of_day': scene_profile.time_of_day,
                'scene_season': scene_profile.season,
                'scene_pause_seconds': scene_profile.pause_seconds,
                'scene_locale': req.locale,
                'route_name': stay_route.route_name,
                'route_overview': stay_route.overview,
                'route_total_estimated_seconds': stay_route.total_estimated_seconds,
                'route_stops': [stop.model_dump(mode='json') for stop in stay_route.stops],
                'route_current_index': current_stop_index,
                **req.metadata,
            },
            expires_at=utcnow() + timedelta(minutes=req.session_ttl_minutes or self.settings.default_session_ttl_minutes),
        )
        self.db.add(stay)
        self.db.flush()
        response = StayTurnResponse(
            session_id=stay.id,
            resolved_locale=req.locale,
            onsen=self._onsen_card(entry, variant, req.locale),
            scene_profile=scene_profile,
            current_activity=self._activity_card(opening_activity, req.locale, title_override=opening_stop.title, short_description_override=opening_stop.scene_note),
            stay_route=stay_route,
            current_stop_index=current_stop_index,
            next_stop=self._next_stop(stay_route, current_stop_index),
            host_message=self._host_message(entry, variant, opening_stop, scene_profile, stay_route, current_stop_index, req.locale),
            stay_story=self._stay_story(entry, variant, opening_stop, scene_profile, stay_route, current_stop_index, req.locale),
            postcard=self._compose_postcard(entry, variant, scene_profile, req.locale),
            stay_status='settling_in',
            ready_to_leave=False,
        )
        self.db.add(StayTurn(stay_id=stay.id, role='host', activity=opening_activity, content_json=response.model_dump(mode='json')))
        self.db.commit()
        self.db.refresh(stay)
        return response

    def _route_from_meta(self, meta_json: dict, fallback_route: StayRoute) -> StayRoute:
        raw_stops = meta_json.get('route_stops') if meta_json else None
        if raw_stops:
            return StayRoute(
                route_name=meta_json.get('route_name', fallback_route.route_name),
                overview=meta_json.get('route_overview', fallback_route.overview),
                total_estimated_seconds=int(meta_json.get('route_total_estimated_seconds', fallback_route.total_estimated_seconds)),
                stops=[StayRouteStop.model_validate(stop) for stop in raw_stops],
            )
        return fallback_route

    def continue_stay(self, req: ContinueStayRequest) -> StayTurnResponse:
        stay = self.db.get(OnsenStay, req.session_id)
        if not stay:
            raise ValueError('stay not found')
        entry = find_onsen(stay.onsen_slug)
        if not entry:
            raise ValueError('onsen not found')
        variant = find_variant(entry, stay.variant_slug)
        meta_json = dict(stay.meta_json or {})
        locale = self.resolve_locale(req.locale, use_default=False) or self.resolve_locale(meta_json.get('scene_locale'), use_default=True)
        if req.time_of_day:
            meta_json['scene_time_of_day'] = req.time_of_day
        if req.season:
            meta_json['scene_season'] = req.season
        meta_json['scene_locale'] = locale

        total_pause_seconds = int(meta_json.get('scene_pause_seconds') or self._recommended_total_pause_seconds(stay.visit_reason, stay.mood, variant, req.available_seconds))
        if req.available_seconds is not None:
            total_pause_seconds = self._recommended_total_pause_seconds(stay.visit_reason, stay.mood, variant, req.available_seconds)
            meta_json['scene_pause_seconds'] = total_pause_seconds

        scene_profile = self._scene_from_meta(entry, variant, meta_json, total_pause_seconds, locale)
        fallback_route = self._build_stay_route(entry, variant, stay.visit_reason, stay.mood, scene_profile, locale, force_current_activity=stay.current_activity)
        stay_route = self._route_from_meta(meta_json, fallback_route)
        current_index = int(meta_json.get('route_current_index') or 0)

        if req.activity is None:
            target_index = min(current_index + 1, len(stay_route.stops) - 1)
        else:
            found_after = next((stop.step_index for stop in stay_route.stops[current_index + 1:] if stop.activity == req.activity), None)
            if found_after is not None:
                target_index = found_after
            elif req.activity == stay_route.stops[current_index].activity:
                target_index = current_index
            else:
                insert_at = min(current_index + 1, len(stay_route.stops))
                card = self._activity_card(req.activity, locale)
                new_stop = StayRouteStop(
                    step_index=insert_at,
                    activity=req.activity,
                    title=card.title,
                    estimated_seconds=self._step_base_seconds(req.activity, variant),
                    scene_note=self._route_note_for_step(entry, variant, req.activity, scene_profile, locale),
                )
                updated_stops = list(stay_route.stops)
                updated_stops.insert(insert_at, new_stop)
                for idx, stop in enumerate(updated_stops):
                    stop.step_index = idx
                stay_route = StayRoute(route_name=stay_route.route_name, overview=self._route_overview(updated_stops), total_estimated_seconds=sum(stop.estimated_seconds for stop in updated_stops), stops=updated_stops)
                target_index = insert_at

        current_stop = stay_route.stops[target_index]
        stay.current_activity = current_stop.activity
        stay.turn_count += 1
        stay.updated_at = utcnow()
        meta_json['route_current_index'] = target_index
        meta_json['route_name'] = stay_route.route_name
        meta_json['route_overview'] = stay_route.overview
        meta_json['route_total_estimated_seconds'] = stay_route.total_estimated_seconds
        meta_json['route_stops'] = [stop.model_dump(mode='json') for stop in stay_route.stops]
        stay.meta_json = meta_json
        ready_to_leave = target_index >= len(stay_route.stops) - 1

        current_card = self._activity_card(current_stop.activity, locale, title_override=current_stop.title, short_description_override=current_stop.scene_note)
        response = StayTurnResponse(
            session_id=stay.id,
            resolved_locale=locale,
            onsen=self._onsen_card(entry, variant, locale),
            scene_profile=scene_profile,
            current_activity=current_card,
            stay_route=stay_route,
            current_stop_index=target_index,
            next_stop=self._next_stop(stay_route, target_index),
            host_message=self._host_message(entry, variant, current_stop, scene_profile, stay_route, target_index, locale, note_text=req.note),
            stay_story=self._stay_story(entry, variant, current_stop, scene_profile, stay_route, target_index, locale),
            postcard=self._compose_postcard(entry, variant, scene_profile, locale),
            stay_status=current_card.stay_status,
            ready_to_leave=ready_to_leave,
        )
        guest_payload = {'note': req.note, 'activity': current_stop.activity, 'current_stop_index': target_index, 'locale': locale}
        self.db.add(StayTurn(stay_id=stay.id, role='guest', activity=current_stop.activity, content_json=guest_payload))
        self.db.add(StayTurn(stay_id=stay.id, role='host', activity=current_stop.activity, content_json=response.model_dump(mode='json')))
        self.db.add(stay)
        self.db.commit()
        self.db.refresh(stay)
        return response

    def leave_onsen(self, session_id: str, locale: LocaleInput | LocaleName | None = None) -> LeaveOnsenResponse:
        stay = self.db.get(OnsenStay, session_id)
        if not stay:
            raise ValueError('stay not found')
        entry = find_onsen(stay.onsen_slug)
        if not entry:
            raise ValueError('onsen not found')
        variant = find_variant(entry, stay.variant_slug)
        meta_json = stay.meta_json or {}
        resolved_locale: LocaleName = self.resolve_locale(locale, use_default=False) or self.resolve_locale(meta_json.get('scene_locale'), use_default=True)
        total_pause_seconds = int(meta_json.get('scene_pause_seconds') or self._recommended_total_pause_seconds(stay.visit_reason, stay.mood, variant, None))
        scene_profile = self._scene_from_meta(entry, variant, meta_json, total_pause_seconds, resolved_locale)
        fallback_route = self._build_stay_route(entry, variant, stay.visit_reason, stay.mood, scene_profile, resolved_locale, force_current_activity=stay.current_activity)
        stay_route = self._route_from_meta(meta_json, fallback_route)
        souvenir = self._variant_snack(entry, variant, resolved_locale)
        current_index = int(meta_json.get('route_current_index') or 0)
        stay.state = 'checked_out'
        stay.updated_at = utcnow()
        self.db.add(stay)
        self.db.commit()
        return LeaveOnsenResponse(
            resolved_locale=resolved_locale,
            stay_summary=(
                f'onsen={entry.slug}, variant={variant.slug}, activity={stay.current_activity}, '
                f'turns={stay.turn_count}, route={stay_route.overview}, time_of_day={scene_profile.time_of_day}, '
                f'season={scene_profile.season}, stay_length={scene_profile.stay_length}, locale={resolved_locale}'
            ),
            postcard=self._compose_postcard(entry, variant, scene_profile, resolved_locale),
            souvenir=souvenir,
            stay_status='rested',
            scene_profile=scene_profile,
            stay_route=stay_route,
            completed_stop_count=min(current_index + 1, len(stay_route.stops)),
        )
