---
name: Clip Curator
description: An editor's cutting bench for an AI clip-curation pipeline; kept clips on select reels, cut clips on pins in the trim bin.
colors:
  bench: "#e6e5e2"
  panel: "#f3f2ef"
  rule: "#cfcdc8"
  rule-strong: "#a9a6a0"
  ink: "#1e1e1f"
  ink-2: "#46464a"
  ink-3: "#5f5f65"
  film: "#151516"
  film-2: "#2a2a2c"
  sprocket: "#e6e5e2"
  tape: "#c4175a"
  tape-fill: "#ff3d8b"
  tape-on: "#111112"
  pencil: "#1e1e1f"
  bench-dark: "#232325"
  panel-dark: "#2c2c2f"
  rule-dark: "#3b3b3f"
  rule-strong-dark: "#5b5b61"
  ink-dark: "#f1f0ee"
  ink-2-dark: "#c9c8c4"
  ink-3-dark: "#9d9c98"
  film-dark: "#0c0c0d"
  film-2-dark: "#1b1b1d"
  sprocket-dark: "#3a3a3e"
  tape-dark: "#ff6aa6"
  pencil-dark: "#f6f5f2"
typography:
  display:
    fontFamily: "Schibsted Grotesk, system-ui, sans-serif"
    fontSize: "clamp(30px, 4.4vw, 48px)"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "Schibsted Grotesk, system-ui, sans-serif"
    fontSize: "24px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Schibsted Grotesk, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 600
  body:
    fontFamily: "Schibsted Grotesk, system-ui, sans-serif"
    fontSize: "15.5px"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Schibsted Grotesk, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 600
  data:
    fontFamily: "Azeret Mono, ui-monospace, Menlo, monospace"
    fontSize: "13px"
    fontWeight: 400
  pencil-slate:
    fontFamily: "Kalam, Segoe Print, cursive"
    fontSize: "clamp(19px, 2.2vw, 26px)"
    fontWeight: 700
    lineHeight: 1.35
  pencil-tag:
    fontFamily: "Kalam, Segoe Print, cursive"
    fontSize: "17px"
    fontWeight: 700
    lineHeight: 1.15
rounded:
  none: "0px"
spacing:
  xs: "6px"
  sm: "10px"
  md: "16px"
  lg: "22px"
  section: "34px"
components:
  tape:
    backgroundColor: "{colors.tape-fill}"
    textColor: "{colors.tape-on}"
    rounded: "{rounded.none}"
    padding: "4px 10px"
  slate:
    backgroundColor: "{colors.film}"
    textColor: "{colors.pencil-dark}"
    typography: "{typography.pencil-slate}"
    padding: "16px 20px 14px"
  reel-strip:
    backgroundColor: "{colors.film}"
    padding: "14px 0"
  reel-frame:
    backgroundColor: "{colors.film-2}"
    width: "118px"
  panel-card:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "14px 16px 16px"
  meter-track:
    backgroundColor: "{colors.bench}"
    height: "10px"
  button-theme:
    backgroundColor: "transparent"
    textColor: "{colors.ink-2}"
    typography: "{typography.label}"
    padding: "4px 10px"
---

# Design System: Clip Curator

## Overview

**Creative North Star: "The Cutting Bench"**

The page is a film editor's bench seen from above: a graphite (dark) or light-table grey (light) worktop, strips of black film base punched with sprocket holes, white or graphite grease pencil for anything an editor would scrawl, and one roll of hot-pink splicing tape. Kept footage runs along select reels; cut footage hangs on pins in a trim bin; a loupe sits beside the work to inspect a single frame; a ruled log sheet keeps the score.

Everything is square-cornered and flat. Depth comes from material contrast (black film on a pale bench, a paler panel sheet on the bench), never from drop shadows. Density is that of a working document: small mono figures, ruled lines, real thumbnails as the dominant imagery.

**Key Characteristics:**
- Black film strips with CSS sprocket rows top and bottom, carrying real 16:9 frames.
- Grease-pencil Kalam for hand marks only; Schibsted Grotesk for reading; Azeret Mono for counts and measurements.
- Hot-pink tape is the single accent, slightly askew, used for highlights, selection and links.
- Zero radius, 1px rules, no shadows.
- Light and dark themes share one structure; the tape and pencil flip for contrast.

## Colors

A near-neutral graphite scale with black film and one saturated pink.

### Primary
- **Splicing Tape Pink** (tape-fill): the tape strip background, selected-frame outline, the highlighted meter fill and text selection. Same fill in both themes; text on it is always near-black (tape-on).
- **Deep Tape** (tape / tape-dark): the text-weight version of the pink for links and the focus ring, darkened in light theme and lightened in dark theme to hold AA on the bench.

### Neutral
- **Light-Table Grey / Graphite Bench** (bench / bench-dark): page ground and meter track.
- **Log Paper** (panel / panel-dark): the sheet under the trim bin, loupe, log and cards.
- **Ruled Line** (rule, rule-strong): 1px panel borders and the heavier log/header rules; rule-strong also draws the trim-bin rail.
- **Ink ramp** (ink, ink-2, ink-3): headings, body/deks, tertiary metadata.
- **Film Base** (film, film-2): reel strips, slate, loupe frame well, thumbnail borders; film-2 is the empty-frame fill.
- **Sprocket** (sprocket): the punched holes, matching the bench so they read as holes through the film.
- **Grease Pencil** (pencil / pencil-dark): Kalam marks; graphite on light, white on dark. The slate always uses the white pencil because it sits on film.

### Named Rules
**The One Tape Rule.** Pink is the only hue on the page. No blue, orange, green, plum, lime, rust or yellow; status is said in words and by placement, never by a second colour.

**The Holes Are Bench Rule.** Sprocket holes are the bench colour showing through the film, not a decoration colour.

## Typography

**Body Font:** Schibsted Grotesk (with system-ui)
**Label/Mono Font:** Azeret Mono (with ui-monospace, Menlo)
**Hand Font:** Kalam 700 (with Segoe Print, cursive)

**Character:** A sturdy, slightly condensed grotesk for reading, a wide technical mono for every number, and a marker hand for what an editor would write on the film.

### Hierarchy
- **Display** (700, clamp 30-48px, 1, -0.03em): the project name only.
- **Headline** (700, 24px, 1.2, -0.02em): section heads naming bench objects ("The select reels", "The trim bin").
- **Title** (600, 15-16px): reel names, card heads; loupe clip ID in mono 600 15px.
- **Body** (400, 15.5px, 1.55): lede at 16.5px capped at 64ch; deks in ink-2 capped at 74ch.
- **Label** (600, 12px): log column heads, theme button.
- **Data** (Azeret Mono 400-600, 11.5-13px): counts, thresholds, measurements, footer.
- **Pencil** (Kalam 700, 14-26px): slate tally, pin tags, trim captions, "ref" marks, loupe verdict note, log recall/precision.

### Named Rules
**The Pencil Is Marks Rule.** Kalam is for marks an editor would write on film or the log: the slate, tags, captions, ref marks and the pencilled recall/precision. Never headings, body copy, labels or controls.

**The Numbers Are Mono Rule.** Every count and measurement sets in Azeret Mono, except where it is a pencil mark.

## Layout

A single 1360px column with fluid side padding (clamp 16-36px). Sections step down a fixed order: header and slate, then a two-column bench (reels and trim bin on the left, a 340px sticky loupe on the right, 22px gap), then the full-width log sheet, a two-card row, the pipeline strip, sources and footer. Section heads sit 34px below the previous block.

At 1080px and below the bench collapses to one column and the loupe is not sticky; it moves directly under the reel or pin the reader tapped. At 900px the card row and pipeline strip stack; at 600px reel frames shrink from 118px to 92px; at 520px meters put the track on its own row. Reels and the log scroll horizontally inside their own containers rather than squeezing.

## Elevation & Depth

Flat. There are no drop shadows. Depth is material: black film on a pale bench, a paler panel sheet framed by a 1px rule. The only shadow-like values are functional: a 3px panel-coloured ring knocking the pin head out of the rail, and a soft 3px dark halo keeping the white "ref" mark legible on bright frames.

### Named Rules
**The Material Not Shadow Rule.** Separate layers by material and rule lines; never by elevation.

## Shapes

Square corners throughout (0px), including buttons, cards, frames and tape. The only circles are sprocket holes and pin heads. Tape strips are rotated a fraction of a degree (-0.6deg, alternating +0.5deg) so they read as stuck on by hand; that tilt belongs to tape alone.

## Components

### Tape
Hot-pink strip (tape-fill, near-black 600 13px text, 4px 10px), tilted. Carries one highlighted fact on the slate and the Kept/Cut verdict in the loupe. Words carry the verdict; the tape is the same for both.

### Slate
A film-leader block: film background, sprocket rows top and bottom, white Kalam tally at 19-26px, one tape strip appended. One per page.

### Select Reel
Reel head (setting name 600 15px, mono count/minutes/scenes in ink-3) over a film strip with sprocket rows; frames are 16:9 buttons 118px wide, 6px apart, lightening on hover. Reference clips carry a white Kalam "ref" mark top right. Selected frame: 3px tape-fill outline, 2px offset. Arrow keys walk the reels.

### Trim Bin
A panel with an auto-fill grid of pins (min 210px). Each pin: a 3px rule-strong rail across the top, a 9px ink pin head, the rule name as a Kalam tag (17px), mono count and threshold, then a hanging list (2px film line on the left) of trims: 84px thumbnail in a 3px film border plus a Kalam caption naming the planted defect and any extra rules that fired. Selected trim: tape-fill border. Unreadable files show "no frame" in mono.

### Loupe
Panel with a 16:9 film well, tape verdict bottom-left, clip ID in mono, metadata in ink-3, a two-column definition list (ink-3 terms, mono values), then a ruled "why" note opening with the pencil verdict. The AI scene line states reference / graded right / graded wrong / not graded in words.

### Log Sheet
Panel-wrapped table, min 620px wide, rule-strong row lines, right-aligned mono numbers, rule names left in Schibsted with an ink-3 sub-line, recall and precision pencilled in Kalam 16px.

### Meters
Three-column grid (label, 10px bench track, mono value). Fill is ink; the one figure being championed fills with tape-fill.

### Pipeline Strip
A five-cell ordered list on panel, 1px rule dividers, bold step name over ink-2 description; stacks at 900px.

### Buttons
Only the theme switch: transparent, 1px rule-strong border, ink-2 600 12px, square. Focus everywhere: 2px tape outline, 2px offset.

## Do's and Don'ts

### Do:
- **Do** show real frames on film; the thumbnails are the evidence.
- **Do** carry kept vs cut by placement (reel or bin) and by words.
- **Do** keep pink to the tape, selection, links, focus and one championed meter.
- **Do** set every number in Azeret Mono unless it is a pencil mark.
- **Do** keep ink-3 for small text on panel surfaces.

### Don't:
- **Don't** introduce a second hue or a status colour scale.
- **Don't** add drop shadows or corner radius.
- **Don't** use Kalam for headings, body text, labels or controls.
- **Don't** tilt anything that isn't tape.
- **Don't** add small labels above headings; section heads stand alone.
