#!/usr/bin/env python3
"""Classify a screenshot of the running port's window into a walk state.

Usage: classify_screen.py <png>  ->  one word on stdout:
  intro | title | loading | menu | getalife | lastname | firstname | overwrite |
  cas | starthouse | question | questionno | dialogue | house

The input is a capture of the game WINDOW (tools/shot_game.sh uses spectacle
-a); picture() cuts the game picture out of it, and every probe below is a
coarse colour fact over a fixed fraction of that picture: reg() regions, the
mean level, and the share of blue, white, red, green or cyan pixels.

Every probe was measured on The Sims' own screens, the walk docs/playtest.md
records, in two kinds of capture: the probe60 run's windowed shots
(out/shots/probe60_*.png, taken before the host cropped the picture, so
measured on the rows the crop keeps: guest rows 24..456 of 480) and borderless
3440x1440 shots of the cropped picture (out/shots/fs1_*.png, a labelled walk of
the current build, each named with its screen and the draw count of the
moment; out/shots/sims1walk_*.png and sims1walk2_*.png, the stage screenshots
of two tools/shot_game.sh runs). The values in the comments are the measured
ranges over all of them; each threshold sits between the screens it separates.
Over the labelled frames the classifier answers the label on all but the
Start-house blink below. Not covered: a frame with the host's F1 settings
panel open over the picture (sims1walk_dialogue2.png, a dialogue behind it,
reads "intro"); the walk never opens it.

Screens that share a word, because no coarse probe tells them apart:
  loading  - "Loading, please wait..." after START, the same bar after Create a
             Sim, the bare logo between that bar and "(A) Start house"
             (probe60_cas4.png), and the off phase of the blinking "(A) Start
             house" itself (fs1_056, fs1_054), which is the same bare logo. That
             blink is the 4 misreads: half the Start-house frames say "loading",
             and tools/shot_game.sh simply waits on until a lit one shows.
  dialogue - every tutorial dialogue in live mode (Welcome to The Sims, Pat's
             and Roxy's lines): one panel, one probe
  house    - live mode with or without a pie menu or a camera inset open
  intro    - whatever is left: the EA, Maxis and intro movie frames and the
             attract movie match none of the facts below, and no walk screen
             falls through to it
"""
import sys

import numpy as np
from PIL import Image

# The aspects the host presents the picture at (sdk gpu/vulkan.cpp
# PresentSrcAspect): 16:9 on an output 3:2 or wider, else 4:3.
ASPECTS = (16 / 9, 4 / 3)


def picture(img):
    """The game picture inside the window capture (RGBA uint8), without its bars.

    The host fits the picture inside the window at its own aspect, centred,
    and clears the rest to black. Since the host crops the title's black rows
    (640x432 at y=24, srcUv (0,0.050)-(1,0.900)) the picture fills the window's
    height on a wide window: on this machine's borderless 3440x1440 it is
    2560x1440 at x=440 with pure black pillars either side (every fs1_*.png).
    The rect is found by geometry, not by trimming dark rows and columns: the
    title, loading and save-question screens are near-black at their own
    edges, and the old content trim cut them to 2056x1206 (fs1_017 title) or
    2248x973 (fs1_063 save question), which moves every probe. A candidate
    rect is taken when one of its two bars is black: the bars are the same
    size either side, and one may not be clean - the host's F1 stats panel
    draws into the right pillar (sims1walk_dialogue2.png: 114135 lit pixels
    there, the left pillar still all black). A window of the picture's own
    shape (4:3 showing 4:3) has no bars and is the picture as captured.
    """
    alpha = img[:, :, 3] == 255  # spectacle's PNG: drop the transparent shadow
    ys, xs = np.where(alpha.any(axis=1))[0], np.where(alpha.any(axis=0))[0]
    if len(ys):
        img = img[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1]
    img = img[:, :, :3]
    h, w, _ = img.shape
    dark = img.max(axis=2) <= 8
    for aspect in ASPECTS:
        pw, ph = min(w, round(h * aspect)), min(h, round(w / aspect))
        if (pw, ph) == (w, h):
            continue
        x0, y0 = (w - pw) // 2, (h - ph) // 2
        if x0:
            bars = (dark[:, :x0], dark[:, x0 + pw:])
        else:
            bars = (dark[:y0], dark[y0 + ph:])
        if max(float(b.mean()) for b in bars) >= 0.99:
            return img[y0:y0 + ph, x0:x0 + pw]
    return img


def classify(pic):
    pic = pic.astype(np.int16)  # 22 MB at 2560x1440; int64 would be 88 MB
    ph, pw, _ = pic.shape

    def reg(fx0, fy0, fx1, fy1):
        return pic[int(ph * fy0):int(ph * fy1), int(pw * fx0):int(pw * fx1)]

    def mean(r):
        return float(r.mean())

    def bluefrac(r):
        return float(((r[:, :, 2] > 140) & (r[:, :, 2] > r[:, :, 0] + 40)).mean())

    def whitefrac(r):
        return float((r.min(axis=2) > 180).mean())

    def redfrac(r):
        return float(((r[:, :, 0] > 150) & (r[:, :, 1] < 90) & (r[:, :, 2] < 90)).mean())

    def greenfrac(r):
        g = r[:, :, 1]
        return float(((g > 140) & (g > r[:, :, 0] + 40) & (g > r[:, :, 2] + 40)).mean())

    def cyanfrac(r):
        return float(((r[:, :, 1] > 150) & (r[:, :, 2] > 150) & (r[:, :, 0] < 120)).mean())

    # The menus' sky-blue panel fills the top right: 0.39-0.41 on the main menu
    # and Get a Life (probe60_after_load.png, probe60_getalife1.png, fs1_033,
    # fs1_036). In live mode only the clock pill is blue there: 0.038-0.051
    # (probe60_live2_2.png, probe60_clock_a.png, fs1_087). 0 everywhere else, a
    # live-mode dialogue included: it dims the HUD (probe60_house3.png, fs1_069).
    top_right = bluefrac(reg(0.78, 0.0, 0.99, 0.10))
    # The red (B) button in the footer: BACK on Get a Life, CANCEL on every Create
    # a Sim screen, 0.107-0.109 (probe60_getalife1.png, probe60_startalife1.png,
    # probe60_cas2.png, probe60_cas3.png, fs1_036/040/043/048); the main menu has
    # only (A) SELECT: 0 (probe60_after_load.png, fs1_033).
    back = redfrac(reg(0.58, 0.86, 0.67, 0.93))

    if top_right > 0.2:
        return "getalife" if back > 0.05 else "menu"
    if back > 0.05:
        # Create a Sim: the cyan highlight sits on the keyboard's Done, one row
        # lower for the first name (Space appears above it), or on the DONE icon
        # in the top bar once both names are in. 0.14-0.22 on its own screen,
        # 0 on the other two (last name: probe60_startalife1.png,
        # attract_fix60_kb_before.png, fs1_040; first name: probe60_cas2.png,
        # fs1_043; DONE: probe60_cas3.png, fs1_048).
        if cyanfrac(reg(0.66, 0.525, 0.72, 0.565)) > 0.05:
            return "lastname"
        if cyanfrac(reg(0.66, 0.575, 0.72, 0.615)) > 0.05:
            return "firstname"
        if cyanfrac(reg(0.66, 0.13, 0.75, 0.19)) > 0.05:
            return "cas"
        return "unknown"
    if top_right > 0.015:
        return "house"
    # A live-mode dialogue: its panel's blue top edge crosses the picture at
    # y 0.16, 0.101-0.121 (probe60_house3.png Welcome, probe60_live1.png Pat,
    # cheat1_live_w0.png Roxy, fs1_069, fs1_077); 0 in live mode without one
    # (fs1_075 with the pie menu open, fs1_087) and at most 0.016 in any intro
    # frame (fs1_002).
    if bluefrac(reg(0.30, 0.15, 0.70, 0.18)) > 0.06:
        return "dialogue"
    # The Sims logo on dark navy: its red outline is 0.184 of this region on the
    # title, both loading screens and "Start house" (probe60_t30.png,
    # probe60_after_start1.png, probe60_cas4.png, probe60_house1.png, fs1_017,
    # fs1_053, fs1_055); the intro movie's own logo frames reach 0.119 at most
    # (fs1_006, fs1_007, fs1_009); the save question's box darkens it to 0.
    if redfrac(reg(0.25, 0.08, 0.75, 0.74)) > 0.15:
        # the loading bar's blue outline, y 0.81 and 0.87: 0.034-0.506 while a
        # bar is up (probe60_after_start1.png, fs1_022, fs1_023, fs1_053), 0 on
        # the title, Start house and the bare logo
        if bluefrac(reg(0.30, 0.80, 0.70, 0.88)) > 0.015:
            return "loading"
        # the green (A) of "(A) Start house", 0.033 while it is lit
        # (probe60_house1.png, fs1_055). It blinks: its off phase (fs1_054,
        # fs1_056, 4 of the 10 labelled Start-house frames) is the bare logo
        # and reads as "loading" below - the only known misread, absorbed by
        # tools/shot_game.sh waiting on for a lit frame.
        if greenfrac(reg(0.30, 0.79, 0.70, 0.86)) > 0.01:
            return "starthouse"
        # the white copyright line, 0.123 on the title (probe60_t30.png,
        # fs1_017, fs1_018) and on the first loading screen (which the bar has
        # already claimed above); 0 on the rest. "Please press START to begin."
        # blinks above it and is not used.
        if whitefrac(reg(0.25, 0.89, 0.75, 0.94)) > 0.06:
            return "title"
        return "loading"  # the bare logo: see the docstring
    # The save question: the logo's black corners (mean 0.14-0.31; the EA intro
    # frame, which also has cyan here, is 3.6-8.7: fs1_002) and the cyan of
    # whichever answer is highlighted, 0.139-0.149 on its own row, 0 on the
    # other (YES: probe60_house2.png, fs1_063; NO after DOWN:
    # probe60_save_q_no.png, fs1_066).
    if mean(reg(0.0, 0.0, 0.10, 0.15)) < 2:
        yes = cyanfrac(reg(0.46, 0.46, 0.54, 0.50))
        no = cyanfrac(reg(0.46, 0.51, 0.54, 0.545))
        if max(yes, no) > 0.05:
            return "question" if yes > no else "questionno"
        # "Warning! There is already a 'Get a Life' save game of the name NEWBIE
        # on the hard disk ... Press (A) to proceed": shown after A on the last
        # name once a NEWBIE save exists (it does once any run has answered YES
        # to the save question; the playtest's runs never had one). White text
        # in the middle of a black-cornered picture: 0.189 of this region
        # (sims1walk2_overwrite.png). The other black-cornered frames are 0-0.065
        # (Maxis, fs1_003) or 0.43-0.52 (the intro's logo on black, fs1_006, and
        # the title, loading and Start-house logo, claimed above). It draws 9 a
        # frame, like a loading screen, and before this probe it read as
        # "intro"; the sims1walk run only got past it by retrying A.
        if 0.12 < whitefrac(reg(0.30, 0.20, 0.70, 0.60)) < 0.30:
            return "overwrite"
    return "intro"


def main() -> int:
    img = np.asarray(Image.open(sys.argv[1]).convert("RGBA"))  # kept uint8 until cropped
    print(classify(picture(img)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
