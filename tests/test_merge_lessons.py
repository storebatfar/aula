import datetime

from homeassistant.components.calendar import CalendarEvent

from custom_components.aula.calendar import merge_parallel_lessons

TZ = datetime.timezone(datetime.timedelta(hours=2))


def lesson(summary, hour, minute=0, location=None, minutes=45):
    start = datetime.datetime(2026, 10, 5, hour, minute, tzinfo=TZ)
    return CalendarEvent(
        summary=summary,
        start=start,
        end=start + datetime.timedelta(minutes=minutes),
        location=location,
    )


def test_same_subject_and_time_merge_into_one_with_all_teachers():
    merged = merge_parallel_lessons(
        [lesson("Lok.V, TT", 12, 55, "C4"), lesson("Lok.V, TH", 12, 55), lesson("Lok.V, EK", 12, 55)]
    )
    assert len(merged) == 1
    assert merged[0].summary == "Lok.V, TT/TH/EK"
    assert merged[0].location == "C4"


def test_location_is_taken_from_any_copy_that_has_one():
    merged = merge_parallel_lessons([lesson("Lok.V, TH", 13, 45), lesson("Lok.V, TT", 13, 45, "C4")])
    assert merged[0].location == "C4"
    assert merged[0].summary == "Lok.V, TH/TT"


def test_different_subjects_or_times_stay_separate():
    events = [lesson("DAN, PH", 8), lesson("ENG, EK", 8), lesson("DAN, PH", 9)]
    assert [e.summary for e in merge_parallel_lessons(events)] == ["DAN, PH", "ENG, EK", "DAN, PH"]


def test_substitute_teacher_is_kept_and_repeats_are_not_listed_twice():
    merged = merge_parallel_lessons(
        [lesson("MAT, VIKAR: Hans Hansen", 10), lesson("MAT, VIKAR: Hans Hansen", 10)]
    )
    assert [e.summary for e in merged] == ["MAT, VIKAR: Hans Hansen"]


def test_summary_without_teacher_part():
    merged = merge_parallel_lessons([lesson("Idræt", 10), lesson("Idræt, ", 10)])
    assert [e.summary for e in merged] == ["Idræt"]
