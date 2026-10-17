"""Rules that decide whether a screenshot is a deletion candidate.

A rule takes a Screenshot and returns True to delete it. To add one, write the
function and list it in RULES.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property


@dataclass
class Screenshot:
    width: int
    height: int
    read_text: Callable[[], list[str]]

    @cached_property
    def lines(self) -> list[str]:
        # OCR is slow, so run it only when a rule asks for the text.
        return self.read_text()


WATCH_SIZE = (368, 448)

LOCK_SCREEN_LABEL = re.compile(r"No Alarm|Swipe up to unlock")
# Only the leading "HH:" — OCR misreads the big lock-screen digits (0 as O, "23:52" as "23:5<").
CLOCK_LINE = re.compile(r"^[0-9O]{1,2}[:：]")
DATE_LINE = re.compile(r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,? [A-Z][a-z]+ \d{1,2}$")


def is_watch_size(s: Screenshot) -> bool:
    return (s.width, s.height) == WATCH_SIZE


def has_lock_screen_label(s: Screenshot) -> bool:
    return any(LOCK_SCREEN_LABEL.search(t) for t in s.lines)


def has_date_and_clock_on_top(s: Screenshot) -> bool:
    """Catches lock screens that show neither label, e.g. with a Downtime notice instead."""
    top = s.lines[:6]
    return any(DATE_LINE.match(t) for t in top) and any(CLOCK_LINE.match(t) for t in top)


# Cheap rules first: a match skips the rest, including OCR.
RULES = [is_watch_size, has_lock_screen_label, has_date_and_clock_on_top]
