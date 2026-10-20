# XGRPH and XMV: names, host bodies and the entry surface

Scope: the `XGRPH` section (XGRAPHC 5233, `0x1A1DA0`, 79328 bytes) and the `XMV` section (XMV 5233,
`0x1BF060`, 162700 bytes) of `assets/default.xbe` (sha1 `40ab6f97e8ee3bf4102a5a7820dcb8047fc30097`).

Sources read:

- `out/game.exe` in the shared IDA database, with guest addresses 1:1.
- The XBE bytes, disassembled independently with `objdump`.
- `generated/game/x86_func_mapping.cpp`, which lists 481 starts in XGRPH and 175 in XMV.
- The four signature sets, `config/ref/5558-signed.toml` and the SDK runtime source.
- The sibling The Sims: Bustin' Out (XDK 5558, `simsbustinout/assets/default.xbe`), whose `.XTLID` names
  these libraries' exports.

Nothing was built or run.

## Answer

1. **No `[symbols]` name belongs to XGRPH or XMV.** Each of the 242 names in `config/game.toml` carries a
   section tag in at least one signature set, and no two sets disagree. The tally is D3D 105, DSOUND 77,
   XNET 34, `.text` 15, XPP 5, BINK 4 and XONLINE 2, which sums to 242. No set tags any name, data symbol or
   anchor with `XGRPH` or `XMV`, and no set's `xtlid` is a XGRAPHC (`0xDxxxx`) or XMV (`0xExxxx`) id.
2. **The SDK has no host body for any XGRAPHICS or XMV function.** Both sections run their original console
   code, recompiled. That is by design (`sdk/runtime/xdk/d3d8.cpp:2`: "Resource creation, locking and the XG
   helpers stay recompiled: they only manage memory"). No XMV body exists anywhere in the SDK.
3. **Nothing to emit.** `config/found-xgrph-xmv.toml` holds an empty `[symbols]` table. Even a proven XG or
   XMV name could not merge: `tools/merge_symbols.py:181-182` refuses a name the scanner does not know ("it
   would never be consulted"), and the runtime binds only names with an `HLE_*` body. Chasing these names
   removes no trap, so this slice does not chase them. As a cross-check, none of the other six
   `config/found-*.toml` files, as they stood when this was written, places any name inside either range.
4. **The real surface is 14 entry points:** 6 into XMV and 8 into XGRPH, all called directly from the game's
   `.text`, plus 3 XGRAPHC static initializers run by the CRT. Each of the 14 is, instruction for instruction
   or nearly, an export that Bustin' Out's `.XTLID` publishes. Their `ret`, `regs`, `calls` and stable
   constants are recorded below for whoever writes a host body some day.
5. **What the movie actually needs lives outside these two sections:** D3D and DSOUND names, this build's
   CDevice offsets, and kernel imports. All of it is owned by other slices, and none of it is an XMV name. The
   last section of this document lists that surface.

## 1. Section membership of the 242 `[symbols]` names

| Set | D3D | DSOUND | XPP | `.text` | XNET | BINK | XONLINE | no `sec` | XGRPH | XMV |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3925 | 103 | 66 | 5 | 18 | 34 | 4 | 2 | 17 | 0 | 0 |
| 5233 (seed) | 105 | 77 | 5 | 7 | 0 | 0 | 0 | 48 | 0 | 0 |
| 5558 | 105 | 77 | 5 | 7 | 0 | 0 | 0 | 48 | 0 | 0 |
| 5849 | 100 | 63 | 5 | 15 | 34 | 4 | 2 | 17 | 0 | 0 |
| union over the four and `config/ref/5558-signed.toml` | 105 | 77 | 5 | 15 | 34 | 4 | 2 | **0** | **0** | **0** |

The per-set rows count each set's own records. 3925 has 249: it lacks `D3DDevice_InsertCallback` and
`D3DDevice_Reset`, and adds nine names this config does not have (`BinkOpen`, `BinkClose`,
`BinkCopyToBuffer`, `D3DDevice_Present`, ...). 5849 has 240, lacking the same two. The union row covers this
config's 242 names.

The names without a `sec`:

- **5233 and 5558, 48 names.** These are the 34 socket/WSA/XNet names, the 2 XOnline names, the 4 Bink names
  and 7 CRT math names (`crt_atan`, `crt_cos`, `crt_log`, `crt_log10`, `crt_sin`, `crt_sqrt`, `crt_tan`). The
  3925 and 5849 sets tag the CRT names `.text`, and this image has no section of its own for LIBCMT. This
  image links `XAPILIB`, `XBOXKRNL`, `LIBCMT`, `D3D8`, `XGRAPHC`, `DSOUND` and `XMV`, all at 5233 (library
  table at XBE `+0x164`). There is no XNET, XONLINE or BINK library, so those names are correct zeros. None
  of the 48 can live in XGRPH or XMV.
- **3925 and 5849, 17 names.** These are D3D and DSOUND names without byte signatures
  (`D3DDevice_BeginPush`, `IDirectSoundBuffer_PlayEx`, ...). The 5233/5558 sets tag every one of them `D3D`
  or `DSOUND`.

`[data]` (12 names) and `[anchors]` are all D3D, DSOUND or XPP in every set.

## 2. Host bodies

The SDK runtime binds 234 distinct names through `HLE_STDCALL`, `HLE_FASTCALL`, `HLE_CDECL`, `HLE_WRAP`,
`GUEST`, `GUEST_ORIG`, `GUEST_CALL`, `SYM` and `HAS`. They come from these files:

| File | Bindings |
| --- | ---: |
| `xdk/dsound.cpp` | 147 |
| `xdk/d3d8.cpp` | 108 |
| `xdk/xnet.cpp` | 37 |
| `xdk/crt_math.cpp` | 13 |
| `xdk/xapi.cpp` | 11 |
| `xdk/bink.cpp` | 7 |

None is an XG or XMV name. A case-insensitive search of all of `sdk/` for `xmv`, `xgrph`, `xgraph`,
`XGSwizzle`, `XGSetTextureHeader` and the other XG names finds one hit only: the word XGRAPHC in the
`sdk/xdk/3925/layout.toml` header. The runtime has no `XMVDecoder*` body, no XG body and no XMV-specific
code path.

Every XGRAPHICS and XMV function therefore runs its console body, recompiled. Both sections are in
`config/game.toml` `code_sections`, and the generated code defines them as `X86_WEAK_FUNC`, which only a
`[symbols]` name with an `HLE_*` body could override. That design is sound for these two libraries, for two
reasons:

- **Neither touches hardware or the kernel directly.** No instruction in XGRPH or XMV references a kernel
  thunk slot (0 of 613 sites; see `docs/kernel-coverage.md`). XGRPH works on guest memory (resource headers,
  swizzles, shader splicing) plus one file writer that goes through XAPI. XMV reaches the machine only
  through D3D, DSOUND and XAPI calls, listed in section 6.
- **The sibling port proves it at run time.** Bustin' Out (XDK 5558, same engine family) names no XMV or XG
  function in its `config/game.toml`, and its SDK fork has no XMV or XG code. Its `docs/status.md`
  (lines 18-19 and 116-132) records the intro XMV opening with a 48 kHz DirectSound stream. Its
  `docs/movie-draw.md` matches the guest frame to an `ffmpeg` decode of `sims_intro.xmv` at 52 dB. Its
  `docs/movie-quad.md` (lines 31-36 and 82-87) documents the same three XMV calls this title makes: create,
  video descriptor and per-frame decode into a locked surface. Its `sub_2B1D3A`, `sub_2B2135` and
  `sub_2B27E2` are the 5558 twins of this image's `0x1BF060`, `0x1BF459` and `0x1BF6C9` (section 4).

## 3. The entry points

### Method

There are two independent passes, which agree.

**IDA.** Every external cross-reference to any instruction head inside the two sections was collected.

- XGRPH has 86 code references from `.text`, 37 data references from `.rdata` and 128 from `.data`.
- XMV has 7 code references from `.text`. Its 24 data references (5 `D3D`, 17 `.data`, 1 `.rdata`, 1
  `DOLBY`) are constants such as `0x1C0000`, `0x1C1C00` and `0x1E001C` that happen to fall inside the
  section. None is a function start.
- No code in `D3D`, `DSOUND` or `XPP` calls into either section.

**Raw bytes.** Every `E8`/`E9` rel32 in the code sections of the XBE was decoded and kept when its target
falls in XGRPH or XMV. That gives 104 candidates.

- 93 sit on a real `call`/`jmp` instruction and are exactly IDA's 86 + 7.
- 11 are byte coincidences inside other instructions, such as `mov esp, [ebp-18h]` at `0x177DF8`, and are
  not instructions at all.

Aligned function-start pointers in `.rdata`/`.data` were enumerated the same way. They point into XGRPH only
(below). None points into XMV.

### XMV: 6 entries, all from the game's movie class

The movie class has its vtable at `0x1FBAF4`. Its members here are:

- `sub_0015C040`, the open method (slot 0).
- `sub_0015BEA0` (slot 3).
- `sub_0015BD60`, the destructor, reached through the deleting destructor `0x15C020` in slot 6.
- `sub_0015BF10`, the per-frame call, which `sub_00153C60` calls directly.

The class hands XMV two packet callbacks: `0x15BF90` waits for the overlapped read of the next packet, and
`0x15BF50` issues the next read. Its read helpers `0x15BBD0` and `0x15BC60` do overlapped `ReadFile`.

| Entry | Called from (game `.text`) | 5558 twin: Bustin' Out address, `.XTLID` id |
| --- | --- | --- |
| `0x1BF060` | `0x15C1C6` in `sub_0015C040` (open) | `0x2B1D3A`, `0xE0003` |
| `0x1BF377` | `0x15BDB5` in `sub_0015BD60` (destructor), `0x15C067` in `sub_0015C040` (re-open) | `0x2B2051`, `0xE0001` |
| `0x1BF459` | `0x15C2A2` in `sub_0015C040` | `0x2B2135`, `0xE000B` |
| `0x1BF4C6` | `0x15C2B4` in `sub_0015C040` | `0x2B21E9`, `0xE0005` |
| `0x1BF643` | `0x15BEB9` in `sub_0015BEA0` | `0x2B23C6`, `0xE000D` |
| `0x1BF6C9` | `0x15BF36` in `sub_0015BF10` (per frame) | `0x2B27E2`, `0xE0008` |

### XGRPH: 8 entries from game code, and what else crosses the boundary

| Entry | Called from (game `.text`) | 5558 twin: Bustin' Out address, `.XTLID` id |
| --- | --- | --- |
| `0x1A1DA0` | `0x12AA02` in `sub_0012A9F0` | `0x26716B`, `0xD001E` |
| `0x1A228B` | `0x15B0F4` in `sub_0015AFF0` | `0x2676E5`, `0xD0012` |
| `0x1A22B5` | `0x1520AE`, `0x1521EB`, `0x15236E` (`sub_00152060`, `sub_00152190`, `sub_00152330`) | `0x267764`, `0xD0013` |
| `0x1A22CD` | `0x15B158` in `sub_0015AFF0` | `0x267794`, `0xD000F` |
| `0x1A2A16` | `0x15AD72`, `0x15ADE2`, `0x15AE24` (`sub_0015AD60`), `0x15AF7B`, `0x15AFC8` (`sub_0015AF10`), `0x15B3EE` (`sub_0015B3C0`) | `0x268033`, `0xD0007` |
| `0x1A3288` | `0x15AFDF` in `sub_0015AF10` | `0x26896E`, `0xD001A` |
| `0x1A39D9` | `0x15AE00`, `0x15AE42` in `sub_0015AD60` | `0x2690BF`, `0xD001C` |
| `0x1A9797` | `0x1680E4` in `sub_00167EC0` | `0x271F52`, `0xD0015` |

Everything else that crosses into XGRPH belongs to XGRAPHC itself. None of it is a game entry point:

- **Static initializers.** `0x1B2E64`, `0x1B2E70` and `0x1B2E7C` are slots `0x20A720`..`0x20A728` of the C++
  initializer table `0x20A700`..`0x20A73C`, whose terminator `sub_000CB257` reads at `0xCB28F`. Each is
  `push offset <dtor>; call 0x17553A; pop ecx; ret`, which registers a destructor (`atexit`-shaped). They run
  once at startup.
- **C++ EH funclets in `.text`.** 70 `jmp`s from `.text` `0x189B0B`..`0x189FC0` go to XGRPH cleanup code
  (`0x1A9955`, `0x1A9AF3`, `0x1ABE51`, `0x1ABE5C`, `0x1ABE79`, `0x1ABE84`, `0x1AC9F7`, `0x1ADDA7`, `0x1AE943`),
  mostly as `lea ecx, [ebp-x]; jmp <destructor>`. They are MSVC unwind funclets, which the compiler places in
  `.text` whatever the `code_seg`. The 33 `__ehhandler` stubs among them (`mov eax, offset FuncInfo; jmp
  0x17508F`) are loaded only by XGRPH functions' EH prologues: `mov eax, offset <stub>; call 0x1810C0`, 44
  references, all in XGRPH, 43 of them at the function's first instruction.
- **XGRAPHC's own tables.**
  - 37 `.rdata` vtable slots (`0x2003E0`..`0x200474`) point at XGRPH virtual methods, and only XGRPH code
    references those vtables.
  - The `.data` handler table `0x21853C`..`0x218598` holds 13 XGRPH handlers and has no code reference. It
    is followed at `0x21859C` by pointers to XGRPH keyword strings such as `PS_COMBINERCOUNT_MUX_LSB`
    (`0x1B46BC`), which marks it as shader-assembler data.
  - The EH catch block `0x1B27D5` is listed at `.rdata` `0x20A1B4`.

## 4. Invariants of the 14 entries

No reference set has a record for any XGRPH or XMV function, so there is nothing in `signatures.toml` or
`5558-signed.toml` to compare against. The strongest available cross-check is the 5558 image, whose own
`.XTLID` publishes 17 XMV ids (`0xE0001`-`0xE0011`) and 26 XGRAPHC ids (`0xD0001`-`0xD001E`). This image's
`.XTLID` has 82 entries: a header (id 0, value 5233) and 81 exports, of which 35 are XAPILIB (`0x1xxxx`)
and 46 come from library 2 (`0x2xxxx`). None points into XGRPH or XMV.

Each entry was compared with its twin by disassembling both images' bytes with `objdump` and comparing
operand-masked instruction streams. Read the columns this way:

- `len` is the extent.
- `ret` is the immediate of `retn`, identical in both builds for all 14.
- `calls` is rel32 call/jump sites leaving the extent.
- Stable `k` are constants ≥ `0x10000` that are not image addresses.
- `regs` is "none" for all 14. Hex-Rays types every one as a plain `__stdcall` with only stack arguments. The
  prologues read nothing before writing it beyond `esp` and the argument slots, for example `0x1BF459`
  `mov eax, [esp+4]`, `0x1BF643` `push ebx; push esi; mov esi, [esp+0Ch]; xor ebx, ebx` and `0x1A22CD`
  `mov ecx, [esp+4]; mov eax, [esp+8]`. Identical instruction streams give the twins the same `regs`.

**XMV**

| Entry | len (5233 / 5558) | ret | regs | calls (5233 / 5558) | stable k (5233 / 5558) | instructions (5233 / 5558), mnemonic match |
| --- | --- | ---: | --- | --- | --- | --- |
| `0x1BF060` | `0x317` / `0x317` | `0x18` | none | 5 / 5 | `0x8007000E` / `0x8007000E` | 220 / 220, 0.995 |
| `0x1BF377` | `0xE2` / `0xE4` | `0x4` | none | 7 / 7 | `0x708B4000` / `0x648C4000` | 92 / 92, 0.978 |
| `0x1BF459` | `0x1C` / `0x1C` | `0x8` | none | 0 / 0 | none / none | 9 / 9, 1.0 |
| `0x1BF4C6` | `0x17D` / `0x17F` | `0x14` | none | 1 / 1 | none / none | 126 / 127, 0.980 |
| `0x1BF643` | `0x86` / `0x86` | `0x4` | none | 0 / 0 | none / none | 42 / 42, 1.0 |
| `0x1BF6C9` | `0x67D` / `0x67D` | `0x10` | none | 12 / 12 | `0x8000000A` / `0x8000000A` | 492 / 492, 1.0 |

`0x708B4000`/`0x648C4000` is the `XMemFree` attribute word. Its allocator-id byte is `0x8B` in 5233 and
`0x8C` in 5558, and nothing else in it differs in the way that matters here. `0x8000000A` is a stream-record
marker compared in the audio loop, and `0x8007000E` is `E_OUTOFMEMORY`.

**XGRPH**

| Entry | len (5233 / 5558) | ret | regs | calls (5233 / 5558) | stable k (5233 / 5558) | instructions (5233 / 5558), match |
| --- | --- | ---: | --- | --- | --- | --- |
| `0x1A1DA0` | `0x2C5` / `0x2C5 window` | `0x8` | none | 14 / 13 | `0x80004005` / `0x80004005` | 265 / 263, 0.989 |
| `0x1A228B` | `0x2A` / `0x2A` | `0x24` | none | 1 / 1 | none / none | 16 / 16, 1.0 |
| `0x1A22B5` | `0x18` / `0x18` | `0x18` | none | 0 / 0 | none / none | 6 / 6, byte-identical, 1.0 |
| `0x1A22CD` | `0x21` / `0x21` | `0xC` | none | 0 / 0 | none / none | 9 / 9, 1.0 |
| `0x1A2A16` | `0x2A + 0x52 tables` / `0x2A + 0x52 tables` | `0x4` | none | 0 / 0 | none / none | 15 / 15, same 66-byte case table, 1.0 |
| `0x1A3288` | `0x751` / `0x751` | `0x20` | none | 30 / 30 | none / none | 655 / 655, 1.0 |
| `0x1A39D9` | `0x717` / `0x717` | `0x20` | none | 30 / 30 | none / none | 572 / 572, 1.0 |
| `0x1A9797` | `0x197` / `0x197` | `0x18` | none | 3 / 3 | `0x0FFFFFFF`, `0x3FFFFFFF` / same | 156 / 156, 1.0 |

Notes on the XGRPH rows:

- `0x1A3288` and `0x1A39D9` are measured over their whole bodies. IDA and the recompiler's inventory both cut
  them at interior starts (`0x1A379F`; `0x1A3DC6`/`0x1A3EDE`), which is why IDA reports no `ret` for the first
  piece. The `retn 20h` is at `0x1A39D6` and `0x1A40ED` (5558: `0x2690BC`, `0x2697D3`), and the twins' export
  spacing is exactly `0x751`/`0x717`. The generated code joins the pieces with `goto` (`x86_recomp.28.cpp`,
  `goto loc_001A39B2` and `goto loc_001A39CF` inside `sub_001A3288`), so the split is harmless.
- `0x1A1DA0` was measured against a same-size window of its twin. The single-call difference is the window
  edge.
- `0x1A22B5` and the 5558 neighbour `0xD000E` (`0x26777C`) differ in one immediate: `1` against `0x10001`,
  the vertex-buffer against the index-buffer resource type. That is how the twin was told apart.

## 5. What each entry does

Each identification comes from the code and the game's use of it. An XDK name in brackets is
**[INFERENCE]**, not a proven symbol. None is emitted.

**XMV**

| Entry | xtlid twin | Behaviour | [INFERENCE] XDK name |
| --- | --- | --- | --- |
| `0x1BF060` | `0xE0003` | Called with (4, the first 4 KB packet, context = movie+0x30, the two packet callbacks, out decoder = movie+0xC). Reads width/height at packet `+0x14/+0x18` and the audio-stream count at `+0x20`, and calls `D3DDevice_GetDisplayMode` (`0x193070`). Returns `E_OUTOFMEMORY` when an allocation fails | `XMVDecoder_CreateDecoderForPackets` |
| `0x1BF377` | `0xE0001` | Flushes each stream with `FlushEx(..., 1)`, polls `GetStatus` with `Sleep(1)` and `DirectSoundDoWork` until playback stops, then releases the streams. Completes and closes its file handle (`GetOverlappedResult`, `CloseHandle`) and `XMemFree`s its buffers | `XMVDecoder_CloseDecoder` |
| `0x1BF459` | `0xE000B` | Copies decoder `+0x40/+0x44/+0x48` to descriptor `+0/+4/+0xC`. The game reads width, height and audio-stream count from it | `XMVDecoder_GetVideoDescriptor` |
| `0x1BF4C6` | `0xE0005` | Builds a `DSSTREAMDESC`: 2 packets, completion callback `0x1BF475` with the decoder as context, and PCM or Xbox ADPCM (`0x69`, 36-byte blocks of 64 samples) `WAVEFORMATEX` from the stream header. Default mix bins come from `0x1C7658`. Calls `DirectSoundCreateStream` and AddRefs the stream out on request | `XMVDecoder_EnableAudioStream` |
| `0x1BF643` | `0xE000D` | Restarts from the first packet once the decoder has drained (clock and frame state reset, first packet re-requested through the callback). Otherwise sets the pending-restart flag `+0x34`, which the next frame call honours | no confident name |
| `0x1BF6C9` | `0xE0008` | Pulls packets, feeds audio through each stream's vtable (`+0x10` Process, `+0x14` Discontinuity) and decodes video. Paces against the VBlank count from `D3DDevice_GetDisplayFieldStatus` (`0x193960`) and starts audio with `IDirectSound_SynchPlayback`. Writes a due frame into the caller's surface (`0x1C0824`: surface GetDesc `0x1958E0`, LockRect `0x195900`, MMX converters for formats `0x12` `LIN_A8R8G8B8`, `0x1E` `LIN_X8R8G8B8` and `0x24` `YUY2`). Result code goes to argument 3, frame time to argument 4 | `XMVDecoder_GetNextFrame` |

**XGRPH**

| Entry | xtlid twin | Behaviour | [INFERENCE] XDK name |
| --- | --- | --- | --- |
| `0x1A1DA0` | `0xD001E` | (surface, path): surface GetDesc and LockRect, `CreateFileA`, six `WriteFile` calls, `CloseHandle`. Returns `E_FAIL` on error. Its only caller is the 11-byte game wrapper `0x12A9F0` | `XGWriteSurfaceToFile` |
| `0x1A228B` | `0xD0012` | Nine arguments, forwarded to the header builder `0x1A223F` with depth 1. The twin `0x2676E5` is the call Bustin' Out's `docs/movie-quad.md:60` reads as `XGSetTextureHeader(640, 448, 1, 0, 0x12, 0, hdr, 0, 0)` | `XGSetTextureHeader` |
| `0x1A22B5` | `0xD0013` | Writes `Common = 1` (vertex buffer, refcount 1), `Data = arg6` and `Lock = 0` into `arg5` | `XGSetVertexBufferHeader` |
| `0x1A22CD` | `0xD000F` | Writes `Common = 0x30001 \| Size << 30` (palette, refcount 1), `Data = arg3` and `Lock = 0` | `XGSetPaletteHeader` |
| `0x1A2A16` | `0xD0007` | Maps D3DFORMAT 0..0x41 to 1, 2, 4 or 0 bytes per pixel through a 66-byte case table (DXT1 and unknown codes give 0) | `XGBytesPerPixelFromFormat` |
| `0x1A3288` | `0xD001A` | 8 arguments, `retn 20h`. Rectangle copy with per-bytes-per-pixel swizzle loops | `XGSwizzleRect` |
| `0x1A39D9` | `0xD001C` | 8 arguments, `retn 20h`. The inverse copy | `XGUnswizzleRect` |
| `0x1A9797` | `0xD0015` | The game passes an output buffer of 2180 bytes and its size, a register-count out, an array of vertex-shader fragments with their count, and 1. It then gives the output to `D3DDevice_CreateVertexShader` (`sub_00167EC0`) | `XGSpliceVertexShaders` |

Each of the 14 carries an IDA function comment in the shared database with its twin and this document.

## 6. What the movie path depends on, which this slice does not own

The title's movies are five XMV streams in `movies.arc`, found by their `xobX` magic at header `+0xC`
(version 4). Width and height sit at `+0x14/+0x18` and the audio-stream count at `+0x20`, the offsets
`0x1BF060` reads from the first packet. The per-stream format words follow. `+0x1C` is probably the duration
in ms [INFERENCE].

| Offset in `movies.arc` | Span | Picture | `+0x1C` | Audio stream (tag, channels, rate, bits) |
| --- | --- | --- | --- | --- |
| `0x800` | `0x1A28000` | 640x480 | `0x263B3` | PCM (1), 2, 44100 Hz, 16 |
| `0x1A28800` | `0x175C000` | 640x480 | `0xE67A` | Xbox ADPCM (0x69), 2, 32000 Hz, 4 |
| `0x3184800` | `0x492000` | 640x480 | `0x4650` | Xbox ADPCM (0x69), 2, 32000 Hz, 4 |
| `0x3616800` | `0x194000` | 320x240 | `0x5F04` | Xbox ADPCM (0x69), 2, 32000 Hz, 4 |
| `0x37AA800` | `0xAC000` | 640x480 | `0xC61` | Xbox ADPCM (0x69), 2, 32000 Hz, 4 |

The host's DirectSound already decodes both audio formats (`sdk/runtime/xdk/dsound.cpp:164-168,204,420`).

The rest of what XMV calls is listed below. Every name in these lists is the one the owning slice gave the
function in the shared IDA database (D3D, DSOUND, XAPI/CRT), not a name this slice proves.

**D3D (`d3d8` slices):**

- `0x193070` is `D3DDevice_GetDisplayMode`-shaped and is called at `0x1BF136`. It reads
  `[[0x19FA08]+0x15C4]`, a surface, at `+0x0C/+0x10`, the refresh qword at `+0x1FE8`, and `+0x197C & 0x400000`.
- `0x193960` is `D3DDevice_GetDisplayFieldStatus`-shaped and is called at `0x1BF9EA`. It reads `+0x1988`
  (VBlank count), `+0x197C & 0x1200000` and `+0x1998`.

  XMV's frame clock is that VBlank count. The host's vertical-blank thread writes it at
  `XDK_CDevice_VBlankCount` from `sdk/xdk/5233/layout.toml`. The layout slice reports the same offsets for
  this build (DisplayFlags `0x197C`, VBlankCount `0x1988`, Field `0x1998`, FrontBuffer `0x15C4`) and is
  recording them in `docs/layout-5233.md`.

  With the provisional 5558 values the count XMV paces on would not advance. In this image only the
  vertical-blank ISR (`0x199A30`, per the layout slice) and the mode-change routine `0x193FC0` write
  `+0x1988`, and the ISR never runs on the host. Frames after the first would then never fall due [INFERENCE
  from the due-time test in `0x1BF6C9`].
- `0x1958E0` and `0x195900` are the surface GetDesc and LockRect wrappers (into `0x197A10`, and into
  `Lock2DSurface` `0x197D10`, which the D3D core slice has proven). They are called from `0x1C0831` and
  `0x1C0841` for every frame XMV writes.

**DSOUND:**

- `DirectSoundCreate` `0x1B7080`
- `DirectSoundCreateStream` `0x1B70C7`
- `IDirectSound_SynchPlayback` `0x1B6155`
- `IDirectSound_Release` `0x1B54E1`
- `DirectSoundDoWork` `0x1B62A5`
- the stream Pause thunk `0x1B6288` (to `CDirectSoundStream_Pause` `0x1B5E6B`)
- the stream FlushEx thunk `0x1B628D` (to `CDirectSoundStream_FlushEx` `0x1B5EBC`)
- the stream vtable slots `+0x0C/+0x10/+0x14`

The two thunk targets match their 5558 lengths exactly (`0x51`, `0x6A`), so these are well placed. All
seven DSOUND names above are in `config/found-dsound.toml` at exactly these addresses, together with
`CDirectSoundStream_GetStatus`, `_Process` and `_Discontinuity` (the methods XMV's three vtable calls name
[INFERENCE from slot use]) and the stream vtable data symbols `DSound_StreamVtable` `0x2004C4` and
`DSound_StreamVtable2` `0x2004B8`. `Lock2DSurface` is in
`config/found-d3d8-core.toml`. The host calls the stream's completion callback from `DirectSoundDoWork`
(`dsound.cpp:146-148,387-389`), which XMV calls itself.

**XAPI/CRT in `.text`:** `XMemAlloc` `0x181400`, `XMemFree` `0x18146F`, `QueryPerformanceCounter` `0x17EE31`,
`QueryPerformanceFrequency` `0x17EE42`, `CloseHandle`, `GetOverlappedResult`, `Sleep`, and `0x176120`. The
last is called as `(lo, hi, divisor, 0)`, so it is a 64-bit unsigned divide helper [INFERENCE]. These are
guest code over the kernel. The 44 kernel imports the movie path's call closure reaches are all covered
(`docs/kernel-coverage.md`).

**Recompilation.** The 71 XMV functions reachable from the six entries (direct calls plus address-taken
functions) contain no recompiler trap except the generated divide-error guards. The recompiler emitted 220
trap sites inside XMV's range: 166 `unimplemented:`, 29 `in`, 22 `hlt`, 1 `cli`, 1 `out` and 1 `int3`. All
of them sit in bytes the recompiler's sweep took for code, at `0x1C7854`..`0x1E6B92`. They read as runs of
`les`, `bound`, `aam` and `arpl`, which is data, and no reachable function contains them. XGRPH's only such
sites are:

- 8 `int3`: one after `_CxxThrowException` at `0x1A9E9F`, seven null-argument asserts (`0x1ACFC6`,
  `0x1AD42C`, `0x1AD53E`, `0x1AD650`, `0x1AD762`, `0x1AD877`, `0x1ADA5F`).
- 2 in the data tail `0x1B3A68`.

## Not established

- XDK names for the 14 entries. Ids `0xD`/`0xE` have no name table in the SDK, and this image's `.XTLID`
  does not publish them. The bracketed names in section 5 are inference from shape and use.
- Which of the five streams plays first, and when. That belongs with the game's movie-list code, which was
  not traced. The run, not this document, decides whether the movie shows.
- Run-time behaviour of any of the above. Everything here is static. In particular, it is not established
  that XMV's pacing behaves at host speed once the VBlank offsets are right. Bustin' Out, whose XMV twins
  match instruction for instruction or nearly, plays its intro, which suggests it does, but only this title's
  run can show it.
- Who calls `0x1A1DA0`'s 11-byte wrapper `0x12A9F0`, and whether the title ever writes a file with it, was
  not traced.
