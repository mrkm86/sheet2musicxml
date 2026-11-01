# Notation review

Use the source image as the authority. OMR and harmonic plausibility are evidence, not substitutes for reading the notation.

## Pitches and accidentals

- Record the printed key separately for each instrument and each page or system. Mixed-staff OMR may copy a transposing part's key into piano or drop one sharp from the melody.
- MusicXML `<pitch><alter>` stores the note's actual alteration. Fixing `<key>` alone does not fix a wrong note.
- Enlarge faint accidental glyphs. A double-sharp `×` can be mistaken for a natural, a single sharp, or no accidental. Check both the written pitch spelling and the resulting sounding pitch after transposition.
- Review octave jumps and grace notes separately from accidental changes.

## Rhythm, ties, and slurs

- Check each note and rest value, beams, dots, tuplets, and voices against the source. A measure may add up correctly while one beamed group is wrong.
- Review every adjacent repeated-pitch pair as a possible tie, especially a short note followed by a longer one. Do not add a tie solely because pitches repeat.
- A real tie needs `<tie type="start|stop">` and matching `<notations><tied type="start|stop"/>` on each tied pitch. A phrase slur uses `<notations><slur .../>` instead. A same-pitch slur with intervening notes usually remains a slur.
- Trace every printed slur from first to last note. Count each arc when two appear in one bar, overlap, or cross a system. A balanced start/stop count only proves that encoded slurs link up; it cannot prove that no slur was omitted.

## Harmony, form, and delivery

- Place a chord label on the beat where its harmony begins. When two harmonies each last two beats in 4/4, their labels belong on beats 1 and 3. Do not repeat an unchanged chord in the next bar unless the source does.
- Use `audit_chord_voicings.py` to prioritize review of accompaniment pitches that poorly overlap the printed chord. Inversions, rootless voicings, suspensions, passing tones, and pedal tones can explain low overlap. Never rewrite notes automatically from the chord label.
- Keep rehearsal letters as rehearsal marks, not generic text. Preserve repeats, navigation, and double barlines shown in the source.
- When an optional notation editor is available, import the final MusicXML and compare its rendered systems with the source. Playback options such as silent chord-symbol display are editor-specific and should be handled only when requested.
