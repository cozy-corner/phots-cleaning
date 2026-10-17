# OCR lines below are taken from real screenshots in the library (personal data left out).
import pytest

from rules import (
    RULES,
    Screenshot,
    has_date_and_clock_on_top,
    has_lock_screen_label,
    is_watch_size,
)

IPHONE = (1290, 2796)


def shot(lines, size=IPHONE):
    return Screenshot(*size, read_text=lambda: lines)


def is_deletable(s):
    return any(rule(s) for rule in RULES)


def test_watch_size():
    assert is_watch_size(shot([], size=(368, 448)))
    assert not is_watch_size(shot([]))


def test_watch_is_decided_without_ocr():
    calls = []
    s = Screenshot(368, 448, read_text=lambda: calls.append(1) or [])
    assert is_deletable(s)
    assert calls == []


@pytest.mark.parametrize(
    "lines",
    [
        # OCR reads the alarm icon as a symbol before the text.
        ["Rakuten", "Tue Oct 13", "23:53", "• No Alarm"],
        ["Rakuten", "© No Alarm", "Downtime"],
        ["Rakuten", ".. .", "Swipe up to unlock", "22:14", "Timer 20:56"],
    ],
)
def test_lock_screen_label(lines):
    assert has_lock_screen_label(shot(lines))


@pytest.mark.parametrize(
    "lines",
    [
        ["Rakuten", "Saturday, November 22", "1:19", "Downtime"],
        ["Rakuten", "Fri Sep 4", "1:19", "Downtime"],
        # OCR misreads the big clock digits: 0 as O, and "23:52" as "23:5<".
        ["Rakuten", "Sunday, December 28", "O:51", "Downtime"],
        ["Rakuten", "•I| 4G", "Thu Mar 5", "23:5<", "Downtime"],
    ],
)
def test_date_and_clock_on_top(lines):
    assert has_date_and_clock_on_top(shot(lines))


def test_date_and_clock_must_be_near_the_top():
    lines = ["a", "b", "c", "d", "e", "f", "Thu Mar 5", "23:52"]
    assert not has_date_and_clock_on_top(shot(lines))


@pytest.mark.parametrize(
    "lines",
    [
        # Every iPhone screenshot has a clock in the status bar; that alone is not a lock screen.
        ["21:09", "Overview", "Repositories", "github.com"],
        ["14:32", "• PayPay", "Ticket"],
        ["8:22", "OURA", "50", "Readiness", "Sleep"],
        # Photos viewer: a Japanese date and a time, but not a lock screen.
        ["20:41", "<", "2019年3月10日", "23:30"],
        [],
    ],
)
def test_not_deletable(lines):
    assert not is_deletable(shot(lines))
