"""Requirement-derived black-box tests for the registration system.

Test IDs are included in parametrized case IDs and test function names so each
case is easy to identify in pytest output.
"""
from copy import deepcopy

import pytest

from registration import (
    Course,
    Student,
    check_credit_limit,
    prerequisites_satisfied,
    register_course,
    registration_decision,
    withdraw_course,
)


@pytest.fixture
def eligible_pair():
    return Student("S100"), Course("CS201", 3, 2)


def state_of(student, course):
    """Capture all mutable and decision-relevant fields for no-mutation checks."""
    return deepcopy((student, course))


# A1. Equivalence Class Partitioning
@pytest.mark.parametrize(
    "current,new,expected",
    [
        pytest.param(0, 1, True, id="A1-ECP-01-zero-current-min-course"),
        pytest.param(15, 3, True, id="A1-ECP-02-exact-limit"),
        pytest.param(14, 4, True, id="A1-ECP-03-max-course-valid"),
        pytest.param(16, 3, False, id="A1-ECP-04-over-limit"),
        pytest.param(-1, 1, "Invalid current credits", id="A1-ECP-05-negative-current"),
        pytest.param(19, 1, "Invalid current credits", id="A1-ECP-06-high-current"),
        pytest.param(0, 0, "Invalid course credits", id="A1-ECP-07-zero-course"),
        pytest.param(0, 5, "Invalid course credits", id="A1-ECP-08-high-course"),
    ],
)
def test_A1_ECP_credit_classes(current, new, expected):
    if isinstance(expected, str):
        with pytest.raises(ValueError, match=f"^{expected}$"):
            check_credit_limit(current, new)
    else:
        assert check_credit_limit(current, new) is expected, (
            f"credit eligibility for current={current}, course={new} "
            f"should be {expected}"
        )


@pytest.mark.parametrize(
    "completed,required,expected",
    [
        pytest.param(set(), set(), True, id="A1-ECP-09-no-prerequisites"),
        pytest.param({"CS101", "MATH101"}, {"CS101", "MATH101"}, True, id="A1-ECP-10-all-prerequisites"),
        pytest.param({"CS101"}, {"CS101", "MATH101"}, False, id="A1-ECP-11-some-prerequisites"),
        pytest.param({"BIO101"}, {"CS101"}, False, id="A1-ECP-12-none-prerequisites"),
    ],
)
def test_A1_ECP_prerequisite_classes(completed, required, expected):
    assert prerequisites_satisfied(completed, required) is expected


@pytest.mark.parametrize(
    "student_changes,course_changes,expected",
    [
        pytest.param({}, {}, "REGISTERED", id="A1-ECP-13-eligible-seat"),
        pytest.param({"outstanding_dues": 1}, {}, "DUES_BLOCK", id="A1-ECP-14-positive-dues"),
        pytest.param({"registered_courses": {"CS201"}}, {}, "ALREADY_REGISTERED", id="A1-ECP-15-existing-registration"),
        pytest.param({}, {"prerequisites": {"CS101"}}, "PREREQUISITES_MISSING", id="A1-ECP-16-missing-prerequisite"),
        pytest.param({"current_credits": 16}, {}, "CREDIT_LIMIT", id="A1-ECP-17-credit-limit"),
        pytest.param({}, {"enrolled": 2}, "WAITLISTED", id="A1-ECP-18-full-course"),
    ],
)
def test_A1_ECP_registration_classes(student_changes, course_changes, expected):
    student = Student("S101", **student_changes)
    course = Course("CS201", 3, 2, **course_changes)
    assert registration_decision(student, course) == expected


# A2. Boundary Value Analysis
@pytest.mark.parametrize(
    "current,new,expected",
    [
        pytest.param(0, 1, True, id="A2-BVA-01-current-zero"),
        pytest.param(18, 1, False, id="A2-BVA-02-current-eighteen"),
        pytest.param(0, 4, True, id="A2-BVA-03-course-four-at-zero"),
        pytest.param(14, 4, True, id="A2-BVA-04-total-exactly-eighteen"),
        pytest.param(15, 4, False, id="A2-BVA-05-total-just-above-eighteen"),
        pytest.param(17, 1, True, id="A2-BVA-06-course-one-total-eighteen"),
        pytest.param(18, 4, False, id="A2-BVA-07-course-four-at-current-eighteen"),
    ],
)
def test_A2_BVA_credit_boundaries(current, new, expected):
    assert check_credit_limit(current, new) is expected


@pytest.mark.parametrize(
    "enrolled,expected",
    [
        pytest.param(2, "WAITLISTED", id="A2-BVA-08-enrollment-at-capacity"),
        pytest.param(1, "REGISTERED", id="A2-BVA-09-enrollment-one-below-capacity"),
        pytest.param(0, "REGISTERED", id="A2-BVA-10-empty-course"),
    ],
)
def test_A2_BVA_capacity_boundaries(enrolled, expected):
    assert registration_decision(Student("S102"), Course("CS202", 1, 2, enrolled)) == expected


@pytest.mark.parametrize(
    "dues,expected",
    [
        pytest.param(0, "REGISTERED", id="A2-BVA-11-dues-zero"),
        pytest.param(1, "DUES_BLOCK", id="A2-BVA-12-dues-one"),
    ],
)
def test_A2_BVA_dues_boundary(dues, expected):
    assert registration_decision(Student("S103", outstanding_dues=dues), Course("CS203", 1, 1)) == expected


# A3. Decision Table and priority combinations
@pytest.mark.parametrize(
    "student_changes,course_changes,expected",
    [
        pytest.param({"outstanding_dues": 1}, {}, "DUES_BLOCK", id="A3-DT-01-dues-block"),
        pytest.param({"registered_courses": {"CS204"}}, {}, "ALREADY_REGISTERED", id="A3-DT-02-already-registered"),
        pytest.param({}, {"prerequisites": {"CS101"}}, "PREREQUISITES_MISSING", id="A3-DT-03-prerequisites-missing"),
        pytest.param({"current_credits": 16}, {}, "CREDIT_LIMIT", id="A3-DT-04-credit-limit"),
        pytest.param({}, {"enrolled": 1}, "WAITLISTED", id="A3-DT-05-waitlisted"),
        pytest.param({}, {}, "REGISTERED", id="A3-DT-06-registered"),
        pytest.param({"outstanding_dues": 1, "registered_courses": {"CS204"}}, {}, "DUES_BLOCK", id="A3-DT-07-priority-dues-over-duplicate"),
        pytest.param({"registered_courses": {"CS204"}}, {"prerequisites": {"CS101"}}, "ALREADY_REGISTERED", id="A3-DT-08-priority-duplicate-over-prerequisite"),
        pytest.param({"current_credits": 16}, {"prerequisites": {"CS101"}}, "PREREQUISITES_MISSING", id="A3-DT-09-priority-prerequisite-over-credit"),
        pytest.param({"current_credits": 16}, {"enrolled": 1}, "CREDIT_LIMIT", id="A3-DT-10-priority-credit-over-full"),
    ],
)
def test_A3_DT_outcomes_and_priority(student_changes, course_changes, expected):
    student = Student("S104", **student_changes)
    course = Course("CS204", 3, 1, **course_changes)
    assert registration_decision(student, course) == expected


# A4. State changes and input validation
def test_A4_STATE_successful_registration_updates_all_fields(eligible_pair):
    student, course = eligible_pair
    assert register_course(student, course) == "REGISTERED"
    assert student.registered_courses == {course.code}, "successful registration must add the course"
    assert student.current_credits == 3, "successful registration must add course credits"
    assert course.enrolled == 1, "successful registration must increment enrollment"


def test_A4_STATE_waitlist_adds_student_id_only_once():
    student = Student("S105")
    course = Course("CS205", 3, 1, enrolled=1)
    assert register_course(student, course) == "WAITLISTED"
    assert register_course(student, course) == "WAITLISTED"
    assert course.waitlist == [student.student_id], "waitlist must contain this ID exactly once"
    assert student.registered_courses == set() and student.current_credits == 0
    assert course.enrolled == 1


@pytest.mark.parametrize(
    "student_changes,course_changes,expected",
    [
        pytest.param({"outstanding_dues": 1}, {}, "DUES_BLOCK", id="A4-STATE-01-dues-failure"),
        pytest.param({"current_credits": 16}, {}, "CREDIT_LIMIT", id="A4-STATE-02-credit-failure"),
        pytest.param({}, {"prerequisites": {"CS101"}}, "PREREQUISITES_MISSING", id="A4-STATE-03-prerequisite-failure"),
    ],
)
def test_A4_STATE_unsuccessful_registration_leaves_state_unchanged(student_changes, course_changes, expected):
    student = Student("S106", **student_changes)
    course = Course("CS206", 3, 2, **course_changes)
    before = state_of(student, course)
    assert register_course(student, course) == expected
    assert (student, course) == before, "unsuccessful registration must preserve both objects"


def test_A4_STATE_successful_withdrawal_updates_registration_credits_and_enrollment():
    student = Student("S107", current_credits=6, registered_courses={"CS207"})
    course = Course("CS207", 3, 4, enrolled=2)
    assert withdraw_course(student, course) is True
    assert "CS207" not in student.registered_courses, "withdrawal must remove the course"
    assert student.current_credits == 3, "withdrawal must subtract course credits"
    assert course.enrolled == 1, "withdrawal must decrement enrollment"


def test_A4_STATE_failed_withdrawal_returns_false_without_mutation():
    student = Student("S108", current_credits=6)
    course = Course("CS208", 3, 4, enrolled=2)
    before = state_of(student, course)
    assert withdraw_course(student, course) is False
    assert (student, course) == before, "failed withdrawal must preserve both objects"


def test_A4_STATE_registration_decision_does_not_mutate_either_object(eligible_pair):
    student, course = eligible_pair
    before = state_of(student, course)
    assert registration_decision(student, course) == "REGISTERED"
    assert (student, course) == before, "decision evaluation must leave student and course unchanged"


@pytest.mark.parametrize(
    "current,new,message",
    [
        pytest.param(-1, 1, "Invalid current credits", id="A4-VAL-01-current-below-range"),
        pytest.param(19, 1, "Invalid current credits", id="A4-VAL-02-current-above-range"),
        pytest.param(0, 0, "Invalid course credits", id="A4-VAL-03-course-below-range"),
        pytest.param(0, 5, "Invalid course credits", id="A4-VAL-04-course-above-range"),
        pytest.param(-1, 0, "Invalid current credits", id="A4-VAL-05-current-before-course-priority"),
    ],
)
def test_A4_VAL_credit_validation_messages_and_priority(current, new, message):
    with pytest.raises(ValueError) as exc_info:
        check_credit_limit(current, new)
    assert str(exc_info.value) == message


@pytest.mark.parametrize(
    "capacity,enrolled,message",
    [
        pytest.param(0, 0, "Invalid capacity or enrollment", id="A4-VAL-06-zero-capacity"),
        pytest.param(2, -1, "Invalid capacity or enrollment", id="A4-VAL-07-negative-enrollment"),
        pytest.param(2, 3, "Invalid capacity or enrollment", id="A4-VAL-08-enrollment-over-capacity"),
    ],
)
def test_A4_VAL_capacity_and_enrollment_validation(capacity, enrolled, message):
    with pytest.raises(ValueError) as exc_info:
        registration_decision(Student("S109"), Course("CS209", 1, capacity, enrolled))
    assert str(exc_info.value) == message


def test_A4_VAL_negative_dues_exact_message():
    with pytest.raises(ValueError) as exc_info:
        registration_decision(Student("S110", outstanding_dues=-1), Course("CS210", 1, 2))
    assert str(exc_info.value) == "Invalid dues"


def test_A4_VAL_dues_validation_precedes_capacity_validation():
    with pytest.raises(ValueError) as exc_info:
        registration_decision(
            Student("S111", outstanding_dues=-1), Course("CS211", 1, 0)
        )
    assert str(exc_info.value) == "Invalid dues", "negative dues must be validated before course capacity"
