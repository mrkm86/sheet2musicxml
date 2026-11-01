---
name: transcribe
description: Convert sheet music PDFs, scans, screenshots, or photos into editable MusicXML. Use for score transcription, OMR correction, page joining, transposing instruments, chord symbols, ties, slurs, and MusicXML import errors.
---

# Transcribe sheet music to MusicXML

Produce an editable MusicXML score from the supplied image pages or PDF. Preserve the written notation, instrument order, measure structure, rhythms, pitches, chord symbols, and navigation. Treat optical music recognition (OMR) as a draft, not as evidence of accuracy.

The required output is a `.musicxml` file. MuseScore, Dorico, or another score editor may help inspect the result, but no particular editor is required. Do not make an app-native score, playback setting, or editor-specific workaround a prerequisite for MusicXML delivery. If an editor is unavailable, use source-image review and the bundled MusicXML checks; state any details that remain uncertain.

## Workflow

1. Establish page order. Render PDF pages or inspect images at a resolution that exposes accidentals, dots, beams, ties, slurs, and rests. Correct photo rotation or perspective if necessary. Record each system's measure range, staff order, key and time signatures, clefs, transpositions, repeats, rehearsal marks, and double barlines.
2. Obtain a first draft with an available OMR tool when useful, or transcribe directly from the image. Never require one named OMR model or a local installation. If a combined read confuses adjacent staves, crop and read the affected staff or system separately.
3. Compare every measure with the source. Check individual note and rest durations, not just the measure total. Resolve ambiguous pitches and accidentals from enlarged source crops. For transposing parts, compare the printed key on each page and system with the draft and inspect each resulting MusicXML `<pitch><alter>`. A printed double sharp needs `<alter>2</alter>` and, when the glyph is explicit, `<accidental>double-sharp</accidental>`.
4. Trace every source tie and slur to its endpoints. Ties must join the same sounding pitch and use both `<tie>` and `<notations><tied>`; a visual slur is not a tie. Check every pitch of a tied chord. Keep separate slurs when two arcs occur in one bar or phrase, including overlaps and system crossings. Read [notation-quality.md](references/notation-quality.md) for the detailed review criteria.
5. Build one partwise MusicXML score. Keep multi-staff instruments in one part with numbered staves unless an editor-specific export variant is requested. Place chord symbols at the harmony onset and rehearsal letters in `<rehearsal>`. Encode printed tempo with `<metronome>` and `<sound tempo="…">`; use MusicXML `<sound><swing>` for explicit swing. Read [navigation.md](references/navigation.md) when the source has segno, D.S., or coda instructions.
6. Join pages without duplicating unchanged key, meter, or clef declarations. Keep real changes. Avoid forced page breaks unless requested. Renumber measures continuously, preserving pickups and printed repeats.
7. Run the bundled checks below. Review every reported candidate against the source, then open the MusicXML in any available notation editor for an additional visual check if possible. A successful import alone does not establish note accuracy. Deliver the MusicXML and a concise list of unresolved locations, if any.

## Bundled checks

Run these scripts from this skill's `scripts/` directory with Python 3; they use only the standard library.

- `check_musicxml.py OUTPUT.musicxml`: part and measure structure, including incomplete bars.
- `check_ties.py OUTPUT.musicxml`: broken tie links and repeated-pitch candidates requiring image review.
- `check_slurs.py OUTPUT.musicxml`: slur endpoints and bars containing multiple arcs. It cannot discover a missing arc on its own.
- `audit_omr_pitches.py PAGE.musicxml OUTPUT.musicxml ...`: key and pitch differences between an OMR page and the joined score.
- `audit_chord_voicings.py OUTPUT.musicxml --harmony-part P2`: chord-tone overlap at chord changes. This is a review aid; passing notes and omissions can be correct.

The conversion workflow needs a way to read the supplied images. The optional scripts need Python 3. OMR, PDF rendering software, and notation editors are interchangeable aids rather than package dependencies.

If the user supplies a corrected MuseScore file or asks for editor-specific playback and layout review, read [editor-validation.md](references/editor-validation.md). Those checks are optional and do not change the MusicXML deliverable.
