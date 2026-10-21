# Boot crashes and wedges

Each defect met on the way to the first frame, with the guest address, the mechanism and the fix.
The state before each fix is the state of the tree at that moment; the A/B proof is named where one
was run.

## 1. Fault reading `0xFD001804` on the first device creation — fixed by naming `Direct3D_CreateDevice`

**Symptom.** The first build (24 XDK names) booted cleanly through disc mount, `$$XTIMAGE` load,
`TitleMeta.xbx`/`TitleImage.xbx` opens and four guest threads, then 122 ms in, on guest thread 18:

```
[error] fault at guest address FD001804 (host 0x1fd001804)
[error] signal 11 on guest thread 18
  eax 001A1374 ecx 001A11D8 edx 00000180 ebx 00000001 esp D008FD60 ebp D008FD7C esi 001A11D8 edi 83100060
```

**Mechanism.** `0xFD000000` is the NV2A register window; `0xFD001804` is PCI configuration space
offset 4 within it. The faulting instruction is `mov eax, [0xFD001804]` at `0x19A450` inside the
miniport routine `0x19A44A`: it stores `0xFD000000` as the register base and then sets bus-master in
the GPU's PCI command register. The live chain is title `0x12A8D0` → title `0x156900` →
`Direct3D_CreateDevice` `0x18F8B0` → device init `0x196590` → miniport init `0x19A93D` → `0x19A44A`.
`ecx`/`esi` = `0x1A11D8` is the device `0x19FA10` + `0x17C8`, the miniport embedded in the device
(the layout file records the same derivation: `CDevice_Init 0x196590` does `add esi, 17C8h` at
`0x196643`). Nothing on the host backs the NV2A window, so the guest routine faulted.

**Fix.** `config/found-d3d8-core.toml` names `Direct3D_CreateDevice = 0x18F8B0` (each function in
that chain has exactly one caller, so the host body supplants the whole chain). Evidence and the
full stack-value mapping: `docs/d3d8-core-symbols.md`.

## 2. No frame at all after `DATASETS.ARC` — fixed by a host body for `D3DDevice_InsertCallback`

**Symptom.** With 128 names merged, the title created its device
(`d3d: CreateDevice 640x480 format 12 buffers 1 multisample 11 depth 1 format 2E interval 2 flags 120`),
built the Vulkan swapchain, walked 52 surfaces through `Lock2DSurface` (`d3d: BlockOnResource`
stacks `00197D26 00195780 0015B423 00157B28`), opened `d:\audiostr.xwb`, `d:\dsstdfx.bin` (effects
image, 9 effects), `D:\INDEX.IND` and — the last one — `D:\DATASETS.ARC` at 0.133 s. Then nothing:
**0 `vulkan: present` lines and no `perf:` lines in a 23-second run**, no further `open`, no crash,
audio thread mixing silence the whole time (`dsound: mix renders=2500 … sounding=0 plays=0`).

**Mechanism.** `D3DDevice_InsertCallback` was *named* (0x1926F0, body confirmed: writes push token
`0x00081D8C` at 0x19270B, `retn 0Ch`; the title calls it at 0x156B01 on its render thread, beside
the per-frame `D3DDevice_Swap` at 0x156B1A, and at 0x152829) but **this SDK tree has no host body
for it** — `grep -rn InsertCallback sdk/runtime src` found nothing — so the recompiled console body
still ran. On the console it writes a callback token into the push buffer; the D3D interrupt handler
runs `pCallback(Context)` when the GPU reaches it. The SDK has no push-buffer callback path — the
tokens land in a buffer the renderer walks for draws only — so the callback that releases the
engine's semaphore never ran, and the title completed no frame. The same defect and fix are recorded
on the Bustin' Out port (`simsbustinout/docs/status.md`, its `src/game/hooks.cpp`).

**Fix.** `src/game/hooks.cpp`: `HLE_STDCALL(D3DDevice_InsertCallback, 3)` runs `pCallback(Context)`
immediately through `kernel::CallGuest` — the host renderer has no GPU timeline the guest can be
behind. Gated by `SIMS1_NO_CALLBACK=1` so it can be bisected off without a rebuild; with it off the
wedge returns.

**After.** The same 23-second run shape went from 0 presents to the frame loop running: ~60 presents
a second (`vulkan: present 840 …` at 14.4 s), `D:\MOVIES.ARC` opened at 0.71 s, `D:\MODELS.ARC` and
`D:\RLETEXTU.ARC` at 4.3 s, `T:\config.data` (its first save write) at 17.1 s and `D:\AUDIOSTR.ARC`
at 17.2 s. Per-second perf lines show the intro movie's signature: 1 draw a frame with a
0.5–1.2 MB upload (video playback).

## What has not been verified

- Audio, corrected 2026-10-20 23:39: **Linux audio works**. The silent readings that fed this
  note were post-movie log tails and benchmark runs under `XBE_MUTE`. A no-mute run shows the
  guest stream Processing the same 89 packets the Wine/XAudio2 run completes, the mixer peaking
  0.38-0.46 during the intro movie, the SDL callback submitting those peaks, and the sink going
  `RUNNING` unmuted. No defect remains on the port side; whether the monitor's speakers are on
  is a desk question.
- The F3 frame capture has not yet produced a `frame.txt` on this title (the capture directory
  handling is being re-run); the presents logged above are the renderer's own counts, which are the
  honest signal that frames are being handed to the swapchain.
