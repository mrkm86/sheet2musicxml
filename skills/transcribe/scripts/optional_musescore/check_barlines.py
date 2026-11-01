#!/usr/bin/env python3
"""Check that explicit double barlines appear on every score staff.

Inspect a MuseScore .mscz or .mscx after importing MusicXML. A MusicXML
barline belongs to a part, so its XML alone cannot show which piano staff
MuseScore actually drew it on.
"""

import argparse
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile


def read_score(path: Path):
    if path.suffix.lower() == ".mscz":
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist() if name.endswith(".mscx")]
            if len(names) != 1:
                raise ValueError(f"expected one .mscx in archive; found {len(names)}")
            return ET.fromstring(archive.read(names[0]))
    if path.suffix.lower() == ".mscx":
        return ET.parse(path).getroot()
    raise ValueError("expected .mscz or .mscx (check the editor's imported score)")


def inspect(root, scope: str):
    score = root.find("Score")
    if score is None:
        raise ValueError("no main Score element")
    part_staff_ids = [[s.get("id") for s in p.findall("Staff")]
                      for p in score.findall("Part")]
    staves = {s.get("id"): s.findall("Measure") for s in score.findall("Staff")}
    if not staves:
        raise ValueError("no score staves")
    lengths = {len(measures) for measures in staves.values()}
    if len(lengths) != 1:
        raise ValueError(f"staff measure counts differ: {sorted(lengths)}")
    groups = [list(staves)] if scope == "score" else part_staff_ids
    issues = []
    checked = set()
    for group in groups:
        for index in range(next(iter(lengths))):
            kinds = {}
            for staff_id in group:
                measure = staves[staff_id][index]
                kinds[staff_id] = [b.findtext("subtype", "normal")
                                   for b in measure.findall(".//BarLine")]
            if not any("double" in values for values in kinds.values()):
                continue
            checked.add(index + 1)
            for staff_id, values in kinds.items():
                if "double" not in values:
                    issues.append(f"measure {index + 1}, staff {staff_id}: "
                                  "double barline missing")
    return sorted(checked), issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("score", type=Path)
    parser.add_argument("--scope", choices=("score", "part"), default="score",
                        help="compare every staff, or only staves within each part")
    args = parser.parse_args()
    try:
        bars, issues = inspect(read_score(args.score), args.scope)
    except (OSError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"cannot inspect barlines: {exc}", file=sys.stderr)
        return 2
    print("double barline measures:", ", ".join(map(str, bars)) or "none")
    if issues:
        print("\n".join(issues))
        return 1
    print("double barlines match on all checked staves")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
