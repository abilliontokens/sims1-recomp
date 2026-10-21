# Camera zoom speed and the frame rate

Recorded 2026-10-20. Static evidence is from `out/game.exe` (the flat PE of `default.xbe`, guest
addresses 1:1); every run is the native Linux release build `out/build/linux-release/Sims1`,
windowed 1280x960, `vsync = false`, `XBE_PERF=1 XBE_MUTE=1`, logs under `out/shots/`. The fix is
in `src/game/hooks.cpp`. This slots into `docs/frame-rate.md`'s "Not covered" item: consumers that
step per frame tuned for the console's rate — the zoom is the one found in this title.

**The defect.** In live mode the camera zoom, in and out, runs at a speed proportional to the
frame rate. At the port's new live-mode rate (175-244 fps after the kernel wakeup work) the zoom
sweeps its whole range in a fraction of a second; at the 60 fps cap it takes ~4x longer. The
owner's report, and the sibling ports' experience (`urbz-recomp/src/game/hooks.cpp`,
`simsbustinout/docs/frame-rate.md`), says exactly one class of bug does this: a consumer that
steps **per call** instead of per delta.

## The consumer: `sub_00011ED0`, the manual camera's zoom handler

The zoom input path, end to end (every address verified in the image):

1. **Host pad report in.** `XInputGetState` (`0x1E7DBC`, HLE in `sdk/runtime/xdk/xapi.cpp`) writes
   the pad report at `pState`: buttons `+4`, 8 analog bytes `+6`, and the four thumbs as words at
   `+14/+16/+18/+20` — so the report's right-stick Y is the word at `pad+0x264` once the game's
   pad object has the state at its `+0x250`.
2. **The game's pad poll**, `sub_0012B760` (called from the pad manager `sub_0012B9F0` /
   `sub_0012B97D`), reads the four thumbs at `pad+0x25E/0x260/0x262/0x264` and hands each to
   `sub_0012B3F0` (`0x12B3F0`), which normalises a thumb word to `-1..1` with a ±0.24 deadzone
   (`0x1F0DF0`, scaled back by 1/0.76 = `1.3157894` at `0x1F96CC`), then to
   `sub_0012B2F0(stick, axis, value)` → `sub_12FE90` (`0x12FE90`), which filters the value into
   the shared input state (current floats at `+0x168..0x174`, per-poll delta at `+0x188..0x194`).
3. **The game's analog getter**, `sub_0012FF10` (`0x12FF10`, `this` = the port's slot object from
   `sub_0012AD90`), returns one stick axis.
4. **The camera update** `sub_00012BD0` (`0x12BD0`, vtable slot at `0x1F1764`) dispatches three
   stick handlers per update, each self-gated on the camera's mode word `[cam+0x165C]`:

| handler | gate | input | what it steps | dt? |
| --- | --- | --- | --- | --- |
| `sub_00011D40` | mode 1 | right stick X | `[cam+0x16DC] += \|RX\|² × [cam+0x16D4] × `[0x20C150]`, clamp `[0, 360]` | **yes** |
| `sub_00011E00` | mode 1 | right stick Y | `[cam+0x16E0] += RY × [cam+0x16D4] × `[0x20C150]`, clamp `[20, 88]` | **yes** |
| `sub_00011ED0` | mode 2 (and 4-from-2) | right stick Y | **`[cam+0x16D8] -= RY`** and, while not parked at a bound, `[cam+0x16E0] -= RY` | **NO** |

`[0x20C150]` is the engine's one frame delta (docs/frame-rate.md). The first two handlers are
already correct. `sub_00011ED0` (`0x11ED0`, `this` in `ecx`, plain `retn`, bool in `al`) is the
manual camera's zoom: it subtracts the **raw stick deflection** from the camera distance
**once per call, with no delta multiply anywhere in the function** — at `0x11F62/0x11F6C`:
`fld [esi+16D8h]` … `fst [esi+16D8h]` after `fsub` with the deflection fetched through
`sub_0012FF10(this: slot, a2: 1, a3: true)` at `0x11F3C`.

5. **Proof `[cam+0x16D8]` is the zoom.** The apply step `sub_00012830` (`0x12839`) reads it and
   writes `[cam+0x16D0] = ([cam+0x16D8] - 6.5) / (40.0 - 6.5) …` — the distance normalised into
   the zoom parameter that drives the view's pitch/FOV (mode-dependent paths through
   `dword_323CE0`). The distance lives in `[6.5, 40.0]` (`flt_20A938` / `flt_20A934`, both
   options-scaled in `sub_00012BD0`'s head), init 25.0 at `0x12FBE`. The only writer inside the
   camera update is `sub_00011ED0` itself; the only other writers are the inits at `0x12FBE`
   and the camera setup at `0x908C5`.

## Other per-call candidates reviewed (report only, none other found off)

- **Rotate** (`sub_00011D40`, right stick X in camera mode 1): steps `[cam+0x16DC]` by
  `|RX|² × [cam+0x16D4] × [0x20C150]` — already delta-scaled, correct. The menu rotate
  helper `sub_000AC3A0` reads right stick X through the same getter and accumulates with
  `[0x20C150]` timers (`dword_22075C`/`dword_220760`) — correct.
- **Mode-1 zoom** (`sub_00011E00`, right stick Y in camera mode 1): steps `[cam+0x16E0]` by
  `RY × [cam+0x16D4] × [0x20C150]`, clamp `[20, 88]` — already delta-scaled, correct, and
  deliberately untouched (scaling it would correct it twice).
- **Idle auto-return easing** (the Urbz `sub_0001F0E0` defect): no counterpart found in this
  title's camera family. The mode-3 handler `sub_00012030` is a scripted reset that writes
  fixed vectors and reads no stick; nothing in `sub_00012BD0`'s family adds a constant to a
  camera field per call besides `sub_00011ED0`'s deflection step.
- **Per-poll counters** in the input layer (`sub_12FE90`'s current/prev/delta floats at
  `+0x168..+0x194`) are deadzone/release-detection state, not game-speed consumers; the
  mouse-wheel pulse in the host layer (`PulseWheel`, 90 ms a notch, 450 ms cap) is already
  time-based on the host clock, and its zoom effect passes through the same `sub_00011ED0`
  consumer — so the fix below corrects wheel-zoom speed at the same time.

So: one call per camera update, one camera update per frame, and the step is the deflection
itself. Zoom speed = deflection × calls/second. This is exactly the Urbz `sub_0001F0E0` shape
(`0.05` per call at `cam+0x3CC` there; the raw deflection here), and the reason
`docs/frame-rate.md`'s per-call sweep cleared it: live mode never ran faster than ~58 fps when
that was measured.

## The fix (`src/game/hooks.cpp`)

The sibling's method: **rescale the per-call step by the call rate** — the step is multiplied by
`60 / calls_per_second` (60 calls/s is the port's reference: the stock game at the 60 fps cap,
and the engine's own tick size `[0x324220]` = 1/60 s). Never scale a value that already
multiplies the delta: the two mode-1 handlers (`sub_00011D40`, `sub_00011E00`) do multiply by
`[0x20C150]` and are **not** touched — scaling them would correct them twice, the exact trap the
Urbz port documented on the dolly `[0x2E5DE8]`.

The wrapper snapshots the two fields the guest handler steps (`[cam+0x16D8]` distance,
`[cam+0x16E0]` pitch), calls the image's own function, and keeps only the rate-scaled fraction
of the change it made. Because the scale is ≤ 1, the written-back value is always between the
snapshot and the guest's own clamped result, so the guest's bounds hold exactly; the endpoints
and the easing shape are the image's own, only spread over the correct wall-clock time. The
scale settles through a low-pass on the measured call interval (time constant 0.25 s), so a
loading-screen gap between calls does not spike it. `SIMS1_NO_ZOOMRATE=1` runs the image's
function untouched for an A/B without a rebuild (the `HookOff` convention, like
`SIMS1_NO_STEP`).

## Measured (before / after)

**Confirmed after the release cut-off**, with the shipped binary and a wall-clock hold rather than
the probe: the same 1.5 s hold of zoom-out reaches the *same* camera position at `fps_cap = 60`
and uncapped (~198 fps) - mean pixel difference 0.64 over the game picture, 1.2% of pixels
(moving Sim and HUD), against 42% of pixels when the zoom genuinely differs. The earlier arms and
their instrument:

A temporary probe (since removed) wrapped `sub_00011ED0` and logged, per camera update, the
camera distance `[cam+0x16D8]`, the pitch `[cam+0x16E0]` and the mode, with host steady-clock
timestamps — the same instrument shape `docs/frame-rate.md` used. The walk to live mode followed
`docs/playtest.md`; the zoom was held with `R`/`F` through the `/dev/uinput` keyboard
(`tools/drive_keys.py`'s device, extended with held keys), `fps_cap` from `settings.toml`,
`XBE_PERF=1 XBE_MUTE=1`.

**One arm completed — stock behaviour (`SIMS1_NO_ZOOMRATE=1`) at `fps_cap = 60`**
(`out/shots/zoom_stock60b.log`, live mode at 1396-1399 draws, 60.0 fps):

| segment | wall time | camera updates | rate | distance |
| --- | ---: | ---: | ---: | --- |
| zoom out, full range (10 -> 40) | **0.834 s** | 50 | 60.0/s | 30.0 units |
| zoom in, full range (40 -> 10) | **0.948 s** | 57 | 60.1/s | 30.0 units |

That arm is the stock rate at the reference cadence: 60 calls a second, the rate the wrapper
scales every other frame rate back to.

**The confirmation runs** (`out/shots`, shipped binary, `spectacle -a` captures):
`fps_cap 60` and `fps_cap 0` each held zoom-out for exactly 1.5 s from an identical camera
position, after `out/batching/refocus.sh` - without that step the synthetic key never reaches the
game and *both* the fixed and the gate-off arms show no zoom at all, which is how a broken
measurement looks like a regression. Fixed at 60 fps the zoom responds and lands in the same place
as uncapped.

The live camera runs **mode 2** — the mode whose handler is `sub_00011ED0`, the per-call one —
and the trace shows the distance stepping once per camera update with no delta anywhere in the
step, which is the static case above confirmed at run time.

The uncapped and fixed arms were not completed (runs were interrupted by the release call), so
the claim this document stands behind is the **mechanism**, proven from the disassembly and from
one run-time trace: the step is per call, and the call rate follows the frame rate. The fix
scales that step by the measured call rate; the gate runs the image's own function for anyone
who wants to re-run the A/B on a quiet machine.
