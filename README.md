# phots-cleaning

Once a month, collects deletable screenshots from macOS Photos into a `To Delete` album.
It never deletes anything: review the album in Photos and delete the photos by hand.

## What counts as deletable

Defined in [`scripts/rules.py`](scripts/rules.py). A screenshot is collected if any rule matches:

- `is_watch_size` — Apple Watch screenshot (368×448)
- `has_lock_screen_label` — iPhone lock screen showing "No Alarm" or "Swipe up to unlock"
- `has_date_and_clock_on_top` — iPhone lock screen with a date and a clock at the top

The text rules use OCR (macOS Vision, on-device). To add a rule, write a function that
takes a `Screenshot` and add it to `RULES`.

## Setup

Requires [uv](https://docs.astral.sh/uv/). The repo is expected at `~/code/phots-cleaning`
(the launchd job `cd`s there).

```sh
uv sync
scripts/install-launchd.sh
```

`install-launchd.sh` symlinks `launchd/local.phots-cleaning.plist` into `~/Library/LaunchAgents`
and loads it. The job runs on the 1st of every month at 10:00. Re-run the script after editing
the plist.

## Usage

```sh
uv run scripts/sort_screenshots.py           # dry run: print counts only
uv run scripts/sort_screenshots.py --apply   # add to the album and record the run time
```

Only screenshots added since the last `--apply` run are processed; the time is stored in
`.state/last_run`. Delete that file to process the whole library again.

Logs from the launchd job go to `~/Library/Logs/phots-cleaning.log`. To run the job now:

```sh
launchctl kickstart gui/$(id -u)/local.phots-cleaning
```

## Tests

```sh
uv run pytest
```
