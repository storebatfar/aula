import datetime
import json
import os

from custom_components.aula.client import build_week_note_events, extract_week_notes

MONDAY = datetime.date(2026, 9, 28)


def load_json_fixture(filename):
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(fixture_path) as f:
        return json.load(f)


def test_only_visible_non_empty_texts_are_notes():
    notes = extract_week_notes(load_json_fixture("easyiq_weekplan.json"))
    assert [n["activity"] for n in notes] == ["7A"]
    assert notes[0]["html"].startswith("<p>Vi har projektuge.")


def test_note_becomes_monday_to_friday_all_day_event():
    events = build_week_note_events(load_json_fixture("easyiq_weekplan.json"), MONDAY)
    assert len(events) == 1
    event = events[0]
    assert event.start == MONDAY
    assert event.end == datetime.date(2026, 10, 3)
    assert event.summary == 'Vi har projektuge. Deres overordnede emne er "udvikling".'


def test_note_description_has_one_line_per_paragraph_and_table_cell():
    event = build_week_note_events(load_json_fixture("easyiq_weekplan.json"), MONDAY)[0]
    assert event.description.splitlines() == [
        'Vi har projektuge. Deres overordnede emne er "udvikling".',
        "Mødetid hver dag er fra 8.00-13.25.",
        "Tidslinjen for ugen er følgende:",
        "📅 TIDSLINJE FOR PROJEKTUGEN",
        "📌 MANDAG Emnevalg + problemformulering",
        "🔎 TIRSDAG Undersøgelser + informationssøgning",
        "Det er muligt for eleverne at arbejde på tværs af årgangen.",
    ]


def test_top_level_text_counts_when_visible():
    payload = {"Text": "<p>Hele skolen</p>", "IsVisible": True, "WeekPlans": []}
    events = build_week_note_events(payload, MONDAY)
    assert [e.summary for e in events] == ["Hele skolen"]


def test_several_classes_are_prefixed_with_activity_name():
    payload = {
        "WeekPlans": [
            {"ActivityName": "7A", "IsVisible": True, "Text": "<p>Projektuge</p>"},
            {"ActivityName": "Musik", "IsVisible": True, "Text": "<p>Koncert fredag</p>"},
        ]
    }
    events = build_week_note_events(payload, MONDAY)
    assert [e.summary for e in events] == ["7A: Projektuge", "Musik: Koncert fredag"]


def test_missing_or_odd_payload_gives_no_events():
    assert build_week_note_events(None, MONDAY) == []
    assert build_week_note_events([], MONDAY) == []
    assert build_week_note_events({"WeekPlans": "nope"}, MONDAY) == []


def test_nested_table_cells_collapse_without_error():
    from custom_components.aula.client import html_to_lines

    html = "<table><tr><td><p>Ydre</p><table><tr><td><p>Indre</p><p>celle</p></td></tr></table></td></tr></table>"
    assert html_to_lines(html) == ["Ydre Indre celle"]
