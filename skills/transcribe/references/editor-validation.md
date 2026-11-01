# Optional editor validation

The core deliverable remains MusicXML. Use these checks only when the named editor is available or the user supplies its native score. Do not require MuseScore or Dorico to transcribe an image.

## MuseScore

- Import the MusicXML and compare its rendered systems with the source image. Check the lower piano staff as well as the upper staff: a double barline in a multi-staff MusicXML part may import onto only the upper staff in some MuseScore versions. `scripts/optional_musescore/check_barlines.py IMPORTED.mscz` compares the barline states in a MuseScore 3 native file.
- If the user supplies a corrected `.mscz` or `.mscx`, preserve it separately and run `scripts/optional_musescore/compare_mscx.py BEFORE.mscz AFTER.mscz` to identify musical changes by staff and measure. The comparison includes notes, accidentals, slurs, chord symbols, and barlines. Do not overwrite the user's corrected score.
- If chord symbols should display without sounding, keep them as semantic Harmony elements. In a MuseScore native score, disable each Harmony's playback. That native setting is not carried by a MusicXML export; importing the same XML in a different editor may restore chord playback. Do not replace editable chord symbols with plain staff text unless the user explicitly accepts that loss.
- Playback navigation may need app-specific repair after import. Preserve the portable MusicXML and verify the jump route only when playback was requested.

## Other editors

An editor can give useful visual evidence, but its import behavior may differ. Check the rendered score against the source and report any feature the editor dropped. Do not infer that MusicXML itself is wrong solely from an editor-specific playback or layout setting.
