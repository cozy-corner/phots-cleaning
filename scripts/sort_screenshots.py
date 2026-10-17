"""Monthly: put deletable screenshots into the "To Delete" album in Photos.

Targets screenshots added since the last --apply run (all of them on the first run).
What counts as deletable is defined in rules.py.

Default is a dry run that only prints counts. --apply adds them to the album and
records the run time. Deleting is done by hand in Photos.
"""

import argparse
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import osxphotos
import photoscript
from osxphotos.text_detection import detect_text

from rules import RULES, Screenshot

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / ".state" / "last_run"
# osxphotos finds the library via Photos' own prefs plist, which a launchd job
# can't read (it's in another app's container), so name the library explicitly.
LIBRARY = Path.home() / "Pictures" / "Photos Library.photoslibrary"

ALBUM = "To Delete"
BATCH = 50


def read_last_run() -> datetime | None:
    if not STATE_FILE.exists():
        return None
    return datetime.fromisoformat(STATE_FILE.read_text().strip())


def write_last_run(t: datetime) -> None:
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(t.isoformat())


def source_image(p: osxphotos.PhotoInfo) -> str | None:
    """Original if on disk, else the largest local preview.

    With iCloud "Optimize Mac Storage" most originals are not downloaded,
    but Photos keeps full-size JPEG previews locally.
    """
    if p.path:
        return p.path
    if p.path_derivatives:
        return max(p.path_derivatives, key=os.path.getsize)
    return None


def ocr_lines(p: osxphotos.PhotoInfo) -> list[str]:
    src = source_image(p)
    if src is None:
        print(f"warning: no local image for {p.uuid}, text rules skipped", file=sys.stderr)
        return []
    return [text.strip() for text, _ in detect_text(src)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="add to the album and record run time")
    args = ap.parse_args()

    started = datetime.now(timezone.utc)
    last_run = read_last_run()
    screenshots = [
        p for p in osxphotos.PhotosDB(dbfile=str(LIBRARY)).photos(movies=False)
        if p.screenshot and (last_run is None or p.date_added >= last_run)
    ]
    print(f"{len(screenshots)} screenshots added since {last_run or 'the beginning'}")

    targets, matched_by = [], Counter()
    for p in screenshots:
        shot = Screenshot(p.width, p.height, read_text=lambda p=p: ocr_lines(p))
        rule = next((r for r in RULES if r(shot)), None)
        if rule:
            targets.append(p)
            matched_by[rule.__name__] += 1
    print(f"to delete: {len(targets)} {dict(matched_by)}")

    if args.apply:
        if targets:
            lib = photoscript.PhotosLibrary()
            album = lib.album(ALBUM) or lib.create_album(ALBUM)
            uuids = [p.uuid for p in targets]
            # One AppleEvent for 250+ photos timed out in Photos; add in small batches.
            for i in range(0, len(uuids), BATCH):
                album.add(list(lib.photos(uuid=uuids[i : i + BATCH])))
            print(f"added {len(targets)} to album '{ALBUM}'")
        write_last_run(started)
        print(f"recorded last run: {started.isoformat()}")


if __name__ == "__main__":
    main()
