# Playtest: the unattended walk from boot to live mode

Recorded 2026-10-20 on this machine (CachyOS, KDE Plasma Wayland, AMD BC-250/RADV), native Linux
release build `out/build/linux-release/Sims1`, windowed 1280x960, `vsync = false`, `fps_cap = 60`
unless the run's name says 144 or 0 (uncapped), `XBE_PERF=1 XBE_MUTE=1`. Screenshots and logs are
under `out/shots/` (gitignored, kept on disk); every claim below names the log line or screenshot
that proves it.

**Farthest screen reached unattended: live mode in the household** — Pat Newbie standing in the
furnished starter lot, the HUD up (portrait, the action pad, §200, the clock running), 1231-2208
draws a frame against the menus' 21-23. Nothing blocks the walk: no screen refused an input. The F3
capture says the same as the per-second counts: `frame.txt` holds 23 lines on the main menu
(`out/build/linux-release/cap_pic/144635`) and 1236 in live mode (`cap_pic/144727`).

The walk is repeatable: the same driver reached live mode in **17 of 17 runs** that went for it
(`probe60`, `stock144`, `stock0`, `fix60/144/0`, `host60/144/0`, `nostep60/144/0`, `pic_before`,
`pic_after`, `cheat1`, `cheat2`, `cheat3`; the first draw count of 1100 or more came 62-440 s after
launch, depending on how long each run lingered on the menus for its measurements). The other
runs in `out/shots/` stopped on purpose at the main menu or Create a Sim.

## How the walk is driven

- **Pad tokens through `SIMS1_STEP=<file>`** (the existing hook in `src/common/game_info.cpp`,
  unchanged): each new token written to the file is one 130 ms press on pad 0; `NONE` is written
  between presses so an identical token is a new burst. It only ORs bits in. No game-side code was
  added for the walk; `SIMS1_AUTOSTART` was not needed and was not used.
- **The keyboard** (`/dev/uinput`, as `tools/drive_keys.py` does it) only for what a 130 ms pulse
  cannot do: the F1 panel (F1, Tab, Shift+Tab, Space) and held keys for the frame-rate
  measurements. Caveat found on the way: KWin gives the game the active window at launch, but SDL
  sometimes never reports the focus to the game (`SDL_EVENT_WINDOW_FOCUS_GAINED`), and the
  keyboard-as-pad layer (`input_kbm.cpp`) then ignores every key - no `input: keyboard and mouse on
  port 0` line appears. The ImGui F-keys and `SIMS1_STEP` are unaffected. Activating another
  window and then the game again through a KWin script fixes it for the run.
- **Screenshots**: `spectacle -a -b -n -o <png>` of the game window (the active window for the whole
  run; nothing else is clicked).
- **Classification by draw count**: the `XBE_PERF=1` line `perf: per frame N draws` once a second,
  plus the `open` lines of the archives each screen loads. The counts are unambiguous: a movie is
  0-1 draws, the title 2, the menus 21-23, Create-a-Sim 223-313, a load 10, the household 860-2208.

The driver presses a token, waits for the draw count of the next screen, screenshots, and only then
presses again; the walk below is the first run, confirmed screen by screen that way (`probe60`,
`out/shots/probe60.log`, screenshots `out/shots/probe60_<screen>.png`, the stock build at
`fps_cap = 60`).

## The walk, per screen

Times are the log's seconds since launch. Draw counts are the per-second `perf:` lines.

| # | Screen (screenshot) | Input that leaves it | Evidence of arrival |
| ---: | --- | --- | --- |
| 1 | Intro movies (EA, Maxis, intro) | none needed - they end by themselves | `open D:\MOVIES.ARC` at 0.72 s and again at 7.55 s; 0-1 draws a frame 1.1-26.4 s |
| 2 | Title: "Please press START to begin", © 2003 (`probe60_t30.png`) | `START` | 2 draws a frame from 27.4 s; no further `open` |
| 3 | "Loading, please wait..." with a progress bar (`probe60_after_start1.png`) | none - it ends by itself | `sims1 step: holding 'START'` at 60.39 s; `open T:\config.data` 60.41 s and `open D:\AUDIOSTR.ARC` 60.44 s; 4 then 9 draws |
| 4 | Main menu over the neighbourhood: **Get a Life** / Options / Credits, Get a Life highlighted (`probe60_after_load.png`) | `A` | 21 draws a frame from 70.1 s |
| 5 | Get a Life: **Start a Life** / Load, Start a Life highlighted (`probe60_getalife1.png`) | `A` | `A` at 177.37 s; 22 draws from 178.4 s |
| 6 | Create a Sim, "Enter your Sim's last name", keyboard with the cursor on **Done**, default **NEWBIE** (`probe60_startalife1.png`) | `A` (accepts the default) | `A` at 201.12 s; `open d:\story.ngh` 201.12 s; 57 then 223 draws |
| 7 | Create a Sim, "Enter your Sim's first name", default **PAT**, cursor on Done (`probe60_cas2.png`) | `A` | `A` at 221.27 s; 220-224 draws |
| 8 | Create a Sim: PERSONAL / BODY / HEAD / **DONE**, Pat in front of the mirror, focus on DONE (`probe60_cas3.png`) | `A` | `A` at 246.15 s; 310-313 draws |
| 9 | Loading (the Sims logo) (`probe60_cas4.png`) | none | `A` at 265.39 s; `open D:\SAMPLES.ARC` 267.47 s; 10 draws for 2 s |
| 10 | The Sims logo, "(A) Start house" (`probe60_house1.png`) | `A` | 864 / 863 draws a frame from 269 s (the lot is drawn behind the logo) |
| 11 | "Would you like to save before starting this house?" **YES** / NO, YES highlighted (`probe60_house2.png`) | `DOWN`, `A` (NO: nothing is written) | `A` at 315.78 s; 984 then 1040 draws; `probe60_save_q_no.png` shows NO highlighted |
| 12 | Welcome to The Sims dialog over the lot, §200, clock 9:07 PM (`probe60_house3.png`) | `A` | `A` at 350.73 s; 1148-1174 draws |
| 13 | Pat's first lines ("What the...what am I doing here? Whose mansion is this?") and two more tutorial dialogs (`probe60_live1.png`) | `A` x4 | `A` at 377.19 / 396.37 / 401.48 / 406.51 s; 1164-1979 draws |
| 14 | **Live mode**: Pat by the fireplace, HUD up, clock running (`probe60_live2_2.png`) | - | 1231-1242 draws from 408.4 s, 1395-1401 from 448 s; the HUD clock read 9:41 PM at 450.0 s and 10:06 PM at 481.0 s (`out/shots/probe60_clock_a.png`, `probe60_clock_b.png`) |

So the whole token sequence from a cold boot is: wait for the title (about 27 s), `START`, wait for
the main menu (about 10 s), then `A A A A A`, wait for the "Start house" logo (about 5 s after the
last `A`), `A`, `DOWN`, `A`, then `A` for each tutorial dialog (four or five). Every wait above was a
screen settling, not a press being retried: no press was swallowed in this run.

**One screen that interrupts the walk: the attract movie.** Left alone on the main menu, the game
plays its attract movie (`open D:\MOVIES.ARC`, 0 draws) once its 115 s idle timer runs out; `A`
leaves it and returns to the main menu (21 draws). With the frame-step fix the timer is real time
(113.8-115.0 s, `docs/frame-rate.md`). Without it, uncapped, the menu runs at ~1400 fps and the
timer 20-30x fast, so the movie starts 3.3-3.7 s after the menu appears; the one walk that failed
to find the menu (`in_no0`, `SIMS1_NO_STEP=1` uncapped) failed on exactly that. The driver handles
it by pressing `A` until the menu's 21 draws are back before going on.

## What the walk does not cover

- The YES branch of the save question (it writes a save to `hdd/`) and the Load path were not
  driven.
- Options, Credits and Play The Sims were not driven (Play The Sims appears once the SIMS code is
  on: `docs/cheats.md`).
- Build and buy modes, and any interaction (the pie menu) in live mode, were not driven; live mode
  was entered, its clock watched and its camera switched (`docs/cheats.md`, FISH EYE), nothing
  more.
- No controller was plugged in; every press came from `SIMS1_STEP` or the uinput keyboard.
