"""Automated checks for Lab 4, Part A. Run with: pytest -q"""
import math

import pytest

import sizing


def test_slots_is_four():
    assert sizing.SLOTS == 4, "One copy of the agent handles 4 questions at a time: keep SLOTS = 4."


@pytest.mark.parametrize(
    "per_minute, seconds, expected",
    [(6, 40, 4), (30, 90, 45), (30, 180, 90)],
)
def test_in_progress_littles_law(per_minute, seconds, expected):
    got = sizing.in_progress(per_minute, seconds)
    assert got == pytest.approx(expected), (
        f"in_progress({per_minute}, {seconds}) returned {got}, expected {expected}. "
        "L = λ × W: convert the rate per minute into a rate per second (or the seconds into minutes) first."
    )


@pytest.mark.parametrize(
    "per_minute, seconds, without_margin, with_margin",
    [(6, 40, 1, 2), (30, 90, 12, 15), (30, 180, 23, 29)],
)
def test_copies_three_cases(per_minute, seconds, without_margin, with_margin):
    got = sizing.copies(per_minute, seconds)
    assert got == without_margin, (
        f"copies({per_minute}, {seconds}) returned {got}, expected {without_margin}: L / 4, rounded up."
    )
    got = sizing.copies(per_minute, seconds, margin=0.25)
    assert got == with_margin, (
        f"copies({per_minute}, {seconds}, margin=0.25) returned {got}, expected {with_margin}: "
        "L × 1.25 / 4, rounded up."
    )


def test_copies_is_a_whole_number():
    assert isinstance(sizing.copies(30, 90), int), "copies() must return a whole number (an int): you cannot run 11.25 copies."


def test_copies_does_not_add_a_copy_on_an_exact_fit():
    # 12 per minute × 40 s = 8 questions in progress = exactly 2 copies of 4 slots.
    got = sizing.copies(12, 40)
    assert got == 2, (
        f"copies(12, 40) returned {got}, expected 2: L = 8 fits exactly in 2 copies. "
        "Round up with math.ceil, not with int(x) + 1."
    )


def test_copies_uses_the_slots_argument():
    assert sizing.copies(30, 90, slots=9) == 5, "copies(30, 90, slots=9) should be 5 (45 / 9): use the slots argument."


def test_occupancy_case_1():
    assert sizing.occupancy(6, 40, 1) == pytest.approx(1.0), "Case 1 with one copy: L = 4 on 4 slots, ρ should be 1.0 (100%)."
    assert sizing.occupancy(6, 40, 2) == pytest.approx(0.5), "Case 1 with two copies: L = 4 on 8 slots, ρ should be 0.5 (50%)."


def test_occupancy_uses_slots():
    assert sizing.occupancy(30, 90, 12) == pytest.approx(45 / 48), "Case 2 with 12 copies: ρ = 45 / (12 × 4)."
    assert sizing.occupancy(30, 90, 5, slots=9) == pytest.approx(1.0), "occupancy() must use its slots argument."


def test_wait_with_two_copies_is_one_task_duration():
    got = sizing.wait_seconds(0.5, 40)
    assert got == pytest.approx(40), f"wait_seconds(0.5, 40) returned {got}: ρ / (1 − ρ) × 40 = 40 s."


def test_wait_grows_fast_near_full():
    assert sizing.wait_seconds(0.8, 40) == pytest.approx(160), "wait_seconds(0.8, 40) should be 0.8 / 0.2 × 40 = 160 s."
    assert sizing.wait_seconds(0.0, 40) == pytest.approx(0), "With nobody in the system (ρ = 0), nobody waits."


@pytest.mark.parametrize("rho", [1.0, 1.5])
def test_wait_is_infinite_when_full(rho):
    got = sizing.wait_seconds(rho, 40)
    assert got == math.inf, (
        f"wait_seconds({rho}, 40) returned {got}. When ρ ≥ 1 the queue grows without bound: return math.inf "
        "(and do not divide by zero)."
    )


def test_case_1_end_to_end():
    one = sizing.wait_seconds(sizing.occupancy(6, 40, 1), 40)
    two = sizing.wait_seconds(sizing.occupancy(6, 40, 2), 40)
    assert one == math.inf, "Case 1 with one copy runs at 100%: the average wait is unbounded (math.inf)."
    assert two == pytest.approx(40), "Case 1 with two copies runs at 50%: the average wait is about 40 s."
