
from registration import Student, Course, registration_decision


def test_dues_take_priority_over_full_course():
    student = Student("S201", outstanding_dues=1)
    course = Course("CS301", 3, 1, enrolled=1)

    result = registration_decision(student, course)

    assert result == "DUES_BLOCK"
