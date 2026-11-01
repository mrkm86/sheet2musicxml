#!/usr/bin/env python3
"""Report incomplete/overfull MusicXML measures without external dependencies."""

import argparse
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def child_text(parent, path, default=None):
    node = parent.find(path)
    return node.text if node is not None else default


def check(path: Path, allow_pickup: bool) -> list[str]:
    root = ET.parse(path).getroot()
    if root.tag != "score-partwise":
        return ["expected a score-partwise MusicXML document"]
    issues = []
    part_counts = []
    for part in root.findall("part"):
        part_id = part.get("id", "?")
        divisions = 1
        expected = Fraction(4)
        staff_count = 1
        measures = part.findall("measure")
        part_counts.append(len(measures))
        for index, measure in enumerate(measures):
            number = measure.get("number", str(index + 1))
            position = Fraction(0)
            last_note_start = Fraction(0)
            ends = defaultdict(lambda: Fraction(0))
            for item in measure:
                if item.tag == "attributes":
                    d = child_text(item, "divisions")
                    if d is not None:
                        divisions = int(d)
                    beats = child_text(item, "time/beats")
                    beat_type = child_text(item, "time/beat-type")
                    if beats and beat_type:
                        expected = Fraction(sum(int(x) for x in beats.split("+")) * 4, int(beat_type))
                    staves = child_text(item, "staves")
                    if staves is not None:
                        staff_count = int(staves)
                elif item.tag in ("backup", "forward"):
                    duration = Fraction(int(child_text(item, "duration", "0")), divisions)
                    position += -duration if item.tag == "backup" else duration
                elif item.tag == "note":
                    staff = int(child_text(item, "staff", "1"))
                    duration = Fraction(int(child_text(item, "duration", "0")), divisions)
                    if item.find("grace") is None:
                        chord = item.find("chord") is not None
                        start = last_note_start if chord else position
                        ends[staff] = max(ends[staff], start + duration)
                        if not chord:
                            last_note_start = start
                            position += duration
            for staff in range(1, staff_count + 1):
                actual = ends[staff]
                pickup = allow_pickup and index == 0 and actual < expected
                if actual != expected and not pickup:
                    issues.append(
                        f"part {part_id}, measure {number}, staff {staff}: "
                        f"expected {expected} quarter notes; found {actual}"
                    )
            if position < 0:
                issues.append(f"part {part_id}, measure {number}: backup before start")
    if len(set(part_counts)) > 1:
        issues.append(f"part measure counts differ: {part_counts}")
    if not part_counts:
        issues.append("no parts found")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("musicxml", type=Path)
    parser.add_argument("--allow-pickup", action="store_true")
    args = parser.parse_args()
    try:
        issues = check(args.musicxml, args.allow_pickup)
    except (ET.ParseError, OSError, ValueError, ZeroDivisionError) as exc:
        print(f"cannot inspect MusicXML: {exc}", file=sys.stderr)
        return 2
    if issues:
        print("\n".join(issues))
        return 1
    print("MusicXML structure and measure lengths OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
