"""Lab 4, Part A: size a service before you deploy it.

One copy of the agent handles SLOTS questions at the same time.
How many copies do you need for a given load, and how long do questions wait?

Run it:   python sizing.py
Test it:  pytest -q

Your job: write the four functions below. Watch the units: the arrival rate
is given per MINUTE, the duration of one question in SECONDS.
"""
import math

SLOTS = 4  # questions one copy of the agent handles at the same time


def in_progress(per_minute, seconds):
    """Little's law: the average number of questions in progress, L = λ × W.

    per_minute: arrival rate λ, in questions per minute.
    seconds:    average time W one question spends in the system, in seconds.
    """
    raise NotImplementedError("TODO: L = λ × W, with λ and W in the same unit of time")


def copies(per_minute, seconds, slots=SLOTS, margin=0.0):
    """Number of copies needed so that the slots cover L, plus a safety margin.

    margin=0.25 means 25% more capacity than the average load.
    A copy cannot be split: round UP to a whole number of copies.
    """
    raise NotImplementedError("TODO: L × (1 + margin) / slots, rounded up")


def occupancy(per_minute, seconds, n_copies, slots=SLOTS):
    """Occupancy rate ρ: the share of all slots that is busy on average.

    1.0 means every slot is busy all the time.
    """
    raise NotImplementedError("TODO: ρ = L / (n_copies × slots)")


def wait_seconds(rho, task_seconds):
    """Simple queue model: the average wait before a question starts.

    wait = ρ / (1 − ρ) × task duration.
    When ρ ≥ 1, more questions arrive than you can serve: the queue grows
    without bound, so return math.inf.
    """
    raise NotImplementedError("TODO: ρ / (1 − ρ) × task_seconds, or math.inf when ρ ≥ 1")


CASES = [
    ("Case 1", 6, 40),
    ("Case 2", 30, 90),
    ("Case 3 (slow provider)", 30, 180),
]

if __name__ == "__main__":
    print(f"{'case':<24}{'L':>8}{'copies':>9}{'+25%':>7}")
    for name, per_minute, seconds in CASES:
        print(
            f"{name:<24}{in_progress(per_minute, seconds):>8.2f}"
            f"{copies(per_minute, seconds):>9}{copies(per_minute, seconds, margin=0.25):>7}"
        )
    print()
    for n in (1, 2):
        rho = occupancy(6, 40, n)
        print(f"Case 1 with {n} cop{'y' if n == 1 else 'ies'}: occupancy {rho:.0%}, average wait {wait_seconds(rho, 40):.0f} s")
