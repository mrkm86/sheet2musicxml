# MusicXML navigation

Use visual direction elements and playback `<sound>` attributes together. These identifiers must match:

```xml
<direction><direction-type><segno/></direction-type><sound segno="segno"/></direction>
<direction><direction-type><words>To Coda</words></direction-type><sound tocoda="coda"/></direction>
<direction><direction-type><words>D.S. to D</words></direction-type><sound dalsegno="segno"/></direction>
<direction><direction-type><coda/></direction-type><sound coda="coda"/></direction>
```

Place a D.S. direction at the end of the measure where the jump occurs. Place To Coda at the actual jump point shown in the source; do not infer it from page boundaries. Keep rehearsal letters in separate `<rehearsal>` elements, even when a segno appears at the same place. For a plain D.S. without a coda, omit the To Coda and Coda directions.

Notation editors may import the visible jump while dropping some playback behavior. If the user also requests verified playback, inspect the imported score's jump properties and play through the route or export MIDI. Keep the MusicXML as the portable source.

References: [W3C MusicXML `<sound>`](https://www.w3.org/2021/06/musicxml40/musicxml-reference/elements/sound/), [W3C `<segno>`](https://www.w3.org/2021/06/musicxml40/musicxml-reference/elements/segno/).
