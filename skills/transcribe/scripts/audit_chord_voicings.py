"""List harmony/accompaniment pitch-class mismatches for visual review.

This is a heuristic, not a validator: inversions, omitted tones, passing notes,
pedal tones, and suspensions can all be intentional. Use the printed score to
decide whether a flagged note is wrong.
"""

import argparse
from fractions import Fraction
import xml.etree.ElementTree as ET


PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
INTERVALS = {
    'major': (0, 4, 7),
    'minor': (0, 3, 7),
    'dominant': (0, 4, 7, 10),
    'major-seventh': (0, 4, 7, 11),
    'minor-seventh': (0, 3, 7, 10),
    'half-diminished': (0, 3, 6, 10),
    'diminished': (0, 3, 6),
    'diminished-seventh': (0, 3, 6, 9),
    'augmented': (0, 4, 8),
}
KINDS = {'major': '', 'minor': 'm', 'dominant': '7', 'major-seventh': 'maj7',
         'minor-seventh': 'm7', 'half-diminished': 'm7(b5)',
         'diminished': 'dim', 'diminished-seventh': 'dim7', 'augmented': 'aug'}


def pitch_class(node):
    pitch = node.find('pitch')
    if pitch is None:
        return None
    return (PC[pitch.findtext('step')] + int(pitch.findtext('alter', '0'))) % 12


def root_class(harmony, element):
    root = harmony.find(element)
    if root is None:
        return None
    step = root.findtext(f'{element}-step')
    if step not in PC:
        return None
    return (PC[step] + int(root.findtext(f'{element}-alter', '0'))) % 12


def scan_measure(measure, divisions):
    cursor = Fraction(0)
    last_onset = Fraction(0)
    notes, harmonies = [], []
    for element in measure:
        if element.tag == 'attributes':
            divisions = int(element.findtext('divisions') or divisions)
        elif element.tag == 'backup':
            cursor -= Fraction(int(element.findtext('duration')), divisions)
        elif element.tag == 'forward':
            cursor += Fraction(int(element.findtext('duration')), divisions)
        elif element.tag == 'harmony':
            offset = Fraction(int(element.findtext('offset', '0')), divisions)
            harmonies.append((cursor + offset, element))
        elif element.tag == 'note':
            onset = last_onset if element.find('chord') is not None else cursor
            pc = pitch_class(element)
            if pc is not None:
                notes.append((onset, pc, element.findtext('staff', '1')))
            if element.find('chord') is None:
                last_onset = cursor
                cursor += Fraction(int(element.findtext('duration', '0')), divisions)
    return divisions, notes, harmonies


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('musicxml')
    parser.add_argument('--harmony-part', required=True, help='Part ID containing chord symbols, e.g. P2')
    parser.add_argument('--accompaniment-parts', nargs='+', help='Part IDs to compare (default: harmony part)')
    parser.add_argument('--max-rows', type=int, default=50)
    args = parser.parse_args()
    tree = ET.parse(args.musicxml)
    parts = {part.get('id'): part for part in tree.getroot().findall('part')}
    if args.harmony_part not in parts:
        parser.error(f'No part {args.harmony_part}')
    accompaniment = args.accompaniment_parts or [args.harmony_part]
    for part in accompaniment:
        if part not in parts:
            parser.error(f'No part {part}')
    by_measure = {}
    for part_id in set(accompaniment + [args.harmony_part]):
        divisions = 1
        for ordinal, measure in enumerate(parts[part_id].findall('measure')):
            divisions, notes, harmonies = scan_measure(measure, divisions)
            by_measure[(part_id, ordinal)] = (notes, harmonies)
    report = []
    for ordinal, measure in enumerate(parts[args.harmony_part].findall('measure')):
        harmonies = by_measure[(args.harmony_part, ordinal)][1]
        for onset, harmony in harmonies:
            kind = harmony.findtext('kind')
            root = root_class(harmony, 'root')
            if root is None or kind not in INTERVALS:
                continue
            expected = {(root + interval) % 12 for interval in INTERVALS[kind]}
            simultaneous = []
            for part_id in accompaniment:
                simultaneous.extend(pc for note_onset, pc, _ in by_measure[(part_id, ordinal)][0]
                                    if note_onset == onset)
            if not simultaneous:
                continue
            unexpected = sorted(set(simultaneous) - expected)
            overlap = len([pc for pc in simultaneous if pc in expected]) / len(simultaneous)
            bass = root_class(harmony, 'bass')
            label = NAMES[root] + KINDS[kind]
            if bass is not None:
                label += '/' + NAMES[bass]
            # Rank by likely mismatch, but print every chord so a musician can
            # review the whole progression rather than trust a binary verdict.
            report.append((overlap, ordinal + 1, onset + 1, label, simultaneous, unexpected, bass))
    report.sort(key=lambda row: (row[0], row[1], row[2]))
    for overlap, bar, beat, label, played, unexpected, bass in report[:args.max_rows]:
        suffix = ' [slash bass; check lowest note]' if bass is not None else ''
        print(f'm{bar} beat {beat}: {label} chord-tone {overlap:.0%}; '
              f'onset={",".join(NAMES[pc] for pc in played)}; '
              f'outside={",".join(NAMES[pc] for pc in unexpected) or "none"}{suffix}')
    print(f'SUMMARY: {len(report)} chord onsets checked; '
          f'{sum(row[0] < 0.5 for row in report)} have <50% chord tones at onset. '
          'All flags require score review.')


if __name__ == '__main__':
    main()
