# Bring-up status

Recorded 2026-10-20, Windows rows added 2026-10-21. Every number below was observed on this machine
or read from a file in this repository. Where a claim has not been exercised at runtime it says so;
that is the authoritative distinction in this document.

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
| Windows build (D3D12 + XAudio2), cross-compiled | builds and links: `out/build/windows-cross/Sims1.exe`, 13908480 bytes; under Wine 11.20 it boots the title, creates its D3D12 device, runs the movie path and mixes audio |
| Windows build, native | `build.bat` on VS 2022 BuildTools + LLVM clang 23.1.3 configures, recompiles the whole XBE and links `out/build/release/Sims1.exe` in **108 s**, 388 ninja edges |
| Windows run, real hardware | **the v0.2.0 release zip's own `Sims1.exe` runs on Windows 11 26200** — RTX 5060 Ti, D3D12, 3840×2160 borderless, 640×480 guest at render scale 4.5. It mounts `assets\Sims, The (USA).xiso.iso` as `D:` with nothing else in `assets\`, reports the 14 files on it, matches the XBE sha1, and reaches the EA/Maxis title screen and the attract demo at 60.0 fps / 16.74 ms; two screen grabs 1.2 s apart differ on 1.7-7.9 % of pixels, so frames are advancing |
| Audio, real Windows | **sounding**: XAudio2 mastering voice at 48 kHz stereo float, `submitted=500 rendered=500 queued=2 peak=0.4605` at 5 s, and the process's own Windows audio session metered 0.023-0.051 continuously (WASAPI `IAudioMeterInformation`, 40 samples at 10 Hz, 100 % non-zero), unmuted at session volume 1.00 on the default endpoint. Owner-confirmed audible |
| Controller, real hardware | **a DualSense (PS5) pad works**, on the shipped exe and a local build: SDL 3.4.16 opens it by name (`input: controller 1 plugged in: DualSense Wireless Controller`) and the guest's own `XInputGetState` reads it — 658 of 748 pad-change packets carried an intermediate analogue byte (R2 ramping `07 35 48 6C 99 B2 B7 C7`), a value the keyboard-to-pad layer cannot produce since it only ever writes `00` or `FF`. Owner-confirmed in play |
| Boot | starts, mounts the disc, loads `$$XTIMAGE`, resolves every kernel import, creates the Direct3D device, plays the intro movies |
| Picture on screen | intro movies, title, loading, main menu, Create a Sim and live mode; F3 capture 640×480, 19843 distinct colours, 0.0 % black |
| Gameplay | **a playable household in live mode, unattended, 17 of 17 runs** (`docs/playtest.md`); sustained 1396–1401 draws a frame, 35k verts, 3.3 MB upload |
| Game speed vs frame rate | **1.000** simulated seconds per real second at `fps_cap` 60 / 144 / uncapped after the host-clock quantiser fix (was 2.34 / 22.9), cross-checked against the menu's own 115 s idle timer (`docs/frame-rate.md`) |
| Throughput ceiling | live mode **175-244 fps** (owner-confirmed in play) after the kernel wakeup fix (SDK `2ea4a5c`): every guest dispatcher wait used to sleep on one process-wide condvar and every signal woke all waiters, and this title's semaphore-based guest lock broadcast on every release - the title thread was 19-27% blocked, 1400-2900 voluntary switches a frame, invisible to every in-process counter until `/proc` sampling found it. Earlier ceilings quoted in this table (58, then 62.9) were measured under that storm and are obsolete; draw batching is a measured dead end (`docs/draw-batching.md`) and no build flag moves it (`docs/frame-rate.md`) |
| Cheats | no pad-sequence table exists in this game — codes are words typed on the main menu's trigger-held keyboard (`sub_0005E6A0`); the F1 panel types them through the menu's own update; SIMS, FISH EYE and GARGAMEL confirmed visually, the other four by log (`docs/cheats.md`) |
| F1 / F2 panels | verified on screen: F1 settings (with the Cheats section), F2 frame times |
| Audio, Windows/Wine | **sounding**: XAudio2 mixed 89 stream packets at peak 0.44 during the Wine run's intro movie |
| Audio, Linux | **works** — the earlier "silent" finding was a measurement artifact. Proven end to end (`out/shots`, run of 2026-10-20 23:39): the guest stream Processes and completes exactly the 89 packets the Wine/XAudio2 run does, the mixer peaks 0.38-0.46 during the intro movie, the SDL callback submits those same peaks, and the sink goes `RUNNING`, unmuted. The silent readings came from post-movie log tails and from every benchmark running under `XBE_MUTE`. If no sound is heard on hardware, check the HDMI monitor's own volume — the machine's only sink is `hdmi-stereo` at 40% |

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

1. **Hor+ ultrawide**: the frame target widens, but the title's own aspect path has not been analysed the way Bustin' Out's was (`docs/guest-projection.md` there is the model).
2. **Full-screen movies are trimmed** by the measured 24-row picture crop (they are copied raw over all 480 rows); a movie-path exception may be worth it (`docs/picture-rect.md`).
3. **A DualSense resting trigger reads `0x04-0x06`**, not `0x00`, straight out of SDL's axis; nothing in this title has been seen to act on it, and the cheat gate wants both triggers fully held, but no dead zone is applied anywhere in the pad path.
4. Four of the seven cheat codes are confirmed by log only (`docs/cheats.md`).
5. Only one pad has been tried. Xbox and Switch controllers go down the same SDL path and are untested here.

## Reproducing

```sh
./build.sh                                   # Linux; writes config/game.toml on first run
cmake --preset host-tools && cmake --build --preset host-tools   # then windows-cross for the exe
./release.sh                                 # Sims1-linux-x64.tar.zst + Sims1-win64.zip
```

Drive it unattended with `tools/shot_game.sh <tag>`; the walk and its evidence are `docs/playtest.md`.
