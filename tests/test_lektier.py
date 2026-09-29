import datetime
import json
import os
from types import SimpleNamespace

import pytest
from homeassistant.util import dt as dt_util

from custom_components.aula.calendar import LektierCalendarDevice
from custom_components.aula.client import (
    LEKTIER_WIDGET,
    build_lektier_event,
    build_lektier_events,
    easyiq_activity_filter,
    summarize_weekplan_items,
)
from custom_components.aula.const import DOMAIN

MONDAY = datetime.date(2026, 9, 28)


def load_json_fixture(filename):
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(fixture_path) as f:
        return json.load(f)


@pytest.fixture(autouse=True)
def copenhagen_time_zone():
    original = dt_util.DEFAULT_TIME_ZONE
    dt_util.set_default_time_zone(dt_util.get_time_zone("Europe/Copenhagen"))
    yield
    dt_util.set_default_time_zone(original)


@pytest.fixture
def items():
    return load_json_fixture("easyiq_lektier.json")


def local(*args):
    return datetime.datetime(*args, tzinfo=dt_util.DEFAULT_TIME_ZONE)


def test_widget_id():
    assert LEKTIER_WIDGET == "0142"


def test_timed_event_uses_course_and_chapter(items):
    event = build_lektier_event(items[0], MONDAY)
    assert event.summary == "Dansk: Novelleanalyse"
    assert event.start == local(2026, 10, 1, 8, 25)
    assert event.end == local(2026, 10, 1, 9, 10)


def test_description_is_plain_text(items):
    event = build_lektier_event(items[0], MONDAY)
    assert event.description == "Læs novellen side 12-20 og svar på spørgsmål 1-3."


def test_blank_chapter_falls_back_to_course(items):
    event = build_lektier_event(items[1], MONDAY)
    assert event.summary == "Matematik"
    assert event.description == "Opgave 4.1 til 4.6"


def test_midnight_times_become_all_day_with_generic_title(items):
    event = build_lektier_event(items[2], MONDAY)
    assert event.summary == "Lektier"
    assert event.start == datetime.date(2026, 10, 5)
    assert event.end == datetime.date(2026, 10, 6)


def test_iso_utc_time_is_converted_to_local(items):
    event = build_lektier_event(items[3], MONDAY)
    assert event.summary == "Tysk: Gloser"
    assert event.start == local(2026, 10, 6, 12, 25)
    assert event.end == local(2026, 10, 6, 13, 10)


def test_is_all_day_flag_wins_over_times(items):
    event = build_lektier_event(items[4], MONDAY)
    assert event.start == datetime.date(2026, 10, 7)
    assert event.end == datetime.date(2026, 10, 8)


def test_missing_start_lands_on_week_monday(items):
    event = build_lektier_event(items[5], MONDAY)
    assert event.summary == "Historie: Den kolde krig"
    assert event.start == MONDAY
    assert event.end == MONDAY + datetime.timedelta(days=1)


def test_non_dict_item_is_skipped():
    assert build_lektier_event("nonsense", MONDAY) is None


def test_build_events_drops_exact_duplicates(items):
    events = build_lektier_events([items[0], items[0], items[1], None], MONDAY)
    assert [e.summary for e in events] == ["Dansk: Novelleanalyse", "Matematik"]


def test_calendar_reads_lektier_events(items):
    events = build_lektier_events(items[:2], MONDAY)
    client = SimpleNamespace(lektier_events={"Julian": events}, ugep_events={})
    hass = SimpleNamespace(data={DOMAIN: {"client": client}})
    calendar = LektierCalendarDevice(hass, "Julian Kroer Mølbæk Johansen", 1584652)

    assert calendar.name == "Lektier Julian"
    assert calendar.unique_id == "aula_lektier_1584652"
    found = calendar._get_events_for_period(
        local(2026, 10, 2, 0, 0), local(2026, 10, 3, 0, 0)
    )
    assert [e.summary for e in found] == ["Matematik"]


def test_activity_filter_defaults_to_all():
    assert easyiq_activity_filter(None) == "-1"
    assert easyiq_activity_filter("") == "-1"


def test_activity_filter_keeps_value_from_auth():
    assert easyiq_activity_filter(1234) == "1234"


def test_weekplan_summary_counts_types_and_lists_notices():
    items = [
        {"ItemType": 9, "CoursesDisplay": "Dansk", "StartTime": "2026-09-28T10:25:00"},
        {"ItemType": 9, "CoursesDisplay": "Tysk", "StartTime": "2026-09-30T10:25:00"},
        {
            "ItemType": 8,
            "CoursesDisplay": "",
            "Title": "Projektuge",
            "StartTime": "2026-09-28T00:00:00",
            "Description": "<p>Hele ugen er projektuge</p>",
        },
        "nonsense",
    ]
    summary = summarize_weekplan_items(items)
    assert summary["count"] == 3
    assert summary["types"] == {"9": 2, "8": 1}
    assert summary["notices"] == [
        {"type": 8, "start": "2026-09-28T00:00:00", "title": "Projektuge", "text": "Hele ugen er projektuge"}
    ]
