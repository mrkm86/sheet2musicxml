"""List MusicXML slur spans, including bars with two or more slurs.

This checks encoding and supports comparison with the printed arcs. It cannot
discover an arc that was omitted from both OCR and MusicXML.
"""

import argparse
from collections import Counter
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('musicxml')
    args = parser.parse_args()
    root = ET.parse(args.musicxml).getroot()
    total = 0
    problems = []
    for part in root.findall('part'):
        active = {}
        starts_by_bar = Counter()
        spans = []
        for measure in part.findall('measure'):
            bar = measure.get('number')
            for note_index, note in enumerate(measure.findall('note'), 1):
                staff = note.findtext('staff', '1')
                pitch = note.find('pitch')
                label = ('rest' if pitch is None else
                         f'{pitch.findtext("step")}{pitch.findtext("alter", "0")}/{pitch.findtext("octave")}')
                position = f'm{bar} note{note_index} {label}'
                slurs = note.findall('notations/slur')
                # A note can stop one phrase and start the next.
                for slur in sorted(slurs, key=lambda s: 0 if s.get('type') == 'stop' else 1):
                    key = (staff, slur.get('number', '1'))
                    if slur.get('type') == 'stop':
                        start = active.pop(key, None)
                        if start is None:
                            problems.append(f'{part.get("id")} {position}: stop without start (staff {staff}, number {key[1]})')
                        else:
                            spans.append((start, position))
                    elif slur.get('type') == 'start':
                        if key in active:
                            problems.append(f'{part.get("id")} {position}: start before prior stop (staff {staff}, number {key[1]})')
                        active[key] = position
                        starts_by_bar[bar] += 1
        for key, start in active.items():
            problems.append(f'{part.get("id")} {start}: start without stop (staff {key[0]}, number {key[1]})')
        total += len(spans)
        print(f'{part.get("id")}: {len(spans)} complete slurs')
        for bar, count in starts_by_bar.items():
            if count >= 2:
                print(f'  m{bar}: {count} slur starts; inspect every arc in the source')
        for start, stop in spans:
            print(f'  {start} -> {stop}')
    print(f'SUMMARY: {total} complete slurs; {len(problems)} encoding problems')
    for problem in problems:
        print('ERROR', problem)
    if problems:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
