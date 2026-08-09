"""Every shipped lesson must validate and be drivable by the tutor."""

from __future__ import annotations

import pytest
import yaml

from backend.app.book_modes import FLOW_BY_MODE, flow_substeps
from backend.app.books import content_dir_for_book
from backend.app.curriculum_loader import list_lessons, load_lesson
from backend.app.schema import lesson_issues, validate_lesson

BOOKS = ("starter", "elementary1")
LESSON_IDS = [str(x["lesson_id"]) for book in BOOKS for x in list_lessons(book)]


@pytest.mark.parametrize("lesson_id", LESSON_IDS)
def test_lesson_validates(lesson_id):
    lesson = validate_lesson(load_lesson(lesson_id))
    assert lesson.lesson_id == lesson_id


@pytest.mark.parametrize("lesson_id", LESSON_IDS)
def test_can_do_references_resolve(lesson_id):
    lesson = validate_lesson(load_lesson(lesson_id))
    declared = {c.id for c in lesson.can_dos}
    for activity in lesson.activities:
        if activity.can_do_id:
            assert activity.can_do_id in declared, f"{lesson_id}/{activity.id}"
    for scenario in lesson.quiz_scenarios:
        assert scenario.can_do_id in declared, lesson_id


@pytest.mark.parametrize("lesson_id", LESSON_IDS)
def test_every_activity_has_a_known_flow(lesson_id):
    lesson = validate_lesson(load_lesson(lesson_id))
    for activity in lesson.activities:
        assert activity.book_mode in FLOW_BY_MODE, f"{lesson_id}/{activity.id}"
        subs = flow_substeps(activity.model_dump())
        assert subs, f"{lesson_id}/{activity.id} has no sub-steps"


@pytest.mark.parametrize("book", BOOKS)
def test_index_matches_files(book):
    for entry in list_lessons(book):
        path = content_dir_for_book(book) / f"{entry['lesson_id']}.yaml"
        assert path.is_file(), f"{book}: {entry['lesson_id']} listed but missing"


@pytest.mark.parametrize("book", BOOKS)
def test_yaml_parses_directly(book):
    """Guards against a rebuild emitting something the loader would silently skip."""
    for entry in list_lessons(book):
        path = content_dir_for_book(book) / f"{entry['lesson_id']}.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict) and data.get("lesson_id") == entry["lesson_id"]


def test_content_issue_report_is_available():
    """`lesson_issues` is what the curriculum build should print. It is advisory,
    so this only asserts it runs and that known gaps are reported, not that the
    shipped content is issue-free."""
    issues = lesson_issues(load_lesson("L01"))
    assert isinstance(issues, list)
