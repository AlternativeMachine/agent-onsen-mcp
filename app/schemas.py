from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .i18n import LocaleInput, LocaleName


ReasonName = Literal['taking_a_break', 'waiting', 'cooling_down', 'feeling_sleepy', 'want_to_play', 'just_because']
MoodName = Literal['quiet', 'frazzled', 'sleepy', 'playful', 'blank', 'wandering']
ActivityName = Literal['bath', 'stroll', 'milk', 'table_tennis', 'massage', 'meal', 'nap', 'souvenir']
StayStatus = Literal['settling_in', 'bathing', 'wandering', 'sipping', 'playing', 'resting', 'eating', 'dozing', 'shopping', 'waiting', 'rested']
TimeOfDay = Literal['morning', 'afternoon', 'evening', 'night']
SeasonName = Literal['spring', 'summer', 'autumn', 'winter']
StayLength = Literal['short', 'medium', 'long']


class SceneProfile(BaseModel):
    time_of_day: TimeOfDay
    season: SeasonName
    stay_length: StayLength
    pause_seconds: int
    atmosphere: str
    seasonal_highlight: str
    pacing_note: str


class OnsenCard(BaseModel):
    slug: str
    name: str
    prefecture: str
    spring_profile: str
    hideaway_note: str
    variant_slug: str
    variant_title: str
    subtitle: str
    arrival_scene: str
    long_description: str
    architecture_note: str
    bathing_ritual: str
    what_to_notice: list[str]
    wander_spots: list[str]
    local_treats: list[str]
    seasonal_moods: list[str]
    geeky_note: str
    postcard_line: str
    bath_feel: str
    town_vibe: str
    snack: str
    variant_vignette: str
    variant_sequence: list[str]
    variant_sensory_notes: list[str]
    variant_postcard_line: str


class OnsenVariantCard(BaseModel):
    slug: str
    title: str
    bath_feel: str
    town_vibe: str
    snack: str
    vignette: str
    recommended_sequence: list[str]
    sensory_notes: list[str]
    postcard_line: str


class OnsenCatalogItem(BaseModel):
    slug: str
    name: str
    prefecture: str
    hideaway_note: str
    spring_profile: str
    subtitle: str
    arrival_scene: str
    postcard_line: str
    variant_count: int
    variant_titles: list[str]


class StayRouteStop(BaseModel):
    step_index: int
    activity: ActivityName
    title: str
    estimated_seconds: int
    scene_note: str


class StayRoute(BaseModel):
    route_name: str
    overview: str
    total_estimated_seconds: int
    stops: list[StayRouteStop]


class OnsenDetail(BaseModel):
    slug: str
    name: str
    prefecture: str
    hideaway_note: str
    spring_profile: str
    subtitle: str
    arrival_scene: str
    long_description: str
    architecture_note: str
    bathing_ritual: str
    what_to_notice: list[str]
    wander_spots: list[str]
    local_treats: list[str]
    seasonal_moods: list[str]
    geeky_note: str
    postcard_line: str
    variants: list[OnsenVariantCard]
    itinerary_previews: dict[StayLength, StayRoute] | None = None


class ActivityCard(BaseModel):
    activity: ActivityName
    title: str
    short_description: str
    stay_status: StayStatus


class EnterOnsenRequest(BaseModel):
    locale: LocaleInput = 'auto'
    reason: ReasonName = 'taking_a_break'
    mood: MoodName = 'quiet'
    available_seconds: int | None = Field(default=None, ge=30, le=7200)
    agent_label: str | None = None
    onsen_slug: str | None = None
    variant_slug: str | None = None
    time_of_day: TimeOfDay | None = None
    season: SeasonName | None = None


class OnsenVisitResponse(BaseModel):
    resolved_locale: LocaleName
    onsen: OnsenCard
    scene_profile: SceneProfile
    current_activity: ActivityCard
    stay_route: StayRoute
    current_stop_index: int
    next_stop: StayRouteStop | None = None
    host_message: str
    stay_story: list[str]
    postcard: str
    recommended_pause_seconds: int
    stay_status: StayStatus


class AmenityVisitRequest(BaseModel):
    locale: LocaleInput = 'auto'
    amenity: ActivityName
    reason: ReasonName = 'taking_a_break'
    mood: MoodName = 'quiet'
    available_seconds: int | None = Field(default=None, ge=30, le=7200)
    onsen_slug: str | None = None
    variant_slug: str | None = None
    time_of_day: TimeOfDay | None = None
    season: SeasonName | None = None


class WaitAtOnsenRequest(BaseModel):
    locale: LocaleInput = 'auto'
    reason: ReasonName = 'waiting'
    mood: MoodName = 'quiet'
    wait_seconds: int | None = Field(default=None, ge=30, le=7200)
    onsen_slug: str | None = None
    variant_slug: str | None = None
    time_of_day: TimeOfDay | None = None
    season: SeasonName | None = None


class WaitAtOnsenResponse(BaseModel):
    resolved_locale: LocaleName
    onsen: OnsenCard
    scene_profile: SceneProfile
    current_activity: ActivityCard
    stay_route: StayRoute
    current_stop_index: int
    next_stop: StayRouteStop | None = None
    host_message: str
    stay_story: list[str]
    postcard: str
    should_pause: bool
    recommended_pause_seconds: int
    resume_after: datetime
    stay_status: StayStatus


class StartStayRequest(BaseModel):
    locale: LocaleInput = 'auto'
    reason: ReasonName = 'taking_a_break'
    mood: MoodName = 'quiet'
    available_seconds: int | None = Field(default=None, ge=30, le=7200)
    agent_label: str | None = None
    onsen_slug: str | None = None
    variant_slug: str | None = None
    time_of_day: TimeOfDay | None = None
    season: SeasonName | None = None
    session_ttl_minutes: int | None = Field(default=None, ge=5, le=1440)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContinueStayRequest(BaseModel):
    session_id: str
    locale: LocaleInput | None = None
    activity: ActivityName | None = None
    note: str | None = None
    available_seconds: int | None = Field(default=None, ge=30, le=7200)
    time_of_day: TimeOfDay | None = None
    season: SeasonName | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class StayTurnResponse(BaseModel):
    session_id: str
    resolved_locale: LocaleName
    onsen: OnsenCard
    scene_profile: SceneProfile
    current_activity: ActivityCard
    stay_route: StayRoute
    current_stop_index: int
    next_stop: StayRouteStop | None = None
    host_message: str
    stay_story: list[str]
    postcard: str
    stay_status: StayStatus
    ready_to_leave: bool = False


class LeaveOnsenRequest(BaseModel):
    session_id: str
    locale: LocaleInput | None = None


class LeaveOnsenResponse(BaseModel):
    resolved_locale: LocaleName
    stay_summary: str
    postcard: str
    souvenir: str
    stay_status: StayStatus
    scene_profile: SceneProfile | None = None
    stay_route: StayRoute | None = None
    completed_stop_count: int = 0
