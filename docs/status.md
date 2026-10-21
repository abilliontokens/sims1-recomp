# Bring-up status

Recorded 2026-10-20. Every number below was observed on this machine or read from a file in this
repository. Where a claim has not been exercised at runtime it says so; that is the authoritative
distinction in this document.

## Where the port stands

| Stage | Result |
| --- | --- |
| Disc image read | 14 files, 412924266 bytes of file data, partition base `0x00000000` (`docs/iso-extract.md`) |
| XBE identified | `assets/default.xbe`, 2183168 bytes, sha1 `40ab6f97e8ee3bf4102a5a7820dcb8047fc30097`, title `0x4541002F` (EA-47), retail, base `0x10000`, entry `0xC7B1E`, built 2003-03-11, **XDK 5233** — every library |
| XDK signature set | unsupported by the SDK; `sdk/xdk/5233/signatures.toml` seeded from 5558 by `tools/sig_bootstrap.py`, then **signed from this image** (132 byte signatures); a fresh `xbe_symbols` scan reproduces all 128 named addresses (`docs/xbe-analysis.md`) |
| Data layout | `sdk/xdk/5233/layout.toml`, 45 of 45 keys proven from this image; the 5233 `CDevice` is 0x2040 bytes with its miniport at `+0x17C8`, and 26 of 31 offsets differ from 5558's (`docs/layout-5233.md`) |
| Symbols | **128 of 242** `[symbols]` and **11 of 12** `[data]` named. The remaining 114 zeros: 34 XNET + 4 BINK + 2 XONLINE for sections this image has none of; 66 library names and 8 `.text` CRT names proven **absent from this image** by three concording methods — per-name disassembly evidence (`docs/d3d8-core-symbols.md`, `docs/dsound-symbols.md`, `docs/xtlid-and-xapi.md`), the seeded constant matcher, and neighbour-order alignment with 121 anchors (`docs/align-symbols.md`) |
| Kernel imports | 123 imported, **123 covered, 0 uncovered** (`docs/kernel-coverage.md`) |
| Recompilation | 12889 functions, 541952 instructions, 1741548 of 1954908 code bytes (89.1%), 225 jump tables |
| Native Linux build (Vulkan + SDL3) | builds and links: 494 targets, ~125 s clean, ~40 s incremental; `out/build/linux-release/Sims1`, 16202696 bytes |
| Windows build (D3D12 + XAudio2), cross-compiled | builds and links: `out/build/windows-cross/Sims1.exe`, 13908480 bytes; **under Wine 11.20 it boots the title, creates its D3D12 device, runs the movie path and mixes audio** — never run on real Windows |
| Boot | starts, mounts the disc, loads `$$XTIMAGE`, resolves every kernel import, creates the Direct3D device, plays the intro movies |
| Picture on screen | intro movies, title, loading, main menu, Create a Sim and live mode; F3 capture 640×480, 19843 distinct colours, 0.0 % black |
| Gameplay | **a playable household in live mode, unattended, 17 of 17 runs** (`docs/playtest.md`); sustained 1396–1401 draws a frame, 35k verts, 3.3 MB upload |
| Game speed vs frame rate | **1.000** simulated seconds per real second at `fps_cap` 60 / 144 / uncapped after the host-clock quantiser fix (was 2.34 / 22.9), cross-checked against the menu's own 115 s idle timer (`docs/frame-rate.md`) |
| Picture rect | measured: **640×432 at y=24** (mode height − 48 and y-offset 24 in the renderer, confirmed by F3 rows 24..455); the present runs `srcPx (0,72 1920x1296)`, no overscan bars (`docs/picture-rect.md`) |
| Cheats | no pad-sequence table exists in this game — codes are words typed on the main menu's trigger-held keyboard (`sub_0005E6A0`); the F1 panel types them through the menu's own update; SIMS, FISH EYE and GARGAMEL confirmed visually, the other four by log (`docs/cheats.md`) |
| F1 / F2 panels | verified on screen: F1 settings (with the Cheats section), F2 frame times |
| Audio, Windows/Wine | **sounding**: XAudio2 mixed 89 stream packets at peak 0.44 during the Wine run's intro movie |
| Audio, Linux | **silent**: the same run shape on SDL mixes 48 voices at `sounding=0`, `plays=0`, peak 0.0000 — the Linux silence is in the SDL audio path, not in the guest's DirectSound usage, because the identical guest code is audible through XAudio2 (`docs/boot-crash.md`) |

## The two boot defects, in one line each

1. An unnamed `Direct3D_CreateDevice` (0x18F8B0) ran the NV2A miniport init and faulted reading the GPU's PCI config at `0xFD001804` — fixed by naming it.
2. `D3DDevice_InsertCallback` (0x1926F0) had a name but **no host body anywhere in the tree**, so its console body wedged the title before the first frame — fixed by a host body in `src/game/hooks.cpp` that runs the callback immediately.

Both with full mechanism and A/B notes in `docs/boot-crash.md`.

## What this title does NOT have

Findings, not gaps; each one removed work:

- **No `.text` CRT math library beyond acos/asin/pow.** `crt_sin`, `crt_cos`, `crt_tan`, `crt_atan`, `crt_log`, `crt_log10`, `crt_sqrt` are absent — no byte hashes, no name strings, no worker shape; the game computes them inline (`docs/xtlid-and-xapi.md`).
- **No 3D sound, HRTF, I3DL2, effect-data or output-meter DSOUND code**, and no `Lock`/`Unlock`, `StopEx`, `DirectSoundCreateBuffer` or `XAudioDownloadEffectsImage`: it links about 38 % of Bustin' Out's DSOUND functions (`docs/dsound-symbols.md`).
- **No XGRAPHC or XMV names in any signature set**, and the SDK binds none: both sections run their recompiled console code by design, as on every sibling port; the real surface is 14 entry points the game calls directly (`docs/xgrph-xmv-symbols.md`).
- **No pad-sequence cheat system**: codes are typed words, not button sequences (`docs/cheats.md`).
- **XDK 5233 numbers its render and texture-stage states exactly as 5849 does** (`docs/d3d8-state-symbols.md`) — the per-build override table that 3925 needed is deliberately absent.

## Open work, in order of value

1. **Linux audio is silent** while XAudio2 (Windows/Wine) is audible on identical guest code — the defect is localized to the SDL audio path; no investigation started.
2. **Real Windows run**: the exe cross-compiles and runs under Wine; it has never touched real Windows or real Direct3D 12 drivers.
3. **A real gamepad**: none has ever been plugged into the test machine.
4. **Hor+ ultrawide**: the frame target widens, but the title's own aspect path has not been analysed the way Bustin' Out's was (`docs/guest-projection.md` there is the model).
5. **Full-screen movies are trimmed** by the measured 24-row picture crop (they are copied raw over all 480 rows); a movie-path exception may be worth it (`docs/picture-rect.md`).
6. Four of the seven cheat codes are confirmed by log only (`docs/cheats.md`).

## Reproducing

```sh
./build.sh                                   # Linux; writes config/game.toml on first run
cmake --preset host-tools && cmake --build --preset host-tools   # then windows-cross for the exe
./release.sh                                 # Sims1-linux-x64.tar.zst + Sims1-win64.zip
```

Drive it unattended with `tools/shot_game.sh <tag>`; the walk and its evidence are `docs/playtest.md`.
