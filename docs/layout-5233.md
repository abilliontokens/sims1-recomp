# XDK 5233 data layout and D3D/DSOUND/XPP data symbols, proven against The Sims

Image: `assets/default.xbe`, The Sims (USA), title `0x4541002F`, sha1
`40ab6f97e8ee3bf4102a5a7820dcb8047fc30097`; D3D8, DSOUND, XAPILIB, XBOXKRNL, LIBCMT, XGRAPHC and XMV are
all build 5233. Every address below is this image's, read from `out/game.exe` (the `xbe2pe.py` flat PE,
guest addresses 1:1) in the shared IDA database. "5558" is the same code in The Sims: Bustin' Out
(`simsbustinout/out/game.exe`), whose values are `sdk/xdk/5558/layout.toml`'s.

Outputs: `sdk/xdk/5233/layout.toml` (the `[layout]` table) and `config/found-d3d8-data.toml` (`[data]`).

## Result

| | proven | UNPROVEN | left at 0 |
| --- | --- | --- | --- |
| `[layout]` keys in `sdk/xdk/5233/layout.toml` | **45 of 45** | **0** | - |
| `[data]` names of `config/game.toml` | **11 of 12**, each re-checked | - | **1** (`D3D_IndexData`) |

- The provisional header (a copy of 5558's values) is gone. Every line now cites this image's address and
  instruction. No line keeps a 5558 value on trust.
- **26 of the 31 CDevice offsets differ from 5558's.** Only `Push`, `PushThreshold`, `BaseVertex`,
  `Flags` and `Time` are unchanged. The CDevice is `0x2040` bytes, not `0x24A0`. The 14 non-CDevice keys
  (dirty bit, stage stride, stream record, pixel shader definition, DSOUND, XPP) all equal 5558's.
- Render and texture stage states are numbered as in 5849. `D3d8StateSymbols` owns that question and
  reported it (proof in `docs/d3d8-state-symbols.md`). The corroboration I measured independently is
  below. **The layout carries no `RenderState_`/`TextureState_` table.**
- `config/found-d3d8-data.toml` is **not staged**, because the numbering is settled (see "Staging").

## How each key was found

The D3D section here (`0x18F680..0x1A1DA0`, 282 recompiled functions) was aligned with 5558's
(`0x243D00..0x267134`) by instruction sequence. Each function was disassembled with `objdump`,
displacements and image addresses were normalised, and the sequences were scored with `difflib`
(1.0 = the same instructions, only offsets and addresses changed). Each 5558 function that proves a key
in `sdk/xdk/5558/layout.toml` has a twin here. The score of each pair is in the table below; where a
body differs, the row says how.

The alignment only shows which function to read. Every value was then read from this image's
disassembly at the cited address. Where 5558's proving function is not linked in this image
(`SetIndices`, `SetGammaRamp`, `GetBackBufferScale`, `GetRenderTarget2`), the key is proven from another
function here that reads or writes the same field. That function is named in the table.

The functions used, as their bodies identify them:

| 5233 | 5558 twin | function (score) |
| --- | --- | --- |
| 0x18F8B0 | 0x2443C0 | `Direct3D_CreateDevice` (0.878; 6 args, `retn 18h`, the 0x80000/0x8000 push buffer defaults) |
| 0x196590 | 0x2500E0 | `CDevice_Init` (0.721; `this` = device) |
| 0x196AF0 | 0x2505B0 | `CDevice_UnInit` (0.873) |
| 0x192460 | 0x24CD10 | push buffer init, called by `CDevice_Init` at 0x196612 (0.857) |
| 0x192760 (+0x19279D) | 0x24D120 | `CDevice_KickOff` (0.457: the same blocks, with `this` kept on the stack instead of in esi, and one more store, `[+0x3C]` to `[+0x1FE0]`) |
| 0x1928B0 | 0x24D240 | `D3D_SetFence` (0.615: 5558 pushes one more method, 0x4A310, before the same 0x41D70/0x41D90 ones) |
| 0x1936F0 | 0x2471C0 | `D3DDevice_SetTexture` (1.0) |
| 0x1938A0 | 0x2473A0 | `D3DDevice_SetPalette` (1.0) |
| 0x191E90 | 0x24BE90 | `D3DDevice_SetStreamSource` (1.0) |
| 0x192D80 | 0x244FE0 | `D3DDevice_SetTransform` (0.907) |
| 0x192D60 → 0x190BE0 | 0x246040 | `D3DDevice_SetRenderTarget` (0.248): in 5233 a wrapper pushing a third argument to the body 0x190BE0, which has 5558's 0x245CC0 inlined |
| 0x193590 | 0x246B40 | `D3DDevice_SetViewport` (0.542: without 5558's super-sample rounding block) |
| 0x1908C0 | 0x24A700 | viewport push helper (1.0) |
| 0x193C00 | 0x2480F0 | `D3DDevice_SetScreenSpaceOffset` (0.8: the same stores, the add operands swapped) |
| 0x1931F0 | 0x2463E0 | `D3DDevice_GetBackBuffer2` (1.0) |
| 0x193570 | 0x246B20 | `D3DDevice_GetDepthStencilSurface2` (1.0; `GetRenderTarget2` is not linked) |
| 0x1948F0 | 0x2495F0 | `D3DDevice_Swap` (0.993) |
| 0x192E90 | 0x245370 | `D3DDevice_Release` (1.0) |
| 0x195510 | 0x24E740 | `D3DDevice_SetPixelShader` (1.0) |
| 0x192270 | 0x24C3F0 | `D3DDevice_SetVertexShader` (0.764) |
| 0x195E30 | 0x24F940 | `D3D_InitDefaultState` (0.832) |
| 0x192EF0 | 0x245450 | vertical blank callback setter (1.0) |
| 0x192F10 | 0x245490 | `D3DDevice_BlockUntilVerticalBlank` (1.0) |
| 0x193960 | 0x247630 | display field query (`GetDisplayFieldStatus`, 1.0) |
| 0x199A30 | 0x251FF0 | miniport vertical blank handler (1.0) |
| 0x199960/0x199987 | 0x251F10/0x251F37 | its flip and gamma step (0.933/0.766) |
| 0x193C50 | 0x2482B0 | D3D kernel debugger query, published by `CDevice_Init` at 0x196AB9 (0.74) |
| 0x194440, 0x1949D0 | 0x249130, 0x2497F0 | the scaled blit and its caller, both reading the back buffer scale (0.974, 0.773) |
| 0x193070 | 0x245EC0 | `GetDisplayMode` (1.0) |
| 0x18FCF0, 0x190780 | 0x249910, 0x24A5A0 | `SetRenderStateNotInline`, `SetTextureStageStateNotInline` (1.0, 1.0) |
| 0x1B6AD1, 0x1B5BCE | 0x29048D | `CDirectSoundStream` constructor (1.0), destructor |
| 0x1B7710, 0x1B78F1 | 0x294000, 0x29426D | effects image parser (1.0), effects image downloader (0.929) |
| 0x1E7EE4, 0x1E7F06 | 0x2DB063, 0x2DB085 | `XGetDevices`, `XGetDeviceChanges` (1.0, 1.0; .XTLID 0x10032/0x10033 per `XtlidXapiCrtSymbols`) |

## What `0x1A11D8` is: the embedded miniport, `D3D_Device + 0x17C8`

The first Linux boot faulted 122 ms in at guest address `FD001804`, with `ecx = esi = 0x001A11D8`,
`eax = 0x001A1374`, `ebx = 1`, `edi = 0x83100060`. **`0x1A11D8` is not the device. It is the
miniport object embedded in it: `D3D_Device 0x19FA10 + 0x17C8`.** (5558 embeds its miniport at
`+0x1C28`, 3925 at `+0x2308`.)

```asm
; Direct3D_CreateDevice 0x18F8B0 - the static device and its pointer
0x18F8EA  mov   edi, offset dword_19FA10      ; D3D_Device
0x18F8F2  mov   ecx, edi
0x18F8F4  mov   dword_19FA08, edi             ; D3D__pDevice = &D3D_Device
0x18F904  mov   dword_19FA18, esi             ; [device+8] |= BehaviorFlags & 0x10
0x18F90A  call  CDevice_Init                  ; returns to 0x18F90F - on the faulting stack
; CDevice_Init 0x196590, this = device
0x19663F  mov   esi, [esp+184h+var_17C]       ; this
0x196643  add   esi, 17C8h                    ; esi = device + 0x17C8 = 0x1A11D8
0x196649  mov   ecx, esi
0x19664B  call  CMiniport_InitHardware        ; 0x19A93D, returns to 0x196650 - on the faulting stack
; CMiniport_InitHardware 0x19A93D, this = miniport
0x19A945  mov   esi, ecx                      ; esi = ecx = 0x1A11D8, as in the fault
0x19A961  and   byte ptr [esi+194h], 0        ; vertical blank KEVENT: Type 0 ...
0x19A978  lea   eax, [esi+19Ch]               ; eax = 0x1A1374, as in the fault: that event's wait list head
0x19A97E  inc   ebx                           ; ebx = 1, as in the fault
0x19A97F  mov   ecx, esi
0x19A98E  mov   byte ptr [esi+196h], 4        ; ... Size 4
0x19A995  mov   [esi+198h], ebx               ; ... SignalState 1
0x19A9A3  call  CMiniport_MapRegisters        ; 0x19A44A, returns to 0x19A9A8
; CMiniport_MapRegisters 0x19A44A
0x19A44A  mov   dword ptr [ecx], 0FD000000h   ; miniport field 0 = NV2A register base
0x19A450  mov   eax, ds:0FD001804h            ; <- the fault: NV2A PCI config, bus master enable
```

Three more readers of this image tie the same object to the device:

- `CDevice_KickOff` 0x192780: `mov eax, [eax+17C8h]` reads the register base (miniport field 0) through
  `D3D__pDevice`, then flushes through `[eax+100410h]`.
- `CDevice_UnInit` 0x196B4B: `lea edi, [esi+17C8h]` and polls the miniport's shutdown 0x199810.
- `CDevice_Init` 0x196A96: `add ecx, 17C8h` publishes the miniport address in the kernel debugger block.

The other registers: `eax = miniport + 0x19C` is the wait list head of the vertical blank event at
miniport + 0x194, which is `CDevice_VBlankEvent` (0x195C) below. `edi = 0x83100060` is not a register
window. `CDevice_Init` allocates 0x60 bytes of contiguous memory (`MmAllocateContiguousMemoryEx` with
NumberOfBytes 0x60, 0x1965A7) and keeps it at `[device+0x30]`. `[device+0x2030]` points 0x20 into it,
and the `rep stosd` of 16 dwords at 0x19660C leaves `edi` at its end. So `edi − 0x60 = 0x83100000` is
that block. On the stack, 0x1924F8 (after `LocalAlloc` in the push buffer init 0x192460, which
`CDevice_Init` called at 0x196612 and which had returned) and 0x19598A (after `call 0x195960` in
0x19597F) are not on the faulting chain: they are left over in slots from earlier calls. The two
`0x19FA10` slots are `CDevice_Init`'s local copy of `this` (0x1965A3) and the caller's `edi`
(`D3D_Device`), which `CDevice_Init` saves at 0x1965FE.

So this is the canonical unreplaced-`Direct3D_CreateDevice` failure. The guest
`Direct3D_CreateDevice → CDevice_Init → CMiniport_InitHardware → CMiniport_MapRegisters` touches the
NV2A. Every CDevice offset below is relative to `0x19FA10`. The fault confirms `D3D_Device`
independently: `0x1A11D8 − 0x17C8 = 0x19FA10`.

## `[layout]`, key by key

Device = `D3D_Device` 0x19FA10. "miniport + N" = device + 0x17C8 + N.

### CDevice

| key | 5558 | **5233** | proof in this image | also |
| --- | --- | --- | --- | --- |
| `CDevice_Push` | 0x0 | **0x0** | `SetTexture` 0x193742 `mov eax, [ebp+0]` (ebp = `[0x19FA08]`), 0x193766 `mov [ebp+0], eax` | push buffer init 0x19249A `mov [esi], eax`; `SetRenderState_Simple` 0x18FCC0/0x18FCD0 load/store `[0x19FA10]`; game code inlines the same (0x152B5D/0x152C28) |
| `CDevice_PushThreshold` | 0x4 | **0x4** | `SetTexture` 0x193745 `cmp eax, [ebp+4]`, then `call D3DDevice_MakeSpace` 0x192C20 (0x19374A) | `SetRenderState_Simple` 0x18FCC8 `cmp eax, ds:19FA14h`, the same pair as 5558's 0x2498E8 `cmp eax, ds:264954h`; push buffer init 0x1924AF stores the base + `dword_1A1D54` − 0x204 there (0x1924A5; `Direct3D_CreateDevice` defaults that size to 0x8000 at 0x18F8CF) |
| `CDevice_BaseVertex` | 0x1C | **0x1C** | `DrawIndexedVertices` 0x19510E `mov eax, [esi+1Ch]` → argument of the vertex array setup 0x199450, which multiplies it by each stream's stride (0x1995A3 `imul eax, [esp+20h]`) | same instruction as 5558 0x24DD3E; the setup caches it at `[device+0x20]` (0x1994A1). `SetIndices` is not linked, so nothing here writes it |
| `CDevice_IndexBuffer` | 0x7A0 | **0x388** | `CDevice_UnInit` 0x196B6E `mov eax, [esi+388h]` and releases it (`add edx, 0FFF80000h`, `call 0x18F9B0` at 0x196B8D) | 5558's `UnInit` releases its index buffer `[+0x7A0]` (0x25062A) at the same point: after the vertex shader block, before the texture/palette loop. 5558's `SetIndices` (0x247482) proves that field is the index buffer. Here, too, it is vertex shader + 0xC (0x37C → 0x388; 5558 0x794 → 0x7A0). `SetIndices`/`GetIndices` are not linked, and this teardown is the only code that touches the field |
| `CDevice_ZScale` | 0x948 | **0x50C** | viewport push helper 0x1908C0: 0x190A60 `fld [esi+0AA0h]` (MinZ), 0x190A66 `fmul [esi+50Ch]`; 0x190A72 `fld [esi+0AA4h]` (MaxZ), 0x190A78 `fmul [esi+50Ch]` | `SetRenderTarget` body 0x190EBD `lea eax, [esi+50Ch]` → 0x197850, which stores the depth format's maximum (65535.0 / 16777215.0) |
| `CDevice_SuperSampleX` | 0x95C | **0x518** | viewport push helper 0x1909C1 `fmul [esi+518h]` (viewport X `[esi+0A90h]` × scale) | `SetRenderTarget` body stores it at 0x1910F1; that is the back buffer scale X when the target is the back buffer, else 1.0, as 5558's. `SetScissors` 0x193A71 and `Clear` 0x194D0A read it |
| `CDevice_SuperSampleY` | 0x960 | **0x51C** | viewport push helper 0x1909E3 `fmul [esi+51Ch]` (viewport Y × scale) | `SetRenderTarget` body stores it at 0x1910E9; `SetScissors` 0x193A77 |
| `CDevice_Transforms` | 0xC60 | **0x810** | `SetTransform` 0x192D96 `lea edi, [ecx+ebx+810h]` (ecx = type << 6), `rep movsd` of 16 dwords | `D3D_InitDefaultState` loads all 10 through it; the lazy transform reader 0x1991D0 reads `lea eax, [esi+810h]` |
| `CDevice_Textures` | 0xF88 | **0xB38** | `SetTexture` 0x193700 `mov eax, [ebp+esi*4+0B38h]`, 0x193739 `mov [ebp+esi*4+0B38h], ebx` | `CDevice_UnInit` releases `[edi−0x10]` from `lea edi, [esi+0B48h]` (0x196B94) |
| `CDevice_Palettes` | 0xF98 | **0xB48** | `SetPalette` 0x1938AD `mov eax, [esi+edi*4+0B48h]`, 0x1938E5 store; pushes NV2A `0x41B20 + stage * 64` | `CDevice_UnInit` 0x196B94 `lea edi, [esi+0B48h]` releases 4 of them |
| `CDevice_RenderTarget` | 0x1A04 | **0x15B4** | `SetRenderTarget` body 0x190BF7 `mov eax, [esi+15B4h]` for a NULL target; 0x190E8A `mov [esi+15B4h], ebp` | `SetViewport` 0x19359A reads it and compares with the back buffer |
| `CDevice_Depth` | 0x1A08 | **0x15B8** | `SetRenderTarget` body 0x190EAF `mov [esi+15B8h], ebx` | `GetDepthStencilSurface2` 0x193576 `mov esi, [eax+15B8h]` |
| `CDevice_BackBuffer` | 0x1A14 | **0x15C0** | `GetBackBuffer2` 0x193220 `mov esi, [ecx+eax*4+15C0h]`, eax = 0 for index 0 | `SetViewport` 0x1935A0 `cmp eax, [esi+15C0h]`; `CDevice_Init` passes it to `SetRenderTarget` (0x196A2F); the presentation setup 0x196167 fills `[+0x15C0 + i*4]` |
| `CDevice_FrontBuffer` | 0x1A18 | **0x15C4** | `GetBackBuffer2` 0x193205 `mov esi, [ecx+eax*4+15C0h]`, eax = 1 for index −1 | `SetViewport` 0x1935A8 `mov ecx, [esi+15C4h]`; the debugger block 0x196A89; XMV's `GetDisplayMode` 0x193070 |
| `CDevice_SwapCount` | 0x2478 | **0x2018** | `Swap` 0x194950/0x194990 `inc dword ptr [esi+2018h]`, returned at 0x1949C1 | `CDevice_KickOff` 0x192820 copies it to `[+0x1984]` (5558: +0x2478 → +0x1DE4); the debugger block 0x196A7C |
| `CDevice_Size` | 0x24A0 | **0x2040** | `Direct3D_CreateDevice` failure path 0x18F92B `mov ecx, 810h` / 0x18F930 `rep stosd` from the device | `D3DDevice_Release` 0x192EA9 `mov ecx, 810h` / `rep stosd`; 0x19FA10 + 0x2040 = 0x1A1A50, `D3D_Streams`, the next variable |
| `CDevice_Flags` | 0x8 | **0x8** | `Direct3D_CreateDevice` 0x18F8E0 `mov esi, dword_19FA18`, 0x18F8E7 `and eax, 10h`, 0x18F8EF `or esi, eax`, 0x18F904 store | `CDevice_KickOff` 0x192765 tests `[ecx+8]` (4, 2000h) and sets 2000h (0x1927D5); `DrawIndexedVertices` sets 800h (0x19512B) |
| `CDevice_Time` | 0x2C | **0x2C** | `CDevice_KickOff` no-hardware path 0x192811 `mov edx, [eax+2Ch]`, `sub edx, 2`, 0x19281A `mov [eax], edx` through the fence pointer `[+0x30]` (0x192814) | `D3D_SetFence` 0x192937..0x192940 adds 2; push buffer init 0x1924B2 starts it at 5; `SetTexture`/`SetStreamSource` stamp resources with it (0x193713, 0x191EBA) |
| `CDevice_PixelShader` | 0x784 | **0x36C** | `SetPixelShader` 0x195518 `mov eax, [ebx+36Ch]`, 0x195528 `mov [ebx+36Ch], eax` | `SetRenderState_TextureFactor` 0x1901E7 reads it |
| `CDevice_VertexShader` | 0x794 | **0x37C** | `SetVertexShader` 0x1922D8 `mov [esi+37Ch], edi` (object), 0x1922DE `mov [esi+380h], ebx` (handle) | `CDevice_Init` 0x1969FE stores the FVF shader 0x1A1C28 there; the viewport push helper 0x1908C6 and the vertex array setup 0x199497 read it |
| `CDevice_BackBufferScale` | 0x96C | **0x528** | 0x194440: 0x194449 `mov ecx, [eax+528h]` (X), 0x194443 `mov edx, [eax+52Ch]` (Y); the twin of 5558 0x249130's `[eax+0x96C]`/`[eax+0x970]` (0.974) | `SetRenderTarget` body scales the front buffer's width by `[+0x528]` (0x190C1B) and height by `[+0x52C]` (0x190C15) for the back buffer, as 5558's 0x245CC0 does; the presentation setup 0x196030 stores X = MultiSampleType bits 4–7 (0x1960FA) and Y = bits 0–3 (0x196113); 0x1949D0 saves and restores both around a scaled blit. `GetBackBufferScale` is not linked |
| `CDevice_Viewport` | 0xEE0 | **0xA90** | `SetViewport` 0x19368B `mov [esi+0A90h], ecx` (X); 0x193691/0x193697/0x19369D/0x1936A6/0x1936AF store Y, Width, Height, MinZ, MaxZ at +4..+20 | the viewport push helper reads X/Y/MinZ/MaxZ (0x1909AB, 0x1909C7, 0x190A60, 0x190A72) |
| `CDevice_ScreenSpaceOffset` | 0xEF8 | **0xAA8** | `SetScreenSpaceOffset` 0x193C13 `fstp [esi+0AA8h]` = x + 0.53125 (`flt 0x19DA38` = 0x3F080000), 0x193C23 `fstp [esi+0AACh]` = y + 0.53125 | the viewport push helper adds both (0x1909CF, 0x1909F0); `D3D_InitDefaultState` calls `SetScreenSpaceOffset(0, 0)` (0x195EF8) |
| `CDevice_AutoDepth` | 0x1A20 | **0x15CC** | `D3D_InitDefaultState` 0x195E90 `mov esi, [ebp+15CCh]`, `setne cl`, `push 8Fh` (0x195E9E): render state 143 = ZEnable | `CDevice_Init` 0x196A29 passes it to `SetRenderTarget` as the depth surface; the presentation setup 0x1961B9 stores the embedded depth surface `device + 0x1618` there |
| `CDevice_VBlankCallback` | 0x1DB8 | **0x1958** | callback setter 0x192EF0: 0x192EFA `mov [ecx+1958h], eax` | the vertical blank handler 0x199AFE `mov eax, [esi+190h]` (miniport + 0x190), `call eax` (0x199B25) |
| `CDevice_VBlankEvent` | 0x1DBC | **0x195C** | `BlockUntilVerticalBlank` 0x192F1B `mov dword ptr [eax+1960h], 0`, 0x192F27 `add eax, 195Ch` → `KeWaitForSingleObject` (ordinal 159) | the handler 0x199AF1 `lea eax, [esi+194h]` → `KeSetEvent` (145); `CMiniport_InitHardware` builds the KEVENT there (above) |
| `CDevice_DisplayFlags` | 0x1DDC | **0x197C** | display field query 0x193972 `test dword ptr [eax+197Ch], 1200000h` | the handler 0x199A9D tests miniport + 0x1B4 & 0x1000000; XMV's `GetDisplayMode` 0x193070 tests & 0x400000 |
| `CDevice_VBlankCount` | 0x1DE8 | **0x1988** | display field query 0x193965 `mov edx, [eax+1988h]` → the count | the handler 0x199A54..0x199A61 increments miniport + 0x1C0; XMV paces video on it (0x1BF9EA) |
| `CDevice_Field` | 0x1DF8 | **0x1998** | display field query 0x19397F `mov esi, [eax+1998h]`, field = (`== 0`) + 1 | the handler stores port 0x80C0 bit 5 there, miniport + 0x1D0 (0x199AC4/0x199AD3) |
| `CDevice_GammaRamps` | 0x1E04 | **0x19A4** | D3D debugger query 0x193C50, case 88000011h: 0x193E03 `mov eax, [ecx+1FACh]` (ramp index), 0x193E13 `lea esi, [edx+ecx+19A4h]`, copies 0xC0 dwords, ecx = `[0x19FA08]` | flip step 0x1999D3 `lea edx, [ecx+esi+1DCh]` = miniport + 0x1DC + slot * 0x300, loaded by 0x1997B2; 5558's debugger query reads `+0x1E04` at the same point (0x24848F) |
| `CDevice_GammaPending` | 0x2404 | **0x1FA4** | flip step 0x1999C3 `cmp dword ptr [esi+edi*4+7DCh], 1` (esi = miniport, edi = shown count & 1), cleared at 0x1999E2 | the mode set 0x1959F8, called with ecx = miniport (0x1969E9), sets it: 0x195AE2 `mov edx, [esi+7E4h]`, 0x195AEB `mov [esi+edx*4+7DCh], eax`. `SetGammaRamp` is not linked, so only the mode set ever raises it |

Every miniport-relative offset here (`+0x190`, `+0x194`, `+0x1B4`, `+0x1BC`, `+0x1C0`, `+0x1D0`,
`+0x1DC`, `+0x7DC`, `+0x7E4`) equals 5558's. 5558's vertical blank handler 0x251FF0 and 5233's
0x199A30 score 1.0. The flip step 0x199987 uses 5558 0x251F37's offsets on every line; it differs only
in register choice and in one global store 5558 adds. That is why every field from the miniport on sits
exactly 0x460 below 5558's.

### Globals, DSOUND, XPP

| key | 5558 | **5233** | proof in this image | also |
| --- | --- | --- | --- | --- |
| `DirtyFlags_Texture` | 0x4800 | **0x4800** | `SetTexture` 0x193777 `or eax, 4800h`, 0x19377D `mov dword_19F568, eax` | `SetPixelShader` 0x195536 `or ecx, 4800h` |
| `TextureState_Stage` | 32 | **32** | `SetTextureStageStateNotInline` 0x19079B `shl ecx, 5` / 0x1907A0 `add ecx, eax` → 0x1907AC `mov dword_19F570[ecx*4], eax` | the debugger query 0x193C50 indexes the same way (0x193CA8) |
| `Stream_Size` | 12 | **12** | `SetStreamSource` 0x191EAA `lea esi, [eax+eax*2]`, 0x191EAD `shl esi, 2` | `CDevice_UnInit` 0x196C14 `add edi, 0Ch` over 0xC0 bytes |
| `Stream_Stride` | 0x0 | **0x0** | `SetStreamSource` 0x191EF2 `mov dword_1A1A50[esi], eax` (Stride) | the vertex array setup 0x1994E8 reads the stride at `0x1A1A50[i*12]` |
| `Stream_Buffer` | 0x8 | **0x8** | `SetStreamSource` 0x191EF8 `mov dword_1A1A58[esi], edi` (vertex buffer) | vertex array setup 0x199529; `CDevice_UnInit` 0x196BF0 |
| `PixelShader_Definition` | 0x8 | **0x8** | `SetPixelShader` 0x195590 `mov edx, [eax+8]`, 0x1955B7, 0x1955CC `mov ebp, [eax+8]`, then reads the definition (`+0xEC`, `+0xD8`, `+0x20`...) | - |
| `CDirectSoundStream_Vtable` | 0x0 | **0x0** | constructor 0x1B6AD1: 0x1B6AEA `mov dword ptr [esi], offset 0x2004C4` | destructor 0x1B5BCE: 0x1B5BD6 `mov dword ptr [esi-4], offset 0x2004C4` (esi = stream + 4) |
| `CDirectSoundStream_Vtable2` | 0x4 | **0x4** | constructor 0x1B6AD9 `lea edi, [esi+4]`, 0x1B6AE3 `mov dword ptr [edi], offset 0x2004B8` | destructor 0x1B5BDD `mov dword ptr [esi], offset 0x2004B8` |
| `EffectsImage_Skip0` | 0x804 | **0x804** | parser 0x1B7710: 0x1B7729 `add eax, [ebx+804h]` | downloader 0x1B78F1 copies it, 0x1B791C `mov eax, [ebx+804h]` |
| `EffectsImage_Skip1` | 0x80C | **0x80C** | parser 0x1B7723 `mov eax, [ebx+80Ch]` | downloader 0x1B792E |
| `EffectsImage_Desc` | 0x818 | **0x818** | parser 0x1B7732 `lea esi, [ebx+eax*4+818h]`, count read at 0x1B7739 | downloader sends the image from `+0x818` (0x1B794C), length − 0x818 (0x1B7946) |
| `XPP_Current` | 0x0 | **0x0** | `XGetDevices` 0x1E7EEF `mov esi, [edx]`, returned | `XGetDeviceChanges` 0x1E7F30 `and ecx, [esi]` |
| `XPP_Changed` | 0x4 | **0x4** | `XGetDevices` 0x1E7EF1 `and dword ptr [edx+4], 0` | `XGetDeviceChanges` 0x1E7F0F `cmp [esi+4], eax`, 0x1E7F50 clear; the hot-plug updater 0x1E7EBD sets it (`or [ecx+4], eax` at 0x1E7ECA) |
| `XPP_Previous` | 0x8 | **0x8** | `XGetDevices` 0x1E7EF7 `mov [edx+8], esi` | `XGetDeviceChanges` 0x1E7F28 `mov ecx, [esi+8]`, re-copied at 0x1E7F54 |

The `CDirectSoundStream` vtable at `[stream + 0]` (0x2004C4) holds seven methods. Each scores 1.0
against 5558's `AddRef`, `Release`, `GetInfo`, `GetStatus`, `Discontinuity` and `Flush`, and `Process`
scores 0.775: 0x1B5C0F, 0x1B5C56, 0x1B5CA4, 0x1B5DA3, 0x1B5DF4 (`Process`), 0x1B5D0B, 0x1B5D58. That
confirms the two vtable offsets have the meaning `DirectSoundCreateStream`'s host body gives them. Those
names belong to `DsoundSymbols`; they are listed here only as evidence.

## Render and texture stage numbering: 5849's, no table

`D3d8StateSymbols` owns this question and reported that 5233 numbers render and texture stage states
exactly as 5849 does. Its proof is in `docs/d3d8-state-symbols.md`: the complex handler table
0x19D4E0, handlers storing their own 5849 slots, and dirty, default, simple-encode and TSS tables
identical to 5558's. So `sdk/xdk/5233/layout.toml` carries **no `RenderState_`/`TextureState_` table**,
and `sdk/runtime/xdk/layout.h` falls back to `gpu::kRs*`/`gpu::kTss*`. What I read on my own agrees:

- `SetRenderStateNotInline` 0x18FCF0: `cmp esi, 5Ch` (92 = `kRsDeferredFirst`) and `cmp esi, 88h`
  (136 = `kRsComplexFirst`), then `call [esi*4+19D4E0h]`.
- `D3D_RenderState` 0x19F770 runs 166 dwords (`kRsMax`) up to `D3D__pDevice` 0x19FA08, as 5558's
  0x2646B0..0x264948 does.
- `D3D_InitDefaultState` 0x195E30 sets states 57..165 (`mov edi, 39h`, `cmp esi, 1B4h`). It skips
  126, 127 and 154 (`cmp esi, 114h/118h/184h`), as 5558's skips `7Eh/7Fh/9Ah`. It sets 143 = ZEnable
  (`push 8Fh`), then `TSS(0, 0Ch, 4)` and `TSS(0, 10h, 2)`: ColorOp 12 = MODULATE, AlphaOp 16 =
  SELECTARG1. That is 5849's numbering, not 3925's `TSS(0, 0, 4)`/`TSS(0, 4, 2)`.
- `SetTextureStageStateNotInline` 0x190780 has 5558's splits (`cmp eax, 0Ch/16h/1Ch/1Dh/1Eh/1Bh`).
- `SetPixelShader` stores PSTextureModes into `[136]` (0x19560C) and passes `[148]` = TextureFactor to
  the TextureFactor handler 0x1901E0. The presentation setup stores MultiSampleMode into `[154]`
  (0x196148), and `SetRenderTarget` reads `[154]`/`[155]` (0x190C0F, 0x190D80).
- The 92-entry simple encode table, the 44 deferred dirty entries and the 22 texture stage dirty entries
  are byte-identical to 5558's (0x2E1FE0, 0x2E1DB0[92..135], 0x2E1EC8).

## `[data]`: each from one function, re-checked in a second

| name | address | first function | re-check (independent function) |
| --- | --- | --- | --- |
| `D3D_Device` | **0x19FA10** | `Direct3D_CreateDevice` 0x18F8EA `mov edi, offset 0x19FA10` → `D3D__pDevice` (0x18F8F4), `CDevice_Init` (0x18F90A), `*ppDevice` (0x18F94B) | `SetRenderState_Simple` 0x18FCC0 pushes through `[0x19FA10]`; game code's inlined pushes (0x152B5D); the boot fault's `ecx = 0x19FA10 + 0x17C8` |
| `D3D_pDevice` | **0x19FA08** | `Direct3D_CreateDevice` 0x18F8F4 `mov dword_19FA08, edi`; cleared on failure (0x18F935) | `D3DDevice_Release` 0x192EB0 clears it; every `D3DDevice_*` body loads it (`SetTexture` 0x1936F5, `SetStreamSource` 0x191E90; 110 references) |
| `D3D_DirtyFlags` | **0x19F568** | `SetTexture` 0x193771..0x19377D `or eax, 4800h` | `SetStreamSource` 0x191EEC/0x191F04 (`or 40h`/`70h`); `SetTransform` 0x192DA6/0x192DB8; `SetRenderStateNotInline` 0x18FD28 |
| `D3D_DeferredTextureState` | **0x19F570** | `SetTextureStageStateNotInline` 0x1907AC `mov dword_19F570[ecx*4], eax` (`stage*32 + type`) | debugger query 0x193C50, case 8Axxxxxxh: 0x193CA8 `mov edx, dword_19F570[eax*4]` after `shl eax, 5` |
| `D3D_RenderState` | **0x19F770** | `SetPixelShader` 0x1955FF `mov edi, offset 0x19F770` + `rep movsd` of 39h dwords; `[136]` at 0x19560C | `SetRenderStateNotInline` 0x18FD0D/0x18FD32 `mov dword_19F770[esi*4], ...`; debugger query 0x193C74 |
| `D3D_SimpleRenderStateEncode` | **0x1EE768** | `SetRenderStateNotInline` 0x18FCFA `mov ecx, dword_1EE768[esi*4]` for state < 5Ch → `SetRenderState_Simple` | **only reader in the image**, so re-checked by content: 92/92 dwords identical to 5558's 0x2E1FE0 (entry 0 = 0x40260); it starts where the deferred dirty table `0x1EE548[92..135]` ends, and the next object (vtable `0x1EE8D8`) begins 92 dwords later |
| `D3D_Streams` | **0x1A1A50** | `SetStreamSource` 0x191EF2/0x191EF8 | vertex array setup 0x199450 (0x1994E8, 0x199529, 0x199541); `CDevice_UnInit` 0x196BF0 (release ×16) and 0x196C7E (`mov edi, offset 0x1A1A50`, `rep stosd` ×30h) |
| `DSound_StreamVtable` | **0x2004C4** | `CDirectSoundStream` constructor 0x1B6AEA `mov [esi], offset 0x2004C4` | destructor 0x1B5BD6 `mov [esi-4], offset 0x2004C4`; its 7 entries are 5558 0x2F9038's twins |
| `DSound_StreamVtable2` | **0x2004B8** | constructor 0x1B6AE3 `mov [edi], offset 0x2004B8` (edi = stream + 4) | destructor 0x1B5BDD `mov [esi], offset 0x2004B8` |
| `XPP_GamepadType` | **0x1E6C30** | title → `XGetDevices` (push 0x12B96D) and `XInputOpen` 0x1E7B7C (0x12B998, 0x12BA8C) | title → `XGetDeviceChanges` (0x12BA05); its `XInitDevices` preallocation table (0x12B958); XID class record 0x1E6C68 `+4` |
| `XPP_MemoryUnitType` | **0x1E6CE0** | second entry of the title's `XInitDevices` preallocation table (0x12B960) | MU driver init 0x1E6E0C `push 1E6CE0h; call 0x1E71CB`. The result + 1 (at most 8) is how many device objects the init then creates, named `\Device\MU_0`, `MU_1`, ... from 0x1EE42C (`IoCreateDevice` loop 0x1E6E36..0x1E6E5D). It is the same instruction as 5558's 0x2D9EEC `push 0x2D9DC0` |
| `D3D_IndexData` | **0 (not emitted)** | - | No instruction reads or writes it. `SetIndices`/`GetIndices` are not linked, and the one `DrawIndexedVertices` call (0x154255) passes its own index pointer. 0x19F564 is where 5558's layout would put it (5558 0x2644A4 = DirtyFlags − 4), but nothing proves it. The host needs it only inside its `SetIndices` body, which this title never reaches |

`XtlidXapiCrtSymbols` measured the same two XPP addresses independently and emits them in its own
file. The merge tool accepts one name at one address from two files.

## Staging

`D3D_RenderState` is what lets the host `Direct3D_CreateDevice` get past its `XDK_REQUIRE`. After
that, `ApplyDefaultStates` and `SetComplex` write the guest array at the indices the layout gives. In
Fuzion Frenzy (3925) that would have written 5849 indices into a 144-entry array ending at the device,
so its file was staged. Here:

- the numbering is 5849's (above), so the host's indices are this build's;
- the array is 166 dwords, exactly `gpu::kRsMax`, and ends at `D3D__pDevice`;
- every CDevice offset the host writes (`SetupPresentation`, `VerticalBlank`, `PresentFrame`,
  `SetTexture`, ...) is proven above, and none keeps a 5558 value.

So **`config/found-d3d8-data.toml` is not staged.**

## Notes for whoever wires the host bodies

- **Vertical blank callback.** The handler 0x199A30 builds `{[miniport+0x1C0] count,
  [miniport+0x1BC] swaps shown, flag}` on the stack. It then calls the callback with a pointer to it,
  cdecl (`lea ecx, [esp+1Ch+var_C]; push ecx; call eax; add esp, 4`, 0x199B18..0x199B27). That is
  5849's `D3DVBLANKDATA*`, which `sdk/runtime/xdk/d3d8.cpp` `VerticalBlank` already passes. This is not
  3925's by-value count. The title does register one: 0x155383 passes 0x13960 to the setter 0x192EF0,
  and 0x13960 is a bare `retn`.
- **VBlank event header.** `CMiniport_InitHardware` builds the KEVENT at miniport + 0x194 = device +
  0x195C as Type 0, Size 4, SignalState 1. That is exactly the `0x00040000` / `1` that
  `SetupPresentation` writes.
- **Gamma.** `SetGammaRamp` is not linked. The only writer of `GammaPending` is the guest mode set
  0x1959F8. It is reached from `CDevice_Init` (0x1969EB) and `D3DDevice_Reset` 0x193140 (0x1931AF),
  and the host replaces both once `Direct3D_CreateDevice` and `D3DDevice_Reset` are named. So the
  host's pending-ramp path should never fire for this title.
- **Back buffer scale.** The presentation setup derives it from `D3DPRESENT_PARAMETERS.MultiSampleType`
  (X = bits 4–7, Y = bits 0–3). The host's 1.0/1.0 is the no-multisample value.
- **Guest readers of host-written fields.** Several functions the host leaves alone read the fields the
  host writes, so those offsets have to be 5233's. None of the display field query 0x193960,
  `GetDisplayMode` 0x193070 or the callback setter 0x192EF0 is a name in `config/game.toml`
  `[symbols]`, and each keeps running as guest code. XMV paces its frames on the
  first (call at 0x1BF9EA) and reads the second at creation (0x1BF136); `XgrphXmvKernelCoverage`
  pointed this out. With 5558's values the host would write `VBlankCount` at 0x1DE8 while the movie
  read 0x1988, and the movie clock would never advance.
