"""Compare the main score in two MuseScore 3 MSCX/MSCZ files.

Ignores linked part scores and per-element link IDs, which obscure musical edits.
"""

import argparse
import io
import xml.etree.ElementTree as ET
from collections import Counter
from zipfile import ZipFile

def score(path):
    if str(path).lower().endswith('.mscz'):
        with ZipFile(path) as archive:
            name = next(n for n in archive.namelist() if n.endswith('.mscx'))
            root = ET.parse(io.BytesIO(archive.read(name))).getroot()
    else:
        root = ET.parse(path).getroot()
    result = root.find('Score')
    if result is None:
        raise ValueError(f'Main MuseScore score not found in {path}')
    return result

def staves(s):
    return {int(st.get('id')): st.findall('Measure') for st in s.findall('Staff')}

def chord_item(x):
    notes = []
    for n in x.findall('Note'):
        notes.append((n.findtext('pitch'), n.findtext('tpc'),
                      tuple(sorted(t.get('type', '') for t in n.findall('Spanner') if t.get('type') == 'Tie')),
                      tuple((a.tag, a.findtext('subtype')) for a in n.findall('Accidental'))))
    slurs = []
    for spanner in x.findall('Spanner'):
        if spanner.get('type') == 'Slur':
            slurs.append(('start' if spanner.find('Slur') is not None else 'stop',
                          spanner.findtext('next/location/fractions') or spanner.findtext('prev/location/fractions')))
    return (x.tag, x.findtext('durationType'), x.findtext('dots'), x.findtext('duration'),
            tuple(notes), tuple(slurs))

def harmony_item(x, event_index):
    return (event_index, x.findtext('root'), x.findtext('name'), x.findtext('base'),
            x.findtext('extension'), tuple((y.tag, y.text) for y in x if y.tag not in ('root','name','base','extension','linkedMain','linked')))

def measure_data(m):
    notes, harmonies, barlines, directions, layouts = [], [], [], [], []
    for voice in m.findall('voice'):
        event_index = 0
        for x in voice:
            if x.tag in ('Chord', 'Rest'):
                notes.append(chord_item(x));event_index += 1
            elif x.tag == 'Harmony':
                harmonies.append(harmony_item(x, event_index))
            elif x.tag == 'BarLine':
                barlines.append((event_index, x.findtext('subtype')))
            elif x.tag in ('RehearsalMark', 'Dynamic', 'Tempo', 'Jump', 'Marker', 'Text', 'StaffText'):
                directions.append((event_index,x.tag,x.findtext('text'),x.findtext('subtype')))
            elif x.tag == 'location':
                layouts.append(('location', ET.tostring(x, encoding='unicode').strip()))
    for x in m:
        if x.tag in ('LayoutBreak','stretch'):
            layouts.append((x.tag,x.findtext('subtype') or x.text))
    return dict(notes=notes,harmonies=harmonies,barlines=barlines,directions=directions,layouts=layouts)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', help='Original .mscz or .mscx')
    parser.add_argument('after', help='Corrected .mscz or .mscx')
    parser.add_argument('--layout', action='store_true', help='Include line breaks and spacing')
    args = parser.parse_args()
    old, new = staves(score(args.before)), staves(score(args.after))
    if old.keys() != new.keys():
        raise ValueError(f'Staff IDs differ: {sorted(old)} vs {sorted(new)}')
    for staff in sorted(old):
        print(f'\n=== STAFF {staff} ({len(old[staff])} -> {len(new[staff])} measures) ===')
        totals = Counter()
        for i, (a, b) in enumerate(zip(old[staff], new[staff]), 1):
            da, db = measure_data(a), measure_data(b)
            changed = [k for k in da if da[k] != db[k] and (args.layout or k != 'layouts')]
            if not changed:
                continue
            for k in changed:
                totals[k] += 1
            print(f'm{i}:', ','.join(changed))
            for k in changed:
                if k == 'notes':
                    aa, bb = da[k], db[k]
                    print('  notes length', len(aa), '->', len(bb))
                    for j in range(max(len(aa), len(bb))):
                        u = aa[j] if j < len(aa) else None
                        v = bb[j] if j < len(bb) else None
                        if u != v:
                            print('   ', j, u, '=>', v)
                else:
                    print(' ', k, 'BEFORE:', da[k])
                    print(' ', k, 'AFTER:', db[k])
        print('TOTALS', dict(totals))

if __name__ == '__main__':
    main()
