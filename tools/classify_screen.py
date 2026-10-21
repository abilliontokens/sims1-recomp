#!/usr/bin/env python3
"""Classify a screenshot of the running port's window into a walk state.

Usage: classify_screen.py <png>  ->  one word on stdout:
  intro | menu | cas | dialog | live | unknown

The input is a capture of the game WINDOW (tools/shot_game.sh uses spectacle
-a). The picture is trimmed of the near-black pillarbox the present leaves
inside the window; a mostly-black frame trims to nothing and answers "intro"
(a movie or a black loading frame - both are only ever waited on).

Every probe below is measured on this title's own screenshots (out/shots/,
the runs docs/playtest.md records). This game's screens are not the sibling
port's blue-gradient scheme:

  intro                     black frame: movies, the first loading frames
  menu   blue(top) > 0.35   the blue-gradient family: the "Loading, please
         and blue(TR) > 0.30 wait..." screen with its progress pill, the main
                            menu and the Get a Life screen share this look
                            (probe60_after_load / pic_after_menu /
                            probe60_getalife1: blue(top) .47-.59, blue(TR)
                            .49-.59). The walk treats them alike: press A.
  cas    blue(top) > 0.35   Create a Sim: the blue top band without the
         and blue(TR) < 0.15 corner pill (probe60_cas2: .405 top, .038 TR).
  dialog dark with a bright the text-on-dark screens: the "Please press
         low band > 0.10     START" title, the save question and the tutorial
                            dialogs (probe60_t30 .19, after_start1 .20,
                            pic_after_movie13 .36 white low, blue(top) 0).
                            Merged deliberately: the walk answers all of them
                            with A.
  live   dark, mean < 35,    live mode: a dark 3-D scene with little bright
         little bright text anywhere (probe60_live1: mean 20.6, white(low)
                            0.000, blue 0.03).
  unknown                   bright but none of the above.
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
    h, w, _ = img.shape
    bright = img.mean(axis=2)
    rows = np.where(bright.max(axis=1) > 20)[0]
    cols = np.where(bright.max(axis=0) > 20)[0]
    if not len(rows) or not len(cols):
        return None
    return img[rows.min():rows.max() + 1, cols.min():cols.max() + 1]


def main() -> int:
    img = np.asarray(Image.open(sys.argv[1]).convert("RGB"), dtype=np.float32)
    p = picture(img)
    if p is None:
        print("intro")  # a black frame: movies / loading
        return 0
    h, w, _ = p.shape

    def reg(fx0, fy0, fx1, fy1):
        return p[int(fy0 * h):int(fy1 * h), int(fx0 * w):int(fx1 * w)]

    def mean(r):
        return float(r.mean())

    def bluefrac(r):
        return float(((r[:, :, 2] > r[:, :, 0] + 25) & (r[:, :, 2] > 90)).mean())

    def whitefrac(r):
        return float((r.mean(axis=2) > 200).mean())

    top, low, tr = reg(0, 0, 1, .25), reg(0, .55, 1, .85), reg(.75, 0, 1, .2)
    bt, bl, btr = bluefrac(top), whitefrac(low), bluefrac(tr)
    if bt > 0.35:
        print("menu" if btr > 0.30 else "cas")
    elif bl > 0.10:
        print("dialog")
    elif mean(p) < 35.0:
        print("live")
    else:
        print("unknown")
    return 0


if __name__ == "__main__":
    sys.exit(main())
