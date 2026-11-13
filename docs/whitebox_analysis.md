# White-box analysis: `registration_decision()`

## Scope and execution record

The tests in `tests/test_whitebox.py` target the control flow of
`registration_decision()` in `registration.py`. Their expected functional
results follow `REQUIREMENTS.md`; the two failures in the white-box run are
retained as defects. The final combined run also collected the existing
black-box and decision-priority suites.

- White-box-only run: **18 passed, 2 failed**. The exact-limit credit case and
  full-course waitlist case fail.
- Combined repository run: **61 passed, 18 failed**.
- Full-module coverage in that combined run: **51/53 statements (96.2%)** and
  **24/26 branch arcs (92.3%)**. Coverage.py's combined `Cover` column is 95%.
- For `registration_decision()` specifically, 14/15 executable statements
  (93.3%) and 13/14 branch arcs (92.9%) were covered. Its uncovered statement
  is the `WAITLISTED` return at line 59; the uncovered branch is the true edge
  of `course.enrolled > course.capacity` at line 58.

The actual pytest transcripts and coverage XML are saved in
`docs/evidence/whitebox-pytest.txt`,
`docs/evidence/whitebox-coverage.xml`,
`docs/evidence/whitebox-only-pytest.txt`, and
`docs/evidence/whitebox-only-coverage.xml`. The combined-run coverage summary
shows two partially covered branches in the whole module: the unreachable
waitlist decision and the corresponding waitlist append path in
`register_course()`.

## Control-flow graph

The following node labels describe the function's decision graph. `T` and `F`
refer to the true and false outcomes respectively.

| Node | Description |
|---|---|
| E | Function entry |
| D1 | `student.outstanding_dues < 0` |
| X1 | Raise `ValueError("Invalid dues")` |
| D2 | Compound invalid-capacity condition: A OR B, where A is enrollment outside `0..capacity` and B is `capacity < 1` |
| X2 | Raise `ValueError("Invalid capacity or enrollment")` |
| D3 | `student.outstanding_dues > 1000` |
| R1 | Return `DUES_BLOCK` |
| D4 | Course code is already registered |
| R2 | Return `ALREADY_REGISTERED` |
| D5 | Prerequisites are not satisfied |
| R3 | Return `PREREQUISITES_MISSING` |
| D6 | Credit limit is not satisfied |
| R4 | Return `CREDIT_LIMIT` |
| D7 | `course.enrolled > course.capacity` |
| R5 | Return `WAITLISTED` |
| R6 | Return `REGISTERED` |

Edges are: `E→D1`; `D1-T→X1`, `D1-F→D2`; `D2-T→X2`,
`D2-F→D3`; `D3-T→R1`, `D3-F→D4`;
`D4-T→R2`, `D4-F→D5`; `D5-T→R3`, `D5-F→D6`; `D6-T→R4`,
`D6-F→D7`; `D7-T→R5`, `D7-F→R6`. Each raise and return node exits the
function.

## Cyclomatic complexity and basis paths

Using the assignment's seven-`if`-decision convention, the cyclomatic
complexity is **M = 1 + 7 = 8**. The compound capacity/enrollment `if` is
counted as one decision for this calculation. This is a structural count; it
does not imply all graph paths are feasible.

An independent basis set of eight structural paths is:

1. `E → D1-T → X1` (negative dues).
2. `E → D1-F → D2-T → X2` (invalid capacity or enrollment).
3. `E → D1-F → D2-F → D3-T → R1` (dues block).
4. `E → D1-F → D2-F → D3-F → D4-T → R2` (duplicate).
5. Continue through D1–D4 false, then `D5-T → R3` (missing prerequisite).
6. Continue through D1–D5 false, then `D6-T → R4` (credit rejection).
7. Continue through D1–D6 false, then `D7-T → R5` (waitlist return).
8. Continue through D1–D7 false to `R6` (registration).

The tests execute the feasible paths among these. Path 7 is included in the
structural basis only; it is infeasible under the preceding validation, as
explained below. Separate invalid-input tests exercise both operands of the
capacity validation, including cases where both are logically true.

## Coverage results

The final combined run measured the entire `registration.py` module, including
helper, registration, and withdrawal functions. It recorded 51 of 53
statements, 26 branch arcs with two partial arcs, and 95% combined coverage in
the coverage.py summary. The 95% figure is **not** statement coverage: the
statement-only ratio is 51/53 (96.2%); branch-arc coverage is 24/26 (92.3%).

For the requested function, the executable lines in its body are 46–60:
14 executed of 15 (93.3%). Seven `if` statements provide 14 branch arcs under
the convention above; 13 arcs were taken (92.9%). The missed statement and
branch both correspond to the waitlist return. The white-box-only run had
lower whole-module coverage because it does not execute `register_course()` or
`withdraw_course()`; its saved transcript reports 73% combined module
coverage. Coverage evidence is in the XML files named above.

## Condition coverage and MC/DC for D2

For the compound invalid-capacity condition define:

- **A** = enrollment is outside `0..capacity`.
- **B** = capacity is less than 1.
- Decision = **A OR B**.

The white-box cases provide the following combinations:

| Case | Example | A | B | Decision |
|---|---|---:|---:|---:|
| WB02A | capacity 2, enrolled -1 | T | F | T |
| WB02B | capacity 2, enrolled 3 | T | F | T |
| WB02C | capacity 0, enrolled 0 | F | T | T |
| WB03 | capacity 2, enrolled 1 | F | F | F |
| WB02D | capacity 0, enrolled -1 | T | T* | T |

`*` In WB02D, Python short-circuits the `or` after A is true, so B is not
evaluated at runtime. Its logical value is true for that input. The four
relevant combinations establish condition coverage for both A and B. They
also satisfy MC/DC: compare WB03 with WB02A to show A independently changes
the decision while B is false, and compare WB03 with WB02C to show B
independently changes the decision while A is false. Each of those pairs
changes only its named condition and changes the overall decision.

## Unreachable branches and limitations

After D2 passes, its constraints imply `capacity >= 1` and
`0 <= enrolled <= capacity`. Therefore `course.enrolled > course.capacity`
at D7 cannot be true. The function cannot reach `WAITLISTED` through valid
execution, and cannot reach it through invalid enrollment because D2 raises
first. The SRS-required full-course test uses `enrolled == capacity` and
expects `WAITLISTED`; it fails because the implementation tests `>` at D7 and
then falls through to `REGISTERED`. The related `register_course()` waitlist
append branch is also unreachable through this function.

The coverage evidence records the current test suite and implementation only;
it does not establish correctness. Full-module percentages include unrelated
functions, so the function-specific ratios are stated separately. Structural
complexity and basis paths include the infeasible waitlist edge and should not
be read as proof that every structural path can execute.
