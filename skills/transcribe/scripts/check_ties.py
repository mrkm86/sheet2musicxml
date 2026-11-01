#!/usr/bin/env python3
"""Check MusicXML tie links and list adjacent repeated pitches for visual review.

The candidate list is not a list of errors: repeated notes may be intentional.
Inspect each candidate against the source score before adding a tie.
"""

import argparse
from dataclasses import dataclass
from fractions import Fraction
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


@dataclass
class Note:
    part: str
    staff: str
    voice: str
    pitch: str
    measure: str
    beat: Fraction
    start: Fraction
    end: Fraction
    ties: set[str]
    tied: set[str]
    slurs: dict[str, set[str]]


def value(element, path, default=None):
    found = element.find(path)
    return default if found is None else found.text


def pitch_name(element):
    pitch = element.find("pitch")
    if pitch is None:
        return None
    step = value(pitch, "step", "?")
    alter = value(pitch, "alter", "0")
    accidental = {"-2": "bb", "-1": "b", "0": "", "1": "#", "2": "x"}.get(alter, f"({alter})")
    return f"{step}{accidental}{value(pitch, 'octave', '?')}"


def read_notes(path: Path):
    root = ET.parse(path).getroot()
    if root.tag != "score-partwise":
        raise ValueError("expected a score-partwise MusicXML document")
    all_notes = []
    for part in root.findall("part"):
        part_id = part.get("id", "?")
        divisions = 1
        bar_length = Fraction(4)
        bar_start = Fraction(0)
        for measure in part.findall("measure"):
            cursor = Fraction(0)
            last_start = Fraction(0)
            number = measure.get("number", "?")
            for item in measure:
                if item.tag == "attributes":
                    d = value(item, "divisions")
                    if d is not None:
                        divisions = int(d)
                    beats = value(item, "time/beats")
                    beat_type = value(item, "time/beat-type")
                    if beats and beat_type:
                        bar_length = Fraction(sum(map(int, beats.split("+"))) * 4, int(beat_type))
                elif item.tag in ("backup", "forward"):
                    amount = Fraction(int(value(item, "duration", "0")), divisions)
                    cursor += -amount if item.tag == "backup" else amount
                elif item.tag == "note" and item.find("grace") is None:
                    duration = Fraction(int(value(item, "duration", "0")), divisions)
                    chord = item.find("chord") is not None
                    onset = last_start if chord else cursor
                    if not chord:
                        last_start = onset
                        cursor += duration
                    pitch = pitch_name(item)
                    if pitch is None:
                        continue
                    slurs = {}
                    for slur in item.findall("notations/slur"):
                        slurs.setdefault(slur.get("number", "1"), set()).add(slur.get("type", "?"))
                    all_notes.append(Note(
                        part_id, value(item, "staff", "1"), value(item, "voice", "1"),
                        pitch, number, onset + 1, bar_start + onset,
                        bar_start + onset + duration,
                        {t.get("type", "?") for t in item.findall("tie")},
                        {t.get("type", "?") for t in item.findall("notations/tied")},
                        slurs,
                    ))
            bar_start += bar_length
    return all_notes


def inspect(notes):
    groups = {}
    same_staff_pitch = {}
    for note in notes:
        groups.setdefault((note.part, note.staff, note.voice, note.pitch), []).append(note)
        same_staff_pitch.setdefault((note.part, note.staff, note.pitch), []).append(note)
    candidates = []
    errors = []
    for (part, staff, voice, pitch), events in groups.items():
        events.sort(key=lambda n: (n.start, n.end))
        for index, note in enumerate(events):
            prev = events[index - 1] if index else None
            nxt = events[index + 1] if index + 1 < len(events) else None
            if note.ties != note.tied:
                errors.append(f"{part} staff {staff} m{note.measure} beat {note.beat}: "
                              f"{pitch} <tie> and <tied> differ")
            possible = same_staff_pitch[(part, staff, pitch)]
            matching_start = any(x is not note and x.end == note.start and "start" in x.ties
                                 for x in possible)
            matching_stop = any(x is not note and note.end == x.start and "stop" in x.ties
                                for x in possible)
            if "stop" in note.ties and not matching_start:
                errors.append(f"{part} staff {staff} m{note.measure} beat {note.beat}: "
                              f"{pitch} tie stop has no matching start")
            if "start" in note.ties and not matching_stop:
                errors.append(f"{part} staff {staff} m{note.measure} beat {note.beat}: "
                              f"{pitch} tie start has no matching stop")
            if nxt and note.end == nxt.start and not ("start" in note.ties and "stop" in nxt.ties):
                same_pitch_slur = any("start" in types and "stop" in nxt.slurs.get(number, set())
                                      for number, types in note.slurs.items())
                short_to_long = nxt.end - nxt.start >= 2 * (note.end - note.start)
                candidates.append({
                    "part": part, "staff": staff, "voice": voice, "pitch": pitch,
                    "from_measure": note.measure, "from_beat": str(note.beat),
                    "to_measure": nxt.measure, "to_beat": str(nxt.beat),
                    "same_pitch_slur": same_pitch_slur,
                    "short_to_long": short_to_long,
                })
    candidates.sort(key=lambda x: (int(x["from_measure"]) if x["from_measure"].isdigit() else 0,
                                   x["part"], x["staff"], Fraction(x["from_beat"]), x["pitch"]))
    return candidates, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("musicxml", type=Path)
    parser.add_argument("--json", action="store_true", help="machine-readable candidate and error list")
    parser.add_argument("--strict", action="store_true", help="fail if review candidates remain")
    args = parser.parse_args()
    try:
        candidates, errors = inspect(read_notes(args.musicxml))
    except (OSError, ValueError, ZeroDivisionError, ET.ParseError) as exc:
        print(f"cannot inspect ties: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"candidates": candidates, "errors": errors}, ensure_ascii=False, indent=2))
    else:
        print(f"broken tie links: {len(errors)}; repeated-pitch review candidates: {len(candidates)}")
        for error in errors:
            print("ERROR", error)
        for c in candidates:
            slur = " [same-pitch slur]" if c["same_pitch_slur"] else ""
            sustain = " [short-to-long]" if c["short_to_long"] else ""
            print(f"REVIEW {c['part']} staff {c['staff']} {c['pitch']}: "
                  f"m{c['from_measure']} beat {c['from_beat']} → "
                  f"m{c['to_measure']} beat {c['to_beat']}{slur}{sustain}")
    return 1 if errors or (args.strict and candidates) else 0


if __name__ == "__main__":
    raise SystemExit(main())
