# Frame rate and game speed

Recorded 2026-10-20. Static evidence is from `out/game.exe` (the flat PE of `default.xbe`, guest
addresses 1:1); every run is the native Linux release build `out/build/linux-release/Sims1`,
windowed 1280x960, `vsync = false`, `fps_cap` as stated, `XBE_PERF=1 XBE_MUTE=1`, logs and
screenshots under `out/shots/` (gitignored, kept on disk). The fix is in `src/game/hooks.cpp`.

## Result

| `fps_cap` | screen | fps | stock: game s per real s | fixed | fixed with `SIMS1_NO_STEP=1` |
| --- | --- | ---: | ---: | ---: | ---: |
| 60 | main menu | 57-58 | 1.018 (window median 1.015) | 1.008 (median 1.0000) | 1.010 (median 1.022) |
| 60 | live mode | 56-59 | 1.031 (median 1.033) | 0.998 (median 1.0000) | 1.043 (median 1.045) |
| 144 | main menu | 137-141 | 2.341 (median 2.387) | 1.0000 (median 1.0000) | 2.330 (median 2.348) |
| 144 | live mode | 55-58 | 1.036 (median 1.034) | 1.0000 (median 1.0000) | 1.051 (median 1.050) |
| uncapped | main menu | 1374-1513 | 22.90 (two windows) | 1.0000 (median 1.0000, 1504 fps) | 25.22 (two windows) |
| uncapped | attract movie | 349-376 | 6.26 (median 5.82) | - | 5.81 (median 5.56) |
| uncapped | live mode | 54-57 | 1.033 (median 1.035) | 1.0000 (median 1.0000) | 1.041 (median 1.037) |

"Stock" is a build with no frame-step change (only the measuring probe); "fixed" is the shipped
change; `SIMS1_NO_STEP=1` is the shipped build with the change switched off, and it reproduces the
stock numbers. Each figure is the engine's own frame delta summed over 20 s (menu) or 30 s (live)
of 2-second windows, divided by the wall time; the median of those windows is beside it. Before the
fix the game runs at `max(1, fps / 60)` times real time plus a few percent; after it, at 1.000.

The game's own clock says the same thing: the front end's 115 s idle timer (below) started the
attract movie **113.8 s** after the main menu appeared at 1481 fps with the fix, and **115.0 s**
after it at 57 fps - but **3.3-3.7 s** after it uncapped without the fix.

Gameplay itself cannot exceed about 58 fps on this machine at any cap (`perf: 52.1 fps 19.19
ms/frame | host 4.02 ... other 15.18`: the title thread, not the renderer, sets the pace), so in
live mode the defect is the few-percent floor effect, not the 2.4x; the front end, which renders
21 draws a frame, is where high frame rates happen and where the stock game ran up to 25x fast.

## The clock: real time, in whole milliseconds

The engine's clock object is the static at `0x20C9DC`, published through `dword_33220C`
(`mov dword_33220C, offset off_20C9DC` at `0x18C855`). Its vtable `0x1FBDF8` holds the stamp
`sub_0015EBC0` (+0xC: `call GetTickCount` at `0x15EBC0`, store at `0x15EBC9`) and the elapsed
reader `sub_0015EBD0` (+0x10): `GetTickCount() - stamp` (`sub eax, [ecx]` at `0x15EBD9`) converted
to seconds by the float 1000.0 at `0x20C9D8` (`fdiv` at `0x15EBED`). `GetTickCount` is the XAPI
routine at `0xC6184`, which returns `*KeTickCount`; on this host `KeTickCount` is the
milliseconds of the host's steady clock since start, written by a 1 ms thread
(`sdk/runtime/kernel/xboxkrnl.cpp`, `InitKernelData`). So the engine measures real time, to the
millisecond.

The image also carries `QueryPerformanceCounter` (`0x17EE31`, `rdtsc`) and
`QueryPerformanceFrequency` (`0x17EE42`, 733,333,333), but the title calls them only from a
debug timer (`sub_000FC130`, "Object unload time") and a random seed (`sub_0011EBB0`); the
others are D3D and DSOUND library code. The frame clock does not use them.

## The frame tick, the quantiser and the delta

The frame tick is `sub_0012FB80` (`EEngine::PreFrameUpdate`, `this` in `ecx`, no stack
arguments): slot +0x18 of the engine frame vtable `0x1F9990`, and of the game's frame subclass
`0x1FB030` through the thunk `sub_00151D70` (`jmp sub_0012FB80`). The frame object is the static
at `0x32D0D0`, built by `sub_0018BD10`. Per frame the tick:

1. stamps `this+0x18` through the clock (`call [edx+0Ch]` at `0x12FBEF`);
2. reads the elapsed time since `this+8` (`call [edx+10h]` at `0x12FC17`, `fstp` to a float at
   `0x12FC1A`), restamps `this+8` (`0x12FC27`) - so successive readings telescope to the real
   time that passed - and adds it to a double total at `0x324238` (`0x12FC2E` / `0x12FC3B`);
3. calls the quantiser `sub_0012F640` with that float (`push ecx` at `0x12FC38`, call at
   `0x12FC41`, the quantiser's only call site);
4. makes the delta from the frame object's byte at `this+5` (test at `0x12FC46`):
   - **byte set** (the "fixed-step" path): `ticks * tick size` - `fild [0x20C14C]` at `0x12FC4F`,
     `fmul [0x324220]` at `0x12FC55`;
   - **byte clear** (the default path): the elapsed clamped to `[tick size, 15 x tick size]`
     (`fcom [0x324220]` at `0x12FC64`; the 15.0 at `0x1EF674`, `fmul` at `0x12FC81`) and averaged
     with the two previous clamped values (`0x12FCC0`-`0x12FCDA`, the 1/3 at `0x1F2614`; the
     first frame seeds the history from the tick size, `byte_20C174` at `0x12FC9C`);
5. stores the delta at **`[0x20C150]`** (`fstp` at `0x12FCE0`) and its reciprocal at `0x20C154`
   (`0x12FD11`; 0 when the delta is 0, `0x12FCF9`; nothing reads it).

**The delta global.** `[0x20C150]` has **208 references in 112 functions: 205 reads and 3
writes** - the tick at `0x12FCE0` and a scoped scale/restore pair (`sub_00113270` saves it to
`[esi+8Ch]` and writes it scaled at `0x113312`; `sub_00112E10` puts it back at `0x112E16`). One
writer per frame, readers everywhere: it is the engine's one frame delta (the sibling Bustin' Out
counts 143 reads, The Urbz 97).

**The tick size** is the float at `0x324220`, written once by the frame constructor
`sub_0012F9B0`: 0.02 (`0x12F9F5`) when `dword_1EFA70` is 1, otherwise 1/60 s (`0x12FA01`). Its
readers are the quantiser (`0x12F6A7`, `0x12F6E4`), the tick (`0x12FC55`-`0x12FCA5`) and two
debug displays (the profiler print `sub_00141220` at `0x14122D` and the "CPU:" overlay
`sub_0014AE50` at `0x14AFD6`).

**The quantiser** `sub_0012F640` (`this` in `ecx`, one float argument, `retn 4` at `0x12F705`)
divides by the tick size and rounds **up** - `sub_001763E2` is the CRT `ceil` (it loads the
control word `0x1B3F`, rounding toward +infinity, from `0x2172C0`) - then truncates with `_ftol`
(`sub_001756D4`). On the byte-set path it quantises not the argument but the largest of four
history floats (`0x20C15C`/`0x20C160`/`0x20C168`/`0x20C16C`) and clamps the count to 1..15
(`0x12F6C0` / `0x12F6D1`). Either way it stores the count at **`[0x20C14C]`** (`0x12F6C3` /
`0x12F6FA`) and adds it to the running total at **`[0x324230]`** (`0x12F6FF`).

**Which path runs.** The constructor sets the byte (`mov [esi+5], al` with `al = 1` at
`0x12F9E9`), but the game's frame subclass init `sub_00151D20` (vtable `0x1FB030` +0xC) clears it
again after the base init (`mov byte ptr [esi+5], 0` at `0x151D65`). The probe below read the
byte as **0 on every screen**: the default path runs in play. So every frame shorter than
16.7 ms advances the world by 16.7 ms, and at the 60 fps cap the frames the host hands over early
are floored too (the stock 1.02-1.03 at 60).

## The fix (`src/game/hooks.cpp`)

Two wrappers, both switched off by `SIMS1_NO_STEP`:

- **`sub_0012F640` (the quantiser)** measures the frame's real length on the host's steady clock
  between successive calls (one a frame, from the same point in the tick as the engine's own
  reading; the first frame uses the engine's reading), keeps the engine's ceiling (15 ticks of
  1/60 s = 250 ms), and hands it over as a count of 1 ms ticks times a tick size of
  `dt / count` written into `[0x324220]`, so the caller's `count x size` is the frame's length to
  the float. It stores the count at `[0x20C14C]`, adds it to `[0x324230]`, returns it in `eax`
  and pops its argument (`retn 4`).
- **`sub_0012FB80` (the frame tick)** writes nothing of its own: it sets the fixed-step byte at
  `this+5` for the duration of the original call, so the tick makes the delta by its product
  path (`0x12FC4F` / `0x12FC55`) instead of the clamped three-frame average, and afterwards puts
  the byte and the engine's tick size back. Nothing else reads either during the tick: the
  byte's other readers are the quantiser's test (replaced) and the tick-count getter
  `sub_0012F710`, whose only caller `sub_0014B350` (application vtable slot +0x14,
  `0x1F9544` / `0x1FAB5C`) runs from the post-frame update `sub_0012FD80` at `0x12FDDE`, after
  the tick has returned; the tick size's other readers are the two debug displays.

Nothing depends on the tick's unit: `[0x20C14C]` is read only by the quantiser, the tick
(`0x12FC4F`) and that getter (which sees the restored byte and returns 1, as before), and the
running total `[0x324230]` only by `sub_0012AEB0` (`0x12AEBA`, copied to `0x323DD4`).

**Why the host clock and not the engine's reading.** The first version kept the engine's
millisecond reading (1 ms ticks, the one-tick floor carried forward as a debt so the sum of the
steps stayed the sum of the readings). It measured 0.990 / 1.0000 / 1.0000 at 60 / 144 in the
menu and live mode, but **1.501 in the uncapped front end**: at 1501 fps most frames are shorter
than 1 ms, read 0 ms, and each still had to take a 1 ms step. The host clock the guest's
`KeTickCount` is made from has no such floor; with it the uncapped front end measured 1.0000 at
1504 fps.

## How it was measured

A temporary probe (removed; it is not in the tree) wrapped the two functions above and, every
2 s of wall time on the host's steady clock, logged the sum of `[0x20C150]` after each tick, the
sum of the quantiser's elapsed argument, the frame count and the byte at `this+5`:

```
sims1 speed: game 46.7100 s measured 20.0500 s real 20.0500 s ...   (shape of the line; per 2 s)
```

The "measured" column (the engine's own elapsed readings) equalled the wall time in every run
(ratio 0.9998-1.0001 except one 60 fps menu span at 1.012) - the clock is right, the quantiser is
what was wrong. Runs: `out/shots/probe60.log` (stock, 60), `stock144.log`, `stock0.log` (stock),
`host60.log`, `host144.log`, `host0.log` (fixed), `nostep60.log`, `nostep144.log`,
`nostep0.log` (fixed, `SIMS1_NO_STEP=1`); every run walked boot -> title -> main menu (20 s
measured) -> Create a Sim -> household -> live mode (30 s measured), driven by `SIMS1_STEP`
tokens (`docs/playtest.md`). The uncapped stock "main menu" row uses the first two windows after
the menu appeared, because without the fix the attract movie took over 3.3-3.7 s later; the 20 s
span after that measured the movie (the "attract movie" row).

### The title's own clock: the 115 s idle timer

The front-end manager's update `sub_000763E0` adds the delta to an idle timer at `[mgr+0x1804]`
every frame (`fld [0x20C150]` / `fadd [esi+1804h]` / `fstp` at `0x7645D`-`0x7646E`), zeroes it on
input (`0x76497`), and starts the attract movie (`open D:\MOVIES.ARC`, 0 draws) once it exceeds
115.0 (the float at `0x1F1C0C`, `fcomp` at `0x764A4`). Left alone on the main menu after the
title's `START`:

| build | fps | menu appeared (first 21-draw second) | attract `open D:\MOVIES.ARC` | real seconds | game s per real s |
| --- | ---: | ---: | ---: | ---: | ---: |
| stock, uncapped (`stock0.log`) | ~1370 | 27.13 s | 30.85 s | 3.7 | ~31 |
| `SIMS1_NO_STEP=1`, uncapped (`nostep0.log`) | ~1510 | 27.14 s | 30.43 s | 3.3 | ~35 |
| fixed, uncapped (`attract_fix0.log`) | 1481 | 31.13 s | 144.91 s | 113.8 | 1.01 |
| fixed, 60 (`attract_fix60.log`) | 57 | 37.74 s | 152.73 s | 115.0 | 1.00 |

(The per-second draw line marks the menu's arrival only to the second, and the uncapped stock
timer also ran during the loading screen at up to 45x, hence "~".)

## Per-call consumers: measured, none off

The siblings found things that step per call instead of per delta (pad auto-repeat, menu
held-repeat gates, camera rates). Here every input path that a held direction can reach in the
front end was measured with a temporary probe (removed) at 60 and uncapped, before and after the
fix, holding the key through the `/dev/uinput` keyboard (`SIMS1_STEP` pulses are 130 ms, too short
for a hold):

- **The main menu** reads its pad through `sub_00130780` (action, out pad; `retn 8`), which
  reports only the press edge (bit 2 of the action state, built by `sub_001302E0`: `|2` when all
  of the action's mask bits are down now and were not at the previous poll). Holding Down for
  6.0 s produced **exactly one** cursor move (action 2, from `0x7625A`; cursor 0 -> 2, "Play The
  Sims" being hidden) with the fix at 60, 144 and uncapped (`host*.log`, `in_fix*.log`) and with
  `SIMS1_NO_STEP=1` at 60, 144 and uncapped (`nostep60.log`, `nostep144.log`,
  `menuhold_no0.log`: one move at ~1400 fps, `sims1 menu: 80255148 cursor 0 -> 2`). There is no
  held repeat to be fast.
- **The Create-a-Sim keyboard** (the name grids) uses the widget input bindings, whose fire test
  `sub_00146880` repeats a held action after an initial delay (`+0x4`, 0.33 s) at a period
  (`+0x8`, 0.125 s), timing both with accumulators that add the delta every frame (`fld [0x20C150]`
  / `fadd [esi+14h]` and `[esi+18h]` at `0x146857`-`0x14686D`). Fires during an 8.0 s hold of
  Right / Down (`kb_*.log`):

  | build | `fps_cap` | fps | Right | Down |
  | --- | --- | ---: | ---: | ---: |
  | fixed | 60 | 55 | 58 (7.3/s) | 59 |
  | fixed | uncapped | 577 | 62 (7.8/s) | 62 |
  | `SIMS1_NO_STEP=1` | 60 | 51 | 59 (7.4/s) | 59 |
  | `SIMS1_NO_STEP=1` | uncapped | 592 | 204 (25.5/s) | 206 |

  The repeat is delta-driven: it was 3.4x fast uncapped only because the delta was, and the
  frame-step fix alone brings it to the 60 fps rate. Scaling it as well would correct it twice.
- **Live mode** never runs faster than about 58 fps on this machine at any cap (the table above),
  so no per-call consumer there can step faster uncapped than at 60; none could be measured off,
  and none was hunted further.

Decision: **no per-call wrapper was added.** Nothing measured off once the delta was right.

## Environment switch

| Variable | Effect when set (and not `"0"`) |
| --- | --- |
| `SIMS1_NO_STEP` | Both frame-step wrappers run the image's own functions untouched: the 1/60 s floor and three-frame average, game speed tied to frame rate. |

## Throughput: where the frame goes, and four levers that do not move it

Recorded 2026-10-20, uncapped (`fps_cap = 0`, `vsync = false`), borderless 3440x1440, render
scale 3.000, in a loaded household at 1450-1760 draws a frame. Driven by the `docs/playtest.md`
walk, 10 steady-state `perf:` seconds per run, `hdd/` wiped before every run so each build loads
the same household.

**The ceiling on this machine is 62.9 fps** (three baseline runs: 62.7, 64.8, 61.1; per-run sd
1.6-2.1). The 60 fps normally seen is the `fps_cap` setting, not the engine.

**The title thread is the whole critical path.** Every live-mode run logs
`title thread per frame: recording X ms, waiting 0.00 ms (0.0 waits)`: the title thread never
waits for the renderer, so the render thread's 3.6 ms is fully hidden and work taken off it buys
nothing. Of a 15.9 ms frame:

| Title-thread leaf | ms/frame | share |
| --- | ---: | ---: |
| guest game logic | ~11.4 | 73% |
| inside XDK draw calls (`in XDK draws`), of it `sendstate` 1.3 | 2.4 | 15% |
| renderer command recording | 1.8 | 12% |
| *(render thread, overlapped: draw 3.3, clear 0.07, present 0.23)* | *3.6* | *not on the path* |

Four build-level levers were each built and measured against that baseline. **None is a win:**

| Build | fps (mean of 10 s) | guest ms | vs baseline |
| --- | ---: | ---: | ---: |
| baseline, `-O2` guest / `-O3` host, `-march=x86-64-v2` | **62.9** | 12.3 | - |
| `-march=znver2` (this CPU: AVX2, BMI1/2, FMA) | 60.6 | 12.7 | -4% |
| generated guest code at `-O3` | 60.4 | 12.8 | -4% |
| clang PGO, two merged gameplay profiles | 57.9 | 13.9 | -8% |

Notes on the method, because two of these figures were wrong on the first attempt:

- An earlier PGO run measured -34%. That number was **contaminated**: its build directory had a
  different `hdd/` (an empty one against a saved household), so the two builds loaded different
  scenes. Re-run with `hdd/` wiped for both, the honest figure is -8%.
- The PGO build was checked to be use-only (`grep profile-instr out/build/linux-pgo/build.ninja`
  shows `profile-instr-use` alone, no stacked `-generate`), and its diagnostics were left
  unsuppressed: 2 `-Wprofile-instr-out-of-date` and a handful of
  `no profile data available` for vendored SDL and libm sources only. The guest code and the SDK
  runtime matched the profile, so the result is PGO genuinely applied, not PGO misconfigured.
- The profile must come from gameplay. A first profile collected over one boot-to-household run
  was dominated by texture decode (`gpu::DecodeLevel`, `gpu::CopySurfaceMemory`, `sat<uint8_t>`),
  which is loading work: in steady live mode the counters read `0.0 tex uploads, 0.0 new tex`.
- Collecting a profile at all needs `-fprofile-continuous`. The harness ends a run with `SIGTERM`
  and `sdk/runtime/app/main_sdl.cpp` calls `_exit(128 + sig)`, which skips the profile writeout;
  without continuous mode every `.profraw` is 0 bytes.
- `-march=znver2` and guest `-O3` both lose on instruction-cache pressure across 12889 large
  recompiled functions. `[INFERENCE]`: not separately measured, but consistent with both losing
  by the same ~4% while the host-side `draw` time is unchanged.

The sibling ports' renderer work is already inherited and is **not** a remaining lever here: the
SDK branch descends from `04bea96` (SendState dirty-masking, host built optimised) and `7575ecb`
(no per-draw re-recording of what the last draw bound).

What is left, and its honest size: `sendstate` (1.3 ms) plus command recording (1.8 ms) are the
only title-thread costs the host owns. Removing **all** of both would leave 11.4 ms, about 88 fps;
a realistic cut is 8-10%, so roughly 70 fps. Guest game logic, 73% of the frame, is the title's
own code and no build flag reaches it. No profiler was available to attribute inside it
(`perf` is absent and `/proc/sys/kernel/yama/ptrace_scope` is 1, so `gdb` cannot attach to a
separately launched process).

## Not covered

- Live mode above ~58 fps: this machine cannot run the title thread faster in a household, so the
  fix's behaviour there at 144 fps and beyond is the front end's measurement, not a live one.
- The console ran the menus and the game at presentation interval 2 (`d3d: Reset ... interval 2`
  in every log; interval 1 for movies), i.e. 30 fps. The host ignores the interval. Anything that
  steps per frame and was tuned for 30 fps would run at the host's frame rate; none was found in
  the paths measured above, and live-mode camera/cursor rates were not compared against a console.
