# XDK names by neighbour-order alignment

Written by `tools/align_symbols.py` (run from the repo root, no arguments); rerun it rather than
editing this file. It writes `config/found-align.toml` with the names below that the image proves,
and lists every other library target name here with its ranked candidates and what failed.

## Result

| Section | Target names | Already anchors | Aligned here | Emitted | Not emitted |
| --- | ---: | ---: | ---: | ---: | ---: |
| D3D | 105 | 83 | 22 | 0 | 22 |
| DSOUND | 77 | 33 | 44 | 0 | 44 |
| XPP | 5 | 5 | 0 | 0 | 0 |
| XGRPH | 0 | 0 | 0 | 0 | 0 |
| XMV | 0 | 0 | 0 | 0 | 0 |
| all | 187 | 121 | 66 | 0 | 66 |

- **0 names emitted** to `config/found-align.toml`, out of the 66 library-section
  target names that `config/game.toml` did not already name (128 names were non-zero there at this run, 121 of them in D3D, DSOUND, XPP, XGRPH and XMV).
- **Decoder self-check:** 187 of 187 signed 5558 target functions re-measured from `out/sims5558.exe` come out exactly as `config/ref/5558-signed.toml` records them (len, ret, regs, k, calls).
- **Held-out anchors:** each of the 121 library anchors was removed in turn and placed by the others: 80 re-emitted at their proven address, **0 emitted at a wrong address**, 41 not emitted (details under *Held-out anchors*).
- **Independent cross-check:** other agents' `config/found-*.toml` files (read for this report only, never as input) name 0 of the emitted names; 0 agree, **0 disagree**. 0 emitted names appear in no other file.
- **Larger truth set:** the same hold-out over the union of `config/game.toml` and those files (121 library names): 80 re-emitted correctly, **0 wrongly** (details under *Validation against the other agents' results*).

## Inputs

| Input | Used for |
| --- | --- |
| `config/game.toml` | the anchors (every non-zero `[symbols]` entry), the XBE path, its code sections |
| `assets/default.xbe` | the section table (`out/game.exe` is a flat image and has lost it); the tool checks every section's bytes against `out/game.exe` |
| `out/game.exe` | the target bytes |
| `generated/game/x86_func_mapping.cpp` | the target function inventory: the recompiler's own `X86FuncMappings` table |
| `out/sims5558.exe` | the reference bytes and its function starts (its exports) |
| `docs/symbol-targets.json` | the target names and their 5558 addresses |
| `sdk/xdk/5849/signatures.toml`, `config/ref/5558-signed.toml` | each name's ret, regs, len, calls and k in two independent builds |

**Inventory used.** The recompiler's table lists 12889 starts. In the 5 library sections the tool adds the starts the SDK signer's own start rule finds there that the recompiler did not list (16-aligned code right after a `ret`, `jmp`, `int3` or `nop` that no conditional or short jump targets; these are functions reached only through another function's jump table), and drops starts that are not call targets and lie inside the extent of the start before them (mid-function entries from pointer seeding):

| Section | Range | Recompiler starts | Added | Dropped as interior | Aligned |
| --- | --- | ---: | ---: | ---: | ---: |
| D3D | 0x18F680-0x1A1DA0 | 283 | 5 | 22 | 266 |
| DSOUND | 0x1B5380-0x1BF044 | 397 | 2 | 0 | 399 |
| XPP | 0x1E6C00-0x1EE45C | 229 | 1 | 1 | 229 |
| XGRPH | 0x1A1DA0-0x1B5380 | 481 | 16 | 28 | 469 |
| XMV | 0x1BF060-0x1E6BEC | 175 | 3 | 16 | 162 |

## How the invariants are measured

`ret`, `regs`, `len`, `calls` and `k` are computed for every candidate by the tool itself, with a standard-library x86 decoder that reproduces what `sdk/tools/symbols/main.cpp` reads through Zydis in sign mode:

- **len** is the signer's `ExtentBefore`: code reachable from the start, following conditional and unconditional relative branches but not calls, stopping at `ret`/`int3`/`hlt`, bounded by the next known start. Known starts are the signer's: every rel32 call target of a linear sweep of the code sections, plus the anchors.
- **ret** is the set of stack bytes the reachable `ret`/`retn imm16` instructions pop; an empty set means the function leaves by jump.
- **regs** is the signer's `Trace`: a path-sensitive walk that records a general register (eax ecx edx ebx ebp esi edi) when an instruction reads it, explicitly or as a hidden operand (`cdq`, `rep movs`, `mul`, ...), before every path to that instruction has written it. A call writes eax, ecx and edx; `xor r,r`/`sub r,r`/`sbb r,r` and `push r` read nothing. **regs is measured, not dropped.**
- **calls** is the number of rel32 call and jump targets that leave the function's extent.
- **k** is the signer's constant list. Only its *stable* part is compared: constants ≥ 0x10000 (NV2A push-buffer method headers, flag masks, HRESULTs, floats). Smaller ones are mostly structure offsets, which move between XDK builds, so 5233 and 5558 cannot be assumed to share them.

Proof that the decoder measures what the signer measures: re-measuring the 187 signed 5558 target functions from `out/sims5558.exe` reproduces 187 of them field for field. The 5558 side has no XBE in this repository, so its sections are rebuilt from the data (`.text` up to the first library target, code up to the end of the last export); that reproduces the signer's sweep and the check above.

## Link order is preserved within an object, not across a section

The premise of neighbour-order alignment is that both images link the same library in the same order. Across XDK builds that holds for runs of functions but not necessarily for a whole section: whole blocks (object files) can sit in a different order in 5233. Anchors per section, in target order, with their rank in 5558 order (a break count above zero is that reordering, measured on this image):

- **D3D** (83 anchors; 7 of 82 target-order neighbours are not neighbours in 5558): `0 1 2 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 9 3 4 5 6 7 8 10 11 12 13 14 15 16 17 19 18 75 76 77 78 79 80 81 82`
- **DSOUND** (33 anchors; 8 of 32 target-order neighbours are not neighbours in 5558): `0 1 2 3 4 5 6 7 8 9 10 11 24 12 13 14 15 26 16 17 18 19 20 21 22 23 28 25 27 29 30 31 32`
- **XPP** (5 anchors; 0 of 4 target-order neighbours are not neighbours in 5558): `0 1 2 3 4`
- **XGRPH**: no anchor.
- **XMV**: no anchor.

A single monotone alignment of a whole section is therefore unsafe. The tool aligns each name only inside the bracket its own nearest anchors give it, and classifies that bracket (next section).

## Algorithm

1. **Sequences.** Reference: the 5558 functions in address order (the target names, plus the unnamed functions between them as spacers, so the alignment knows what separates two names). Target: the inventory above, in address order. Anchors are taken out of both sequences: they are the pins.
2. **Bracket.** For a name, take the anchor nearest below it and nearest above it in 5558 order (same section). The kinds:
   - *tight*: both exist, they are in the same order in the target, no other anchor lies between them in the target, and the two stretches they enclose differ in byte size by at most 3x;
   - *loose*: same order, but another anchor lies between them in the target (a moved block) or the stretches differ grossly in size, so the target stretch holds code from elsewhere;
   - *inverted*: the two anchors are in opposite order in the target (the name sits between two moved blocks); *forward*/*backward*: an anchor on one side only; *unanchored*: no anchor in the section.
   Inverted, one-sided and unanchored names are still aligned (inverted: the stretch after the lower anchor followed by the stretch before the upper one; one-sided: from the anchor to the next anchor or section edge; unanchored: the whole section) so they get candidates, but they are never emitted.
3. **Alignment.** Needleman-Wunsch over the bracket: maximise the summed pair score of a monotone, one-to-one pairing, where leaving either side unpaired costs nothing, so only positive pairings are made and both missing and extra functions are absorbed. A pair whose `ret` differs cannot be made.
4. **Lead.** Forward and backward score tables give, for each name, the best total with the name paired to each candidate and with it unpaired (max-marginals). The lead is the best of those minus the runner-up: how much worse the best alignment is that does not put the name where it was put.
5. **Emission.** A name is written only when every one of these holds:
   - the bracket is tight or loose (two proven anchors, in agreeing order);
   - `ret` equal (required), `regs` equal (required), `calls` within ±1 (required);
   - when the reference builds agree on stable constants, the candidate shares at least one;
   - length within the band, or a *distinctive* shared stable constant stands in for it (one that at most 2 target functions in the section contain);
   - alignment lead ≥ 2;
   - exclusive in the bracket: every other target function in the bracket that itself passes the required checks scores at least 1.5 lower on the pair score alone (so identical-looking functions are never told apart by position alone);
   - in a loose bracket, additionally: length within the band, and the same exclusivity over the whole section;
   - no other name chose the same address.

## Pair score, bands and why

| Term | Value |
| --- | --- |
| ret differs | pairing not allowed |
| regs equal / differ | +2 / -4 |
| len exact | +3 |
| len within band | +0.5 … +2.5, falling linearly to the band edge |
| len outside band | −0.5 … −3, growing with the excess |
| calls equal / ±1 / further | +1 / 0 / −1 per extra call |
| stable constant: distinctive shared / shared / reference has some, candidate none | +3 / +1.5 / -1.5 |

**Length band: |len − reference| ≤ max(8 bytes, 12% of the reference length)**, the reference length being whichever of len5849/len5558 is closer. Measured on the anchors (functions proven by other means, so the measurement is not circular), 5233 against 5558:

| Anchor | Section | len 5233 | len 5849/5558 | Δ | ret | regs | calls Δ |
| --- | --- | ---: | ---: | ---: | --- | --- | ---: |
| `Direct3D_CreateDevice` | D3D | 165 | 164 | +1 | = | = | 0 |
| `D3D_InternalAddRef` | D3D | 50 | 50 | +0 | = | = | 0 |
| `D3D_InternalRelease` | D3D | 98 | 98 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_PSTextureModes` | D3D | 34 | 34 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_Simple` | D3D | 39 | 39 | +0 | = | = | 0 |
| `D3DDevice_SetRenderStateNotInline` | D3D | 93 | 93 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_EdgeAntiAlias` | D3D | 50 | 50 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_ShadowFunc` | D3D | 53 | 53 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_FogColor` | D3D | 77 | 77 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_CullMode` | D3D | 104 | 104 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_FrontFace` | D3D | 58 | 58 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_NormalizeNormals` | D3D | 57 | 57 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_TextureFactor` | D3D | 81 | 81 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_LineWidth` | D3D | 101 | 101 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_Dxt1NoiseEnable` | D3D | 119 | 119 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_LogicOp` | D3D | 82 | 82 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_FillMode` | D3D | 68 | 68 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_BackFillMode` | D3D | 81 | 81 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_TwoSidedLighting` | D3D | 99 | 128 | -29 | = | = | 1 |
| `D3DDevice_SetRenderState_VertexBlend` | D3D | 65 | 65 | +0 | = | = | 0 |
| `D3DDevice_SetTextureState_TexCoordIndex` | D3D | 261 | 261 | +0 | = | = | 0 |
| `D3DDevice_SetTextureState_BumpEnv` | D3D | 99 | 99 | +0 | = | = | 0 |
| `D3DDevice_SetTextureState_BorderColor` | D3D | 61 | 61 | +0 | = | = | 0 |
| `D3DDevice_SetTextureState_ColorKeyColor` | D3D | 57 | 57 | +0 | = | = | 0 |
| `D3DDevice_SetTextureStageStateNotInline` | D3D | 236 | 236 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_ZEnable` | D3D | 143 | 143 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_StencilEnable` | D3D | 132 | 132/152 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_StencilFail` | D3D | 109 | 109/111 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_YuvEnable` | D3D | 43 | 43 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_OcclusionCullEnable` | D3D | 98 | 98 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_StencilCullEnable` | D3D | 98 | 98 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_RopZCmpAlwaysRead` | D3D | 17 | 17 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_RopZRead` | D3D | 17 | 17 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_DoNotCullUncompressed` | D3D | 17 | 17 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_MultiSampleMode` | D3D | 52 | 39 | +13 | = | = | 0 |
| `D3DDevice_SetRenderState_MultiSampleRenderTargetMode` | D3D | 52 | 39 | +13 | = | = | 0 |
| `D3DDevice_SetRenderState_MultiSampleAntiAlias` | D3D | 114 | 114 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_MultiSampleMask` | D3D | 80 | 80 | +0 | = | = | 0 |
| `D3DDevice_SetRenderState_SampleAlpha` | D3D | 78 | 78 | +0 | = | = | 0 |
| `D3DDevice_CreateVertexShader` | D3D | 318 | 318 | +0 | = | = | 0 |
| `D3DDevice_SetVertexShaderConstant1` | D3D | 95 | 95 | +0 | = | = | 0 |
| `D3DDevice_SetVertexShaderConstant4` | D3D | 162 | 162 | +0 | = | = | 0 |
| `D3DDevice_SetVertexShaderConstantNotInlineFast` | D3D | 208 | 208 | +0 | = | = | 0 |
| `D3DDevice_SetStreamSource` | D3D | 140 | 140 | +0 | = | = | 0 |
| `D3DDevice_LoadVertexShader` | D3D | 84 | 84 | +0 | = | = | 0 |
| `D3DDevice_SelectVertexShader` | D3D | 128 | 156 | -28 | = | = | 0 |
| `D3DDevice_SetShaderConstantMode` | D3D | 280 | 280 | +0 | = | = | 0 |
| `D3DDevice_DeleteVertexShader` | D3D | 25 | 27 | -2 | = | = | 0 |
| `D3DDevice_SetVertexShader` | D3D | 338 | 355 | -17 | = | = | 0 |
| `D3DDevice_InsertCallback` | D3D | 107 | 107 | +0 | = | = | 0 |
| `CDevice_KickOff` | D3D | 219 | 176 | +43 | = | = | 0 |
| `D3D_SetFence` | D3D | 164 | 184 | -20 | = | = | 0 |
| `D3D_BlockOnTime` | D3D | 310 | 358/362 | -48 | = | = | 2 |
| `D3D_MakeRequestedSpace` | D3D | 371 | 311 | +60 | = | = | 1 |
| `D3DDevice_MakeSpace` | D3D | 15 | 15 | +0 | = | = | 0 |
| `D3DDevice_BeginPush` | D3D | 68 | 68 | +0 | = | = | 0 |
| `D3D_KickOffAndWaitForIdle` | D3D | 17 | 17 | +0 | = | = | 0 |
| `D3D_BlockOnResource` | D3D | 120 | 120 | +0 | = | = | 0 |
| `D3DDevice_SetRenderTarget` | D3D | 23 | 628 | -605 | = | = | 10 |
| `D3DDevice_SetTransform` | D3D | 270 | 280 | -10 | = | = | 0 |
| `D3DDevice_Release` | D3D | 55 | 55 | +0 | = | = | 0 |
| `D3DDevice_BlockUntilVerticalBlank` | D3D | 36 | 36 | +0 | = | = | 0 |
| `D3DDevice_SetFlickerFilter` | D3D | 66 | 66 | +0 | = | = | 0 |
| `D3DDevice_SetSoftDisplayFilter` | D3D | 81 | 81 | +0 | = | = | 0 |
| `D3DDevice_Reset` | D3D | 173 | 168 | +5 | = | = | 0 |
| `D3DDevice_GetBackBuffer2` | D3D | 67 | 67 | +0 | = | = | 0 |
| `D3DDevice_CopyRects` | D3D | 803 | 803 | +0 | = | = | 0 |
| `D3DDevice_GetDepthStencilSurface2` | D3D | 30 | 30 | +0 | = | = | 0 |
| `D3DDevice_SetViewport` | D3D | 352 | 546 | -194 | = | = | 4 |
| `D3DDevice_SetTexture` | D3D | 420 | 420 | +0 | = | = | 0 |
| `D3DDevice_SetPalette` | D3D | 141 | 141 | +0 | = | = | 0 |
| `D3DDevice_SetScissors` | D3D | 407 | 768 | -361 | = | = | 8 |
| `D3DDevice_SetScreenSpaceOffset` | D3D | 73 | 73 | +0 | = | = | 0 |
| `D3DDevice_Swap` | D3D | 219 | 227/229 | -8 | = | = | 0 |
| `D3DDevice_Clear` | D3D | 916 | 927 | -11 | = | = | 0 |
| `D3DDevice_DrawVerticesUP` | D3D | 349 | 357 | -8 | = | = | 0 |
| `D3DDevice_DrawVertices` | D3D | 148 | 148 | +0 | = | = | 0 |
| `D3DDevice_DrawIndexedVertices` | D3D | 599 | 599 | +0 | = | = | 0 |
| `D3DDevice_Begin` | D3D | 53 | 53 | +0 | = | = | 0 |
| `D3DDevice_End` | D3D | 61 | 65 | -4 | = | = | 0 |
| `D3DDevice_SetPixelShader` | D3D | 499 | 499 | +0 | = | = | 0 |
| `D3D_InitDefaultState` | D3D | 210 | 194 | +16 | = | = | 0 |
| `Lock2DSurface` | D3D | 155 | 155 | +0 | = | = | 0 |
| `IDirectSound_Release` | DSOUND | 22 | 22 | +0 | = | = | 0 |
| `IDirectSoundBuffer_Release` | DSOUND | 22 | 22 | +0 | = | = | 0 |
| `CDirectSoundStream_AddRef` | DSOUND | 71 | 71 | +0 | = | = | 0 |
| `CDirectSoundStream_Release` | DSOUND | 78 | 78 | +0 | = | = | 0 |
| `CDirectSoundStream_GetInfo` | DSOUND | 103 | 103 | +0 | = | = | 0 |
| `CDirectSoundStream_Discontinuity` | DSOUND | 77 | 77 | +0 | = | = | 0 |
| `CDirectSoundStream_Flush` | DSOUND | 75 | 75 | +0 | = | = | 0 |
| `CDirectSoundStream_GetStatus` | DSOUND | 81 | 81 | +0 | = | = | 0 |
| `CDirectSoundStream_Process` | DSOUND | 119 | 119 | +0 | = | = | 0 |
| `CDirectSoundStream_Pause` | DSOUND | 81 | 81 | +0 | = | = | 0 |
| `CDirectSoundStream_FlushEx` | DSOUND | 106 | 106 | +0 | = | = | 0 |
| `CDirectSoundStream_SetVolume` | DSOUND | 82 | 82 | +0 | = | = | 0 |
| `CDirectSoundStream_SetMixBins` | DSOUND | 82 | 82 | +0 | = | = | 0 |
| `CDirectSoundStream_SetMixBinVolumes` | DSOUND | 82 | 82 | +0 | = | = | 0 |
| `IDirectSound_DownloadEffectsImage` | DSOUND | 39 | 39 | +0 | = | = | 0 |
| `IDirectSound_SynchPlayback` | DSOUND | 24 | 24 | +0 | = | = | 0 |
| `IDirectSoundBuffer_SetVolume` | DSOUND | 28 | 28 | +0 | = | = | 0 |
| `IDirectSoundBuffer_SetMixBins` | DSOUND | 28 | 28 | +0 | = | = | 0 |
| `IDirectSoundBuffer_SetMixBinVolumes` | DSOUND | 28 | 28 | +0 | = | = | 0 |
| `IDirectSoundBuffer_Play` | DSOUND | 36 | 36 | +0 | = | = | 0 |
| `IDirectSoundBuffer_PlayEx` | DSOUND | 36 | 36 | +0 | = | = | 0 |
| `IDirectSoundBuffer_Stop` | DSOUND | 24 | 24 | +0 | = | = | 0 |
| `IDirectSoundBuffer_Pause` | DSOUND | 28 | 28 | +0 | = | = | 0 |
| `IDirectSoundBuffer_SetLoopRegion` | DSOUND | 32 | 32 | +0 | = | = | 0 |
| `IDirectSoundBuffer_GetStatus` | DSOUND | 28 | 28 | +0 | = | = | 0 |
| `DirectSoundDoWork` | DSOUND | 41 | 41 | +0 | = | = | 0 |
| `IDirectSoundBuffer_SetFormat` | DSOUND | 28 | 28 | +0 | = | = | 0 |
| `IDirectSoundBuffer_SetFrequency` | DSOUND | 28 | 28 | +0 | = | = | 0 |
| `IDirectSoundBuffer_SetPlayRegion` | DSOUND | 32 | 32 | +0 | = | = | 0 |
| `IDirectSoundBuffer_SetBufferData` | DSOUND | 32 | 32 | +0 | = | = | 0 |
| `IDirectSound_CreateSoundBuffer` | DSOUND | 36 | 36 | +0 | = | = | 0 |
| `DirectSoundCreate` | DSOUND | 71 | 71 | +0 | = | = | 0 |
| `DirectSoundCreateStream` | DSOUND | 87 | 87 | +0 | = | = | 0 |
| `XInitDevices` | XPP | 121 | 121 | +0 | = | = | 0 |
| `XInputOpen` | XPP | 86 | 86 | +0 | = | = | 0 |
| `XInputClose` | XPP | 12 | 12 | +0 | = | = | 0 |
| `XInputGetState` | XPP | 108 | 115 | -7 | = | = | 0 |
| `XInputSetState` | XPP | 51 | 51 | +0 | = | = | 0 |

Over these 121 anchors: ret equal 121/121, regs equal 121/121, calls equal 115/121 and within ±1 117/121, length identical 99/121 and within the band 111/121 (92%).

Between the two reference builds (5849 against 5558), over the library target names both sign: ret equal 168/168, regs 168/168, len 164/168, calls 168/168.

- **ret and regs are required.** ret held for 121/121 anchors and 168/168 reference pairs, regs for 121/121 and 168/168. A mismatch means a different calling convention, which is exactly the failure that corrupts the port.
- **calls within ±1 is required**: it held for 117/121 anchors, and the reference builds agree on 168/168 names.
- **Length is corroboration, not proof.** 5233 code drifts from 5558 wherever a function was rewritten between the builds (the table above shows how far on this title's anchors), so the band keeps the anchors' usual drift, and a length outside it is not disqualifying when a distinctive hardware constant (the NV2A method the function writes) carries the identity instead. When the reference has no stable constant, the length must be inside the band.
- **Stable constants** (NV2A methods, flags, HRESULTs) are hardware and ABI identities; a candidate that shares none of the constants both reference builds agree on is not emitted.
- **Lead ≥ 2** is the weight of one agreeing required invariant (regs): any alignment that places the name elsewhere, or nowhere, must lose at least that much evidence, not a rounding amount of length closeness.
- **Exclusivity ≥ 1.5** is one shared-constant bonus: the candidate must out-score every credible alternative by real evidence, not by a length difference of a few bytes. Order alone does not prove which of several identical-looking functions is which.
- **Size ratio ≤ 3**: an object's code changes by tens of percent between XDK versions, not by multiples; a bracket whose two stretches differ by more holds code from elsewhere.

## Emitted names

None.

## Rejections

First rule each rejected name fails, in the order the rules are checked:

| Reason | D3D | DSOUND | XPP | XGRPH | XMV | all |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| alignment leaves it unmatched | 21 | 40 | 0 | 0 | 0 | 61 |
| nearest anchors inverted in the target | 0 | 4 | 0 | 0 | 0 | 4 |
| anchored on one side only | 1 | 0 | 0 | 0 | 0 | 1 |

Every check the alignment's own candidate fails, counted over the rejected names that have one (a name can fail several):

| Check | Failed |
| --- | ---: |
| (rejected names with a candidate) | 1 |
| regs differ | 0 |
| calls outside ±1 | 0 |
| shares no reference constant | 0 |
| length outside band | 0 |
| length outside band, no distinctive constant | 0 |
| alignment lead too small | 0 |
| not exclusive in bracket | 1 |
| not bracketed by two anchors | 1 |
| ret differs | 0 (a pairing with another ret is never made) |

## Candidates not emitted

### Strongest leads (1)

Names whose pick passes every invariant (ret, regs, calls, constants and the length band) and is held back only by position or ambiguity. They are where static RE pays off first; they are still not proof (the next table shows each one's competitors).

| Name | Pick | Score | Held back because |
| --- | --- | ---: | --- |
| `CDirectSoundStream_SetFormat` | 0x1B6670 | 6.2 | its nearest anchors are in opposite order in the target (a moved block); not exclusive in its bracket: 0x1B6622 also passes, scoring 6.19 against 6.19 |

### All, by section

Ranked within each section by the best pair score any candidate reaches, so the most promising names for static RE come first. *Pick* is the alignment's choice in the name's bracket (score, lead, failed checks); *Others* are the best-scoring functions anywhere in the section with the same `ret`. An address already held by an anchor or an emitted name is marked `= Name`. A pick or an alternative is a lead for a human, **not** evidence: no row here passed the emission rule.

#### D3D (22)

| Name | 5558 | Reference | Bracket | Pick | Others | Why not emitted |
| --- | --- | --- | --- | --- | --- | --- |
| `D3DResource_IsBusy` | 0x244B10 | ret 4, regs -, len 138, calls 0 | tight D3D_InternalAddRef … D3D_InternalRelease | unmatched | 0x18FB60 7.5 (none); 0x18FA50 1.5 (len -85); 0x18FAD0 1.5 (len -83) | the alignment leaves it unmatched |
| `D3DResource_BlockUntilNotBusy` | 0x244BF0 | ret jmp, regs -, len 5, calls 1 | tight D3D_InternalAddRef … D3D_InternalRelease | unmatched | 0x192ED0 6.0 (none); 0x192EE0 4.0 (none); 0x1977A0 4.0 (none) | the alignment leaves it unmatched |
| `D3DDevice_EnableOverlay` | 0x259700 | ret 4, regs -, len 99, calls 0 | forward Lock2DSurface … edge | unmatched | 0x1975E0 5.3 (none); 0x196F30 5.2 (none); 0x18FFC0 4.3 (none) | anchored on one side only: no anchor above it in 5558 order; the alignment leaves it unmatched |
| `D3DDevice_EndPush` | 0x24D0C0 | ret 4, regs -, len 15, calls 0 | tight D3DDevice_InsertCallback … CDevice_KickOff | unmatched | 0x1957B0 4.8 (none); 0x192EF0 4.5 (none); 0x1975C0 4.5 (none) | no target function in the bracket |
| `D3DDevice_SwitchTexture` | 0x245300 | ret 4, regs ecx,edx, len 48, calls 1 | loose D3DDevice_SetTransform … D3DDevice_Release | unmatched | 0x191E50 4.5 (none); 0x19A416 -1.5 (regs); 0x18FA50 -2.8 (regs) | no target function in the bracket |
| `D3DDevice_IsFencePending` | 0x24D010 | ret 4, regs -, len 30, calls 0 | tight D3DDevice_SetVertexShader … D3DDevice_InsertCallback | unmatched | 0x1976A0 4.5 (none); 0x1976C0 4.2 (none); 0x192EF0 2.1 (len -11) | the alignment leaves it unmatched |
| `D3DDevice_SetMaterial` | 0x2451D0 | ret 4, regs -, len 48, calls 0 | loose D3DDevice_SetTransform … D3DDevice_Release | unmatched | 0x18FA50 4.2 (none); 0x18FAD0 3.8 (none); 0x192D20 2.0 (calls ±2) | no target function in the bracket |
| `D3DDevice_SetTile` | 0x247A20 | ret jmp, regs -, len 10, calls 2 | loose D3DDevice_SetPalette … D3DDevice_SetScissors | unmatched | 0x192EE0 4.2 (none); 0x192ED0 3.2 (none); 0x1977A0 2.8 (calls ±2) | the alignment leaves it unmatched |
| `D3DDevice_BlockOnFence` | 0x2453C0 | ret 4, regs -, len 15, calls 1 | tight D3DDevice_Release … D3DDevice_BlockUntilVerticalBlank | unmatched | 0x1957B0 3.8 (none); 0x192EF0 3.5 (none); 0x1975C0 3.5 (none) | the alignment leaves it unmatched |
| `D3DDevice_GetRenderTarget2` | 0x246B00 | ret 0, regs -, len 26, calls 1 | tight D3DDevice_CopyRects … D3DDevice_GetDepthStencilSurface2 | unmatched | 0x1923D0 3.8 (none); 0x195960 3.2 (none); 0x1926C0 0.1 (len +19) | no target function in the bracket |
| `D3DDevice_DeletePixelShader` | 0x24E2E0 | ret 4, regs -, len 29, calls 1 | loose D3DDevice_End … D3DDevice_SetPixelShader | unmatched | 0x1976A0 3.8 (none); 0x1976C0 3.0 (none); 0x192EF0 1.2 (len -10) | the alignment leaves it unmatched |
| `D3DDevice_LightEnable` | 0x247030 | ret 8, regs -, len 337, calls 1 | loose D3DDevice_SetViewport … D3DDevice_SetTexture | unmatched | 0x191620 3.3 (none); 0x199840 2.1 (len -58); 0x18FD50 1.4 (len -44) | no target function in the bracket |
| `D3DDevice_InsertFence` | 0x245790 | ret 0, regs -, len 8, calls 1 | loose D3DDevice_SetSoftDisplayFilter … D3DDevice_Reset | unmatched | 0x199830 3.2 (none); 0x18FE80 0.0 (len +312); 0x190B10 0.0 (len +198) | the alignment leaves it unmatched |
| `D3DDevice_CreatePixelShader` | 0x24E290 | ret 8, regs -, len 72, calls 1 | loose D3DDevice_End … D3DDevice_SetPixelShader | unmatched | 0x195710 2.5 (k); 0x192120 -0.7 (len -15, k); 0x195790 -1.5 (len -42, k) | the alignment leaves it unmatched |
| `D3DDevice_SetVertexShaderConstant1Fast` | 0x24BA70 | ret 0, regs ecx,edx, len 73, calls 1 | tight D3DDevice_SetVertexShaderConstant1 … D3DDevice_SetVertexShaderConstant4 | unmatched | 0x190870 1.6 (k); 0x190AB0 -0.8 (len +16, k); 0x1908C0 -1.5 (len +412, k) | no target function in the bracket |
| `D3DDevice_FlushVertexCache` | 0x2476F0 | ret 0, regs -, len 39, calls 1 | loose D3DDevice_SetPalette … D3DDevice_SetScissors | unmatched | 0x1926C0 1.5 (k); 0x193930 1.0 (k); 0x195960 1.0 (k) | the alignment leaves it unmatched |
| `D3DDevice_GetVertexShaderFunction` | 0x24C870 | ret 12, regs -, len 188, calls 0 | tight D3DDevice_SetVertexShader … D3DDevice_InsertCallback | unmatched | 0x197A10 1.0 (calls ±2, k); 0x194E70 0.0 (len -44, k); 0x196D50 -0.7 (len +62, k) | the alignment leaves it unmatched |
| `D3DDevice_SetGammaRamp` | 0x244EC0 | ret 8, regs -, len 131, calls 1 | loose D3D_InternalRelease … D3DDevice_SetTransform | unmatched | 0x195790 0.0 (len -101); 0x1958E0 0.0 (len -111); 0x199840 0.0 (len +148) | the alignment leaves it unmatched |
| `D3DDevice_SetIndices` | 0x247430 | ret 8, regs -, len 132, calls 1 | loose D3DDevice_SetPalette … D3DDevice_SetScissors | unmatched | 0x195790 -1.5 (len -102, k); 0x1958E0 -1.5 (len -112, k); 0x199840 -1.5 (len +147, k) | the alignment leaves it unmatched |
| `D3DDevice_SetPixelShaderConstant` | 0x24E940 | ret 12, regs -, len 711, calls 1 | tight D3DDevice_SetPixelShader … D3D_InitDefaultState | unmatched | 0x195360 -1.5 (len -656, k); 0x196FF0 -1.5 (len +650, k); 0x191810 -2.5 (len -607, k) | the alignment leaves it unmatched |
| `D3DDevice_PersistDisplay` | 0x247FC0 | ret 0, regs -, len 302, calls 7 | tight D3DDevice_SetScissors … D3DDevice_SetScreenSpaceOffset | unmatched | 0x1993D0 -2.5 (len -180, k); 0x18FE80 -3.0 (calls ±6, k); 0x195F10 -3.9 (regs, k) | no target function in the bracket |
| `D3DDevice_SetLight` | 0x246D70 | ret 8, regs -, len 691, calls 7 | loose D3DDevice_SetViewport … D3DDevice_SetTexture | unmatched | 0x1991D0 -4.3 (len -192, calls ±4, k); 0x192120 -6.5 (len -634, calls ±5, k); 0x1939A0 -6.5 (len -507, calls ±5, k) | no target function in the bracket |

#### DSOUND (44)

| Name | 5558 | Reference | Bracket | Pick | Others | Why not emitted |
| --- | --- | --- | --- | --- | --- | --- |
| `CDirectSoundStream_SetFilter` | 0x28DAFC | ret 8, regs -, len 82, calls 2 | loose CDirectSoundStream_SetVolume … CDirectSoundStream_SetMixBinVolumes | unmatched | 0x1B5AA7 6.8 (none); 0x1B5AF8 6.8 (none); 0x1B5F4E 6.2 (none) | no target function in the bracket |
| `CDirectSoundStream_SetHeadroom` | 0x28DB4E | ret 8, regs -, len 82, calls 2 | loose CDirectSoundStream_SetVolume … CDirectSoundStream_SetMixBinVolumes | unmatched | 0x1B5AA7 6.8 (none); 0x1B5AF8 6.8 (none); 0x1B5F4E 6.2 (none) | no target function in the bracket |
| `CDirectSoundStream_SetFrequency` | 0x28F791 | ret 8, regs -, len 82, calls 2 | inverted DirectSoundDoWork … CDirectSoundStream_SetMixBins | unmatched | 0x1B5AA7 6.8 (none); 0x1B5AF8 6.8 (none); 0x1B5F4E 6.2 (none) | its nearest anchors are in opposite order in the target (a moved block); the alignment leaves it unmatched |
| `CDirectSoundStream_SetFormat` | 0x290740 | ret 8, regs -, len 82, calls 2 | inverted IDirectSoundBuffer_SetPlayRegion … IDirectSoundBuffer_SetFormat | 0x1B6670 score 6.2, lead 6.2; fails: none | 0x1B5AA7 6.8 (none); 0x1B5AF8 6.8 (none); 0x1B5F4E 6.2 (none) | its nearest anchors are in opposite order in the target (a moved block); not exclusive in its bracket: 0x1B6622 also passes, scoring 6.19 against 6.19 |
| `IDirectSound_GetSpeakerConfig` | 0x28DD30 | ret 8, regs -, len 28, calls 1 | loose CDirectSoundStream_SetMixBinVolumes … IDirectSound_DownloadEffectsImage | unmatched | 0x1B5806 6.0 (none); 0x1B862B 5.2 (none); 0x1BC338 5.2 (none) | no target function in the bracket |
| `IDirectSound_EnableHeadphones` | 0x28DDDC | ret 8, regs -, len 28, calls 1 | loose IDirectSound_DownloadEffectsImage … IDirectSound_SynchPlayback | unmatched | 0x1B5806 6.0 (none); 0x1B862B 5.2 (none); 0x1BC338 5.2 (none) | no target function in the bracket |
| `IDirectSoundBuffer_SetFilter` | 0x28DF4A | ret 8, regs -, len 28, calls 1 | loose IDirectSoundBuffer_SetVolume … IDirectSoundBuffer_SetMixBinVolumes | unmatched | 0x1B5806 6.0 (none); 0x1B862B 5.2 (none); 0x1BC338 5.2 (none) | no target function in the bracket |
| `IDirectSoundBuffer_SetHeadroom` | 0x28DF66 | ret 8, regs -, len 28, calls 1 | loose IDirectSoundBuffer_SetVolume … IDirectSoundBuffer_SetMixBinVolumes | unmatched | 0x1B5806 6.0 (none); 0x1B862B 5.2 (none); 0x1BC338 5.2 (none) | no target function in the bracket |
| `IDirectSoundBuffer_SetCurrentPosition` | 0x28E0BE | ret 8, regs -, len 28, calls 1 | loose IDirectSoundBuffer_GetStatus … DirectSoundDoWork | unmatched | 0x1B5806 6.0 (none); 0x1B862B 5.2 (none); 0x1BC338 5.2 (none) | the alignment leaves it unmatched |
| `IDirectSoundStream_SetEG` | 0x28E18D | ret jmp, regs -, len 5, calls 1 | loose IDirectSoundBuffer_GetStatus … DirectSoundDoWork | unmatched | 0x1B5558 6.0 (none); 0x1B555D 6.0 (none); 0x1B6279 6.0 (none) | the alignment leaves it unmatched |
| `IDirectSoundBuffer_SetOutputBuffer` | 0x28FDB2 | ret 8, regs -, len 28, calls 1 | inverted IDirectSoundBuffer_SetFrequency … IDirectSoundBuffer_SetMixBins | unmatched | 0x1B5806 6.0 (none); 0x1B862B 5.2 (none); 0x1BC338 5.2 (none) | its nearest anchors are in opposite order in the target (a moved block); no target function in the bracket |
| `IDirectSound_CommitDeferredSettings` | 0x290CAF | ret 4, regs -, len 24, calls 1 | loose IDirectSoundBuffer_SetBufferData … IDirectSound_CreateSoundBuffer | unmatched | 0x1BA167 5.2 (none); 0x1B8143 4.5 (none); 0x1BB12F 3.8 (none) | the alignment leaves it unmatched |
| `IDirectSound_CommitEffectData` | 0x28DDC4 | ret 4, regs -, len 24, calls 1 | loose IDirectSound_DownloadEffectsImage … IDirectSound_SynchPlayback | unmatched | 0x1BA167 5.2 (none); 0x1B8143 4.5 (none); 0x1BB12F 3.8 (none) | no target function in the bracket |
| `CDirectSoundStream_SetPosition` | 0x28FB02 | ret 20, regs -, len 107, calls 2 | loose CDirectSoundStream_SetMixBins … IDirectSoundBuffer_SetFrequency | unmatched | 0x1B5622 4.9 (none); 0x1BC861 -2.5 (len +100, k); 0x1B85E7 -3.0 (len -39, calls ±2, k) | the alignment leaves it unmatched |
| `CDirectSoundStream_SetVelocity` | 0x28FB6D | ret 20, regs -, len 107, calls 2 | loose CDirectSoundStream_SetMixBins … IDirectSoundBuffer_SetFrequency | unmatched | 0x1B5622 4.9 (none); 0x1BC861 -2.5 (len +100, k); 0x1B85E7 -3.0 (len -39, calls ±2, k) | the alignment leaves it unmatched |
| `IDirectSoundBuffer_SetMaxDistance` | 0x28FE83 | ret 12, regs -, len 36, calls 1 | loose IDirectSoundBuffer_SetMixBins … IDirectSoundBuffer_SetPlayRegion | unmatched | 0x1BBEE3 3.8 (none); 0x1BCF08 0.4 (len +25); 0x1BCF45 0.1 (len +27) | the alignment leaves it unmatched |
| `IDirectSoundBuffer_SetMinDistance` | 0x28FEA7 | ret 12, regs -, len 36, calls 1 | loose IDirectSoundBuffer_SetMixBins … IDirectSoundBuffer_SetPlayRegion | unmatched | 0x1BBEE3 3.8 (none); 0x1BCF08 0.4 (len +25); 0x1BCF45 0.1 (len +27) | the alignment leaves it unmatched |
| `IDirectSound_SetDistanceFactor` | 0x2912F4 | ret 12, regs -, len 36, calls 1 | tight IDirectSound_CreateSoundBuffer … DirectSoundCreate | unmatched | 0x1BBEE3 3.8 (none); 0x1BCF08 0.4 (len +25); 0x1BCF45 0.1 (len +27) | the alignment leaves it unmatched |
| `IDirectSound_SetDopplerFactor` | 0x291318 | ret 12, regs -, len 36, calls 1 | tight IDirectSound_CreateSoundBuffer … DirectSoundCreate | unmatched | 0x1BBEE3 3.8 (none); 0x1BCF08 0.4 (len +25); 0x1BCF45 0.1 (len +27) | the alignment leaves it unmatched |
| `IDirectSound_SetRolloffFactor` | 0x2913BB | ret 12, regs -, len 36, calls 1 | tight IDirectSound_CreateSoundBuffer … DirectSoundCreate | unmatched | 0x1BBEE3 3.8 (none); 0x1BCF08 0.4 (len +25); 0x1BCF45 0.1 (len +27) | the alignment leaves it unmatched |
| `DirectSoundCreateBuffer` | 0x291621 | ret 8, regs -, len 87, calls 3 | tight DirectSoundCreate … DirectSoundCreateStream | unmatched | 0x1B5AA7 3.4 (none); 0x1B5AF8 3.4 (none); 0x1B5F4E 2.8 (none) | no target function in the bracket |
| `DirectSoundUseFullHRTF` | 0x28BB69 | ret 0, regs -, len 31, calls 2 | tight IDirectSoundBuffer_Release … CDirectSoundStream_AddRef | unmatched | 0x1B541F 3.2 (calls ±2); 0x1B5471 3.2 (calls ±2); 0x1BD5B6 2.8 (none) | the alignment leaves it unmatched |
| `DirectSoundUseLightHRTF` | 0x28BB88 | ret 0, regs -, len 31, calls 2 | tight IDirectSoundBuffer_Release … CDirectSoundStream_AddRef | unmatched | 0x1B541F 3.2 (calls ±2); 0x1B5471 3.2 (calls ±2); 0x1BD5B6 2.8 (none) | the alignment leaves it unmatched |
| `IDirectSound_SetMixBinHeadroom` | 0x28DDF8 | ret 12, regs -, len 32, calls 1 | loose IDirectSound_DownloadEffectsImage … IDirectSound_SynchPlayback | unmatched | 0x1BBEE3 2.8 (none); 0x1BCF08 0.0 (len +29); 0x1BCF45 0.0 (len +31) | no target function in the bracket |
| `IDirectSoundBuffer_GetCurrentPosition` | 0x28E09E | ret 12, regs -, len 32, calls 1 | loose IDirectSoundBuffer_GetStatus … DirectSoundDoWork | unmatched | 0x1BBEE3 2.8 (none); 0x1BCF08 0.0 (len +29); 0x1BCF45 0.0 (len +31) | the alignment leaves it unmatched |
| `IDirectSoundBuffer_SetI3DL2Source` | 0x28FFE5 | ret 12, regs -, len 32, calls 1 | loose IDirectSoundBuffer_SetMixBins … IDirectSoundBuffer_SetPlayRegion | unmatched | 0x1BBEE3 2.8 (none); 0x1BCF08 0.0 (len +29); 0x1BCF45 0.0 (len +31) | the alignment leaves it unmatched |
| `IDirectSound_SetI3DL2Listener` | 0x291414 | ret 12, regs -, len 32, calls 1 | tight IDirectSound_CreateSoundBuffer … DirectSoundCreate | unmatched | 0x1BBEE3 2.8 (none); 0x1BCF08 0.0 (len +29); 0x1BCF45 0.0 (len +31) | the alignment leaves it unmatched |
| `IDirectSound_GetOutputLevels` | 0x28DE34 | ret 12, regs -, len 32, calls 1 | loose IDirectSound_DownloadEffectsImage … IDirectSound_SynchPlayback | unmatched | 0x1BBEE3 2.8 (none); 0x1BCF08 0.0 (len +29); 0x1BCF45 0.0 (len +31) | no target function in the bracket |
| `IDirectSoundBuffer_SetAllParameters` | 0x28FDEA | ret 12, regs -, len 32, calls 1 | loose IDirectSoundBuffer_SetMixBins … IDirectSoundBuffer_SetPlayRegion | unmatched | 0x1BBEE3 2.8 (none); 0x1BCF08 0.0 (len +29); 0x1BCF45 0.0 (len +31) | the alignment leaves it unmatched |
| `IDirectSoundBuffer_StopEx` | 0x28DFFE | ret 16, regs -, len 36, calls 1 | tight IDirectSoundBuffer_Stop … IDirectSoundBuffer_Pause | unmatched | 0x1B628D 2.0 (len -12); 0x1B8137 0.5 (len -24); 0x1B82B7 0.5 (len -24) | no target function in the bracket |
| `IDirectSoundBuffer_SetRolloffCurve` | 0x28FFC1 | ret 16, regs -, len 36, calls 1 | loose IDirectSoundBuffer_SetMixBins … IDirectSoundBuffer_SetPlayRegion | unmatched | 0x1B628D 2.0 (len -12); 0x1B8137 0.5 (len -24); 0x1B82B7 0.5 (len -24) | the alignment leaves it unmatched |
| `CDirectSoundStream_SetMaxDistance` | 0x28F9F8 | ret 12, regs -, len 90, calls 2 | loose CDirectSoundStream_SetMixBins … IDirectSoundBuffer_SetFrequency | unmatched | 0x1B5B49 1.5 (len +43); 0x1B62CE 0.9 (calls ±2, k); 0x1B71E4 0.7 (len +14, k) | the alignment leaves it unmatched |
| `CDirectSoundStream_SetMinDistance` | 0x28FA52 | ret 12, regs -, len 90, calls 2 | loose CDirectSoundStream_SetMixBins … IDirectSoundBuffer_SetFrequency | unmatched | 0x1B5B49 1.5 (len +43); 0x1B62CE 0.9 (calls ±2, k); 0x1B71E4 0.7 (len +14, k) | the alignment leaves it unmatched |
| `CDirectSoundStream_SetI3DL2Source` | 0x28FD40 | ret 12, regs -, len 86, calls 2 | loose CDirectSoundStream_SetMixBins … IDirectSoundBuffer_SetFrequency | unmatched | 0x1B5B49 1.5 (len +47); 0x1B6583 0.5 (len +42); 0x1B71E4 0.3 (len +18, k) | the alignment leaves it unmatched |
| `IDirectSoundBuffer_SetPosition` | 0x28FEEB | ret 20, regs -, len 53, calls 1 | loose IDirectSoundBuffer_SetMixBins … IDirectSoundBuffer_SetPlayRegion | unmatched | 0x1B85E7 0.6 (len +15); 0x1B5622 -2.0 (len +47, calls ±2); 0x1BC861 -2.0 (len +154, calls ±2) | the alignment leaves it unmatched |
| `IDirectSoundBuffer_SetVelocity` | 0x28FF20 | ret 20, regs -, len 53, calls 1 | loose IDirectSoundBuffer_SetMixBins … IDirectSoundBuffer_SetPlayRegion | unmatched | 0x1B85E7 0.6 (len +15); 0x1B5622 -2.0 (len +47, calls ±2); 0x1BC861 -2.0 (len +154, calls ±2) | the alignment leaves it unmatched |
| `IDirectSound_SetPosition` | 0x291386 | ret 20, regs -, len 53, calls 1 | tight IDirectSound_CreateSoundBuffer … DirectSoundCreate | unmatched | 0x1B85E7 0.6 (len +15); 0x1B5622 -2.0 (len +47, calls ±2); 0x1BC861 -2.0 (len +154, calls ±2) | the alignment leaves it unmatched |
| `IDirectSound_SetVelocity` | 0x2913DF | ret 20, regs -, len 53, calls 1 | tight IDirectSound_CreateSoundBuffer … DirectSoundCreate | unmatched | 0x1B85E7 0.6 (len +15); 0x1B5622 -2.0 (len +47, calls ±2); 0x1BC861 -2.0 (len +154, calls ±2) | the alignment leaves it unmatched |
| `IDirectSoundBuffer_Unlock` | 0x28BAF7 | ret 20, regs -, len 5, calls 0 | tight IDirectSound_Release … IDirectSoundBuffer_Release | unmatched | 0x1B85E7 0.0 (len +63); 0x1B5622 -3.0 (len +95, calls ±3); 0x1BC861 -3.0 (len +202, calls ±3) | no target function in the bracket |
| `IDirectSound_GetEffectData` | 0x28DD73 | ret 20, regs -, len 39, calls 1 | loose IDirectSound_DownloadEffectsImage … IDirectSound_SynchPlayback | unmatched | 0x1B85E7 -1.0 (len +29); 0x1B5622 -2.0 (len +61, calls ±2); 0x1BC861 -2.0 (len +168, calls ±2) | no target function in the bracket |
| `XAudioDownloadEffectsImage` | 0x28E23D | ret 16, regs -, len 514, calls 27 | inverted DirectSoundDoWork … CDirectSoundStream_SetMixBins | unmatched | 0x1B6BC0 -21.5 (len -369, calls ±23); 0x1B6DFF -21.5 (len -358, calls ±23); 0x1B59AE -26.5 (len -433, calls ±25, k) | its nearest anchors are in opposite order in the target (a moved block); the alignment leaves it unmatched |
| `IDirectSound_SetEffectData` | 0x28DD9A | ret 24, regs -, len 42, calls 1 | loose IDirectSound_DownloadEffectsImage … IDirectSound_SynchPlayback | unmatched | none with equal ret | no target function in the bracket |
| `IDirectSoundBuffer_Lock` | 0x28E0DA | ret 32, regs -, len 48, calls 1 | loose IDirectSoundBuffer_GetStatus … DirectSoundDoWork | unmatched | none with equal ret | the alignment leaves it unmatched |
| `IDirectSound_SetOrientation` | 0x29133C | ret 32, regs -, len 74, calls 1 | tight IDirectSound_CreateSoundBuffer … DirectSoundCreate | unmatched | none with equal ret | the alignment leaves it unmatched |

## Held-out anchors

Each library anchor, removed from the anchor set and placed by the rest exactly as an unknown name would be. This measures the emission rule on names whose answer is known.

| Anchor | Proven | Bracket without it | Result |
| --- | --- | --- | --- |
| `Direct3D_CreateDevice` | 0x18F8B0 | backward | not emitted, pick 0x18F8B0 (right): anchored on one side only: no anchor below it in 5558 order |
| `D3D_InternalAddRef` | 0x18FA90 | tight | not emitted, pick 0x18FA90 (right): not exclusive in its bracket: 0x18FA50 also passes, scoring 6.25 against 7.50 |
| `D3D_InternalRelease` | 0x18FC20 | loose | emitted, **correct** |
| `D3DDevice_SetRenderState_PSTextureModes` | 0x18FC90 | inverted | not emitted, pick 0x18FC90 (right): its nearest anchors are in opposite order in the target (a moved block) |
| `D3DDevice_SetRenderState_Simple` | 0x18FCC0 | tight | emitted, **correct** |
| `D3DDevice_SetRenderStateNotInline` | 0x18FCF0 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_EdgeAntiAlias` | 0x190020 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_ShadowFunc` | 0x190060 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_FogColor` | 0x1900A0 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_CullMode` | 0x1900F0 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_FrontFace` | 0x190160 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_NormalizeNormals` | 0x1901A0 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_TextureFactor` | 0x1901E0 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_LineWidth` | 0x190240 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_Dxt1NoiseEnable` | 0x1902B0 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_LogicOp` | 0x1903B0 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_FillMode` | 0x190410 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_BackFillMode` | 0x190460 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_TwoSidedLighting` | 0x1904C0 | tight | not emitted, pick 0x1904C0 (right): len -29 outside ±15 with no distinctive constant |
| `D3DDevice_SetRenderState_VertexBlend` | 0x190530 | tight | emitted, **correct** |
| `D3DDevice_SetTextureState_TexCoordIndex` | 0x190580 | tight | emitted, **correct** |
| `D3DDevice_SetTextureState_BumpEnv` | 0x190690 | tight | emitted, **correct** |
| `D3DDevice_SetTextureState_BorderColor` | 0x190700 | tight | emitted, **correct** |
| `D3DDevice_SetTextureState_ColorKeyColor` | 0x190740 | tight | emitted, **correct** |
| `D3DDevice_SetTextureStageStateNotInline` | 0x190780 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_ZEnable` | 0x191180 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_StencilEnable` | 0x191210 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_StencilFail` | 0x1912A0 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_YuvEnable` | 0x191310 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_OcclusionCullEnable` | 0x191340 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_StencilCullEnable` | 0x1913B0 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_RopZCmpAlwaysRead` | 0x191420 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_RopZRead` | 0x191440 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_DoNotCullUncompressed` | 0x191460 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_MultiSampleMode` | 0x191480 | tight | not emitted, pick 0x191480 (right): len +13 outside ±8 with no distinctive constant; ambiguous alignment: lead 1.88 < 2.0 |
| `D3DDevice_SetRenderState_MultiSampleRenderTargetMode` | 0x1914C0 | tight | not emitted, pick 0x1914C0 (right): len +13 outside ±8 with no distinctive constant; ambiguous alignment: lead 1.88 < 2.0 |
| `D3DDevice_SetRenderState_MultiSampleAntiAlias` | 0x191500 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_MultiSampleMask` | 0x191580 | tight | emitted, **correct** |
| `D3DDevice_SetRenderState_SampleAlpha` | 0x1915D0 | tight | emitted, **correct** |
| `D3DDevice_CreateVertexShader` | 0x191B20 | tight | emitted, **correct** |
| `D3DDevice_SetVertexShaderConstant1` | 0x191C60 | tight | emitted, **correct** |
| `D3DDevice_SetVertexShaderConstant4` | 0x191CC0 | tight | emitted, **correct** |
| `D3DDevice_SetVertexShaderConstantNotInlineFast` | 0x191D70 | tight | emitted, **correct** |
| `D3DDevice_SetStreamSource` | 0x191E90 | tight | emitted, **correct** |
| `D3DDevice_LoadVertexShader` | 0x191F20 | tight | emitted, **correct** |
| `D3DDevice_SelectVertexShader` | 0x191F80 | tight | not emitted, pick 0x191F80 (right): len -28 outside ±19 with no distinctive constant |
| `D3DDevice_SetShaderConstantMode` | 0x192000 | tight | emitted, **correct** |
| `D3DDevice_DeleteVertexShader` | 0x192160 | tight | emitted, **correct** |
| `D3DDevice_SetVertexShader` | 0x192270 | tight | emitted, **correct** |
| `D3DDevice_InsertCallback` | 0x1926F0 | tight | emitted, **correct** |
| `CDevice_KickOff` | 0x192760 | tight | not emitted, pick 0x192760 (right): len +43 outside ±21 with no distinctive constant |
| `D3D_SetFence` | 0x1928B0 | tight | emitted, **correct** |
| `D3D_BlockOnTime` | 0x192960 | tight | not emitted, pick 0x192960 (right): calls off by 2; len -48 outside ±43 with no distinctive constant; ambiguous alignment: lead 1.88 < 2.0 |
| `D3D_MakeRequestedSpace` | 0x192AA0 | tight | emitted, **correct** |
| `D3DDevice_MakeSpace` | 0x192C20 | tight | emitted, **correct** |
| `D3DDevice_BeginPush` | 0x192C30 | tight | emitted, **correct** |
| `D3D_KickOffAndWaitForIdle` | 0x192C80 | tight | emitted, **correct** |
| `D3D_BlockOnResource` | 0x192CA0 | loose | emitted, **correct** |
| `D3DDevice_SetRenderTarget` | 0x192D60 | loose | not emitted, no pick: no target function in the bracket |
| `D3DDevice_SetTransform` | 0x192D80 | loose | not emitted, pick 0x18FD50 (wrong): calls off by 2; shares none of the reference's stable constants; ambiguous alignment: lead 1.07 < 2.0; not exclusive in its bracket: 0x192D80 also passes, scoring 6.40 against 1.23; loose bracket and not exclusive in D3D: 0x192D80 also passes, scoring 6.40 against 1.23 |
| `D3DDevice_Release` | 0x192E90 | tight | emitted, **correct** |
| `D3DDevice_BlockUntilVerticalBlank` | 0x192F10 | loose | emitted, **correct** |
| `D3DDevice_SetFlickerFilter` | 0x192F40 | loose | not emitted, pick 0x192F40 (right): loose bracket and not exclusive in D3D: 0x195920 also passes, scoring 5.00 against 6.00 |
| `D3DDevice_SetSoftDisplayFilter` | 0x192F90 | loose | not emitted, pick 0x192F90 (right): loose bracket and not exclusive in D3D: 0x197560 also passes, scoring 5.29 against 6.00 |
| `D3DDevice_Reset` | 0x193140 | inverted | not emitted, pick 0x193140 (right): its nearest anchors are in opposite order in the target (a moved block) |
| `D3DDevice_GetBackBuffer2` | 0x1931F0 | loose | emitted, **correct** |
| `D3DDevice_CopyRects` | 0x193240 | tight | emitted, **correct** |
| `D3DDevice_GetDepthStencilSurface2` | 0x193570 | tight | not emitted, pick 0x193570 (right): ambiguous alignment: lead 1.50 < 2.0 |
| `D3DDevice_SetViewport` | 0x193590 | loose | not emitted, no pick: the alignment leaves it unmatched |
| `D3DDevice_SetTexture` | 0x1936F0 | tight | emitted, **correct** |
| `D3DDevice_SetPalette` | 0x1938A0 | loose | emitted, **correct** |
| `D3DDevice_SetScissors` | 0x193A60 | loose | not emitted, no pick: the alignment leaves it unmatched |
| `D3DDevice_SetScreenSpaceOffset` | 0x193C00 | loose | emitted, **correct** |
| `D3DDevice_Swap` | 0x1948F0 | inverted | not emitted, no pick: its nearest anchors are in opposite order in the target (a moved block); the alignment leaves it unmatched |
| `D3DDevice_Clear` | 0x194A90 | tight | not emitted, no pick: the alignment leaves it unmatched |
| `D3DDevice_DrawVerticesUP` | 0x194F00 | loose | emitted, **correct** |
| `D3DDevice_DrawVertices` | 0x195060 | tight | emitted, **correct** |
| `D3DDevice_DrawIndexedVertices` | 0x195100 | tight | emitted, **correct** |
| `D3DDevice_Begin` | 0x195450 | tight | emitted, **correct** |
| `D3DDevice_End` | 0x195490 | loose | emitted, **correct** |
| `D3DDevice_SetPixelShader` | 0x195510 | tight | emitted, **correct** |
| `D3D_InitDefaultState` | 0x195E30 | tight | emitted, **correct** |
| `Lock2DSurface` | 0x197D10 | forward | not emitted, pick 0x197D10 (right): anchored on one side only: no anchor above it in 5558 order |
| `IDirectSound_Release` | 0x1B54E1 | backward | not emitted, pick 0x1B5380 (wrong): anchored on one side only: no anchor below it in 5558 order; len +9 outside ±8 with no distinctive constant; not exclusive in its bracket: 0x1B54E1 also passes, scoring 6.00 against 2.38 |
| `IDirectSoundBuffer_Release` | 0x1B54F7 | tight | not emitted, no pick: the alignment leaves it unmatched |
| `CDirectSoundStream_AddRef` | 0x1B5C0F | tight | not emitted, pick 0x1B5C0F (right): not exclusive in its bracket: 0x1B55A1 also passes, scoring 7.50 against 7.50 |
| `CDirectSoundStream_Release` | 0x1B5C56 | tight | emitted, **correct** |
| `CDirectSoundStream_GetInfo` | 0x1B5CA4 | tight | emitted, **correct** |
| `CDirectSoundStream_Discontinuity` | 0x1B5D0B | tight | emitted, **correct** |
| `CDirectSoundStream_Flush` | 0x1B5D58 | tight | emitted, **correct** |
| `CDirectSoundStream_GetStatus` | 0x1B5DA3 | tight | emitted, **correct** |
| `CDirectSoundStream_Process` | 0x1B5DF4 | tight | emitted, **correct** |
| `CDirectSoundStream_Pause` | 0x1B5E6B | tight | emitted, **correct** |
| `CDirectSoundStream_FlushEx` | 0x1B5EBC | loose | emitted, **correct** |
| `CDirectSoundStream_SetVolume` | 0x1B6038 | loose | not emitted, no pick: the alignment leaves it unmatched |
| `CDirectSoundStream_SetMixBins` | 0x1B608A | loose | not emitted, no pick: the alignment leaves it unmatched |
| `CDirectSoundStream_SetMixBinVolumes` | 0x1B60DC | loose | not emitted, no pick: the alignment leaves it unmatched |
| `IDirectSound_DownloadEffectsImage` | 0x1B612E | loose | not emitted, no pick: the alignment leaves it unmatched |
| `IDirectSound_SynchPlayback` | 0x1B6155 | loose | not emitted, no pick: the alignment leaves it unmatched |
| `IDirectSoundBuffer_SetVolume` | 0x1B616D | loose | not emitted, no pick: the alignment leaves it unmatched |
| `IDirectSoundBuffer_SetMixBins` | 0x1B6189 | loose | not emitted, no pick: no target function in the bracket |
| `IDirectSoundBuffer_SetMixBinVolumes` | 0x1B61A5 | loose | not emitted, no pick: the alignment leaves it unmatched |
| `IDirectSoundBuffer_Play` | 0x1B61C1 | tight | emitted, **correct** |
| `IDirectSoundBuffer_PlayEx` | 0x1B61E5 | tight | emitted, **correct** |
| `IDirectSoundBuffer_Stop` | 0x1B6209 | tight | emitted, **correct** |
| `IDirectSoundBuffer_Pause` | 0x1B6221 | tight | emitted, **correct** |
| `IDirectSoundBuffer_SetLoopRegion` | 0x1B623D | tight | emitted, **correct** |
| `IDirectSoundBuffer_GetStatus` | 0x1B625D | loose | not emitted, no pick: the alignment leaves it unmatched |
| `DirectSoundDoWork` | 0x1B62A5 | inverted | not emitted, pick 0x1B62A5 (right): its nearest anchors are in opposite order in the target (a moved block) |
| `IDirectSoundBuffer_SetFormat` | 0x1B66BE | tight | not emitted, no pick: the alignment leaves it unmatched |
| `IDirectSoundBuffer_SetFrequency` | 0x1B66DA | loose | not emitted, no pick: no target function in the bracket |
| `IDirectSoundBuffer_SetPlayRegion` | 0x1B66F6 | loose | not emitted, no pick: the alignment leaves it unmatched |
| `IDirectSoundBuffer_SetBufferData` | 0x1B6BA0 | loose | not emitted, no pick: the alignment leaves it unmatched |
| `IDirectSound_CreateSoundBuffer` | 0x1B6EB6 | tight | not emitted, no pick: the alignment leaves it unmatched |
| `DirectSoundCreate` | 0x1B7080 | tight | emitted, **correct** |
| `DirectSoundCreateStream` | 0x1B70C7 | forward | not emitted, pick 0x1B75BA (wrong): anchored on one side only: no anchor above it in 5558 order; len -20 outside ±10 with no distinctive constant; ambiguous alignment: lead 0.43 < 2.0; not exclusive in its bracket: 0x1B70C7 also passes, scoring 6.00 against 1.58 |
| `XInitDevices` | 0x1E70D5 | backward | not emitted, pick 0x1E70D5 (right): anchored on one side only: no anchor below it in 5558 order |
| `XInputOpen` | 0x1E7B7C | tight | emitted, **correct** |
| `XInputClose` | 0x1E7BD2 | tight | emitted, **correct** |
| `XInputGetState` | 0x1E7DBC | tight | emitted, **correct** |
| `XInputSetState` | 0x1E7E28 | forward | not emitted, pick 0x1EA768 (wrong): anchored on one side only: no anchor above it in 5558 order; ambiguous alignment: lead 0.00 < 2.0; not exclusive in its bracket: 0x1E7E28 also passes, scoring 6.00 against 6.00 |

## Validation against the other agents' results

The other `config/found-*.toml` files hold names other agents proved by reading the code. They are never an input to the decisions above; here they serve as a larger set of known answers.

- **Held out against the union.** Taking `config/game.toml` and those files together (121 library names, 0 of them not yet in `config/game.toml`) and removing each name in turn: 80 re-emitted at the proven address, **0 at a different address**, 41 held back.
- **Projection.** With every name those files give merged in as anchors, the alignment emits 0 further names.

## Names outside this tool's scope

Target names whose section is not D3D, DSOUND, XPP, XGRPH or XMV (game code and statically linked CRT/XAPI in `.text`, where 5558 neighbour order says nothing about this game's link order), or that have no 5558 address:

- `BinkDoFrame` (BINK): not a library section
- `BinkGetSummary` (BINK): not a library section
- `BinkNextFrame` (BINK): not a library section
- `BinkWait` (BINK): not a library section
- `WSACancelOverlappedIO` (XNET): not a library section
- `WSAGetLastError` (XNET): not a library section
- `WSAGetOverlappedResult` (XNET): not a library section
- `WSARecv` (XNET): not a library section
- `WSARecvFrom` (XNET): not a library section
- `WSASend` (XNET): not a library section
- `WSASendTo` (XNET): not a library section
- `WSAStartup` (XNET): not a library section
- `XLaunchNewImageA` (.text): not a library section (= 0xC796D in game.toml)
- `XMountUtilityDrive` (.text): not a library section (= 0xC64AB in game.toml)
- `XNetCreateKey` (XNET): not a library section
- `XNetDnsLookup` (XNET): not a library section
- `XNetDnsRelease` (XNET): not a library section
- `XNetGetEthernetLinkStatus` (.text): not a library section
- `XNetGetTitleXnAddr` (XNET): not a library section
- `XNetInAddrToXnAddr` (XNET): not a library section
- `XNetRandom` (XNET): not a library section
- `XNetRegisterKey` (XNET): not a library section
- `XNetStartup` (XNET): not a library section
- `XNetUnregisterKey` (XNET): not a library section
- `XNetXnAddrToInAddr` (XNET): not a library section
- `XOnlineCleanup` (XONLINE): not a library section
- `XOnlineStartup` (XONLINE): not a library section
- `_CIacos` (.text): not a library section (= 0x1759F4 in game.toml)
- `_CIasin` (.text): not a library section (= 0x176F60 in game.toml)
- `accept` (XNET): not a library section
- `bind` (XNET): not a library section
- `closesocket` (XNET): not a library section
- `connect` (XNET): not a library section
- `crt_acos` (.text): not a library section (= 0x175A11 in game.toml)
- `crt_asin` (.text): not a library section (= 0x176F7D in game.toml)
- `crt_atan` (.text): not a library section
- `crt_cos` (.text): not a library section
- `crt_log` (.text): not a library section
- `crt_log10` (.text): not a library section
- `crt_pow` (.text): not a library section (= 0x17714C in game.toml)
- `crt_sin` (.text): not a library section
- `crt_sqrt` (.text): not a library section
- `crt_tan` (.text): not a library section
- `getsockname` (XNET): not a library section
- `getsockopt` (XNET): not a library section
- `ioctlsocket` (XNET): not a library section
- `listen` (XNET): not a library section
- `recv` (XNET): not a library section
- `recvfrom` (XNET): not a library section
- `select` (XNET): not a library section
- `send` (XNET): not a library section
- `sendto` (XNET): not a library section
- `setsockopt` (XNET): not a library section
- `shutdown` (XNET): not a library section
- `socket` (XNET): not a library section

## Before merging

This tool identifies addresses; it does not check that the SDK's host body for a name reads this build's data. The SDK runtime uses the 5849 render-state and texture-stage-state tables and the 5849 CDevice layout; XDK 5233 is not 5849, so until the runtime reads those per build this title's numbering and layout cannot be assumed to match. Merged before then, the complex render-state setters (every `SetRenderState_*` but `_Simple`) would make the host write 5849 indices into the 5233 state array and can land inside CDevice, the two `NotInline` dispatchers would route by 5849 numbering, and the device-state setters (`SetTexture`, `SetIndices`, `SetStreamSource`, `SetViewport`, `SetTransform`, `SetMaterial`) would read and write 5849 CDevice fields. `SetRenderState_Simple` and the `SetTextureState_*` leaves have no such dependency.

None of the emitted names falls in those families, so `config/found-align.toml` is not staged.

## Assessment

Of the 187 library-section target names, 121 were already named in `config/game.toml` when this ran, leaving 66. The alignment proves 0 of those (0%), 0 of which no other agent's file names.

Precision, measured rather than assumed: held out one at a time, the 121 library anchors were re-emitted at a wrong address 0 times (correctly 80 times, the rest held back), and the independent manual results in other agents' files agree with 0 of the 0 emitted names they also give.

Of the 66 names left after this run, 1 have a pick that passes every invariant and is held back only by position or ambiguity (*Strongest leads*), 65 have no pick in their bracket, and the rest have a pick that fails at least one invariant. The automated alignment therefore closes the part of the gap that sits in agreeing brackets with a distinguishing shape; the rest needs a human to read the code, starting from the leads.

Measured against what the other agents found by hand: of this run's 0 names, 0 are in none of their files; with their files merged in as anchors, the alignment emits 0 names beyond them. Held out one at a time, it independently re-derives 80 of the 121 library names known so far. So with the anchors available now, the alignment adds little beyond the manual work; its value is confirmation by an independent method and the ranked leads above.

Why the yield is bounded, from the rejection table:

- **Block moves.** Link order holds inside an object, not across a section, so a name is only placed between anchors that agree with each other. Names whose nearest anchors disagree, or that have an anchor on one side only, cannot be emitted however good their candidate looks.
- **Identical-looking runs.** Runs of setters with the same shape (same ret, length, call count and no distinguishing constant) are told apart only by order; the tool refuses to emit those, by design.
- **Absent or rewritten functions.** A title links only what it calls, and 5233 lacks APIs 5558 has. A name the alignment leaves unmatched has nothing in its bracket with the same ret that scores positively: either it is not in this image (a correct zero), or it moved out of its bracket or was rewritten past what these invariants recognise. The *Others* column is where to look for the latter.
- **Length drift.** 5233 is an older build than 5558; functions rewritten in between fail the length band, and without a distinctive hardware constant they stay unproven.

Each run uses whatever `config/game.toml` holds. Every name merged into it becomes an anchor that narrows the brackets around its neighbours, so rerun the tool after each merge; the held-out-anchor table above is the running check that the rule stays safe as the anchor set grows.
