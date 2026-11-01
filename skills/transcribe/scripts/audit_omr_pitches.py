#!/usr/bin/env python3
"""List pitch risks when an OMR page is joined into a MusicXML score.

This is a review aid: a key exception or pitch difference needs comparison with
the printed score. It cannot decide whether an accidental is musically correct.
"""

import argparse
from collections import Counter
from xml.etree import ElementTree as ET


SHARPS = "FCGDAEB"
FLATS = "BEADGCF"


def part_and_measures(path, part_id):
    root = ET.parse(path).getroot()
    part = root.find(f"./part[@id='{part_id}']")
    if part is None:
        raise ValueError(f"part {part_id} is absent from {path}")
    return part.findall("measure")


def key_at(measures, index):
    key = None
    for measure in measures[: index + 1]:
        value = measure.findtext("attributes/key/fifths")
        if value is not None:
            key = int(value)
    return key


def key_alter(step, fifths):
    if fifths is None:
        return None
    if fifths > 0:
        return 1 if step in SHARPS[:fifths] else 0
    if fifths < 0:
        return -1 if step in FLATS[: -fifths] else 0
    return 0


def notes(measure, staff):
    result = []
    for note in measure.findall("note"):
        if staff and note.findtext("staff", "1") != staff:
            continue
        pitch = note.find("pitch")
        if pitch is None:
            result.append(("rest", None, None, note.find("grace") is not None))
            continue
        result.append(
            (
                pitch.findtext("step"),
                int(pitch.findtext("alter", "0")),
                int(pitch.findtext("octave")),
                note.find("grace") is not None,
            )
        )
    return result


def label(item):
    step, alter, octave, grace = item
    if step == "rest":
        return "rest"
    accidental = {1: "#", -1: "b", 0: ""}.get(alter, f"({alter:+})")
    return f"{step}{accidental}{octave}{' grace' if grace else ''}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="OMR page MusicXML")
    parser.add_argument("target", help="joined or corrected MusicXML")
    parser.add_argument("--source-part", required=True)
    parser.add_argument("--target-part", required=True)
    parser.add_argument("--target-start", required=True, type=int,
                        help="target measure containing source measure 1")
    parser.add_argument("--source-staff", help="staff number in a mixed OMR part")
    parser.add_argument("--target-staff", help="staff number in target part")
    parser.add_argument("--source-count", type=int,
                        help="number of source measures to compare when an OMR crop has trailing extras")
    args = parser.parse_args()

    source = part_and_measures(args.source, args.source_part)
    if args.source_count is not None:
        if args.source_count < 1 or args.source_count > len(source):
            parser.error("source-count must be within the source measure range")
        source = source[:args.source_count]
    target = part_and_measures(args.target, args.target_part)
    if args.target_start < 1 or args.target_start + len(source) - 1 > len(target):
        parser.error("source measures extend beyond the target part")

    counts = Counter()
    for i, sm in enumerate(source):
        target_number = args.target_start + i
        tm = target[target_number - 1]
        skey = key_at(source, i)
        tkey = key_at(target, target_number - 1)
        src = notes(sm, args.source_staff)
        dst = notes(tm, args.target_staff)
        if skey != tkey:
            changed = [s for s in "ABCDEFG" if key_alter(s, skey) != key_alter(s, tkey)]
            hits = [f"{j}:{label(p)}" for j, p in enumerate(src, 1) if p[0] in changed]
            print(f"m{target_number} KEY {skey} -> {tkey}; affected {','.join(changed)}; source notes {', '.join(hits) or 'none'}")
            counts["key_mismatch_measures"] += 1
        if len(src) != len(dst):
            print(f"m{target_number} COUNT {len(src)} -> {len(dst)}")
            counts["count_mismatch_measures"] += 1
        for j, (a, b) in enumerate(zip(src, dst), 1):
            if a != b:
                print(f"m{target_number} note {j}: {label(a)} -> {label(b)}")
                counts["changed_notes"] += 1
        exceptions = [f"{j}:{label(p)}" for j, p in enumerate(src, 1)
                      if p[0] != "rest" and key_alter(p[0], skey) != p[1]]
        if exceptions:
            print(f"m{target_number} OMR key exceptions: {', '.join(exceptions)}")
            counts["key_exception_measures"] += 1
    print("SUMMARY " + " ".join(f"{k}={counts[k]}" for k in
          ("key_mismatch_measures", "count_mismatch_measures", "changed_notes", "key_exception_measures")))


if __name__ == "__main__":
    main()
