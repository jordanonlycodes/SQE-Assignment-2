"""White-box path and branch tests for registration_decision().

Expected functional outcomes follow REQUIREMENTS.md. Test IDs identify the
decision/branch exercised; the full-course case intentionally keeps the SRS
expectation even though the current implementation takes the other outcome.
"""
import pytest

from registration import Course, Student, registration_decision


def decide(*, dues=0, registered=False, completed=None, prerequisites=None,
           credits=0, course_credits=3, capacity=2, enrolled=0):
    code = "WB101"
    student = Student(
        "WB-STUDENT",
        completed_courses=set() if completed is None else set(completed),
        current_credits=credits,
        outstanding_dues=dues,
        registered_courses={code} if registered else set(),
    )
    course = Course(
        code,
        course_credits,
        capacity,
        enrolled,
        set() if prerequisites is None else set(prerequisites),
    )
    return registration_decision(student, course)


# D1: negative dues validation, before any capacity or eligibility decision.
def test_WB01_negative_dues_raises_first():
    with pytest.raises(ValueError) as error:
        decide(dues=-1, capacity=0)
    assert str(error.value) == "Invalid dues"


# D2: compound invalid-capacity/enrollment decision:
# A = enrollment is outside [0, capacity], B = capacity < 1; invalid = A or B.
@pytest.mark.parametrize(
    "capacity,enrolled,test_id",
    [
        pytest.param(2, -1, "WB02A-enrollment-below-zero-A-true-B-false", id="WB02A-enrollment-below-zero-A-true-B-false"),
        pytest.param(2, 3, "WB02B-enrollment-above-capacity-A-true-B-false", id="WB02B-enrollment-above-capacity-A-true-B-false"),
        pytest.param(0, 0, "WB02C-zero-capacity-A-false-B-true", id="WB02C-zero-capacity-A-false-B-true"),
        pytest.param(0, -1, "WB02D-both-conditions-true", id="WB02D-both-conditions-true"),
    ],
)
def test_WB02_invalid_capacity_or_enrollment(capacity, enrolled, test_id):
    # D2 true branch: each invalid shape must raise the documented exception.
    with pytest.raises(ValueError) as error:
        decide(capacity=capacity, enrolled=enrolled)
    assert str(error.value) == "Invalid capacity or enrollment", test_id


def test_WB03_compound_condition_false_path_is_eligible():
    # D2 false branch: A=false and B=false; the condition falls through.
    assert decide(capacity=2, enrolled=1) == "REGISTERED"


# D3: positive dues branch is true only for dues > 1000 in this implementation.
@pytest.mark.parametrize(
    "dues,expected",
    [
        pytest.param(1001, "DUES_BLOCK", id="WB04A-dues-over-1000-true-branch"),
        pytest.param(1, "REGISTERED", id="WB04B-positive-dues-false-branch-current-code"),
        pytest.param(0, "REGISTERED", id="WB04C-zero-dues-false-branch"),
    ],
)
def test_WB04_dues_threshold_branch(dues, expected):
    assert decide(dues=dues) == expected


# D4: duplicate registration true branch; otherwise continue to prerequisites.
def test_WB05_duplicate_registration_returns_already_registered():
    assert decide(registered=True, prerequisites={"PRE101"}) == "ALREADY_REGISTERED"


# D5: prerequisite helper false branch and true branch.
@pytest.mark.parametrize(
    "completed,required,expected",
    [
        pytest.param(set(), {"PRE101"}, "PREREQUISITES_MISSING", id="WB06A-prerequisites-false-branch"),
        pytest.param({"PRE101"}, {"PRE101"}, "REGISTERED", id="WB06B-prerequisites-true-branch"),
        pytest.param(set(), set(), "REGISTERED", id="WB06C-empty-prerequisite-set"),
    ],
)
def test_WB06_prerequisite_decision(completed, required, expected):
    assert decide(completed=completed, prerequisites=required) == expected


# D6: credit-limit helper false (reject) and true (continue) branches.
@pytest.mark.parametrize(
    "credits,course_credits,expected",
    [
        pytest.param(16, 3, "CREDIT_LIMIT", id="WB07A-credit-limit-false-branch"),
        pytest.param(13, 4, "REGISTERED", id="WB07B-credit-limit-true-branch"),
        pytest.param(14, 4, "REGISTERED", id="WB07C-exact-limit-srs-expectation"),
    ],
)
def test_WB07_credit_limit_decision(credits, course_credits, expected):
    assert decide(credits=credits, course_credits=course_credits) == expected


@pytest.mark.parametrize(
    "credits,course_credits,message",
    [
        pytest.param(-1, 3, "Invalid current credits", id="WB07D-invalid-current-credits"),
        pytest.param(0, 5, "Invalid course credits", id="WB07E-invalid-course-credits"),
    ],
)
def test_WB07_credit_validation_paths(credits, course_credits, message):
    with pytest.raises(ValueError) as error:
        decide(credits=credits, course_credits=course_credits)
    assert str(error.value) == message


# D7: availability condition `enrolled > capacity` true is unreachable after
# D2 accepts only enrolled <= capacity. Keep the SRS boundary expectation here
# so the current implementation's incorrect final outcome remains visible.
def test_WB08_full_course_is_waitlisted_per_srs():
    assert decide(capacity=2, enrolled=2) == "WAITLISTED"


def test_WB09_final_registration_outcome_below_capacity():
    assert decide(capacity=2, enrolled=1) == "REGISTERED"
