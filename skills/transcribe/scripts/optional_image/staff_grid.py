"""Overlay labelled pitch lines on a crop of a photographed or scanned score.

Tracks each five-line staff column by column, so tilted and curved staves from
phone photos keep accurate guides. Every line and space position is drawn and
labelled with its note name, which makes it practical to read notes on ledger
lines and dense chords from an enlarged crop.

Requires Pillow and NumPy (optional dependencies, not used by the core checks).

Example:
    python3 staff_grid.py page.png 400 600 900 420 out.png --clefs G
    python3 staff_grid.py page.png 400 500 900 700 out.png --clefs G,F --scale 2
"""

import argparse

import numpy as np
from PIL import Image, ImageDraw, ImageFont

LETTERS = "CDEFGAB"
# (letter index, octave) of the top staff line for each clef
TOP_LINE = {"G": (3, 5), "F": (5, 3), "C": (4, 4)}


def find_staves(dark, band, min_gap):
    """Return {staff_index: [(x_centre, top_line_y, spacing), ...]}."""
    height, width = dark.shape
    tracks = {}
    for bx in range(0, width - band, max(band // 2, 1)):
        profile = dark[:, bx:bx + band].mean(axis=1)
        rows = np.where(profile > 0.55)[0]
        if len(rows) < 5:
            continue
        groups = [[rows[0]]]
        for row in rows[1:]:
            if row - groups[-1][-1] <= 2:
                groups[-1].append(row)
            else:
                groups.append([row])
        centres = [float(np.mean(g)) for g in groups]
        found, i = [], 0
        while i <= len(centres) - 5:
            gaps = np.diff(centres[i:i + 5])
            if gaps.min() > min_gap and gaps.max() - gaps.min() < 0.2 * gaps.mean():
                found.append((centres[i], float(gaps.mean())))
                i += 5
            else:
                i += 1
        for top, spacing in found:
            tracks.setdefault("all", []).append((bx + band / 2, top, spacing))
    return tracks.get("all", [])


def assign_staves(detections, count):
    """Group detections into `count` staves by vertical position.

    A column crossed by a dense chord or stem may miss one staff, so detections
    are matched to the nearest staff band instead of by their order in the column.
    """
    if not detections:
        return {}
    tops = sorted(d[1] for d in detections)
    spacing = float(np.median([d[2] for d in detections]))
    clusters = [[tops[0]]]
    for t in tops[1:]:
        if t - clusters[-1][-1] > 3 * spacing:
            clusters.append([t])
        else:
            clusters[-1].append(t)
    clusters.sort(key=len, reverse=True)
    centres = sorted(float(np.median(c)) for c in clusters[:count])
    staves = {}
    for x, top, sp in detections:
        k = int(np.argmin([abs(top - c) for c in centres]))
        if abs(top - centres[k]) < 2 * spacing:
            staves.setdefault(k, []).append((x, top, sp))
    for k in staves:
        staves[k].sort()
    return staves


def reject_outliers(points):
    xs, tops, sps = (np.array(v) for v in zip(*points))
    keep = np.ones(len(xs), bool)
    for i in range(len(xs)):
        lo, hi = max(0, i - 12), min(len(xs), i + 13)
        if abs(tops[i] - np.median(tops[lo:hi])) > 4 or abs(sps[i] - np.median(sps[lo:hi])) > 1.5:
            keep[i] = False
    return xs[keep], tops[keep], sps[keep]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("image")
    parser.add_argument("x", type=int)
    parser.add_argument("y", type=int)
    parser.add_argument("w", type=int)
    parser.add_argument("h", type=int)
    parser.add_argument("output")
    parser.add_argument("--clefs", default="G", help="clef per staff, top to bottom, e.g. G or G,F")
    parser.add_argument("--scale", type=float, default=2.0)
    parser.add_argument("--threshold", type=int, default=120, help="grey level counted as ink")
    parser.add_argument("--min-gap", type=float, default=8.0, help="minimum staff-line spacing in pixels")
    args = parser.parse_args()

    crop = Image.open(args.image).convert("L").crop((args.x, args.y, args.x + args.w, args.y + args.h))
    dark = np.asarray(crop) < args.threshold
    height, width = dark.shape
    clefs = args.clefs.split(",")
    tracks = assign_staves(find_staves(dark, 10, args.min_gap), len(clefs))

    big = crop.convert("RGB").resize((int(width * args.scale), int(height * args.scale)), Image.LANCZOS)
    draw = ImageDraw.Draw(big, "RGBA")
    try:
        font = ImageFont.truetype("Arial.ttf", 14)
    except OSError:
        font = ImageFont.load_default()

    for k, clef in enumerate(clefs):
        points = tracks.get(k, [])
        if len(points) < 4:
            print(f"staff {k + 1} ({clef}) not found; widen the crop or adjust --min-gap")
            continue
        xs, tops, sps = reject_outliers(points)
        cols = np.arange(width)
        top = np.interp(cols, xs, tops)
        spacing = np.interp(cols, xs, sps)
        letter0, octave0 = TOP_LINE[clef]
        for n in range(-7, 16):  # half-steps below the top line
            index = letter0 - n
            label = f"{LETTERS[index % 7]}{octave0 + index // 7}"
            colour = (0, 90, 255, 90) if n % 2 == 0 else (255, 0, 60, 70)
            line = [(c * args.scale, (top[c] + n * spacing[c] / 2) * args.scale) for c in range(0, width, 6)]
            draw.line(line, fill=colour, width=1)
            for frac in np.linspace(0.01, 0.97, 4):
                c = int(width * frac)
                draw.text((c * args.scale, (top[c] + n * spacing[c] / 2) * args.scale - 8),
                          label, fill=(220, 0, 0, 220), font=font)
        print(f"staff {k + 1} ({clef}): spacing {float(np.median(sps)):.1f}px")
    big.save(args.output)


if __name__ == "__main__":
    main()
