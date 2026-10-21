# The Sims — original Xbox, statically recompiled for PC

A native port of **The Sims** (original Xbox, USA retail) to Linux and Windows by static
recompilation of the game's own executable: the retail `default.xbe`'s x86 code is translated to
C++ once, at build time, and runs against [XboxXBERecomp](https://github.com/TGP482/XboxXBERecomp)'s
host runtime — Vulkan and SDL3 on Linux, Direct3D 12 and XAudio2 on Windows. No Wine, no emulator,
no original Xbox hardware.

This is the fourth Maxis console Sims title ported with this framework, after
The Urbz, The Sims: Bustin' Out and The Sims 2, and the first on **XDK 5233**, a build the SDK
shipped no signatures for — the 5233 signature set, data layout and symbol proof in this repository
are this port's own work.

## What works

- Boots from the disc image, plays its intro movies, and reaches its menus, Create a Sim and a
  **playable household in live mode**, unattended, every run tried (17 of 17; `docs/playtest.md`).
- The whole frame loop presents at ~60 fps with 860–2208 draws a frame in live mode.
- The **F1 settings panel** (display mode, resolution, aspect, ultrawide, vsync, frame cap, HDR on
  Windows, render scale, anisotropic filtering, key bindings, and this game's own typed-word cheats
  as toggle rows) and the **F2 performance panel** (frame-time graph, fps/ms, backend, counters).
- Keyboard and mouse as controller port 0, plus a real gamepad through SDL3 — a DualSense (PS5) pad
  reaches the title's own `XInputGetState`, analogue triggers and all.
- Game speed is real time at any frame rate: the engine's 60th-of-a-second quantiser is replaced
  with a host-clock tick, measured 1.000 simulated seconds per real second at 60, 144 and uncapped
  (`docs/frame-rate.md`).
- The picture rect is measured from the game's own renderer — it draws 640×432 at y=24 inside its
  640×480 back buffer — so there are no overscan bars (`docs/picture-rect.md`).
- **Runs on real Windows.** The released `Sims1.exe` boots, mounts the disc image straight out of
  `assets/`, draws through Direct3D 12 and sounds through XAudio2 (Windows 11 26200, RTX 5060 Ti;
  `docs/status.md`).

## What does not (yet)

- Full-screen movies are trimmed by the measured 24-row picture crop: they are copied raw over all
  480 rows, so the crop takes 24 rows off them (`docs/picture-rect.md`).
- Hor+ ultrawide widens the frame target, but the title's own aspect path has not been analysed.

The authoritative list, with evidence, is `docs/status.md`.

## Building (Linux)

Bring your own disc: drop the disc image into `assets/` as a `.iso` and that is the whole setup —
the port mounts it as the console's `D:` at startup, and `build.sh` takes `default.xbe` back out of
it for the recompiler (the build needs that one file on disk). Extracting the 14 disc files into
`assets/` yourself with `tools/xiso_extract.py` works too, and is not faster.

```sh
./build.sh                 # configures, writes config/game.toml, builds out/build/linux-release/Sims1
```

Requirements: clang, cmake ≥ 3.25, ninja, python3, a Vulkan loader. SDL3, ImGui, Zydis, toml++ and
the shader compilers are fetched at configure time. The first build recompiles the whole XBE
(12889 functions; about two minutes on a recent machine).

## Building (Windows, cross-compiled from Linux)

```sh
cmake --preset host-tools && cmake --build --preset host-tools
cmake --preset windows-cross && cmake --build --preset windows-cross
```

`cmake/windows-cross.cmake` drives clang-cl + lld-link against an xwin-downloaded Windows SDK;
`out/build/windows-cross/Sims1.exe` is the result. On Windows itself, `build.bat` does the same
with a local MSVC and LLVM — about two minutes for the whole XBE on a 12-thread desktop.

## Running

The executable finds the game beside it in `assets/`: the disc image as a `.iso`, or the disc's
files extracted there. Runtime switches the siblings share:

- `XBE_PERF=1` — per-second draw/upload/voice counters.
- `XBE_CAPTURE_DIR=cap` + **F3** — dump a frame (`frame.txt`, per-target BMPs) and every guest
  thread's stack.
- **F1** settings, **F2** frame times.
- `SIMS1_AUTOSTART=1` — a repeating pad cycle through the intro movies (a self-test).
- `SIMS1_NO_STEP=1`, `SIMS1_NO_CALLBACK=1` — switch the frame-step fix and the push-buffer
  callback body off, to bisect against the stock behaviour.

## Repository layout

| Path | What it is |
| --- | --- |
| `config/game.toml` | the recompiler input: XDK symbol addresses (128 of 242 named; the rest proven absent from this image) and data addresses |
| `config/found-*.toml` | per-area symbol proofs, merged by `tools/merge_symbols.py` |
| `sdk/xdk/5233/` | this port's XDK 5233 signature set (seeded from 5558, then signed from this image) and the proven data layout |
| `src/common/` | the overlay (F1/F2), keyboard/mouse-as-pad, the title record, the cheat table |
| `src/game/` | the game hooks: the frame-step quantiser fix, the `D3DDevice_InsertCallback` body, the cheat entry |
| `docs/` | every proof: symbol naming, layout, boot defects, frame rate, picture rect, cheats, playtest |
| `tools/` | disc extraction, XBE analysis, symbol merging/alignment, the unattended driving loop |

## Legal

Bring your own disc. The disc image, `default.xbe`, everything extracted into `assets/`, the
generated recompilation and all build output stay out of git; only names, addresses, proofs and
port code are tracked. Nothing here distributes EA's or Maxis's content.
