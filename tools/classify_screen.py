#!/usr/bin/env python3
"""Classify a screenshot of the running port's window into a walk state.

Usage: classify_screen.py <png>  ->  one word on stdout:
  intro | blue | saveselect | name | cas | question | house | dialogue | unknown

The input is a capture of the game WINDOW (tools/shot_game.sh uses spectacle
-a). It used to be a capture of the whole desktop, and picture() had to find
the game inside it by looking for bright columns - which finds the wallpaper
instead as soon as the game is windowed on anything but a black desktop. That
misread a loaded household as "intro" through six retries. All this has to do
now is trim the pillarbox or letterbox the present leaves inside the window.

"blue" covers the title and the main menu (both are blue-gradient screens the
walk treats alike: START then A). The probes are coarse colour facts measured
on the sibling Sims: Bustin' Out port's real screens (its docs/playtest.md):
the name keyboard is a bright-lettered grid low in a dark picture, the
household is a lot whose clock pill is bright blue at the picture's top right,
its greeting dialogue is a bright translucent panel in the centre, and
Create-a-Sim is a warm brown room whose save question covers the centre in blue.

CAVEAT: none of these probes has been measured on The Sims' screens yet.
The window trim in picture() and the black-frame "intro" answer hold for any
title; the named states are the sibling's and have to be re-measured and
renamed for this game before tools/shot_game.sh can walk it past the intro.
"""
import sys

import numpy as np
from PIL import Image


def picture(img):
    """The game picture inside the window capture, without its bars.

    Trims whole rows and columns that are essentially black: the pillarbox at
    4:3 or 16:9 on a wider window, the letterbox the other way, and the window
    manager's own border. A mostly-black frame (a movie, a loading screen)
    trims to nothing, which the caller reads as "intro".
    """
    lit = img.sum(axis=2) > 60
    cols = np.where(lit.mean(axis=0) > 0.08)[0]
    rows = np.where(lit.mean(axis=1) > 0.08)[0]
    if len(cols) < 50 or len(rows) < 50:
        return None
    return img[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]


def main() -> int:
    img = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(int)
    pic = picture(img)
    if pic is None or pic.shape[0] < 50:
        print("intro")  # a black frame: movies / loading
        return 0
    ph, pw, _ = pic.shape

    def reg(fx0, fy0, fx1, fy1):
        return pic[int(ph * fy0):int(ph * fy1), int(pw * fx0):int(pw * fx1)]

    def mean(r):
        return r.reshape(-1, 3).mean(axis=0)

    def bluefrac(r):
        return float(((r[:, :, 2] > 140) & (r[:, :, 2] > r[:, :, 0] + 40)).mean())

    def whitefrac(r):
        return float((r.min(axis=2) > 180).mean())

    centre = reg(0.35, 0.35, 0.65, 0.65)
    lowmid = reg(0.30, 0.60, 0.70, 0.95)
    clock = reg(0.84, 0.0, 0.99, 0.09)
    cm, pm = mean(centre), float(pic.reshape(-1, 3).mean())

    # the intro movie's sunset frame: warm orange centre, no UI anywhere
    if cm[0] > cm[2] + 80 and cm[0] > 150:
        print("intro")
        return 0
    left = mean(reg(0.02, 0.30, 0.20, 0.80))
    # household: dark lot, bright-blue clock pill top-right; dialogue covers centre
    if pm < 100 and bluefrac(clock) > 0.015:
        print("dialogue" if bluefrac(centre) > 0.5 else "house")
        return 0
    # the warm CAS room: name entry and the save question both overlay it in blue
    if left[0] > left[2] + 25:
        if bluefrac(centre) > 0.6:
            print("name" if whitefrac(lowmid) > 0.04 else "question")
        else:
            print("cas")
        return 0
    if bluefrac(centre) > 0.6:
        print("dialogue" if pm < 100 else "blue")
        return 0
    if cm[0] > cm[2] + 25:
        print("cas")
        return 0
    if bluefrac(lowmid) > 0.5:
        print("blue")
        return 0
    print("intro")  # no UI facts matched: a movie frame (only waited on at launch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
