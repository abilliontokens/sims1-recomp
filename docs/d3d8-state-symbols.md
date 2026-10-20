# D3D8 render-state and texture-stage setters in The Sims (XDK 5233)

Image: `out/game.exe`, the `xbe2pe.py` flat PE of `assets/default.xbe`, with guest addresses 1:1. Section `D3D` runs
from 0x18F680 to 0x1A1DA0. Reference: The Sims: Bustin' Out, `simsbustinout/out/game.exe` (XDK 5558, names applied;
its 194 names are the same as `out/sims5558.exe`'s). A "5558 twin" is the function with the same name there. Every
address below was read from these two images.

**Result.**

- **All 36 target names are proven** and listed in `config/found-d3d8-state.toml`: 30 new ones, plus the 6 anchors
  re-proven at the addresses `config/game.toml` already holds. No target is left unproven.
- **XDK 5233 numbers render states and texture-stage states exactly as XDK 5849 does.**
  - Render states: `DeferredFirst` 92, `ComplexFirst` 136, `Max` 166. Every `gpu::kRs<name>` is this build's index.
  - Texture-stage states: types 0..30 are 5849's own, and the deferred ones are those below 22.
  - So `sdk/xdk/5233/layout.toml` needs **no** `RenderState_*`/`TextureState_*` table. With none,
    `sdk/runtime/xdk/layout.h` falls back to `gpu::kRs*`/`gpu::kTss*`, which is this build's numbering, and
    `kRsMap`/`kTssMap` in `d3d8.cpp` come out as the identity. `D3d8DataLayout`, which owns that file, has been told
    and has recorded it.
- **The found file is not staged.** Fuzion Frenzy's file was staged because the host would have written 5849 indices
  into a 144-entry 3925 array. That hazard does not exist in this build. See [Wiring preconditions](#wiring-preconditions).

## Target list

These are the `[symbols]` keys of `sdk/xdk/5558/signatures.toml` with `sec = "D3D"` whose names start with
`D3DDevice_SetRenderState_` or `D3DDevice_SetTextureState_`, plus the two `NotInline` entry points (`Simple` matches
the first prefix). The file has 36 such keys, every one is a key of `config/game.toml`, and no key with those prefixes
carries another `sec`. "Slot" is the entry of the complex-handler table that points at the function. It equals the
render-state index.

| Name | Address | Identity | Status |
|---|---|---|---|
| D3DDevice_SetRenderStateNotInline | 0x18FCF0 | the bounds and the table dispatch | new |
| D3DDevice_SetRenderState_PSTextureModes | 0x18FC90 | slot 136 | new |
| D3DDevice_SetRenderState_Simple | 0x18FCC0 | NotInline's simple-state callee | new |
| D3DDevice_SetRenderState_VertexBlend | 0x190530 | slot 137 | new |
| D3DDevice_SetRenderState_FogColor | 0x1900A0 | slot 138 | anchor, re-proven |
| D3DDevice_SetRenderState_FillMode | 0x190410 | slot 139 | new |
| D3DDevice_SetRenderState_BackFillMode | 0x190460 | slot 140 | new |
| D3DDevice_SetRenderState_TwoSidedLighting | 0x1904C0 | slot 141 | new |
| D3DDevice_SetRenderState_NormalizeNormals | 0x1901A0 | slot 142 | new |
| D3DDevice_SetRenderState_ZEnable | 0x191180 | slot 143 | new |
| D3DDevice_SetRenderState_StencilEnable | 0x191210 | slot 144 | anchor, re-proven |
| D3DDevice_SetRenderState_StencilFail | 0x1912A0 | slot 145 | anchor, re-proven |
| D3DDevice_SetRenderState_FrontFace | 0x190160 | slot 146 | new |
| D3DDevice_SetRenderState_CullMode | 0x1900F0 | slot 147 | anchor, re-proven |
| D3DDevice_SetRenderState_TextureFactor | 0x1901E0 | slot 148 | new |
| D3DDevice_SetRenderState_LogicOp | 0x1903B0 | slot 150 | new |
| D3DDevice_SetRenderState_EdgeAntiAlias | 0x190020 | slot 151 | new |
| D3DDevice_SetRenderState_MultiSampleAntiAlias | 0x191500 | slot 152 | new |
| D3DDevice_SetRenderState_MultiSampleMask | 0x191580 | slot 153 | new |
| D3DDevice_SetRenderState_MultiSampleMode | 0x191480 | slot 154 | new |
| D3DDevice_SetRenderState_MultiSampleRenderTargetMode | 0x1914C0 | slot 155 | new |
| D3DDevice_SetRenderState_ShadowFunc | 0x190060 | slot 156 | new |
| D3DDevice_SetRenderState_LineWidth | 0x190240 | slot 157 | anchor, re-proven |
| D3DDevice_SetRenderState_SampleAlpha | 0x1915D0 | slot 158 | new |
| D3DDevice_SetRenderState_Dxt1NoiseEnable | 0x1902B0 | slot 159 | new |
| D3DDevice_SetRenderState_YuvEnable | 0x191310 | slot 160 | new |
| D3DDevice_SetRenderState_OcclusionCullEnable | 0x191340 | slot 161 | new |
| D3DDevice_SetRenderState_StencilCullEnable | 0x1913B0 | slot 162 | new |
| D3DDevice_SetRenderState_RopZCmpAlwaysRead | 0x191420 | slot 163 | new |
| D3DDevice_SetRenderState_RopZRead | 0x191440 | slot 164 | new |
| D3DDevice_SetRenderState_DoNotCullUncompressed | 0x191460 | slot 165 | new |
| D3DDevice_SetTextureState_TexCoordIndex | 0x190580 | TSS NotInline, type 1Ch | anchor, re-proven |
| D3DDevice_SetTextureState_BumpEnv | 0x190690 | TSS NotInline, types 16h..1Bh | new |
| D3DDevice_SetTextureState_BorderColor | 0x190700 | TSS NotInline, type 1Dh | new |
| D3DDevice_SetTextureState_ColorKeyColor | 0x190740 | TSS NotInline, type 1Eh | new |
| D3DDevice_SetTextureStageStateNotInline | 0x190780 | TSS dispatch | new |

Slot 149 is `ZBias` (0x190330). It is not a target, because neither the signature set nor `config/game.toml` has the
name. The 30 new names and ZBias are applied in the shared IDA database; the 6 anchors already carried theirs.

## How the shapes were measured

`ret`, `regs`, `len`, `calls` and `k` were measured by a scratch reimplementation of `xbe_symbols`' own
`Image::Extent`, `Image::Trace` and `Image::ExternalTargets`, plus its constant filter
(`sdk/tools/symbols/main.cpp:266-354` and `:395-400`), written over capstone. The scratch script is not part of the
tree. Function bounds came from the recompiler's start list, `generated/game/x86_func_mapping.cpp`, plus the named
symbols.

**Calibration.** The same script measured all 36 5558 twins in the Bustin' Out image. It reproduced every one of the
36 rows of `sdk/xdk/5558/signatures.toml` exactly: `len`, `ret`, `regs`, the number of `calls` and the `k` list.

**Instruction-level comparison.** Every candidate was also disassembled next to its twin.

- 33 of the 36 are instruction-for-instruction identical to their twins: same count, same mnemonics, same operand
  shapes.
- Their only differing operands are of two kinds:
  - **Image addresses.** They map one to one between the builds, and every `D3D_RenderState` or
    `D3D_DeferredTextureState` slot maps to the **same index**.
  - **CDevice displacements**, each listed in that name's section.
- The three exceptions are `MultiSampleMode`, `MultiSampleRenderTargetMode` and `TwoSidedLighting`. Their sections
  explain each one.

## This build's state numbering: XDK 5849's

### 1. SetRenderStateNotInline: the block bounds

The 5233 body is on the left and the 5558 twin on the right, instruction for instruction.

```
5233 0x18FCF0                              5558 0x249910
18FCF0 push esi                            249910 push esi
18FCF1 mov  esi, [esp+8]                   249911 mov  esi, [esp+8]
18FCF5 cmp  esi, 5Ch                       249915 cmp  esi, 5Ch            ; 92 = DeferredFirst
18FCF8 jge  18FD19                         249918 jge  249939
18FCFA mov  ecx, [esi*4+1EE768h]           24991A mov  ecx, [esi*4+2E1FE0h]  ; D3D_SimpleRenderStateEncode
18FD01 push edi                            249921 push edi
18FD02 mov  edi, [esp+10h]                 249922 mov  edi, [esp+10h]
18FD06 mov  edx, edi                       249926 mov  edx, edi
18FD08 call 18FCC0                         249928 call 2498E0              ; SetRenderState_Simple
18FD0D mov  [esi*4+19F770h], edi           24992D mov  [esi*4+2646B0h], edi  ; D3D_RenderState[state]
18FD14 pop edi / pop esi / retn 8          249934 pop edi / pop esi / retn 8
18FD19 cmp  esi, 88h                       249939 cmp  esi, 88h            ; 136 = ComplexFirst
18FD1F jge  18FD3D                         24993F jge  24995D
18FD21 mov  eax, [esi*4+1EE548h]           249941 mov  eax, [esi*4+2E1DB0h]  ; per-state dirty bits
18FD28 or   [19F568h], eax                 249948 or   [2644A8h], eax        ; D3D_DirtyFlags
18FD2E mov  ecx, [esp+0Ch]                 24994E mov  ecx, [esp+0Ch]
18FD32 mov  [esi*4+19F770h], ecx           249952 mov  [esi*4+2646B0h], ecx  ; deferred store: index = state
18FD39 pop esi / retn 8                    249959 pop esi / retn 8
18FD3D mov  edx, [esp+0Ch]                 24995D mov  edx, [esp+0Ch]
18FD41 push edx                            249961 push edx
18FD42 call [esi*4+19D4E0h]                249962 call [esi*4+259BB0h]       ; complex handler table
18FD49 pop esi / retn 8                    249969 pop esi / retn 8
```

The bounds `5Ch`/`88h` are 5849's 92/136, against 3925's `52h`/`74h`. The deferred setter stores the value at
`D3D_RenderState + 4 × state`, with no remapping, so a deferred state's array index is its number.

### 2. The complex-handler table: its order is the numbering

`0x19D4E0 + 4 × state` for states 136..165 (0x19D700..0x19D774) holds 30 function pointers. The next slot, 166 at
0x19D778, holds `3F800000h` (1.0f). That is data, so `Max` = 166. 5558's table at `0x259BB0 + 4 × state` holds its
named functions in the same 30 slots and has data (`C1000000h`) at 166. Every handler stores its argument into its own
slot, `0x19F770 + 4 × slot`. Searched as raw little-endian dwords, each handler's address appears exactly once in the
image, in its own table slot.

| Slot | 5849 name (`gpu::kRs`) | 5233 handler | 5233 store | 5558 handler (named) |
|---|---|---|---|---|
| 136 | PsTextureModes | 0x18FC90 | 0x19F990 | 0x2498B0 PSTextureModes |
| 137 | VertexBlend | 0x190530 | 0x19F994 | 0x24A340 VertexBlend |
| 138 | FogColor | 0x1900A0 | 0x19F998 | 0x249EA0 FogColor |
| 139 | FillMode | 0x190410 | 0x19F99C | 0x24A210 FillMode |
| 140 | BackFillMode | 0x190460 | 0x19F9A0 | 0x24A260 BackFillMode |
| 141 | TwoSidedLighting | 0x1904C0 | 0x19F9A4 | 0x24A2C0 TwoSidedLighting |
| 142 | NormalizeNormals | 0x1901A0 | 0x19F9A8 | 0x249FA0 NormalizeNormals |
| 143 | ZEnable | 0x191180 | 0x19F9AC | 0x24AEC0 ZEnable |
| 144 | StencilEnable | 0x191210 | 0x19F9B0 | 0x24AF50 StencilEnable |
| 145 | StencilFail | 0x1912A0 | 0x19F9B4 | 0x24AFE0 StencilFail |
| 146 | FrontFace | 0x190160 | 0x19F9B8 | 0x249F60 FrontFace |
| 147 | CullMode | 0x1900F0 | 0x19F9BC | 0x249EF0 CullMode |
| 148 | TextureFactor | 0x1901E0 | 0x19F9C0 | 0x249FE0 TextureFactor |
| 149 | ZBias | 0x190330 | 0x19F9C4 | 0x24A130 (unnamed, same body) |
| 150 | LogicOp | 0x1903B0 | 0x19F9C8 | 0x24A1B0 LogicOp |
| 151 | EdgeAntiAlias | 0x190020 | 0x19F9CC | 0x249E20 EdgeAntiAlias |
| 152 | MultiSampleAntiAlias | 0x191500 | 0x19F9D0 | 0x24B220 MultiSampleAntiAlias |
| 153 | MultiSampleMask | 0x191580 | 0x19F9D4 | 0x24B2A0 MultiSampleMask |
| 154 | MultiSampleMode | 0x191480 | 0x19F9D8 | 0x24B1C0 MultiSampleMode |
| 155 | MultiSampleRenderTargetMode | 0x1914C0 | 0x19F9DC | 0x24B1F0 MultiSampleRenderTargetMode |
| 156 | ShadowFunc | 0x190060 | 0x19F9E0 | 0x249E60 ShadowFunc |
| 157 | LineWidth | 0x190240 | 0x19F9E4 | 0x24A040 LineWidth |
| 158 | SampleAlpha | 0x1915D0 | 0x19F9E8 | 0x24B2F0 SampleAlpha |
| 159 | Dxt1NoiseEnable | 0x1902B0 | 0x19F9EC | 0x24A0B0 Dxt1NoiseEnable |
| 160 | YuvEnable | 0x191310 | 0x19F9F0 | 0x24B050 YuvEnable |
| 161 | OcclusionCullEnable | 0x191340 | 0x19F9F4 | 0x24B080 OcclusionCullEnable |
| 162 | StencilCullEnable | 0x1913B0 | 0x19F9F8 | 0x24B0F0 StencilCullEnable |
| 163 | RopZCmpAlwaysRead | 0x191420 | 0x19F9FC | 0x24B160 RopZCmpAlwaysRead |
| 164 | RopZRead | 0x191440 | 0x19FA00 | 0x24B180 RopZRead |
| 165 | DoNotCullUncompressed | 0x191460 | 0x19FA04 | 0x24B1A0 DoNotCullUncompressed |
| 166 | (data `3F800000h`) | — | 0x19FA08 = `D3D_pDevice` | (data `C1000000h`) |

The five render-state anchors the constant matcher found by NV2A token sit in slots 138, 144, 145, 147 and 157. Those
are 5849's FogColor, StencilEnable, StencilFail, CullMode and LineWidth, so they confirm the table independently.
`D3D_RenderState` = 0x19F770 has 166 dwords and ends exactly at `D3D_pDevice` 0x19FA08, just as 5558's 0x2646B0
ends at its 0x264948.

### 3. The deferred block, 92..135

Three things hold the order, each compared with 5558:

- **Dirty-bit table.** `dword_1EE548[state]` for 92..135 is identical, entry by entry, to 5558's `dword_2E1DB0[state]`:
  - fog ×6 `2000h`
  - wrap ×4 `0Fh`
  - Lighting `1200h`
  - SpecularEnable `3000h`
  - light and material ×12 `1000h`
  - point ×2 `100h`
  - PointSpriteEnable `900h`
  - point ×5 `100h`
  - 124..135 `0`

  In .rdata the table sits between the texture-stage dirty table, 22 dwords at 0x1EE660..0x1EE6B4, and the
  simple-encode table, which starts at 0x1EE768 = `0x1EE548 + 136 × 4`. Its used part is therefore exactly the 44
  dwords 92..135.
- **The draw-time dispatcher** 0x1993D0, twin 0x2550B0, routes each dirty bit to one reader. Each reader reads the same
  slots as its 5558 twin:

  ```
  1993D1 mov  ebx, [19F568h]        ; D3D_DirtyFlags
  1993D7 test bh, 1   -> 198050     ; 100h: point reader, reads 116..123     (5558 253AF0, same set)
  1993E9 test bh, 8   -> 19B9A0     ; 800h: point-sprite reader, reads 118   (5558 258F80, same)
  1993F7 test bh, 40h -> 1981C0     ; 4000h: the bit PSTextureModes sets
  199402 test bl, 0Fh -> 198320     ; 0Fh: wrap reader, reads 98 + n         (5558 253FE0, same)
  19940E test bh, 20h -> 198510     ; 2000h: fog reader, reads 92..97, 103    (5558 2541D0, same)
  199419 test bh, 4   -> 1986F0     ; 400h: the bit texture-stage type 21 (TextureTransformFlags) sets
  199424 test bh, 10h -> 198E90     ; 1000h: light update, reads 102, 103, 104, 141 (5558 254B60: 102..104)
  19942F test bh, 2   -> 1991D0     ; 200h: reads 102, 137, 142              (5558 254EB0, same)
  19943B and  ebx, 0C0000070h
  ```

  Other readers agree as well:
  - material-source reader 0x197FB0 reads 105..113 (5558 0x253850).
  - ambient readers 0x198BB0 and 0x198BED read 115 and 114 (5558 0x254860 and 0x254898).
  - constants reader 0x192180 reads 93, 143 and 152 (5558 0x24C300).
  - frame-buffer setup 0x196030 reads 126, 127 and 154 (5558 0x24FB40).

  As a worked example, the fog reader 0x198510 loads `19F8E0h`, `19F8E8h`, `19F8E4h`, `19F8ECh`, `19F8F4h`,
  `19F8F0h` and `19F90Ch`. Those are 92, 94, 93, 95, 97, 96 and 103. 5558's 0x2541D0 loads 92, 94, 93, 95, 97, 96 and
  103 in the same order, from `264820h` onward, and both push `802A0h`, `4029Ch` and `0C09C0h`. Patch, 124 and 125,
  has no reader in either build.
- **Defaults.** `D3D_InitDefaultState`'s value table at 0x19E4E0, for states 57..165, is identical in all 109 entries
  to 5558's 0x2632C8. The values are D3D's documented defaults, each sitting at its 5849 index:

  | Index | State | Default |
  |---|---|---|
  | 95, 96 | FogEnd, FogDensity | 1.0 |
  | 102 | Lighting | 1 |
  | 104 | LocalViewer | 1 |
  | 105 | ColorVertex | 1 |
  | 106 | BackSpecularMaterialSource | 2, D3DMCS_COLOR2 |
  | 110 | SpecularMaterialSource | 2, D3DMCS_COLOR2 |
  | 111 | DiffuseMaterialSource | 1, D3DMCS_COLOR1 |
  | 116 | PointSize | 1.0 |
  | 120 | PointScaleA | 1.0 |
  | 123 | PointSizeMax | 64.0 (`42800000h`) |
  | 125 | PatchSegments | 1.0 |
  | 139, 140 | FillMode, BackFillMode | `1B02h`, D3DFILL_SOLID |
  | 145 | StencilFail | `1E00h`, KEEP |
  | 146 | FrontFace | `900h`, CW |
  | 147 | CullMode | `901h`, CCW |
  | 148 | TextureFactor | `FFFFFFFFh` |
  | 153 | MultiSampleMask | `FFFFFFFFh` |
  | 156 | ShadowFunc | `200h`, NEVER |
  | 157 | LineWidth | 1.0 |
  | 126, 127, 154 | the three states it skips | `DEADBEEFh` |

### 4. The simple block, 0..91

`D3D_SimpleRenderStateEncode` = 0x1EE768 has 92 entries. They are identical one by one to 5558's 0x2E1FE0[0..91]. The
next dwords (`11260h`, `1294D0h`, …) are .text pointers, not encode values. Some entries:

| Index | Encode value | State |
|---|---|---|
| 57 | `40354h` | ZFUNC |
| 64 | `4035Ch` | ZWRITEENABLE |
| 66 | `4037Ch` | SHADEMODE |
| 77 | `40384h` | SlopeScale |
| 78 | `40388h` | DepthOffset |
| 81 | `40338h` | SolidOffsetEnable |
| 82 | `41D78h` | DepthClipControl |
| 83 | `4147Ch` | StippleEnable |

5849's 82 and 83 are present here, and 3925 lacks both. Every entry is `(1 << 18) | method` with the method below
`2000h`, so the host's `R32(kSimpleEncode + rs*4) & 0x1FFC` decode applies.

### 5. D3D_InitDefaultState 0x195E30

D3d8CoreSymbols emits this name. It is cited here only as evidence.

```
195E40..195E4F  SetTransform(0..9, identity 19D778h)          ; 5558: 0x24F950..0x24F95F, SetTransform 0x244FE0
195E51 mov  edi, 39h          ; first state 57
195E56 mov  ebx, 19E4E0h      ; default values
195E60 cmp  esi, 184h  -> skip  ; byte offset (154-57)*4 : MultiSampleMode       (5558: cmp esi, 9Ah)
195E68 cmp  esi, 114h  -> skip  ; (126-57)*4 : SwapFilter                         (5558: cmp esi, 7Eh)
195E70 cmp  esi, 118h  -> skip  ; (127-57)*4 : PresentationInterval               (5558: cmp esi, 7Fh)
195E7C call SetRenderStateNotInline(edi, [ebx])
195E88 cmp  esi, 1B4h  -> loop  ; (166-57)*4 : states 57..165                      (5558: cmp esi, 0A6h)
195E90 mov  esi, [ebp+15CCh]  ; auto depth surface (5558 [ebx+1A20h])
195E9E push 8Fh               ; 143 = ZEnable                                      (5558: push 8Fh)
195EA3 call SetRenderStateNotInline
195EB2..195EC5  for stage 0..3, type 0..31: SetTextureStageStateNotInline(stage, type, byte_19E4BC[type])
195EC8..195ECB  SetTextureStageStateNotInline(stage, 1Ch, stage)          ; TexCoordIndex
195ED3          D3DDevice_SetTexture(stage, 0)                            ; 0x1936F0, already named
195EDE..195EE4  SetTextureStageStateNotInline(0, 0Ch, 4)                  ; COLOROP = MODULATE   (5558 0x24F9DF)
195EE9..195EEF  SetTextureStageStateNotInline(0, 10h, 2)                  ; ALPHAOP = SELECTARG1 (5558 0x24F9EA)
195EF8          D3DDevice_SetScreenSpaceOffset(0, 0)                      ; 0x193C00 (5558 0x2480F0)
```

The 5233 compiler counts by byte offset rather than by state, but the swept range, 57..165, and the three skipped
states, 126, 127 and 154, are 5558's exactly. 3925 swept 57..143, skipped only 134, and passed `7Bh` for ZEnable.

### 6. Texture-stage states

`D3DDevice_SetTextureStageStateNotInline` 0x190780 is instruction-for-instruction identical to 5558's 0x24A5A0:

```
190780 mov  eax, [esp+8]          ; type
190784 cmp  eax, 0Ch
190787 jge  1907B7
19078D mov  edx, 1 / shl edx, cl  ; type < 12 (AddressU..AlphaKill): D3D_DirtyFlags |= 1 << stage
19079B shl  ecx, 5 / add ecx, eax
1907AC mov  [ecx*4+19F570h], eax  ; D3D_DeferredTextureState[stage*32 + type]
1907B4 retn 0Ch
1907B7 jne  1907EC                ; type == 12, ColorOp:
1907C3 cmp  eax, 19h / sbb ecx, ecx / and ecx, 0FFFFBFF1h / add ecx, 480Fh   ; dirty 800h or 480Fh by value
1907E0 shl  edx, 7
1907E3 mov  [edx+19F5A0h], eax    ; [stage][12]
1907EC cmp  eax, 16h
1907EF jge  190815                ; 13..21: dirty |= dword_1EE660[type], store [stage*32 + type]
1907F1 mov  ecx, [eax*4+1EE660h]
19080B mov  [edx*4+19F570h], eax
190815 cmp  eax, 1Ch -> call 190580    ; TexCoordIndex
19082C cmp  eax, 1Dh -> call 190700    ; BorderColor
190843 cmp  eax, 1Eh -> call 190740    ; ColorKeyColor
19085A cmp  eax, 1Bh / jg return
190867 jmp  190690                     ; 16h..1Bh: BumpEnv
```

These constants are 5849's own:

- `0Ch` is ColorOp, the 5849-only case the 3925 build lacked.
- `16h` = 22 is `kTssDeferredMax`.
- `1Ch`, `1Dh` and `1Eh` are TexCoordIndex, BorderColor and ColorKeyColor.
- 22..27 are the BumpEnv types.

The 3925 build has no `0Ch` case and rotates 0..21 by 10. This build does not rotate. The per-type tables confirm it:

| Table | 5233 | 5558 twin | Contents |
|---|---|---|---|
| Dirty, by type 0..21 | 0x1EE660 | 0x2E1EC8 | identical: `0Fh` ×12, `800h` ×9, `400h` |
| Defaults, by type 0..31 | byte_19E4BC | byte_2632A4 | identical: 1 1 1 1 1 0 0 0 1 0 0 0 1 1 2 1 1 1 2 1 1 0, then zeros |

In 5849 order those defaults are D3D's: ADDRESSU/V/W = WRAP, MAG/MIN = POINT, MIP = NONE, MAXANISOTROPY = 1,
COLOROP = DISABLE, COLORARG1 = TEXTURE, COLORARG2 = CURRENT, ALPHAOP = DISABLE, ALPHAARG1 = TEXTURE, and so on. The
stage's array index is `stage × 32 + type`, from `shl ecx, 5; add ecx, eax` here, `shl esi, 5` in BumpEnv, and
`shl ecx, 7` in BorderColor, ColorKeyColor and TexCoordIndex. That is `TextureState_Stage` = 32. The setters for types
28, 29 and 30 store `[stage][28]`, `[stage][29]` and `[stage][30]`, at 0x19F5E0, 0x19F5E4 and 0x19F5E8 + 128·stage.

### 7. The title's own inlined code agrees

The game was compiled against these 5233 headers, and it writes deferred states directly:

```
15526F or   dword ptr [19F568h], 1200h   ; Lighting's dirty bits (dword_1EE548[102])
155280 mov  dword ptr [19F908h], 0       ; D3D_RenderState[102] = LIGHTING FALSE  (5849 kRsLighting = 102)
1552A6 or   ecx, 3                       ; D3D_DirtyFlags |= (1<<0)|(1<<1): types below 12, stages 0 and 1
1552AE mov  [19F57Ch], ebx               ; D3D_DeferredTextureState[0][3]  MAGFILTER
1552B4 mov  [19F580h], ebx               ;                          [0][4]  MINFILTER
1552BA mov  [19F5FCh], ebx               ;                          [1][3]
1552C6 mov  [19F600h], ebx               ;                          [1][4]
```

Under the 3925 numbering, LIGHTING would be 92 and MAG/MINFILTER 13/14. The same function sets ZWRITEENABLE inline
with `mov [19F870h], 1` (index 64) and SHADEMODE with `mov ecx, 4037Ch` and `call 0x18FCC0`. The title calls
`Simple` directly from 43 sites.

### 8. Against 3925 and against `gpu::kRs*`/`gpu::kTss*`

| Quantity | 3925 (`sdk/xdk/3925/layout.toml`) | 5233 (this image) | 5849 (`sdk/runtime/gpu/state.h`) |
|---|---|---|---|
| RenderState_DeferredFirst | 82 | **92** | 92 |
| RenderState_ComplexFirst | 116 | **136** | 136 |
| RenderState_Max | 144 | **166** | 166 |
| simple 82 DepthClipControl, 83 StippleEnable | absent | **present** | present |
| SwapFilter, PresentationInterval | -1 | **126, 127** | 126, 127 |
| MultiSampleMode, MultiSampleRenderTargetMode | -1 (slot 134 is MULTISAMPLETYPE) | **154, 155** | 154, 155 |
| SampleAlpha | -1 | **158** | 158 |
| ShadowFunc … DoNotCullUncompressed | 135 … 143 | **156 … 165** | 156 … 165 |
| TextureState_DeferredMax | 22 | **22** | 22 (`kTssDeferredMax`) |
| texture-stage types 0..21 | rotated: (5849 + 10) mod 22 | **identity** | identity |
| texture-stage types 22..30 | as 5849 | **as 5849** | — |

Every `gpu::kRs<name>`, by name:

| state.h name | 5849 | **5233** | 3925 | 5233 evidence | Default (0x19E4E0) |
|---|---|---|---|---|---|
| FogEnable | 92 | **92** | 82 | fog reader 0x198510 (5558 0x2541D0); dirty 0x2000 | 0x0 |
| FogTableMode | 93 | **93** | 83 | fog reader 0x198510; constants reader 0x192180 (5558 0x24C300); dirty 0x2000 | 0x0 |
| FogStart | 94 | **94** | 84 | fog reader 0x198510; dirty 0x2000 | 0x0 |
| FogEnd | 95 | **95** | 85 | fog reader 0x198510; dirty 0x2000 | 1.0 |
| FogDensity | 96 | **96** | 86 | fog reader 0x198510; dirty 0x2000 | 1.0 |
| RangeFogEnable | 97 | **97** | 87 | fog reader 0x198510; dirty 0x2000 | 0x0 |
| Wrap0 | 98 | **98** | 88 | wrap reader 0x198320 reads 98+n (5558 0x253FE0); dirty 0xF | 0x0 |
| Wrap1 | 99 | **99** | 89 | wrap reader; dirty 0xF | 0x0 |
| Wrap2 | 100 | **100** | 90 | wrap reader; dirty 0xF | 0x0 |
| Wrap3 | 101 | **101** | 91 | wrap reader; dirty 0xF | 0x0 |
| Lighting | 102 | **102** | 92 | readers 0x198E90, 0x1991D0; the title writes it inline at 0x155280; dirty 0x1200 | 0x1 |
| SpecularEnable | 103 | **103** | 93 | fog reader 0x198510 and light update 0x198E90; dirty 0x3000 | 0x0 |
| LocalViewer | 104 | **104** | 94 | light update 0x198E90 (5558 0x254B60); dirty 0x1000 | 0x1 |
| ColorVertex | 105 | **105** | 95 | material-source reader 0x197FB0 (5558 0x253850); dirty 0x1000 | 0x1 |
| BackSpecularMaterialSource | 106 | **106** | 96 | material-source reader; dirty 0x1000 | 0x2 |
| BackDiffuseMaterialSource | 107 | **107** | 97 | material-source reader; dirty 0x1000 | 0x1 |
| BackAmbientMaterialSource | 108 | **108** | 98 | material-source reader; dirty 0x1000 | 0x0 |
| BackEmissiveMaterialSource | 109 | **109** | 99 | material-source reader; dirty 0x1000 | 0x0 |
| SpecularMaterialSource | 110 | **110** | 100 | material-source reader; dirty 0x1000 | 0x2 |
| DiffuseMaterialSource | 111 | **111** | 101 | material-source reader; dirty 0x1000 | 0x1 |
| AmbientMaterialSource | 112 | **112** | 102 | material-source reader; dirty 0x1000 | 0x0 |
| EmissiveMaterialSource | 113 | **113** | 103 | material-source reader; dirty 0x1000 | 0x0 |
| BackAmbient | 114 | **114** | 104 | ambient reader 0x198BED (5558 0x254898); dirty 0x1000 | 0x0 |
| Ambient | 115 | **115** | 105 | ambient reader 0x198BB0 (5558 0x254860); dirty 0x1000 | 0x0 |
| PointSize | 116 | **116** | 106 | point reader 0x198050 (5558 0x253AF0); dirty 0x100 | 1.0 |
| PointSizeMin | 117 | **117** | 107 | point reader; dirty 0x100 | 0x0 |
| PointSpriteEnable | 118 | **118** | 108 | point readers 0x198050 and 0x19B9A0 (5558 0x258F80); dirty 0x900 | 0x0 |
| PointScaleEnable | 119 | **119** | 109 | point reader; dirty 0x100 | 0x0 |
| PointScaleA | 120 | **120** | 110 | point reader; dirty 0x100 | 1.0 |
| PointScaleB | 121 | **121** | 111 | point reader; dirty 0x100 | 0x0 |
| PointScaleC | 122 | **122** | 112 | point reader; dirty 0x100 | 0x0 |
| PointSizeMax | 123 | **123** | 113 | point reader; dirty 0x100 | 64.0 |
| PatchEdgeStyle | 124 | **124** | 114 | place in the block; no reader and dirty 0 in both builds | 0x0 |
| PatchSegments | 125 | **125** | 115 | place in the block; no reader and dirty 0 in both builds | 1.0 |
| SwapFilter | 126 | **126** | -1 | frame-buffer setup 0x196030 (5558 0x24FB40); InitDefaultState skips it | 0xDEADBEEF |
| PresentationInterval | 127 | **127** | -1 | 0x196030, and 0x1945C0, 0x1947A0, 0x19AF60, 0x19B390, as 5558's 0x2492B0, 0x2494A0, 0x255460, 0x2558F0; InitDefaultState skips it | 0xDEADBEEF |
| (128..135 unused) | 128..135 | 128..135 | — | dirty 0, defaults 0, no reader | 0x0 |
| PsTextureModes | 136 | **136** | 116 | table slot → 0x18FC90, stores 0x19F990 | 0x0 |
| VertexBlend | 137 | **137** | 117 | table slot → 0x190530, stores 0x19F994 | 0x0 |
| FogColor | 138 | **138** | 118 | table slot → 0x1900A0, stores 0x19F998 | 0x0 |
| FillMode | 139 | **139** | 119 | table slot → 0x190410, stores 0x19F99C | 0x1B02 |
| BackFillMode | 140 | **140** | 120 | table slot → 0x190460, stores 0x19F9A0 | 0x1B02 |
| TwoSidedLighting | 141 | **141** | 121 | table slot → 0x1904C0, stores 0x19F9A4 | 0x0 |
| NormalizeNormals | 142 | **142** | 122 | table slot → 0x1901A0, stores 0x19F9A8 | 0x0 |
| ZEnable | 143 | **143** | 123 | table slot → 0x191180, stores 0x19F9AC; InitDefaultState `push 8Fh` | 0x2 |
| StencilEnable | 144 | **144** | 124 | table slot → 0x191210, stores 0x19F9B0 | 0x0 |
| StencilFail | 145 | **145** | 125 | table slot → 0x1912A0, stores 0x19F9B4 | 0x1E00 |
| FrontFace | 146 | **146** | 126 | table slot → 0x190160, stores 0x19F9B8 | 0x900 |
| CullMode | 147 | **147** | 127 | table slot → 0x1900F0, stores 0x19F9BC | 0x901 |
| TextureFactor | 148 | **148** | 128 | table slot → 0x1901E0, stores 0x19F9C0 | 0xFFFFFFFF |
| ZBias | 149 | **149** | 129 | table slot → 0x190330, stores 0x19F9C4 | 0x0 |
| LogicOp | 150 | **150** | 130 | table slot → 0x1903B0, stores 0x19F9C8 | 0x0 |
| EdgeAntiAlias | 151 | **151** | 131 | table slot → 0x190020, stores 0x19F9CC | 0x0 |
| MultiSampleAntiAlias | 152 | **152** | 132 | table slot → 0x191500, stores 0x19F9D0 | 0x1 |
| MultiSampleMask | 153 | **153** | 133 | table slot → 0x191580, stores 0x19F9D4 | 0xFFFFFFFF |
| MultiSampleMode | 154 | **154** | -1 | table slot → 0x191480, stores 0x19F9D8; InitDefaultState skips it | 0xDEADBEEF |
| MultiSampleRenderTargetMode | 155 | **155** | -1 | table slot → 0x1914C0, stores 0x19F9DC | 0x0 |
| ShadowFunc | 156 | **156** | 135 | table slot → 0x190060, stores 0x19F9E0 | 0x200 |
| LineWidth | 157 | **157** | 136 | table slot → 0x190240, stores 0x19F9E4 | 1.0 |
| SampleAlpha | 158 | **158** | -1 | table slot → 0x1915D0, stores 0x19F9E8 | 0x0 |
| Dxt1NoiseEnable | 159 | **159** | 137 | table slot → 0x1902B0, stores 0x19F9EC | 0x1 |
| YuvEnable | 160 | **160** | 138 | table slot → 0x191310, stores 0x19F9F0 | 0x0 |
| OcclusionCullEnable | 161 | **161** | 139 | table slot → 0x191340, stores 0x19F9F4 | 0x1 |
| StencilCullEnable | 162 | **162** | 140 | table slot → 0x1913B0, stores 0x19F9F8 | 0x1 |
| RopZCmpAlwaysRead | 163 | **163** | 141 | table slot → 0x191420, stores 0x19F9FC | 0x0 |
| RopZRead | 164 | **164** | 142 | table slot → 0x191440, stores 0x19FA00 | 0x0 |
| DoNotCullUncompressed | 165 | **165** | 143 | table slot → 0x191460, stores 0x19FA04 | 0x0 |

Every `gpu::kTss<name>` is also 5849's: AddressU 0 … TextureTransformFlags 21, BumpEnvMat00..BumpEnvLOffset 22..27,
TexCoordIndex 28, BorderColor 29, ColorKeyColor 30, all by section 6.

**Conclusion.** XDK 5233 uses 5849's numbering for both state families. `sdk/xdk/5233/layout.toml` needs no
`RenderState_*`/`TextureState_*` table: one would only re-state the default that `layout.h` already applies. Nothing
from this analysis goes into that file beyond `TextureState_Stage = 32`. Its provisional copy already carries that
value, and section 6 proves it for this build.

## Wiring preconditions

Each emitted name has the ABI of its SDK HLE declaration in `sdk/runtime/xdk/d3d8.cpp`:

| Host declaration | 5233 shape |
|---|---|
| `COMPLEX_STATE` → `HLE_STDCALL(…, 1)` | `retn 4` |
| FrontFace | no `retn`; it tail-jumps into CullMode, which pops the one argument |
| `HLE_FASTCALL(D3DDevice_SetRenderState_Simple, 0)` | regs [ecx, edx], `retn` |
| `HLE_STDCALL(D3DDevice_SetRenderStateNotInline, 2)` | `retn 8` |
| `HLE_STDCALL(D3DDevice_SetTextureStageStateNotInline, 3)` | `retn 0Ch` |
| TexCoordIndex, BorderColor, ColorKeyColor (2 each) | `retn 8` |
| BumpEnv (3) | `retn 0Ch` |

What the host bodies read from the build:

| Host bodies | They need | Status in this build |
|---|---|---|
| the 29 complex setters (`COMPLEX_STATE` → `SetComplex`) | `D3D_RenderState` and the render-state numbering | numbering: 5849's, no table needed. `D3D_RenderState` is 0x19F770 by sections 1-2; D3d8DataLayout owns the `[data]` entry |
| `SetRenderStateNotInline` | `D3D_SimpleRenderStateEncode`, `D3D_RenderState`, the numbering | as above; encode table 0x1EE768 |
| `SetTextureStageStateNotInline`, `SetTextureState_TexCoordIndex` | `D3D_DeferredTextureState`, `TextureState_Stage`, the numbering | numbering: 5849's. 0x19F570; stage = 32 dwords |
| `SetRenderState_Simple`, `SetTextureState_BumpEnv`, `_BorderColor`, `_ColorKeyColor` | nothing from the build: method/value pairs and types 22..30 | — |

None of the 36 host bodies reads a CDevice offset. They do need three data symbols and one layout key:
`D3D_RenderState`, `D3D_DeferredTextureState`, `D3D_SimpleRenderStateEncode` and `TextureState_Stage`. Every one of
them is in the `XDK_REQUIRE` list of the host `Direct3D_CreateDevice` (`d3d8.cpp:660-668`). A run that creates its
device through the host therefore stops there, naming each missing value, until they are supplied, and these setters
only run on a created device. That loud failure is what the staging rule protects, and these names do not bypass it.
The six anchors already in `config/game.toml` are in the same position today. This file therefore declares no
`staged`.

## Evidence per name

"Reference" is the 5558 row of `sdk/xdk/5558/signatures.toml`, which the 5558 twin reproduces exactly. "Measured" is
the same quantities at the 5233 candidate. Each complex handler has exactly one data reference in the image: its own
slot in the table at `0x19D4E0 + 4 × slot`. The four texture-stage leaves have none and are reached only from
SetTextureStageStateNotInline. `Simple` and the two `NotInline` entry points are reached by direct calls. `pDevice`
below is `D3D_pDevice` 0x19FA08, read with `mov esi, [19FA08h]`.

### D3DDevice_SetRenderStateNotInline = 0x18FCF0

- **Reference:** len 0x5D, ret 8, regs [], calls 1, k [0x5C, 0x88]
- **Measured:** len 0x5D, ret 8, regs [], calls 1, k [0x5C, 0x88]
- **Invariants:** ret, regs and calls (1/1) hold. k and len are equal.
- **Body:** the listing in section 1, identical to the twin 0x249910 instruction for instruction.
- **Callers:** ZBias 0x190369..0x190393 (states `4Dh`..`51h`, 77..81, whose encode entries are SlopeScale `40384h`,
  DepthOffset `40388h`, …, SolidOffsetEnable `40338h`); the render-target setup 0x19114D (re-applies LineWidth, 157);
  0x194118 in 0x1940E0 and 0x194264, 0x1942D9 and 0x1942F0 in 0x194200 (twins 0x248D90 and 0x248EB0, unnamed there);
  D3D_InitDefaultState 0x195E7C and 0x195EA3. D3d8CoreSymbols named the same address from InitDefaultState's call
  sites independently.
- **Confidence:** high.

### D3DDevice_SetRenderState_PSTextureModes = 0x18FC90

- **Reference:** len 0x22, ret 4, regs [], calls 0, k [0x790, 0x4000]
- **Measured:** len 0x22, ret 4, regs [], calls 0, k [0x378, 0x4000]
- **Invariants:** ret, regs and calls (0/0) hold. len is equal. No k is at or above 0x10000.
- **Slot 136** (0x19D700).
- **Body:** `mov eax,[esp+4]; mov ecx,[pDevice]; mov [ecx+378h],eax; or [19F568h],4000h; mov [19F990h],eax; retn 4`.
  0x19F990 is RS[136].
- **Twin** 0x2498B0: the same six instructions with `[ecx+790h]`, `or [2644A8h],4000h`, `mov [2648D0h],eax`
  (RS[136]). The only differing operand is the CDevice field, 0x378 against 0x790.
- **Readers:** the dispatcher's `4000h` bit (0x1993F7) calls 0x1981C0, and SetPixelShader 0x195510 reads RS[136] and
  RS[148], as 5558's 0x24E740 does.
- **Confidence:** high.

### D3DDevice_SetRenderState_Simple = 0x18FCC0

- **Reference:** len 0x27, ret 0, regs [ecx, edx], calls 1, k []
- **Measured:** len 0x27, ret 0, regs [ecx, edx], calls 1, k []
- **Invariants:** ret, regs and calls (1/1) hold. len is equal.
- **Body:**
  ```
  18FCC0 mov  eax, [19FA10h]      ; D3D_Device.Push
  18FCC5 add  eax, 8
  18FCC8 cmp  eax, [19FA14h]      ; D3D_Device.Threshold
  18FCCE jae  18FCDC
  18FCD0 mov  [19FA10h], eax
  18FCD5 mov  [eax-8], ecx        ; method token
  18FCD8 mov  [eax-4], edx        ; value
  18FCDB retn
  18FCDC push edx / push ecx / call 192C20 (MakeSpace) / pop ecx / pop edx / jmp 18FCC0
  ```
  It is identical to the twin 0x2498E0, including the length. The 3925 build needed an extra `mov ecx`.
- **Uniqueness:** inside `D3D`, the only other functions that move `D3D_Device.Push` by absolute address are the
  vertex-shader-constant pushers at 0x191C61..0x191E20. Those push `41EA4h` headers, not a method/value pair.
- **Callers:** SetRenderStateNotInline 0x18FD08, with `ecx = D3D_SimpleRenderStateEncode[state]` and `edx = value`,
  plus 43 call sites in the title's own code, its inlined SetRenderState. For example 0x15527B is
  `mov ecx,4037Ch` (SHADEMODE) followed by `call 0x18FCC0`.
- **Confidence:** high.

### D3DDevice_SetRenderState_VertexBlend = 0x190530

- **Reference:** len 0x41, ret 4, regs [], calls 1, k [0x200, 0x40328]
- **Measured:** len 0x41, ret 4, regs [], calls 1, k [0x200, 0x40328]
- **Invariants:** ret, regs and calls (1/1) hold. k and len are equal.
- **Slot 137.**
- **Body:** `mov edx,[19F568h]; or edx,200h; mov [19F568h],edx` (dirty bit `200h`), then token `40328h` (skin mode)
  with the value, then `mov [19F994h],ecx` (RS[137]), `retn 4`.
- **Twin** 0x24A340 is identical. `40328h` occurs nowhere else in the image.
- **Confidence:** high.

### D3DDevice_SetRenderState_FogColor = 0x1900A0 (anchor)

- **Reference:** len 0x4D, ret 4, regs [], calls 1, k [0xFF, 0x402A8, 0xFF00FF00]
- **Measured:** len 0x4D, ret 4, regs [], calls 1, k [0xFF, 0x402A8, 0xFF00FF00]
- **Invariants:** ret, regs and calls (1/1) hold. k and len are equal.
- **Slot 138.**
- **Body:** token `402A8h` with the red/blue swap (`and edi,0FFh; shl edi,10h`, `movzx edx,byte [esp+0Eh]`,
  `and edi,0FF00FF00h`), then `mov [19F998h],ecx` (RS[138]), `retn 4`.
- **Twin** 0x249EA0 is identical. This re-proves the matcher's address.
- **Confidence:** high.

### D3DDevice_SetRenderState_FillMode = 0x190410

- **Reference:** len 0x44, ret 4, regs [], calls 1, k [0x8038C]
- **Measured:** len 0x44, ret 4, regs [], calls 1, k [0x8038C]
- **Invariants:** ret, regs and calls (1/1) hold. k and len are equal.
- **Slot 139.**
- **Body:** token `8038Ch` with front = argument and back = (RS[141] TwoSidedLighting ? RS[140] BackFillMode :
  argument), read from `[19F9A4h]` and `[19F9A0h]`, then `mov [19F99Ch],ecx` (RS[139]), `retn 4`.
- **Twin** 0x24A210 is identical. The title calls it directly twice.
- **Separation from the other two `8038Ch` setters:** the slot the argument is stored to, 139, 140 or 141, and the
  polygon-mode formula. Both match the twins.
- **Confidence:** high.

### D3DDevice_SetRenderState_BackFillMode = 0x190460

- **Reference:** len 0x51, ret 4, regs [], calls 1, k [0x8038C]
- **Measured:** len 0x51, ret 4, regs [], calls 1, k [0x8038C]
- **Invariants:** ret, regs and calls (1/1) hold. k and len are equal.
- **Slot 140.**
- **Body:** it stores the argument first, `mov [19F9A0h],eax` (RS[140]). It then pushes `8038Ch` with
  front = RS[139] and back = (RS[141] ? RS[140] : RS[139]), and writes RS[139] back unchanged. `retn 4`.
- **Twin** 0x24A260 is identical.
- **Confidence:** high.

### D3DDevice_SetRenderState_TwoSidedLighting = 0x1904C0

- **Reference:** len 0x80, ret 4, regs [], calls 2, k [0x9000, 0x417C4, 0x8038C]
- **Measured:** len 0x63, ret 4, regs [], calls 1, k [0x1000, 0x8038C]
- **Invariants:**
  - ret and regs hold.
  - calls is 1 against 2, within ±1.
  - Length is 29 bytes (23%) short, outside the corroboration band. The reason is below.
  - k lacks `417C4h`.
- **Slot 141.** This is the only handler in the table at 141, and the handler stores its argument to RS[141].
- **Body:**
  ```
  1904C0 mov  edx, [19F568h]
  1904D1 or   edx, 1000h
  1904D7 mov  [19F568h], edx        ; D3D_DirtyFlags |= 1000h, unconditionally
  1904DD mov  [19F9A4h], eax        ; RS[141]
  1904E8 mov  edi, [19F99Ch]        ; FillMode
  1904F5 mov  ecx, [19F9A4h] / test ecx, ecx / mov ecx, [19F9A0h] / jne / mov ecx, edi
  190507 mov  [eax], 8038Ch / [eax+4] = edi / [eax+8] = ecx   ; the same re-emit as BackFillMode
  190518 mov  [19F99Ch], edi
  190520 retn 4
  ```
- **Twin** 0x24A2C0 additionally pushes the two-sided-light enable `417C4h` with the value inline, and executes
  `or [2644A8h],9000h` only when the value is non-zero. It reserves push space twice; the second MakeSpace call is
  its second `calls` entry.
- **Where 5233 emits `417C4h`:** in the lazy light update 0x198E90, the only user of the token in this image. It
  loads RS[141] (`mov eax,[19F9A4h]` at 0x198F2F) and pushes `mov [edx+10h],417C4h` (0x198F34), and does the same on a
  second path (0x1991AC/0x1991B2). The draw-time dispatcher calls that function for exactly the bit this setter sets
  (0x199424 `test bh,10h` → `call 198E90`). This build therefore defers the push that 5558 makes inline. The 3925 build
  does the same.
- **Host consequence:** none. The host body stores RS[141] and the renderer reads it.
- **Confidence:** high, from the slot, the store index and the shared `8038Ch` re-emit, despite the length.

### D3DDevice_SetRenderState_NormalizeNormals = 0x1901A0

- **Reference:** len 0x39, ret 4, regs [], calls 1, k [0x200, 0x403A4]
- **Measured:** len 0x39, ret 4, regs [], calls 1, k [0x200, 0x403A4]
- **Invariants:** ret, regs and calls (1/1) hold. k and len are equal.
- **Slot 142.**
- **Body:** token `403A4h` with the value, `or [19F568h],200h`, `mov [19F9A8h],ecx` (RS[142]), `retn 4`. The `200h`
  bit drives 0x1991D0, which reads 102, 137 and 142.
- **Twin** 0x249FA0 is identical. `403A4h` occurs nowhere else.
- **Confidence:** high.

### D3DDevice_SetRenderState_ZEnable = 0x191180

- **Reference:** len 0x8F, ret 4, regs [], calls 6, k [0x1A08, 0x4030C, 0x41D78]
- **Measured:** len 0x8F, ret 4, regs [], calls 6, k [0x15B8, 0x4030C, 0x41D78]
- **Invariants:** ret, regs and calls (6/6) hold. len is equal, and so is every k at or above 0x10000.
- **Slot 143.**
- **Body:**
  - token `4030Ch` with (argument && `[esi+15B8h]`), the depth surface;
  - token `41D78h` with RS[82], `mov ecx,[19F8B8h]`: DepthClipControl, the simple state 5849 numbers 82;
  - `mov [19F9ACh],edx` (RS[143]);
  - when the old or the new value is 2 (`cmp eax,2` / `cmp edx,2`): 0x18FE80, the constants reader 0x192180, the
    control0 builder 0x190AB0 and the viewport push 0x1908C0;
  - `retn 4`.
- **Twin** 0x24AEC0 is identical except for the depth-surface offset, 0x15B8 against 0x1A08.
- **Default state:** InitDefaultState passes `8Fh` = 143 for it, as 5558 does. The title calls it directly three
  times.
- **Confidence:** high.

### D3DDevice_SetRenderState_StencilEnable = 0x191210 (anchor)

- **Reference:** len 0x84, ret 4, regs [], calls 1, k [0x1A08, 0x1E00, 0x4032C, 0x41D84]
- **Measured:** len 0x84, ret 4, regs [], calls 1, k [0x15B8, 0x1E00, 0x4032C, 0x41D84]
- **Invariants:** ret, regs and calls (1/1) hold. len is equal, and so is every k at or above 0x10000.
- **Slot 144.**
- **Body:**
  - token `41D84h` with `(RS[162] ? 2 : 0) | (RS[161] && (!RS[144] || RS[145] == 1E00h) ? 1 : 0)`;
  - token `4032Ch` with (argument && `[esi+15B8h]`);
  - `mov [19F9B0h],edx` (RS[144]);
  - `retn 4`.
- **Twin** 0x24AF50 is identical except for the depth-surface offset. This re-proves the matcher's address.
- **Confidence:** high.

### D3DDevice_SetRenderState_StencilFail = 0x1912A0 (anchor)

- **Reference:** len 0x6D, ret 4, regs [], calls 1, k [0x1E00, 0x40370, 0x41D84]
- **Measured:** len 0x6D, ret 4, regs [], calls 1, k [0x1E00, 0x40370, 0x41D84]
- **Invariants:** ret, regs and calls (1/1) hold. k and len are equal.
- **Slot 145.**
- **Body:** `41D84h` with the occlusion value above, then `40370h` with the argument, then `mov [19F9B4h],ecx`
  (RS[145]), `retn 4`.
- **Twin** 0x24AFE0 is identical. `40370h` occurs nowhere else. This re-proves the matcher's address.
- **Confidence:** high.

### D3DDevice_SetRenderState_FrontFace = 0x190160

- **Reference:** len 0x3A, ret none (it leaves by `jmp`), regs [], calls 2, k [0x403A0]
- **Measured:** len 0x3A, ret none (it leaves by `jmp`), regs [], calls 2, k [0x403A0]
- **Invariants:** ret, regs and calls (2/2) hold. k and len are equal.
- **Slot 146.**
- **Body:** token `403A0h` with the value, then `mov [19F9B8h],ecx` (RS[146]). It then loads `mov eax,[19F9BCh]`
  (CullMode, RS[147]), stores it over its own argument with `mov [esp+4],eax`, and leaves through
  `jmp 0x1900F0` (CullMode). CullMode's `retn 4` balances the stack, which is why `HLE_STDCALL(…, 1)` is right.
- **Twin** 0x249F60 is identical, with the same tail `jmp` into its CullMode. `403A0h` occurs nowhere else.
- **Confidence:** high.

### D3DDevice_SetRenderState_CullMode = 0x1900F0 (anchor)

- **Reference:** len 0x68, ret 4, regs [], calls 1, k [0x404, 0x40308, 0x4039C]
- **Measured:** len 0x68, ret 4, regs [], calls 1, k [0x404, 0x40308, 0x4039C]
- **Invariants:** ret, regs and calls (1/1) hold. k and len are equal.
- **Slot 147.**
- **Body:** token `40308h`. A zero argument pushes 0. Otherwise it pushes 1, then `4039Ch` with
  `404h + (cull != RS[146])` (`mov edi,[19F9B8h]`; `cmp ecx,edi`; `setne dl`; `add edx,404h`). Both paths store
  `[19F9BCh]` (RS[147]) and end in `retn 4`.
- **Twin** 0x249EF0 is identical.
- **Callers:** FrontFace's tail `jmp` (0x190195) and 4 call sites in the title. This re-proves the matcher's address.
- **Confidence:** high.

### D3DDevice_SetRenderState_TextureFactor = 0x1901E0

- **Reference:** len 0x51, ret 4, regs [], calls 1, k [0x784]
- **Measured:** len 0x51, ret 4, regs [], calls 1, k [0x36C]
- **Invariants:** ret, regs and calls (1/1) hold. len is equal. No k is at or above 0x10000: `400A60h` is filtered as
  an address-range value in both builds.
- **Slot 148.**
- **Body:** it tests `[esi+36Ch]`, the current pixel shader. If one is set, it only stores. Otherwise it pushes
  `400A60h` followed by 16 copies of the value (`mov edx,10h` … `dec edx; jne`). Both paths store `[19F9C0h]`
  (RS[148]) and end in `retn 4`.
- **Twin** 0x249FE0 is identical except for the pixel-shader field, 0x36C against 0x784.
- **Callers:** SetPixelShader 0x195510 calls it at 0x19555F, as 5558's 0x24E740 does. `400A60h` occurs nowhere else.
- **Confidence:** high.

### D3DDevice_SetRenderState_LogicOp = 0x1903B0

- **Reference:** len 0x52, ret 4, regs [], calls 1, k [0x417BC, 0x817BC]
- **Measured:** len 0x52, ret 4, regs [], calls 1, k [0x417BC, 0x817BC]
- **Invariants:** ret, regs and calls (1/1) hold. k and len are equal.
- **Slot 150.**
- **Body:** a zero argument pushes `417BCh`, 0. A non-zero argument pushes `817BCh`, 1, value. Both paths store
  `mov [19F9C8h],ecx` (RS[150]) and end in `retn 4`.
- **Twin** 0x24A1B0 is identical. Neither token occurs elsewhere.
- **Confidence:** high.

### D3DDevice_SetRenderState_EdgeAntiAlias = 0x190020

- **Reference:** len 0x32, ret 4, regs [], calls 1, k [0x80320]
- **Measured:** len 0x32, ret 4, regs [], calls 1, k [0x80320]
- **Invariants:** ret, regs and calls (1/1) hold. k and len are equal.
- **Slot 151.**
- **Body:** token `80320h` (line smooth and polygon smooth), then the value twice (`[eax+4]`, `[eax+8]`), then
  `mov [19F9CCh],ecx` (RS[151]), `retn 4`.
- **Twin** 0x249E20 is identical. `80320h` occurs nowhere else.
- **Confidence:** high.

### D3DDevice_SetRenderState_MultiSampleAntiAlias = 0x191500

- **Reference:** len 0x72, ret 4, regs [], calls 4, k [0x41D7C]
- **Measured:** len 0x72, ret 4, regs [], calls 4, k [0x41D7C]
- **Invariants:** ret, regs and calls (4/4) hold. k and len are equal.
- **Slot 152.**
- **Body:**
  - `mov [19F9D0h],eax` (RS[152]);
  - the constants reader 0x192180;
  - `edi = (RS[153] << 16) | RS[158]`, plus `or edi,1` when bit 15 of `[esi+8]` is set and RS[152] is non-zero;
  - token `41D7Ch`, edi;
  - the viewport push 0x1908C0;
  - `retn 4`.
- **Twin** 0x24B220 is identical.
- **Separation of the three `41D7Ch` setters** (152, 153 and 158): which slot takes the argument, and where it enters
  the word. 152 gates bit 0, 153 is shifted into the high 16 bits, and 158 is ORed into the low bits. All three match
  their twins.
- **Confidence:** high.

### D3DDevice_SetRenderState_MultiSampleMask = 0x191580

- **Reference:** len 0x50, ret 4, regs [], calls 1, k [0x41D7C]
- **Measured:** len 0x50, ret 4, regs [], calls 1, k [0x41D7C]
- **Invariants:** ret, regs and calls (1/1) hold. k and len are equal.
- **Slot 153.**
- **Body:** `mov ecx,[19F9E8h]` (RS[158]); `mov [19F9D4h],eax` (RS[153]); `shl eax,10h`; `or eax,ecx`; `or edi,1`
  under the same gate on RS[152]; token `41D7Ch`; `retn 4`.
- **Twin** 0x24B2A0 is identical.
- **Confidence:** high.

### D3DDevice_SetRenderState_MultiSampleMode = 0x191480

- **Reference:** len 0x27, ret 4, regs [], calls 1, k [0x1A04, 0x1A14]
- **Measured:** len 0x34, ret 4, regs [], calls 1, k [0xA90, 0x15B4, 0x15B8, 0x15C0]
- **Invariants:** ret, regs and calls (1/1) hold. Length is 13 bytes (33%) long, outside the corroboration band. The
  reason is below.
- **Slot 154.**
- **Body:**
  ```
  191480 mov  ecx, [esp+4]
  191484 mov  eax, [19FA08h]
  191489 mov  [19F9D8h], ecx        ; RS[154]
  19148F mov  ecx, [eax+15B4h]      ; render target
  191495 cmp  ecx, [eax+15C0h]      ; back buffer
  19149B jne  1914B1                ; act only when the render target is the back buffer
  19149D lea  edx, [eax+0A90h]      ; the device's viewport
  1914A3 mov  eax, [eax+15B8h]      ; depth surface
  1914A9 push edx / push eax / push ecx
  1914AC call 190BE0                ; render-target setup (RT, Z, viewport), retn 0Ch
  1914B1 retn 4
  ```
- **Twin** 0x24B1C0 is the same logic. It stores RS[154], tests `[ecx+1A04h] == [ecx+1A14h]` with `jne`, and calls
  its setup helper 0x24AAC0 with `xor edx,edx` in registers. The extra 13 bytes are the three pushed arguments, so the
  difference is the helper's convention, not the setter's.
- **The value is 5849's D3DMULTISAMPLEMODE, not 3925's MULTISAMPLETYPE.** 0x190BE0 reads RS[154] when the target is
  the back buffer (0x190C0F) and RS[155] otherwise (0x190D80). It decodes the value exactly as 5558's 0x24AAC0 does:
  - 0 means off (`cmp ebp,edi; je`);
  - anything else sets `or eax,8000h` in `[esi+8]` and halves the X scale;
  - 2 also halves Y and gives `or ecx,2000h`;
  - any other value gives `or ecx,1000h`.

  5558 0x24AC8E..0x24ACC9 has the same `test ebp,ebp`, `or eax,8000h`, `cmp ebp,2`, `or ebx,2000h` and `or ebx,1000h`.
  D3d8CoreSymbols identified 0x190BE0 as the internal behind the public SetRenderTarget wrapper 0x192D60, which passes
  the full viewport 0x19D6D0.
- **Default state:** InitDefaultState skips 154, as 5558's skips `9Ah`.
- **Confidence:** high.

### D3DDevice_SetRenderState_MultiSampleRenderTargetMode = 0x1914C0

- **Reference:** len 0x27, ret 4, regs [], calls 1, k [0x1A04, 0x1A14]
- **Measured:** len 0x34, ret 4, regs [], calls 1, k [0xA90, 0x15B4, 0x15B8, 0x15C0]
- **Invariants:** ret, regs and calls (1/1) hold. Length is 13 bytes long, for the reason given under MultiSampleMode.
- **Slot 155.**
- **Body:** the same as MultiSampleMode, but it stores `[19F9DCh]` (RS[155]) and uses `je 1914F1`: it acts only when
  the render target is **not** the back buffer.
- **Twin** 0x24B1F0 stores RS[155] and uses the same `je`.
- **Separation from MultiSampleMode:** the stored slot, and `je` against `jne`. Both agree with the twins and with
  0x190BE0, which reads 155 for a non-back-buffer target.
- **Confidence:** high.

### D3DDevice_SetRenderState_ShadowFunc = 0x190060

- **Reference:** len 0x35, ret 4, regs [], calls 1, k [0x41E6C, 0xFFFFFE00]
- **Measured:** len 0x35, ret 4, regs [], calls 1, k [0x41E6C, 0xFFFFFE00]
- **Invariants:** ret, regs and calls (1/1) hold. k and len are equal.
- **Slot 156.**
- **Body:** token `41E6Ch` with `lea edx,[ecx-200h]` (D3DCMP to 0..7), then `mov [19F9E0h],ecx` (RS[156]), `retn 4`.
- **Twin** 0x249E60 is identical. `41E6Ch` occurs nowhere else.
- **Confidence:** high.

### D3DDevice_SetRenderState_LineWidth = 0x190240 (anchor)

- **Reference:** len 0x65, ret 4, regs [], calls 2, k [0x1FF, 0x1FF, 0x964, 0x40380]
- **Measured:** len 0x65, ret 4, regs [], calls 2, k [0x1FF, 0x1FF, 0x520, 0x40380]
- **Invariants:** ret, regs and calls (2/2) hold. len is equal, and so is every k at or above 0x10000.
- **Slot 157.**
- **Body:** `fmul [esi+520h]` and `fmul [1EF2ECh]`, `fadd [1EEA20h]`, float to int through 0x197550, clamped with
  `cmp edi,1FFh`, then token `40380h`, then `mov [19F9E4h],ebx` (RS[157]), `retn 4`.
- **Twin** 0x24A040 is identical except for the scale field, 0x520 against 0x964. This re-proves the matcher's address.
- **Confidence:** high.

### D3DDevice_SetRenderState_SampleAlpha = 0x1915D0

- **Reference:** len 0x4E, ret 4, regs [], calls 1, k [0x41D7C]
- **Measured:** len 0x4E, ret 4, regs [], calls 1, k [0x41D7C]
- **Invariants:** ret, regs and calls (1/1) hold. k and len are equal.
- **Slot 158.** It exists in this build; 3925 lacks it.
- **Body:** `esi = (RS[153] << 16) | argument`; `mov [19F9E8h],eax` (RS[158]); `or esi,1` under the RS[152] gate;
  token `41D7Ch`; `retn 4`.
- **Twin** 0x24B2F0 is identical.
- **Confidence:** high.

### D3DDevice_SetRenderState_Dxt1NoiseEnable = 0x1902B0

- **Reference:** len 0x77, ret 4, regs [], calls 1, k [0x1A04, 0x40100, 0x40110]
- **Measured:** len 0x77, ret 4, regs [], calls 1, k [0x15B4, 0x40100, 0x40110]
- **Invariants:** ret, regs and calls (1/1) hold. len is equal, and so is every k at or above 0x10000.
- **Slot 159.**
- **Body:**
  - the render-target format test: `mov eax,[edi+15B4h]; movzx ecx,byte [eax+0Dh]; mov dl,[ecx+19D688h];
    and dl,3Ch; cmp dl,20h`;
  - `esi` is the argument when the format test passes, and 0 otherwise;
  - when `esi` differs from bit 0 of `[edi+8]`, it toggles that bit and pushes `40110h` 0 and `40100h`
    `(esi << 5) | 8`;
  - `mov [19F9ECh],ebx` (RS[159]);
  - `retn 4`.
- **Twin** 0x24A0B0 is identical except for the render-target field, 0x15B4 against 0x1A04.
- **Callers:** the render-target setup re-applies it at 0x19116E.
- **Confidence:** high.

### D3DDevice_SetRenderState_YuvEnable = 0x191310

- **Reference:** len 0x2B, ret 4, regs [], calls 2, k []
- **Measured:** len 0x2B, ret 4, regs [], calls 2, k []
- **Invariants:** ret, regs and calls (2/2) hold. len is equal.
- **Slot 160.**
- **Body:** `mov [19F9F0h],eax` (RS[160]), then the push reservation, then `mov edx,eax; mov ecx,esi; call 0x190AB0`,
  `mov [esi],eax`, `retn 4`.
- **Helper 0x190AB0** chooses `10100001h` or `100001h` by RS[160]. It adds `or esi,10000h` when RS[143] = 2, adds
  `1000h` for depth formats `2Dh`, `2Bh`, `31h` and `2Fh`, and pushes `40290h`.
- **Twin** 0x24B050 calls 5558's identical builder 0x24A8F0.
- **Confidence:** high.

### D3DDevice_SetRenderState_OcclusionCullEnable = 0x191340

- **Reference:** len 0x62, ret 4, regs [], calls 1, k [0x1E00, 0x41D84]
- **Measured:** len 0x62, ret 4, regs [], calls 1, k [0x1E00, 0x41D84]
- **Invariants:** ret, regs and calls (1/1) hold. k and len are equal.
- **Slot 161.**
- **Body:** it stores the argument first, `mov [19F9F4h],eax` (RS[161]). It then pushes `41D84h` with
  `(RS[162] ? 2 : 0) | (RS[161] && (!RS[144] || RS[145] == 1E00h) ? 1 : 0)`, `retn 4`.
- **Twin** 0x24B080 is identical.
- **Separation from StencilCullEnable:** data flow. The slot this function writes feeds the gated bit 0 of the
  formula; StencilCullEnable's slot feeds bit 1. That is the same in both builds.
- **Confidence:** high.

### D3DDevice_SetRenderState_StencilCullEnable = 0x1913B0

- **Reference:** len 0x62, ret 4, regs [], calls 1, k [0x1E00, 0x41D84]
- **Measured:** len 0x62, ret 4, regs [], calls 1, k [0x1E00, 0x41D84]
- **Invariants:** ret, regs and calls (1/1) hold. k and len are equal.
- **Slot 162.**
- **Body:** `mov [19F9F8h],eax` (RS[162]), then the same `41D84h` formula, in which RS[162] gives bit 1
  (`mov ecx,2`). `retn 4`.
- **Twin** 0x24B0F0 is identical.
- **Confidence:** high.

### D3DDevice_SetRenderState_RopZCmpAlwaysRead = 0x191420

- **Reference:** len 0x11, ret 4, regs [], calls 1, k []
- **Measured:** len 0x11, ret 4, regs [], calls 1, k []
- **Invariants:** ret, regs and calls (1/1) hold. len is equal.
- **Slot 163.**
- **Body:** `mov eax,[esp+4]; mov [19F9FCh],eax` (RS[163]); `call 0x190B10; retn 4`.
- **Helper 0x190B10**, identical to 5558's 0x24A9F0, maps RS[163] to `or eax,100000h` in `[dev+1FCCh]` (5558
  `[dev+242Ch]`). It then pushes `40110h`, `81D8Ch` `400094h`, `40100h`, `81D8Ch` `400B80h`, `40100h`.
- **Twin** 0x24B160 is identical.
- **Separation of the three 17-byte twins:** data flow in the shared helper, the same in both builds:

  | Slot | Name | Helper writes |
  |---|---|---|
  | 163 | RopZCmpAlwaysRead | `100000h` |
  | 164 | RopZRead | `8000000h` |
  | 165 | DoNotCullUncompressed | `8` in the other word |

- **Confidence:** high.

### D3DDevice_SetRenderState_RopZRead = 0x191440

- **Reference:** len 0x11, ret 4, regs [], calls 1, k []
- **Measured:** len 0x11, ret 4, regs [], calls 1, k []
- **Invariants:** ret, regs and calls (1/1) hold. len is equal.
- **Slot 164.**
- **Body:** `mov [19FA00h],eax` (RS[164]); `call 0x190B10`, which ORs `8000000h` into `[dev+1FCCh]` when RS[164] is
  set; `retn 4`.
- **Twin** 0x24B180 is identical.
- **Confidence:** high.

### D3DDevice_SetRenderState_DoNotCullUncompressed = 0x191460

- **Reference:** len 0x11, ret 4, regs [], calls 1, k []
- **Measured:** len 0x11, ret 4, regs [], calls 1, k []
- **Invariants:** ret, regs and calls (1/1) hold. len is equal.
- **Slot 165**, the last complex state. The next dword, 0x19FA08, is `D3D_pDevice`.
- **Body:** `mov [19FA04h],eax` (RS[165]); `call 0x190B10`, which ORs `8` into `[dev+1FC8h]` when RS[165] is set (5558
  `[dev+2428h]`); `retn 4`.
- **Twin** 0x24B1A0 is identical.
- **Confidence:** high.

### D3DDevice_SetTextureState_TexCoordIndex = 0x190580 (anchor)

- **Reference:** len 0x105, ret 8, regs [], calls 1, k [0x200, 0x47F, 0x950 ×3, 0x2400, 0x2401, 0x8511, 0x8512, 0xC03C, 0x30000, 0x41964, 0xFF000000, 0xFFFF0000]
- **Measured:** len 0x105, ret 8, regs [], calls 1, k [0x200, 0x47F, 0x514 ×3, 0x2400, 0x2401, 0x8511, 0x8512, 0xC03C, 0x30000, 0x41964, 0xFF000000, 0xFFFF0000]
- **Invariants:** ret, regs and calls (1/1) hold. len is equal, and so is every k at or above 0x10000.
- **Store:** `shl eax,7; mov [eax+19F5E0h],ebx`, which is `D3D_DeferredTextureState[stage][28]`.
- **Body:**
  - when the value's high word is non-zero, it pushes `edi*4 + 41964h` with `0FF000000h` and decodes that word into
    the texgen modes `8511h`, `8512h`, `2400h` and `2401h`;
  - it pushes `(stage + 0C03Ch) << 4` with three texgen dwords;
  - it keeps a per-stage mask in `[esi+514h]` (5558 `950h`);
  - it ORs `47Fh`, and `200h` conditionally, into `D3D_DirtyFlags`;
  - `retn 8`.
- **Twin** 0x24A390 is identical except for the mask field.
- **Callers:** SetTextureStageStateNotInline calls it for type `1Ch` (0x190824). This re-proves the matcher's address.
- **Confidence:** high.

### D3DDevice_SetTextureState_BumpEnv = 0x190690

- **Reference:** len 0x63, ret 12, regs [], calls 1, k [0x784, 0x41AD0]
- **Measured:** len 0x63, ret 12, regs [], calls 1, k [0x36C, 0x41AD0]
- **Invariants:** ret, regs and calls (1/1) hold. len is equal, and so is every k at or above 0x10000.
- **Body:**
  - `ebx = stage` when a pixel shader is set (`[edi+36Ch]` ≠ 0; 5558 `784h`), otherwise `stage + 1`;
  - when `test bl,3` is non-zero: `lea ecx,[ebx*4+41AD0h]` with ebx = stage' × 16 + type, then the value;
  - then `shl esi,5; add esi,eax; mov [esi*4+19F570h],ebp`, which is `D3D_DeferredTextureState[stage][type]`;
  - `retn 0Ch`.
- **Reached by:** SetTextureStageStateNotInline's `jmp 0x190690` (0x190867) for types 16h..1Bh. This is its only
  reference. The address is not in the recompiler's start list today; naming it makes it an entry point
  (`sdk/tools/recomp/main.cpp:166-167`).
- **Twin** 0x24A4A0 is identical except for the pixel-shader field. `41AD0h` occurs nowhere else.
- **Confidence:** high.

### D3DDevice_SetTextureState_BorderColor = 0x190700

- **Reference:** len 0x3D, ret 8, regs [], calls 1, k [0x41B24]
- **Measured:** len 0x3D, ret 8, regs [], calls 1, k [0x41B24]
- **Invariants:** ret, regs and calls (1/1) hold. k and len are equal.
- **Body:** `shl edx,6; add edx,41B24h` and the value, then `shl ecx,7; mov [ecx+19F5E4h],edx`, which is
  `[stage][29]`. `retn 8`.
- **Callers:** SetTextureStageStateNotInline calls it for type `1Dh` (0x19083B).
- **Twin** 0x24A510 is identical. `41B24h` occurs nowhere else.
- **Confidence:** high.

### D3DDevice_SetTextureState_ColorKeyColor = 0x190740

- **Reference:** len 0x39, ret 8, regs [], calls 1, k [0x40AE0]
- **Measured:** len 0x39, ret 8, regs [], calls 1, k [0x40AE0]
- **Invariants:** ret, regs and calls (1/1) hold. k and len are equal.
- **Body:** `lea edx,[ecx*4+40AE0h]` and the value, then `shl ecx,7; mov [ecx+19F5E8h],edx`, which is
  `[stage][30]`. `retn 8`.
- **Callers:** SetTextureStageStateNotInline calls it for type `1Eh` (0x190852).
- **Twin** 0x24A550 is identical. `40AE0h` occurs nowhere else.
- **Confidence:** high.

### D3DDevice_SetTextureStageStateNotInline = 0x190780

- **Reference:** len 0xEC, ret 12, regs [], calls 4, k [0x480F, 0xFFFFBFF1]
- **Measured:** len 0xEC, ret 12, regs [], calls 4, k [0x480F, 0xFFFFBFF1]
- **Invariants:** ret, regs and calls (4/4) hold. k and len are equal.
- **Body:** the listing in section 6, identical to the twin 0x24A5A0 instruction for instruction. `480Fh` and
  `0FFFFBFF1h` occur nowhere else.
- **Callers:**
  - D3D_InitDefaultState: 0x195EBC, 0x195ECB, 0x195EE4 and 0x195EEF, at the same positions as 5558's 0x24F9BD,
    0x24F9CC, 0x24F9E5 and 0x24F9F0;
  - 0x194149, 0x194170, 0x194182 and 0x194196 in 0x1940E0, and 0x194233 and 0x194295 in 0x194200, the two functions
    named above.

  D3d8CoreSymbols named the same address from InitDefaultState independently.
- **Confidence:** high.

## Unproven targets

None. All 36 targets are proven above, so there are no ranked candidates to give. The three states 3925 lacks,
MultiSampleMode, MultiSampleRenderTargetMode and SampleAlpha, are present in this build.

## Identified in passing (not emitted)

| Address | Identity | Proof | Owner |
|---|---|---|---|
| 0x190330 | D3DDevice_SetRenderState_ZBias | Slot 149, stores RS[149] 0x19F9C4. Converts the bias into slope and offset, then calls SetRenderStateNotInline for states 77..81. `retn 4`. Twin 0x24A130 | not a `game.toml` name |
| 0x195E30 | D3D_InitDefaultState | Section 5 | D3d8CoreSymbols, who emits it |
| 0x192D80 | D3DDevice_SetTransform | Callee of InitDefaultState's 0..9 identity loop. `lea edi,[ecx+ebx+810h]; rep movsd` ×16, `retn 8`. len 0x10E against 0x118 | D3d8CoreSymbols |
| 0x193C00 | D3DDevice_SetScreenSpaceOffset | Called with (0, 0) last, as 5558 calls 0x2480F0. Stores at `[dev+0AA8h]`/`[dev+0AACh]`. len 0x49, equal to 5558 | D3d8CoreSymbols |
| 0x192C20 | D3DDevice_MakeSpace | Every setter's push reservation calls it at the instruction where its 5558 twin calls `D3DDevice_MakeSpace` 0x24D5B0 | D3d8CoreSymbols |
| 0x190BE0 | render-target setup internal | `retn 0Ch`. Reads RS[154]/RS[155] (section above) and re-applies LineWidth and Dxt1NoiseEnable. Behind the public SetRenderTarget wrapper 0x192D60 | D3d8CoreSymbols |
| 0x1993D0 | lazy-state dispatcher | Section 3; twin 0x2550B0 | — |
| 0x1908C0, 0x190AB0, 0x190B10, 0x192180 | viewport push, control0 builder, RopZ helper, constants reader | Twins 0x24A700, 0x24A8F0, 0x24A9F0 and 0x24C300 | — |

## Data the proofs rely on

These addresses come out of the bodies above. They are **not** emitted here: D3d8DataLayout owns `[data]` and
`sdk/xdk/5233/layout.toml`, and has them.

| Symbol | Address | Where it shows |
|---|---|---|
| D3D_pDevice | 0x19FA08 | `mov esi,[19FA08h]` in every setter |
| D3D_Device | 0x19FA10 | Simple's push cursor `[19FA10h]` and threshold `[19FA14h]` |
| D3D_RenderState | 0x19F770 | NotInline 0x18FD0D/0x18FD32 `mov [esi*4+19F770h]`. 166 dwords, ending at D3D_pDevice |
| D3D_DeferredTextureState | 0x19F570 | TSS NotInline 0x1907AC/0x19080B `mov [ecx*4+19F570h]`. [4][32], 0x200 below D3D_RenderState |
| D3D_DirtyFlags | 0x19F568 | NotInline 0x18FD28 `or [19F568h],eax`, a separate global as in 5558/5849 |
| D3D_SimpleRenderStateEncode | 0x1EE768 | NotInline 0x18FCFA `mov ecx,[esi*4+1EE768h]`. 92 entries |
| (complex-handler table) | 0x19D4E0 | NotInline 0x18FD42 `call [esi*4+19D4E0h]`. Used for states 136..165 |
| TextureState_Stage | 32 | TSS NotInline `shl ecx,5; add ecx,eax` |
