import json
import os

import pytest

from custom_components.aula.calendar import merge_parallel_lessons, parseCalendarLesson
from custom_components.aula.const import TEACHER_NAME_INITIALS, TEACHER_NAME_NONE, expand_subject


def load_json_fixture(filename):
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(fixture_path) as f:
        return json.load(f)


@pytest.mark.parametrize(
    "code, name",
    [
        ("DAN", "Dansk"),
        ("SAM", "Samfundsfag"),
        ("F/K", "Fysik/kemi"),
        ("KRI", "Kristendomskundskab"),
        ("Lok.V", "Lokalt valgfag"),
        ("LÆS", "Læsebånd"),
        ("TIL", "Tilvalgsfag"),
        ("MUSv", "Musik (valgfag)"),
        ("MADv", "Madkundskab (valgfag)"),
        ("DAN2", "Dansk"),
        ("ENG2", "Engelsk"),
        ("dan", "Dansk"),
        (" IDR ", "Idræt"),
    ],
)
def test_known_codes_expand(code, name):
    assert expand_subject(code) == name


def test_unknown_code_is_kept_as_is():
    assert expand_subject("XYZ") == "XYZ"
    assert expand_subject("Trivselstime") == "Trivselstime"


def lesson_with_title(fixture, title):
    lesson = load_json_fixture(fixture)
    lesson["title"] = title
    return lesson


def test_full_subject_and_hidden_teacher():
    lesson = lesson_with_title("calendar_lesson_normal.json", "SAM")
    event = parseCalendarLesson(lesson, TEACHER_NAME_NONE, full_subjects=True)
    assert event.summary == "Samfundsfag"


def test_hidden_teacher_still_marks_substitute():
    lesson = lesson_with_title("calendar_lesson_substitute_without_location.json", "DAN")
    event = parseCalendarLesson(lesson, TEACHER_NAME_NONE, full_subjects=True)
    assert event.summary == "Dansk (vikar)"


def test_full_subject_with_initials():
    lesson = lesson_with_title("calendar_lesson_normal.json", "MAT")
    event = parseCalendarLesson(lesson, TEACHER_NAME_INITIALS, full_subjects=True)
    assert event.summary == "Matematik, JB"


def test_defaults_are_unchanged():
    lesson = lesson_with_title("calendar_lesson_normal.json", "MAT")
    assert parseCalendarLesson(lesson).summary == "MAT, JB"


def test_co_taught_team_merges_once_expanded():
    first = parseCalendarLesson(lesson_with_title("calendar_lesson_normal.json", "DAN"), TEACHER_NAME_NONE, full_subjects=True)
    second = parseCalendarLesson(lesson_with_title("calendar_lesson_normal.json", "DAN2"), TEACHER_NAME_NONE, full_subjects=True)
    assert [e.summary for e in merge_parallel_lessons([first, second])] == ["Dansk"]


def test_emoji_matches_expanded_name():
    lesson = lesson_with_title("calendar_lesson_normal.json", "DAN")
    event = parseCalendarLesson(lesson, TEACHER_NAME_NONE, show_emoji=True, full_subjects=True)
    assert event.summary == "📖 Dansk"


def test_room_is_kept_by_default_and_dropped_when_hidden():
    lesson = lesson_with_title("calendar_lesson_substitute_with_location.json", "DAN")
    assert parseCalendarLesson(lesson).location == "Test Location"
    hidden = parseCalendarLesson(lesson, TEACHER_NAME_NONE, full_subjects=True, show_room=False)
    assert hidden.location is None
    assert hidden.summary == "Dansk (vikar)"
