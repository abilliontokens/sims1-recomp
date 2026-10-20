# Cheat codes

The F1 panel's **Cheats** section enters the game's own codes the game's own way
(`src/game/cheats.cpp`, `src/common/cheats.h`, the section in `src/common/overlay.cpp`).

Recorded 2026-10-20. Static evidence is from `out/game.exe` (the flat PE of `default.xbe`, guest
addresses 1:1); the runs are the native Linux release build, logs and screenshots under
`out/shots/` (gitignored, kept on disk).

**This title has no pad-sequence cheats.** Its codes are words typed on an on-screen keyboard that
the main menu opens while both triggers are held. There is no ring of recent button presses and no
table of button masks anywhere in the image (search below), so the F1 rows type words, not button
sequences.

## How the game takes a code

**Opening the keyboard.** The main menu's update `sub_00075FE0` (vtable `0x1F1A5C` slot 1; the
front-end manager `sub_000763E0` calls it at `0x76511` while the main menu is its current screen)
opens the dialog when:

- no dialog is open over the menu: the byte `[menu+0x69]` is clear (`0x76025` / `0x76117`);
- the developer menu is closed: `[[0x21A294]+0x101]` is clear (`0x76120` / `0x76125`);
- some pad holds action 12 (`sub_001306B0(12, &pad)` at `0x7613A`). The action table at
  `0x20A780` maps action 12 to the mask `0x0C` (entry at `0x20A7E8`) - the left and right
  triggers in the game's pad layout (`sub_0012B450`: L `0x4` at `0x12B47A`, R `0x8` at
  `0x12B487`).

The dialog (`sub_000BB290` at `0x761CC`, the only call) is titled "Enter Cheat" and starts with the
text "CHEATS" in the field (the string keys `cheat_title` / `default_text_cheats` at `0x76180` /
`0x761A0`, their values in the data archive). Its keyboard has A-Z, Space, Backspace, Clear and
Done. On Done the update copies the text into a 32-character buffer on its stack
(`sub_000B9A20` at `0x760AE`) and calls the recogniser:

```asm
760B3  lea  ecx, [esp+6Ch+var_4C]   ; the typed text
760B7  push ecx
760B8  mov  ecx, offset dword_21A1E8 ; the game object
760BD  call _sub_0005E6A0           ; the recogniser's only caller
```

**The recogniser** `sub_0005E6A0` (`this` = `0x21A1E8`, one argument, `retn 4` at `0x5EB37`)
compares the text with each code by `wcsncmp(text, code, wcslen(code))` (`sub_001758B5`): exact,
upper case, and a prefix match. On a match it sets a byte of the game object:

| Code (UTF-16 at) | Byte | Write | What reads it |
| --- | --- | --- | --- |
| `FREEALL` (`0x1F09E8`) | `0x21A2AD` (+0xC5) | toggle, `0x5E6FF` | 27 purchase paths in build and buy mode skip the funds check and the charge (e.g. the charge at `0x2E987`) |
| `MIDAS` (`0x1F09BC`) | `0x21A2AF` (+0xC7) | toggle, `0x5E7CF` | 46 unlock gates: locked buy-mode objects, locked Create-a-Sim items, Play The Sims on the main menu (`0x723FF`), the two-player levels (`0x76A64`) |
| `PARTY M` (`0x1F09AC`) | `0x21A2B0` (+0xC8) | toggle, `0x5E818` | the Party Motel two-player level's button (`0x76D54`, `0x73814`) |
| `SIMS` (`0x1F09C8`) | `0x21A2B1` (+0xC9) | **set**, `0x5E794` | main menu item 1, Play The Sims: drawn (`0x72B37`) and reachable by the cursor (`0x76243` / `0x7628B`) |
| `FISH EYE` (`0x1F09D4`) | `0x21A2B7` (+0xCF) | toggle, `0x5E746` | live mode: Black (action 16) toggles the first-person camera (`sub_0006F170` at `0x6F1A0`, `sub_00012B70` at `0x12B70`) |
| `SHALL` `WE` `PLAY` `A` `GAME` | `0x219590` | 0 -> 5, one word an entry, `0x5E861`-`0x5E984`; any other entry resets it, `0x5EA72` | only the recogniser |
| then `GARGAMEL` (`0x1F096C`) | `0x21A2BB` / `0x21A2B9` (+0xD3 / +0xD1) | toggle together, `0x5E9C8`-`0x5E9F5` | +0xD3: 20 skin-tint sites (hue -0.38); +0xD1: two skeleton callbacks scaling 11 bones by (3, 2, 1.03) |
| then `PICTURES` (`0x1F0958`) | `0x219591` | toggle, `0x5EA39` | the credits sequence `sub_00039320` adds a ten-step timed picture sequence (`0x395AF`-`0x395F6`) |

It then plays its own hit or miss sound (`0x8E959EBA` / `0x1C99B71C`, `0x5EA59` / `0x5EA60`).
SIMS is set, never cleared: entering it again leaves it on. The five chain words each play the miss
sound; the hidden pair is not in any public code list we found.

**Nothing is saved.** The game object's static constructor zeroes these bytes at boot and no save
or load code touches them; every code is gone after a restart, on the console as here.

**No other cheat path.** The game object also registers its bytes in a developer variable menu
(opened with X + B + Y, action 11, by `sub_0002A220`), but that menu needs the byte `cheatmenu`
at `0x21A2BC`, which only the constructor writes (to 0) - it never opens. A search for the sibling
Bustin' Out's kind of recogniser found none: the only reader of the raw XInput bytes is the pad
mapper `sub_0012B450`; the raw-mask getters' users are a widget, the 115 s idle timer and a debug
list; no data table or code-built table of single-bit button masks exists; and none of the 31
action queries with a non-constant action is an ordered sequence. (Static search by a helper
agent; its notes are not in the repo.)

## How the host enters a code

The override of `sub_00075FE0` in `src/game/cheats.cpp` runs at the top of the main menu's update:

- each frame it records whether the menu would open the keyboard itself - the dialog byte and the
  developer-menu byte above both clear - which the panel reads (`cheats::OnMainMenu`, true for
  250 ms after such a frame);
- when the panel has queued codes and those conditions hold, it writes each code's text into a
  64-byte buffer on the guest stack, as the dialog's is, and calls
  `sub_0005E6A0(0x21A1E8, text)` through `hle::Call`, then logs the game's byte read back:
  `cheats: entered FISH EYE on the main menu: on`. For GARGAMEL and PICTURES it enters
  `SHALL`, `WE`, `PLAY`, `A`, `GAME` first, unless the chain already stands at 5, and it enters
  the plain codes first in a batch, because any of them resets the chain.

What the dialog does around the call needs no copy: it binds player 0 to the pad that held the
triggers and sets the dialog byte, pointer and layout targets when it opens, and undoes each when it
closes; `byte_21A34A`, which it sets while open, has no reader. Everything runs on the title thread,
in the function that makes the call in the game.

**The panel.** F1 -> Cheats lists seven rows (Free items, Unlock all, Party Motel, Play The Sims,
First person, Gargamel, Pictures), each a checkbox showing the game's own byte (with a click the
title thread has not taken yet counted in). The rows are enabled only while the main menu takes
codes, and say so when they are not; a click on Play The Sims while it is on does nothing, as in the
game.

## Verified in play

| Code | Run | Log | Effect seen |
| --- | --- | --- | --- |
| SIMS | `cheat1` | `[342.140] cheats: entered SIMS on the main menu: on` | the main menu shows **Play The Sims** between Get a Life and Options (`cheat1_menu_sims_pair.png`: before / after; 21 -> 23 draws a frame) |
| FISH EYE | `cheat1`, `cheat2` | `[340.973] ... FISH EYE ... on` | in live mode Black switched the camera to first person - the walls dropped and the view went to the Sim's eyes - and Black again switched back (`cheat2_fisheye_black_cycle.png`, `cheat1_fisheye_strip.png`) |
| FISH EYE off | `cheat3` | `[77.870] ... FISH EYE ... on`, `[78.737] ... FISH EYE ... off` | with the code entered twice (off), Black in live mode does nothing (`cheat3_fisheye_off_black2.png`: four frames, the overhead view throughout) - the control for the row above |
| GARGAMEL | `cheat2` | `[99.566] cheats: entered GARGAMEL on the main menu: on` | Create a Sim shows Pat with a large head and pale blue skin (`cheat2_gargamel_cas_pair.png`: a normal run on the left) |
| FREEALL, MIDAS, PARTY M, PICTURES | `cheat4a`, `cheat4` | `cheat4a.log`: `[45.191] ... FREEALL ... on`, `[46.308] ... MIDAS ... on`, `[47.424] ... PARTY M ... on`; `cheat4.log`: `[44.205] ... PICTURES ... on`, `[47.567] PARTY M ... on`, `[56.802] PARTY M ... off` | the game's byte flips as logged; the effects themselves (a free purchase in buy mode, unlocked items, the Party Motel button, the credits pictures) were not driven |

The panel itself: `cheat1_f1_open.png` (F1 opened on the main menu, the top of the panel),
`cheat2_f1_fisheye_gargamel.png` (the Cheats section with First person and Gargamel ticked),
`cheat4_f1_rows.png` (the section part way through `cheat4`), `cheat3_f1_live_disabled.png` (live
mode: every row greyed out, with the note saying why).

## Not verified

- The effects of FREEALL, MIDAS, PARTY M and PICTURES were not seen on screen (only their bytes);
  buy mode, the two-player levels and the credits were not driven.
- No controller was plugged in: the triggers + keyboard dialog path itself (L + R on the main menu)
  was not driven by hand; the panel calls the same recogniser the dialog calls.
