# D3D8 core symbols — The Sims (USA), XDK 5233

This file covers the device, push-buffer, fence, draw, target, resource, shader and presentation
half of the `D3D` section (`0x18F680-0x1A1DA0`, code to `0x19E934`) of `out/game.exe`.
`D3d8StateSymbols` owns the render-state and texture-stage setters (`docs/d3d8-state-symbols.md`),
and `D3d8DataLayout` owns the `[data]` symbols and `sdk/xdk/5233/layout.toml`
(`docs/layout-5233.md`).
The machine-readable result is `config/found-d3d8-core.toml`.

## Result

**47 of the 69 target names are proven and written: 35 new ones, and the 12 constant-matcher
anchors re-proven at the address `config/game.toml` already gives them. The other 22 are not
linked into this image.** The image keeps only the D3D8 functions the title references, so its
`D3D` section has 266 functions where Bustin' Out's 5558 section has 758. Each absent name was
looked for by its body, its constants and its callers ("Not emitted").

> **The file is not staged; its preconditions are met.** All of these host bodies run on the device
> the host `Direct3D_CreateDevice` builds. That body sizes, clears and fills the device through
> `sdk/xdk/5233/layout.toml`, and needs the seven D3D `[data]` names. 5233's `CDevice` is laid out
> differently from 5558's; one example is that it is `0x2040` bytes, not `0x24A0`. I measured every
> offset these bodies read independently. `D3d8DataLayout`'s now-proven `layout.toml` carries the
> same values for every one of them, and `config/found-d3d8-data.toml` (not staged) carries the
> data. "Wiring preconditions" below has the table. Merge this file together with the data file;
> without the data, the host `Direct3D_CreateDevice` stops at its `XDK_REQUIRE` with a loud abort.

> **The boot fault (`fault at guest address FD001804` on thread 18) is the guest's own
> `Direct3D_CreateDevice` at `0x18F8B0` doing what it does on a console.** It runs
> `CDevice_Init` `0x196590`, which runs the NV2A miniport init `0x19A93D`, which calls
> `CMiniport_MapRegisters` `0x19A44A`. That function stores `0xFD000000` as the register base and
> faults reading PCI configuration word `0xFD001804` at `0x19A450`.
> `Direct3D_CreateDevice = 0x18F8B0` is in the file. Once the name is merged with its data and
> layout, the host body replaces the whole chain, and nothing else in the image reaches it. The
> frame-by-frame mapping is in "The boot fault".

> **API shape of XDK 5233. The host must call these forms:**
> - **Presentation is `D3DDevice_Swap(Flags)` at `0x1948F0`, `retn 4` at `0x1949C8`. There is no
>   four-argument `D3DDevice_Present` (`retn 10h`).** The title presents once a frame from its
>   render-thread command loop with `push 0; call D3DDevice_Swap` (`0x156B18`/`0x156B1A`).
> - **The back buffer comes from `D3DDevice_GetBackBuffer2(BackBuffer)` at `0x1931F0`, `retn 4`
>   (`0x193215`, `0x193230`), and the depth surface from
>   `D3DDevice_GetDepthStencilSurface2()` at `0x193570`, plain `retn` (`0x193583`, `0x19358D`).**
>   These are the newer forms. The 3925 forms `GetBackBuffer(BackBuffer, Type, ppSurface)` and
>   `GetDepthStencilSurface(ppSurface)` do not exist in this image.
> - **`D3DDevice_Reset` EXISTS at `0x193140`, `retn 4` (`0x193186`, `0x1931EA`), and the title calls
>   it**, from `0x152869` and `0x152885`, every time it switches the presentation interval between 1
>   and 2. Its body is the one the Bustin' Out boot crash came from:
>   1. `D3D_KickOffAndWaitForIdle`
>   2. a miniport poll on `CDevice + 0x17C8`, which is the miniport's offset here, not `+0x1C28`
>   3. frame-buffer teardown and re-creation
>   4. the miniport mode set
>   5. `SetRenderTarget` with the back-buffer and auto-depth fields (`+0x15C0`, `+0x15CC`)
>   6. `D3DDevice_Clear(0, NULL, 3, 0, 1.0f, 0)`
>
>   Left unreplaced, the guest mode set writes NV2A registers through the miniport's register base
>   at `CDevice + 0x17C8`, which is NULL on the host. **This SDK copy already has the host body**,
>   `HLE_STDCALL(D3DDevice_Reset, 1)` at `sdk/runtime/xdk/d3d8.cpp:692`, which shares
>   `SetupPresentation` with `Direct3D_CreateDevice`. What was missing is the `[symbols]` entry,
>   and it is in this file.
> - **`D3DDevice_InsertCallback` = `0x1926F0` is confirmed by its body.** It writes the push token
>   `0x00081D8C` at `0x19270B` and returns with `retn 0Ch` at `0x192733` and `0x192758`. The title
>   uses it twice, `InsertCallback(1, 0x152590, ctx)` at `0x156B01` and `0x152829`. **No host body
>   for it exists anywhere in this tree:** neither `sdk/runtime` nor `src/` contains
>   `InsertCallback`. The name is already in `config/game.toml`, but without a strong definition the
>   guest body still runs. Its token lands in the scratch push buffer, which the host walks for draws
>   only, so the title's callback never fires. That is the Bustin' Out silent deadlock, with every
>   guest thread idle-waiting. The port needs the body Bustin' Out carries in
>   `simsbustinout/src/game/hooks.cpp:48`:
>   `HLE_STDCALL(D3DDevice_InsertCallback, 3) { if (a[1]) kernel::CallGuest(ctx, a[1], {a[2]}); return 0; }`.

## This build's API shape: the evidence

### Presentation: `D3DDevice_Swap`, not `D3DDevice_Present`
- `0x1948F0` is instruction for instruction the 5558 `D3DDevice_Swap` at `0x2495F0`. The two bodies
  have the same normalized instruction sequence, ratio 0.993. Its steps:
  1. It takes `Flags` from `[esp+0Ch]`, defaulting to 5 (`0x19491A`), and tests device flag `0x4000`.
  2. It calls `SetFence(2)`, at `0x19492C`/`0x19496C`.
  3. It calls `BlockOnTime(flip time [dev + ((swap - 1) & 1) * 4 + 0x1524], 1)`. 5558 uses `+0x1974`.
  4. It increments the swap count with `inc dword [esi+2018h]` (`0x194950`, `0x194990`). 5558 uses
     `+0x2478`.
  5. It runs the flip helpers `0x1945C0`, `0x1947A0` and `0x1948B0`, the 5558 `0x2492B0`, `0x2494A0`
     and `0x2495B0`. `0x1948B0` applies a pending mode change through `0x193FC0`.
  6. It returns the swap count (`0x1949C1`) with **`retn 4` at `0x1949C8`**.
- **The once-a-frame call.** The title draws on a render thread. Its command loop is `0x156A40`,
  a 6-way switch at `0x156A7B`:

  | Case | What it does |
  | --- | --- |
  | 1 | `0x152700` |
  | 2 | `0x152900` |
  | 3 | `D3DDevice_InsertCallback(1, 0x152590, obj)` |
  | **4** | **`push 0` at `0x156B18`, `call D3DDevice_Swap` at `0x156B1A`** |
  | 5 | `0x1527F0`, a flush with `InsertCallback` plus `D3DDevice_KickPushBuffer` |
  | 6 | `0x152840`, the presentation-interval change that calls `D3DDevice_Reset` |

  The only other `Swap` call site in the title is `0x158363` in `0x1581B0`. It is followed by
  `D3DDevice_KickPushBuffer` (`0x158368`) and a `jmp $` (`0x158371`): a screen that presents once
  and halts, called from 11 places.
- **There is no 4-argument `D3DDevice_Present`.** The 3925 `Present` body is `SetFence(2)`, a
  swap-count spin and the flip. In this image `SetFence` is called with 2 only by `Swap`
  (`0x19492C`, `0x19496C`). Its other callers are `BlockOnTime` (0), `MakeRequestedSpace` (1),
  `DrawVerticesUP` (1), `DrawIndexedVertices` (1), `End` (1) and the Swap helper `0x1948B0` (0). The
  flip helpers have `Swap` as their only caller. No `retn 10h` function in the section calls
  `SetFence` at all. Those functions are `DrawVerticesUP` `0x194F00`, `CreateVertexShader`
  `0x191B20`, the surface-lock wrapper `0x195900`, and surface and miniport helpers (`0x1957C0`,
  `0x195810`, `0x195840`, `0x196CF0`, `0x198AB0`, `0x19A280`, `0x19A5D1`, `0x199DA4`, `0x19C652`).
- `config/game.toml` has no `D3DDevice_Present` key, and it does not need one.

### Back buffer and depth: the `...2` forms
- `0x1931F0` is identical to the 5558 `D3DDevice_GetBackBuffer2` at `0x2463E0` (ratio 1.0).
  - It takes one stack argument and compares it with -1 (`0x1931F4`). It returns
    `[dev + idx*4 + 0x15C0]`, where idx is 1 for -1 (the front buffer, `0x193205`), 0 for 0 and 2
    otherwise (`0x193220`).
  - It AddRefs the surface through `0x18FAD0` (5558 `0x2449F0`) and returns it in `eax`.
  - **`retn 4`** at `0x193215` and `0x193230`.
- `0x193570` is identical to the 5558 `D3DDevice_GetDepthStencilSurface2` at `0x246B20` (ratio
  1.0). It has no arguments, returns `[dev+0x15B8]` AddRef'd, or NULL, and ends with a **plain
  `retn`** (`0x193583`, `0x19358D`).
- The title's call sites, in the device bring-up `0x156900`, are the newer ABI:
  - `push 0` at `0x1569C7`, `call 0x1931F0` at `0x1569C9`, then `mov [esi+730h], eax` at
    `0x1569CE`. One argument, and the result comes back in `eax`.
  - `call 0x193570` at `0x1569D4`, with no arguments pushed. It is then followed by the inlined
    HRESULT wrapper `setnz cl; dec ecx; test ecx, 88760866h` (D3DERR_NOTFOUND, `0x1569D9-0x1569E7`).
- These are exactly the host's `HLE_STDCALL(D3DDevice_GetBackBuffer2, 1)` and
  `HLE_STDCALL(D3DDevice_GetDepthStencilSurface2, 0)`. The 3925-form host bodies,
  `D3DDevice_GetBackBuffer` with 3 arguments and `D3DDevice_GetDepthStencilSurface` with 1, must
  not be wired.

### `D3DDevice_Reset` exists, at `0x193140`
- It is instruction for instruction the 5558 `D3DDevice_Reset` at `0x245F90` (ratio 0.992), and
  its measurements match the 5558 signature exactly: `retn 4`, no register inputs, 9 calls, `0xAD`
  bytes against `0xA8`. The body, step by step:

  | Address | Step | 5558 twin |
  | --- | --- | --- |
  | `0x19314A` | `call D3D_KickOffAndWaitForIdle` | `0x24D610` |
  | `0x19314F` | `lea ebp, [edi+17C8h]`, the embedded miniport | `[edi+1C28h]` |
  | `0x193155-0x19315E` | spin on `0x199810(ecx = miniport)` until it returns 0. That is a read of miniport fields `+0x1BC` and `+0x174/+0x180` | `0x251D40` |
  | `0x193162` | free the frame buffers, `0x195F10(device)` | `0x24FA10` |
  | `0x19316E` | `InitializeFrameBuffers(device, pPresentationParameters)`, `0x196030`; on failure free them again and return the HRESULT | `0x24FB40` |
  | `0x193190` | `0x18FFC0([dev+0x15C4])`, the front buffer's pitch in bytes (from its Size dword, or width × bytes per pixel) | `0x245A00([dev+0x1A18])` |
  | `0x1931AF` | the miniport mode set `0x1959F8(ecx = miniport; Width, Height, RefreshRate, Flags, Format, PresentationInterval, pitch)`, pushed at `0x193195-0x1931AC` | `0x24F204` |
  | `0x1931CB` | `D3D_SetRenderTargetInternal([dev+0x15C0], [dev+0x15CC], 0x19D6D0)`: back buffer, auto depth, and the full-target viewport | `D3DDevice_SetRenderTarget([+0x1A14], [+0x1A20])` |
  | `0x1931DF` | `D3DDevice_Clear(0, NULL, 3, 0, 1.0f, 0)` | `0x24602A` |
  | `0x1931EA` | **`retn 4`** | |
- **The title calls it.** `0x152840` is the render thread's case 6. If the command asks for it, it
  first calls `D3DDevice_BlockUntilVerticalBlank` (`0x152852`). Then, for mode 1 or 2, it stores
  the mode in `this+0x2C04` and calls `D3DDevice_Reset(this+0x2BD4)` (`0x152869`, `0x152885`).
  `this+0x2BD4` is the title's `D3DPRESENT_PARAMETERS`, which it also passed to `CreateDevice`.
  `+0x2C04` is that structure's `+0x30`, `FullScreen_PresentationInterval`. The device bring-up
  `0x156900` sets it to 2 before `CreateDevice` (`0x1569B0`).
- **Unreplaced, it crashes the way Bustin' Out's did.** The mode set `0x1959F8` and the frame-buffer
  code drive the NV2A through the miniport at `CDevice + 0x17C8`, whose field 0, the register base
  that `CMiniport_MapRegisters` fills, is NULL on a host-created device.
- **The host body already exists**, `HLE_STDCALL(D3DDevice_Reset, 1)` at
  `sdk/runtime/xdk/d3d8.cpp:692`. It reads `pp+0x00/0x04/0x08/0x0C/0x10/0x20/0x24/0x28/0x2C/0x30`.
  This build's guest body reads the same offsets: it passes `[esi]`, `[esi+4]`, `[esi+28h]`,
  `[esi+8]`, `[esi+2Ch]` and `[esi+30h]` to the mode set at `0x193195-0x1931AC`. It reuses the
  frame surfaces when the parameters are unchanged, which matters here because this title calls
  Reset at every interval switch.

### `D3DDevice_InsertCallback` at `0x1926F0`
This is the address the constant matcher found. I confirmed it by reading the body, which is the
5558 `0x24D030` byte for byte (ratio 1.0):
- `push esi; mov esi, D3D_pDevice`, then `MakeSpace` if the push buffer is full (`0x1926FE`).
- `mov dword [eax], 81D8Ch` at `0x19270B`. That is the callback token, with `[esp+0Ch]` (pCallback)
  at `+4` and `[esp+10h]` (Context) at `+8`.
- `[esp+8]` (Flags) selects either `0x40100, 6` or `0x40110, 0, 0x40100, 7`.
- **`retn 0Ch`** at `0x192733` and `0x192758`.

The title uses it twice. Neither use works without a host body:
- **Render-thread case 3**, `0x156AF2-0x156B01`: `push obj; push 0x152590; push 1; call 0x1926F0`.
- **`0x1527F0`, render-thread case 5**: it clears stream sources 0..4, then calls
  `InsertCallback(1, 0x152590, this+0x68)` (`0x152829`) and `D3DDevice_KickPushBuffer`
  (`0x15282E`).

The callback `0x152590` is `mov ecx, [esp+4]; mov eax, [ecx]; jmp [eax+0Ch]`, which calls virtual
function 3 of the context object.

As stated above, the host has **no** `D3DDevice_InsertCallback` body in this tree.

## The boot fault

The Linux build of `config/game.toml` (24 names) faulted on guest thread 18:
`fault at guest address FD001804`, `eax 001A1374 ecx 001A11D8 edx 00000180 ebx 00000001 esi 001A11D8 edi 83100060`.

**The faulting instruction is `0x19A450`, `mov eax, ds:0FD001804h`, in `0x19A44A`.** That function is
`CMiniport_MapRegisters` (the XDK's internal name for it is my [inference]); its 5558 twin is
`0x2529F6`, and 3925's is quoted in `fuzion frenzy/docs/boot-crash.md`. Its whole body:

```
0x19A44A  mov dword [ecx], 0FD000000h   ; register base into miniport field 0 (succeeded: ecx is in the image)
0x19A450  mov eax, ds:0FD001804h        ; NV2A PCI command register  <-- fault
0x19A455  or  eax, 4                    ; bus master
0x19A458  mov ds:0FD001804h, eax
0x19A45F  mov dword ds:0FD600140h, 0    ; PCRTC interrupt enable
0x19A469  mov dword ds:0FD009140h, 0    ; PTIMER interrupt enable
0x19A473  inc eax / ret                 ; TRUE
```

The registers match this exactly:
- `ecx = esi = 0x1A11D8` is `D3D_Device` `0x19FA10 + 0x17C8`, the embedded miniport.
  `CDevice_Init` computes it at `0x196643`, `add esi, 17C8h`.
- `eax = 0x1A1374` is `miniport + 0x19C`, from `lea eax, [esi+19Ch]` at `0x19A978` in the caller.
- `ebx = 1` comes from `inc ebx` at `0x19A97E`.
- `edi = 0x83100060` is left over from `CDevice_Init`'s `rep stos` over its `0x60`-byte
  contiguous allocation at `0x196605-0x19660C` (base `0x83100000`, cleared from `+0x20`).

The live call chain, from the call instructions:

| Return address | Inside | Call instruction | Status |
| --- | --- | --- | --- |
| `0x19A9A8` (not in the printed list) | `CMiniport_InitHardware` `0x19A93D` | `0x19A9A3 call 0x19A44A` | live, the innermost frame |
| `0x196650` | `CDevice_Init` `0x196590` | `0x19664B call 0x19A93D` (`ecx = device+0x17C8`) | live |
| `0x18F90F` | `Direct3D_CreateDevice` `0x18F8B0` | `0x18F90A call CDevice_Init` (`ecx = 0x19FA10`, arg pPP) | live |
| `0x1569C3` | title `0x156900`, the device bring-up | `0x1569BE call Direct3D_CreateDevice(0, HAL, 0, 0x40, pPP, &dev)` | live |
| `0x12A9E3` | title `0x12A8D0` | `0x12A9DE call 0x156900` | live |

Every value in the reported list:

| Value | Function containing it | What it is |
| --- | --- | --- |
| `0x1924F8` | `CDevice_InitPushBuffer` `0x192460` | **Stale.** The return address of its call to the allocator `0xCA252` (xtlid `0x2002D`). That call finished before the miniport init. It sits in `CMiniport_InitHardware`'s uninitialised locals (`sub esp, 10h` at `0x19A940`). `0x192460` allocates the push buffer, `MmAllocateContiguousMemoryEx([0x1A1D58])` at `0x192477`, and sets `[dev+0]` to the push pointer, `[+4]` to the threshold, `[+0x24]`/`[+0x28]` to base and end, and `[+0x2C]` to 5. It is called from `CDevice_Init` at `0x196612`. |
| `0x196650` | `CDevice_Init` `0x196590` | **Live.** Returns from the call to `CMiniport_InitHardware` `0x19A93D`. |
| `0x19FA10`, twice | none: this is data | `D3D_Device`, the static `CDevice`. One copy is `CDevice_Init`'s saved `this` (`mov [esp+14h], ecx` at `0x1965A3`); the other is the `edi` it saved with `push edi` at `0x1965FE`, which `Direct3D_CreateDevice` had set to `&device` at `0x18F8EA`. |
| `0x19598A` | `0x19597F`, the display-mode table lookup (`0xB9` entries of 12 bytes at `0x19DC10`) | **Stale.** Returns from the call to `0x195960`, the cached `AvSendTVEncoderOption(0, 6, 0, &av)` query (`0x195973`). It was left behind by the title's IDirect3D8 mode queries, called from the same `0x12A8D0` before `CreateDevice` (`0x12A906 call 0x18F690`, `0x12A941 call 0x18F730`). `0x18F690` and `0x18F730` are identical to 5558's `0x243D40` and `0x243DE0` (ratio 1.0): a mode count (`retn 4`) and a mode enumeration (`retn 0Ch`). By shape they are `GetAdapterModeCount` and `EnumAdapterModes` [inference]. |
| `0x18F90F` | `Direct3D_CreateDevice` `0x18F8B0` | **Live.** Returns from the call to `CDevice_Init`. |
| `0x13E701`, `0x13E9AC`, `0x13EA43`, `0x127363` | title `0x13E6A0`, `0x13E900`, `0x13EA30`, `0x127349` | Each follows a call: `0x13E6A0 -> 0x175BE0`, `0x13E900 -> 0x13E510`, `0x13EA30 -> 0x13E900`, `0x127349 -> 0x13EA30`. **None is on the live chain:** `0x156900`'s live caller is `0x12A8D0` (return `0x12A9E3`), and `Direct3D_CreateDevice`'s only caller is `0x156900`. These slots hold leftover values. Not D3D. |
| `0x1569C3`, `0x12A9E3` | title `0x156900`, `0x12A8D0` | **Live**, see the chain above. |
| `0x12F76B`, `0x12FB30`, `0x151D5C`, `0x1294DE`, `0x14B5A9` | title | Each follows a call (`call [edx+0Ch]`, `call [edx+2Ch]`, `call 0x12FB10`, `call [eax+0Ch]`, `call [eax+4]`). This fits the title's outer frames from the thread entry `0x14B5A0` down to `0x12A8D0`, but I did not trace the indirect calls. Not D3D. |
| `0x14B5A0` | title `0x14B5A0` | The thread entry itself (its first byte), not a return address. |
| `0xCB617` | XAPI `.text` `0xCB5A5` | Follows `call [ebp+8]`, the XAPI thread start calling the thread routine. This is the outermost live frame. |
| `0xCB81A`, `0xCB851` | XAPI `0xCB808` and `0xCB82E` (xtlid `0x2008C`, `0x200D5`) | **Stale.** Returns from `NtReleaseSemaphore` (`0x1EE568`) and `NtWaitForSingleObjectEx` (`0x1EE56C`) inside the XAPI semaphore and wait wrappers. |
| `0x179FC4` | `sub_179FC4` | Not preceded by a call. It is the first byte of a recompiled function, not a return address. |

**What fixes it.** `CMiniport_MapRegisters` `0x19A44A` has one caller, `CMiniport_InitHardware`
`0x19A93D`. That function has one caller, `CDevice_Init` `0x196590`. That function has one caller,
`Direct3D_CreateDevice` `0x18F8B0`. All four were checked with IDA cross-references. With
`Direct3D_CreateDevice = 0x18F8B0` merged, the host body runs instead, and none of the four is
reachable. `0x19A44A` and `0x19A93D` are XDK-internal and have no `[symbols]` key; they need no
host body of their own.

The host `Direct3D_CreateDevice` has two requirements, and both are now met:
1. The seven D3D `[data]` symbols, in `config/found-d3d8-data.toml`. Without them it fails its
   `XDK_REQUIRE` and aborts loudly, which is safe.
2. A correct 5233 layout. With the provisional 5558 values it would have corrupted memory silently;
   `sdk/xdk/5233/layout.toml` now holds the measured 5233 values ("Wiring preconditions").

The other console-hardware paths that become live once a host device exists are covered by this
file too:
- `CDevice_KickOff` writes `[[dev+0x17C8]] + 0x100410`.
- `D3D_MakeRequestedSpace` reads `[[dev+0x4F8]] + 0x324C`.
- `Swap`'s flip helpers and `D3DDevice_Reset`'s mode set reach the miniport.

Merge the file as a unit.

## Wiring preconditions

Every host body this file selects depends on `sdk/xdk/5233/layout.toml`. When I started, that file
was the PROVISIONAL copy of 5558's values. `XDK_REQUIRE` only checks that a key is present, so the
wrong values would have passed, and I had this file staged on that basis. `D3d8DataLayout` has
since proven the file (no PROVISIONAL header, every key proven). For every key below it carries
exactly the value I measured, so the file is no longer staged. The values the host bodies read,
measured in this image:

| Key | 5558 value (the provisional file) | 5233, measured; `layout.toml` now agrees | Proving instruction(s) |
| --- | --- | --- | --- |
| `CDevice_Size` | `0x24A0` | **`0x2040`** | `Direct3D_CreateDevice` failure path `mov ecx, 810h; rep stos` (`0x18F92B`/`0x18F930`); `D3DDevice_Release` the same (`0x192EA9`/`0x192EBA`) |
| `CDevice_Flags` | `0x8` | `0x8` | `Direct3D_CreateDevice` `0x18F904` ORs `BehaviorFlags & 0x10` into `[0x19FA18]` |
| `CDevice_Push` / `PushThreshold` | `0x0` / `0x4` | `0x0` / `0x4` | every pusher, e.g. `InsertCallback` `0x1926F7`/`0x1926F9`; title inline pusher `0x152ED7`/`0x152FD6` |
| `CDevice_Time` | `0x2C` | `0x2C` (fence pointer `+0x30`) | `D3D_KickOffAndWaitForIdle` `0x192C85`; `D3D_SetFence` `0x19293A` adds 2 |
| `CDevice_RenderTarget` | `0x1A04` | **`0x15B4`** | `D3D_SetRenderTargetInternal` `0x190BE0` stores it at `0x190E8A`; teardown `0x195F33` |
| `CDevice_Depth` | `0x1A08` | **`0x15B8`** | stored at `0x190EAF`; `GetDepthStencilSurface2` reads it at `0x193576` |
| `CDevice_BackBuffer` / `FrontBuffer` | `0x1A14` / `0x1A18` | **`0x15C0` / `0x15C4`** | `GetBackBuffer2` `[dev+idx*4+0x15C0]` (`0x193205`, `0x193220`); `CDevice_Init` publishes `[+0x15C4]` (`0x196A89`) where 5558 publishes `[+0x1A18]` |
| `CDevice_AutoDepth` | `0x1A20` | **`0x15CC`** | `D3D_InitDefaultState` `0x195E90` (ZEnable `0x8F`); `D3DDevice_Reset` `0x1931B8` |
| `CDevice_ZScale` | `0x948` | **`0x50C`** | `0x190EBD lea eax, [esi+50Ch]` then `0x197850`, which stores `65535.0` / `16777215.0` / `511.9375` / `1e30` by depth format |
| `CDevice_SuperSampleX/Y` | `0x95C` / `0x960` | the scale pair is **`0x518` / `0x51C`** | stored by `0x1910F1`/`0x1910E9`; `D3DDevice_SetScissors` multiplies rects by them (`0x193A71`, `0x193A77`). 5233's `SetViewport` does not scale; see `D3DDevice_SetViewport`. |
| `CDevice_Transforms` | `0xC60` | **`0x810`** | `D3DDevice_SetTransform` `0x192D96 lea edi, [ecx+ebx+810h]` |
| `CDevice_Textures` | `0xF88` | **`0xB38`** | `D3DDevice_SetTexture` `0x193700` (read), `0x193739` (store) |
| `CDevice_Palettes` | `0xF98` | **`0xB48`** | `D3DDevice_SetPalette` `0x1938AD`, `0x1938E5` |
| `CDevice_VertexShader` | `0x794` | **`0x37C`** (handle `+0x380`) | `D3DDevice_SetVertexShader` `0x1922D8`/`0x1922DE`; `CDevice_Init` stores the FVF shader `0x1A1C28` there at `0x1969FE` |
| `CDevice_Viewport` | `0xEE0` | **`0xA90`** | `D3DDevice_SetViewport` stores X..MaxZ at `0x19368B-0x1936AF` |
| `CDevice_ScreenSpaceOffset` | `0xEF8` | **`0xAA8`** | `D3DDevice_SetScreenSpaceOffset` `0x193C13`/`0x193C23` |
| `CDevice_VBlankEvent` | `0x1DBC` | **`0x195C`** | `D3DDevice_BlockUntilVerticalBlank` `0x192F27` waits on it and clears `+0x1960` first (`0x192F1B`) |
| `CDevice_VBlankCallback` | `0x1DB8` | **`0x1958`** | the setter `0x192EF0` (5558 `0x245450`) stores its argument there |
| `CDevice_SwapCount` | `0x2478` | **`0x2018`** | `D3DDevice_Swap` `inc [esi+2018h]` (`0x194950`), returns it (`0x1949C1`); `CDevice_KickOff` copies it to `+0x1984` (`0x192820`/`0x192826`) |
| `CDevice_BaseVertex` | `0x1C` | `0x1C` | `D3DDevice_DrawIndexedVertices` `0x19510E mov eax, [esi+1Ch]` |
| `DirtyFlags_Texture` | `0x4800` | `0x4800` | `D3DDevice_SetTexture` `0x193777 or eax, 4800h` |
| `CDevice_GammaRamps` | `0x1E04` | **`0x19A4`** (miniport `+0x1DC`, the same miniport-relative offset as 5558) | the vertical-blank handler `0x199960` (`esi` = miniport) loads the ramp from `esi + idx*0x300 + 0x1DC` (`0x1999D3`); `CMiniport_InitHardware` builds two identity ramps there (`0x19AA1A-0x19AA57`) |
| `CDevice_GammaPending` | `0x2404` | **`0x1FA4`** (miniport `+0x7DC`) | `0x199960` tests `[esi + idx*4 + 0x7DC] == 1` (`0x1999C3`) and clears it (`0x1999E2`); the mode set writes `+0x7DC`/`+0x7E4` (`0x195AE4`, `0x195AEE`) |

Other fields I used to read functions, for `D3d8DataLayout`:

| Field | Offset | Where |
| --- | --- | --- |
| reference count | `+0x4FC` | `D3DDevice_Release` `0x192E97`; 5558 `+0x938` |
| alternate push pointer | `+0x358` | `CDevice_KickOff` `0x19276C`; 5558 `+0x770` |
| push-segment fields | `+0x34C` / `+0x350` | `D3D_MakeRequestedSpace` `0x192AB3`/`0x192ABC`; 5558 `+0x764` / `+0x768` |
| DMA control | `+0x17C0` | `CDevice_KickOff` `0x1927B0`; `CDevice_Init` `0x19692A` |
| register-base copy | `+0x4F8` | `CDevice_Init` `0x19691C` |
| miniport | `+0x17C8` | `CDevice_Init` `0x196643` |
| fence ring | `+0x4C` + `((t >> 1) & 0x3F) * 12` | `D3D_SetFence` `0x1928F9` |
| vertical-blank wait event | `+0x196C` | `D3D_BlockOnTime` `0x192A77` |
| flip times | `+0x1524/+0x1528` | `D3DDevice_Swap` `0x19493D` |
| debug-capture requests | `+0x498/+0x49C/+0x4A0` | `D3DDevice_Swap` `0x1948F7`; `CDevice_Init` `0x196AA3` |
| frame-buffer count | `+0x15BC` | teardown `0x195F89` |
| push-buffer size defaults (globals) | `0x1A1D58` (`0x80000`), `0x1A1D54` (`0x8000`) | `Direct3D_CreateDevice` `0x18F8BC`/`0x18F8CF` |
| filter caches (globals) | `0x1A1D44..0x1A1D50` | `SetFlickerFilter`, `SetSoftDisplayFilter` |
| `D3D_FvfShader` | `0x1A1C28` | `CDevice_Init` `0x1969FE`; `SetVertexShader` `0x19229A` |
| dirty-flags global | `0x19F568` | `SetTransform` `0x192DA6`/`0x192DB8` |

To merge: `python3 tools/merge_symbols.py --apply` picks this file up together with
`config/found-d3d8-data.toml` and `config/found-d3d8-state.toml`, none of which is staged.
`D3D_Device` `0x19FA10` and `D3D_pDevice` `0x19FA08` were proven here by `Direct3D_CreateDevice`
`0x18F8EA`/`0x18F8F4`, and every `mov reg, ds:19FA08h` in the section re-checks them.
`config/found-d3d8-data.toml` gives the same two addresses.

## Method

1. **The reference is the 5558 image `out/sims5558.exe` (Bustin' Out).** I took its names from
   `simsbustinout/config/game.toml` and its sections from `simsbustinout/assets/default.xbe`.
2. **Measurement used the signer's own rules.** I imported the x86 decoder and extent, trace and
   external-target code of `tools/align_symbols.py`, which reproduces the signer's `len`, `ret`,
   `regs`, `calls` and `k`. Self-check: the 69 target names at their Bustin' Out addresses measure
   exactly as `sdk/xdk/5558/signatures.toml` records them, 69 of 69, on `len`, `ret`, `regs` and
   `calls`. I then measured this image's `D3D` section the same way. It has 288 candidate starts:
   282 from the recompiler's inventory and 6 more from the signer's aligned-start rule. 266 remain
   after the 22 interior starts are dropped.
3. **Body comparison.** Each candidate was disassembled next to its 5558 twin (objdump, Intel
   syntax) and read. As a second measure I report the `difflib` ratio of the two normalized
   instruction sequences. Normalization masks image addresses and constants below `0x10000`, and
   keeps NV2A method headers and other stable constants. This ratio is evidence, not proof:
   `D3DResource_BlockUntilNotBusy` scores 1.0 against a `jmp` thunk that jumps somewhere else
   (see "Not emitted").
4. **Positional proof.** `CDevice_Init` (`0x196590`) and `D3D_InitDefaultState` (`0x195E30`) call
   the device API in the same order and with the same literal arguments as their 5558 twins. The
   title's render-thread command loop (`0x156A40`) and device bring-up (`0x156900`) call it with
   distinctive arguments.
5. **Target list.** I built it from `sdk/xdk/5558/signatures.toml`: the 105 `[symbols]` keys with
   `sec = "D3D"`, minus the 36 `D3DDevice_SetRenderState_*`, `D3DDevice_SetTextureState_*`,
   `SetRenderStateNotInline`, `SetTextureStageStateNotInline` and `SetRenderState_Simple` names.
   That leaves 69. Every one of them is a key in `config/game.toml`.
6. **Host ABI.** For all 43 emitted names that have a host body, the body's stdcall argument count
   × 4 equals the guest's `retn`. The fastcall bodies' register use matches the guest's `regs`:
   `CDevice_KickOff` `ecx`; `SetVertexShaderConstant1`/`4` `ecx, edx`;
   `SetVertexShaderConstantNotInlineFast` `ecx, edx` plus 1 stack dword. The other four names have
   no host replacement. The host calls `D3D_InitDefaultState`, `D3D_InternalAddRef` and
   `D3D_InternalRelease` as guest code through `GUEST_CALL`, and `D3DDevice_InsertCallback` has no
   host body at all (see the top).
7. **IDA.** Every proven function is renamed in the shared database. So are these internal ones,
   which are not targets: `CDevice_Init`, `CDevice_UnInit`, `CDevice_InitPushBuffer`,
   `CMiniport_InitHardware`, `CMiniport_MapRegisters`, `D3D_SetRenderTargetInternal`,
   `D3D_ApplyDisplayModeChange`, `D3DDevice_BlockUntilIdle` and `D3DDevice_KickPushBuffer`.
   `0x19A450` and `0x193140` carry comments.

Invariant tags in the sections below:
- `ret`, `regs`, `calls` (within ±1) and `len` (within max(8, 12%)) mean the invariant held.
- `✗` marks a miss, with the reason given in the section.
- `k=` means the stable constants (≥ `0x10000`) are identical, and `k⊂`/`k⊃` means one set
  contains the other.

## Emitted names: evidence

### Direct3D_CreateDevice = 0x18F8B0
| | ret, regs, len, calls, k |
| --- | --- |
| 5558 `0x2443C0` | `ret 24, regs -, len 0xA4, calls 2, k {0x80000}` |
| 5233 `0x18F8B0` | `ret 24, regs -, len 0xA5, calls 2, k {0x80000}` |

All invariants held; ratio 0.878. Its xtlid (`0x800C5`) is not exported: this XBE's `.XTLID`
lists no D3D ids.

The body:
1. It defaults the push-buffer size `[0x1A1D58]` to `0x80000` (`0x18F8BC`) and the kick-off size
   `[0x1A1D54]` to `0x8000` (`0x18F8CF`).
2. It ORs `BehaviorFlags & 0x10` into `[0x19FA18]`, which is `device + 8` (`0x18F8E7`, `0x18F904`).
3. It points `D3D_pDevice` `0x19FA08` at the static device `0x19FA10` (`0x18F8F4`) and sets the
   created flag `[0x19FF0C] = 1`.
4. It calls `CDevice_Init(ecx = device, pPresentationParameters)` at `0x18F90A`.
5. On failure it calls `CDevice_UnInit` `0x196AF0`, clears `0x810` dwords and clears `D3D_pDevice`.
   On success it stores the device through `ppReturnedDeviceInterface` (`0x18F94B`).
6. **`retn 18h`** at `0x18F941` and `0x18F952`.

It is called once, by the title at `0x1569BE` in the device bring-up `0x156900`, as
`(0, D3DDEVTYPE_HAL, 0, 0x40, pPP, &dev)`. This is the same shape as 5558's and as the 3925
precedent. **Confidence: certain.**

### D3DDevice_Release = 0x192E90
5558 `0x245370` and 5233 both measure `ret 0, regs -, len 0x37, calls 1`. All invariants held;
ratio 1.0.
- If the count `[dev+0x4FC]` is 1 (5558 `+0x938`), it calls `CDevice_UnInit` `0x196AF0`, clears
  `D3D_pDevice` and zeroes `0x810` dwords (`0x192EA9`).
- Otherwise it decrements the count and returns it.

Title call: `0x1550BD`. The host's `Release` returns 1 forever. **Confidence: certain.**

### D3DDevice_Reset = 0x193140
5558 `0x245F90`: `ret 4, regs -, len 0xA8, calls 9`; 5233: `ret 4, regs -, len 0xAD, calls 9`.
All invariants held; ratio 0.992. The body and title calls are in "This build's API shape".
**Confidence: certain.**

### D3D_InitDefaultState = 0x195E30
5558 `0x24F940`: `ret 0, regs -, len 0xC2, calls 9`; 5233: `ret 0, regs -, len 0xD2, calls 9`.
All invariants held; ratio 0.832.

The body follows 5558's step for step:
1. `SetTransform(i, identity 0x19D778)` for i = 0..9 (`0x195E46`).
2. `SetRenderStateNotInline(state, default)` for states `0x39..0xA5`, skipping `0x7E`, `0x7F` and
   `0x9A` (`0x195E60-0x195E8E`; 5558 skips the same three). The call goes through `0x18FCF0`,
   which `D3d8StateSymbols` names.
3. `SetRenderStateNotInline(0x8F, [dev+0x15CC] != 0)`, ZEnable from the auto-depth field
   (`0x195E90-0x195EA3`).
4. For each of the 4 stages: 32 texture-stage defaults from the byte table `0x19E4BC` through
   `SetTextureStageStateNotInline` `0x190780`, then `(stage, 0x1C, stage)` and
   `SetTexture(stage, NULL)` (`0x195ED3`).
5. `(0, 0xC, 4)`, `(0, 0x10, 2)`, and `SetScreenSpaceOffset(0, 0)` (`0x195EF8`).

`CDevice_Init` calls it at `0x196A3C`, between `SetRenderTarget` and `Clear`, which is 5558's
order (`0x25051C`). The host's `ApplyDefaultStates` runs it as guest code. **Confidence: certain.**

### D3D_InternalAddRef = 0x18FA90 (anchor)
Both builds: `ret 4, regs -, len 0x32, calls 0, k {0x50000, 0x70000, 0x80000}`; ratio 1.0.
`test ecx, 780000h` (`0x18FA96`), then `add [ecx], 80000h` and, for a surface with a parent,
`add [parent], 80000h` (`0x18FAB3`, `0x18FAB9`); `retn 4`. Confirmed.

### D3D_InternalRelease = 0x18FC20 (anchor)
Both builds: `ret 4, regs -, len 0x62, calls 2, k {0x50000, 0x70000, 0x80000, 0xFFF80000}`;
ratio 1.0. It subtracts `0x80000` (`0x18FC4C`, `0x18FC77`) and frees through the resource destroyer
`0x18F9B0` (5558 `0x2448D0`) at `0x18FC5F` and `0x18FC6E`. Confirmed.

### D3D_BlockOnResource = 0x192CA0
Both builds: `ret 4, regs -, len 0x78, calls 5, k {0x50000, 0x70000}`; ratio 1.0. It is 5558
`0x24D630` instruction for instruction:
- It returns at once without a device.
- For a surface (`Common & 0x70000 == 0x50000`) with a parent: if the in-use test `0x18FA50` (5558
  `0x244970`) holds, it calls `BlockOnTime(clock, 2)`; otherwise it moves on to the parent.
- Then the same test on the resource, and `BlockOnTime(clock, 2)` or `BlockOnTime(fence [+8], 0x10)`.

Callers: the resource destroyer `0x18F9B0` and `Lock2DSurface` `0x197D21`. **Confidence: certain.**

### Lock2DSurface = 0x197D10
Both builds: `ret 24, regs -, len 0x9B, calls 2, k {0xF0000000}`; ratio 1.0. It is 5558 `0x250FC0`
instruction for instruction:
- `Flags & 0x20` skips `D3D_BlockOnResource` (`0x197D16`, `0x197D21`).
- The level-info helper `0x197AD0` (5558 `0x250D40`).
- `Flags & 0x40` ORs in `0xF0000000` (`0x197D58`).
- The pitch arithmetic over the format table `0x19D688`.
- **`retn 18h`**.

Callers are the surface-lock wrappers `0x195760` (`retn 14h`) and `0x195900` (`retn 10h`).
`XgrphXmvKernelCoverage` reports `0x195900` being called by XMV every decoded frame (`0x1C0841`)
and by XGRPH (`0x1A1E9F`). **Confidence: certain.**

### D3DDevice_InsertCallback = 0x1926F0 (anchor)
Both builds: `ret 12, regs -, len 0x6B, calls 1, k {0x40100, 0x40110, 0x81D8C}`; ratio 1.0.
Confirmed by its body; details are under "This build's API shape". **It has no host body in this
tree.**

### CDevice_KickOff = 0x192760
| | ret, regs, len, calls, k |
| --- | --- |
| 5558 `0x24D120` | `ret 0, regs ecx, len 0xB0, calls 1, k {0x100410, 0xFFFFFFF}` |
| 5233 | `ret 0, regs ecx, len 0xDB, calls 1, k {0x100410, 0xFFFFFFF}` |

`ret`, `regs`, `calls` and `k` held. `len ✗ (+43)`: 5233 spills `this` to `[esp]` and reloads it
before every field access. The ratio is only 0.457, for the same register-allocation reason.

The structure is 5558's:
- **Push pointer.** `[ecx+0x358]` if flag 4 (5558 `+0x770`), else `[ecx]`.
- **Hardware path.** `[D3D_pDevice+0x17C8]` (the miniport register base) at `0x192780`, `sfence`,
  NV2A `+0x100410 |= 0x10000` and spin on it (`0x192789-0x1927AA`). Then `PUT & 0xFFFFFFF` goes to
  `[[dev+0x17C0]+0x40]` (`0x1927BC`), followed by the `0x193930` loop and flag `0x2000`.
- **No-hardware path** (global `0x19F560`). It points the DMA control pointer `[dev+0x17C0]` at a
  fake block (`0x19F550 - 0x40`, `0x1927DE-0x1927E6`) and writes PUT into both its PUT (`+0x40`) and
  GET (`+0x44`) slots. It then sets the completed time `[[dev+0x30]] = [dev+0x2C] - 2` and copies
  the swap count `+0x2018` to `+0x1984`. 5558 does the same with `+0x2478` and `+0x1DE4`. It also
  does `[dev+0x1FE0] = [dev+0x3C]`, which is 5233-only.

Callers: `D3D_SetFence`, `D3D_MakeRequestedSpace` (twice), `D3DDevice_KickPushBuffer`,
`CDevice_Init` and `CDevice_UnInit`. **Confidence: certain.**

### D3D_SetFence = 0x1928B0
| | ret, regs, len, calls, k |
| --- | --- |
| 5558 `0x24D240` | `ret 4, regs -, len 0xB8, calls 2, k {0x41D70, 0x41D90, 0x4A310}` |
| 5233 | `ret 4, regs -, len 0xA4, calls 2, k {0x41D70, 0x41D90}` |

`ret`, `regs`, `calls` and `len` held; `k⊂`. Ratio 0.615 (register allocation).

The algorithm is 5558's:
1. `0x41D70` with the clock, then `0x41D90, 0` twice (`0x1928CF-0x1928E0`).
2. The clock and push position go into the 64-entry ring at `dev + ((t >> 1) & 0x3F) * 12 + 0x4C`
   (`0x1928F9`).
3. Flag 1 also records them in the second ring `[dev+0x48]`, indexed by `[dev+0x34] & [dev+0x38]`.
4. `[dev+0x2C] += 2` (`0x19293A`).
5. `CDevice_KickOff` unless flag 2 (`0x192948`).
6. It returns the old clock with `retn 4`.

5558 also pushes `0x4A310`; this build does not, and neither does 3925. **Confidence: certain.**

### D3D_BlockOnTime = 0x192960
| | ret, regs, len, calls, k |
| --- | --- |
| 5558 `0x24D300` | `ret 8, regs -, len 0x166, calls 9, k {0x40100, 0x40110, 0x80000000}` |
| 5233 | `ret 8, regs -, len 0x136, calls 7, k {0x40100, 0x40110, 0x80000000}` |

`ret`, `regs` and `k=` held; ratio 0.855. `calls ✗ (7/9)` and `len ✗ (-48)` are explained under
"Exceptions".

The algorithm is 5558's step for step:
1. Return if the time has completed (`0x19297E`).
2. `SetFence(0)` if the time is the current clock (`0x19298A`).
3. Find the ring entry with `0x1925A0` (5558 `0x24CDE0`) and measure the distance to GET with the
   fastcall `0x192530`.
4. If the distance is at least `0x2400`, run the callback `[dev+0x15AC]`. Unless flag 8, patch the
   entry with `0x40110, 0` (`0x1929EC`) and `0x40100, 5`, and poke the GPU with `0x1926C0` (5558
   `0x24CFE0`).
5. Either spin on the clock or loop `KeWaitForSingleObject(dev+0x196C, 6, 1, 0, 0)` (`0x192A71`).
6. **`retn 8`**.

Callers: `D3D_KickOffAndWaitForIdle`, `D3D_BlockOnResource` (three times), `0x192D20`,
`D3D_MakeRequestedSpace` and `D3DDevice_Swap` (twice). **Confidence: certain.**

### D3D_MakeRequestedSpace = 0x192AA0
| | ret, regs, len, calls, k |
| --- | --- |
| 5558 `0x24D470` | `ret 8, regs -, len 0x137, calls 5, k {0xFFFFFFF, 0xFFFFFDFC}` |
| 5233 | `ret 8, regs -, len 0x173, calls 4, k {0xFFFFFFF, 0x80000000, 0xFFFFFDFC}` |

`ret`, `regs` and `calls` held; `k⊃`. `len ✗ (+60)`: 5233 inlines the GET read
`[[dev+0x17C0]+0x44] | 0x80000000` (`0x192AE6`) that 5558 calls `0x24CEE0` for. Ratio 0.461.

The body is the same:
1. With flag 4 it advances the segment through `[dev+0x34C]`/`[dev+0x350]` (5558 `+0x764`/`+0x768`).
2. Otherwise it wraps or blocks on the ring with `BlockOnTime(time, 8)` (`0x192BC6`).
3. It sets the threshold to `end - 0x204` (`0x192BD3`).
4. Flag `0x800`: set `0x1000` and `CDevice_KickOff`. Otherwise `SetFence(1)` and `CDevice_KickOff`.
5. It returns `[dev]`, the push pointer, with `retn 8`.

Callers: `D3DDevice_MakeSpace` and `D3DDevice_BeginPush` only. **Confidence: certain.**

### D3DDevice_MakeSpace = 0x192C20
Both builds: `ret 0, regs -, len 0xF, calls 1`; ratio 1.0. The body is
`mov eax, [0x1A1D54]; push eax; shr eax, 1; push eax; call D3D_MakeRequestedSpace; ret`, identical
to 5558 `0x24D5B0`. It is the target of 90 call instructions: every inline pusher in the section
and five title sites (`0x152B71`, `0x152EE4`, `0x1530FE`, `0x1546BD`, `0x154860`).
**Confidence: certain.**

### D3DDevice_BeginPush = 0x192C30
Both builds: `ret 4, regs -, len 0x44, calls 1`; ratio 1.0. It is 5558 `0x24D5C0` byte for byte:
- If `push + count*4` is at least `threshold + 0x200`, it calls
  `MakeRequestedSpace(max(count*4 + 0x204, size/2), max(count*4 + 0x204, size))`.
- `retn 4`.

Callers:
- The title's inline constant writer `0x152EC0` (`0x152EEC`). It writes
  `0x41EA4, reg, 0x300B80/0x600B80, data...` itself and stores the end pointer straight into
  `[0x19FA10]` (`0x152FD6`), an inlined `EndPush`.
- `LoadVertexShader`, `0x192180`, `DrawVerticesUP`, `DrawVertices` and `DrawIndexedVertices`.

**Confidence: certain.**

### D3D_KickOffAndWaitForIdle = 0x192C80
Both builds: `ret 0, regs -, len 0x11, calls 1`; ratio 1.0. The body is
`BlockOnTime([dev+0x2C], 2)`, identical to 5558 `0x24D610`.

Callers:
- the thunk `D3DDevice_BlockUntilIdle` `0x192ED0` (`jmp`), which the title calls at `0x167F26`
  and `0x168344`
- `D3DDevice_Reset` `0x19314A`
- `D3D_ApplyDisplayModeChange` `0x193FE6`
- `CDevice_UnInit` `0x196AFA`

**Confidence: certain.**

### D3DDevice_BlockUntilVerticalBlank = 0x192F10
Both builds: `ret 0, regs -, len 0x24, calls 0`; ratio 1.0. It clears `[dev+0x1960]` (`0x192F1B`)
and calls `KeWaitForSingleObject(dev+0x195C, 6, 1, 0, 0)` (`0x192F2D`, import `0x1EE5A4` =
ordinal `0x9F`). 5558 `0x245490` is the same with `+0x1DBC`/`+0x1DC0`. Callers: title `0x152852`
and `D3D_ApplyDisplayModeChange` `0x194008`. **Confidence: certain.**

### D3DDevice_CreateVertexShader = 0x191B20 (anchor)
Both builds: `ret 16, regs -, len 0x13E, calls 5, k {0x8007000E}`; ratio 0.982. It returns
`0x8007000E` on allocation failure (`0x191B7F`), checks the program header tokens `0x2078`/`0x7378`
(`0x191BE3`, `0x191BF6`) and ends with `retn 10h`. Title calls: `0x1552CC`, `0x1552E1`,
`0x1552F6`, `0x1680F7`. Confirmed.

### D3DDevice_SetVertexShaderConstant1 = 0x191C60
Both builds: `ret 0, regs ecx,edx, len 0x5F, calls 1, k {0x41EA4, 0x100B80}`; ratio 1.0. It is
5558 `0x24BA10` instruction for instruction:
- a fastcall with `ecx` = register and `edx` = source
- it reserves 7 dwords and writes `0x41EA4, reg, 0x100B80` plus 4 dwords, mirroring them into the
  constant shadow at `0x19E950 + reg*16` (5558 `0x263890`)
- `MakeSpace` and a retry when full

Title call: `0x15533F`. It is not `SetVertexShaderConstant1Fast` (5558 `0x24BA70`, `0x49` bytes,
which does not mirror). That function is absent here. **Confidence: certain.**

### D3DDevice_SetVertexShaderConstant4 = 0x191CC0
Both builds: `ret 0, regs ecx,edx, len 0xA2, calls 1, k {0x41EA4}`; ratio 1.0. It is 5558
`0x24BAC0` instruction for instruction: an MMX copy of 4 registers with `0x41EA4, reg, 0x400B80`,
mirrored to `0x19E950`. Title call: `0x15545A`. **Confidence: certain.**

### D3DDevice_SetVertexShaderConstantNotInlineFast = 0x191D70 (anchor)
Both builds: `ret 4, regs ecx,edx, len 0xD0, calls 2, k {0x41EA4}`; ratio 1.0. It writes
`0x41EA4` (`0x191D8A`) and `0x400B80` (`0x191DE1`) and ends with `retn 4`. Its only caller is
`0x191E50`, 5558 `0x24BC50`, the non-fast `SetVertexShaderConstant` wrapper that copies into the
shadow first. The title calls that wrapper at `0x15541F` and `0x15542D`. Confirmed.

### D3DDevice_LoadVertexShader = 0x191F20
Both builds: `ret 8, regs -, len 0x54, calls 2, k {0x41E9C}`; ratio 1.0. It is 5558 `0x24BFC0`
instruction for instruction:
- device flag `0x10` decides whether the program is checked through `0x191760`
- `BeginPush(n + 2)` (`0x191F48`)
- `0x41E9C` (SET_TRANSFORM_PROGRAM_LOAD) = Address (`0x191F51`), then `n` program dwords from
  `object + 0x114` (`0x191F5C`, `0x191F65`)
- `retn 8`

Caller: `D3DDevice_SetVertexShader` `0x1922EF`. **Confidence: certain.**

### D3DDevice_SelectVertexShader = 0x191F80
| | ret, regs, len, calls, k |
| --- | --- |
| 5558 `0x24C090` | `ret 8, regs -, len 0x9C, calls 3, k {0x41EA0, 0x81E94}` |
| 5233 | `ret 8, regs -, len 0x80, calls 3, k {0x41EA0, 0x81E94}` |

`ret`, `regs`, `calls` and `k=` held. `len ✗ (-28)`: 5233 omits 5558's "did the shader mode change"
test and always dirties. Ratio 0.775.

The body:
- With a handle it stores the object and handle at `[dev+0x37C]`/`[dev+0x380]` (5558 `+0x794`/`+0x798`).
- It ORs `0x1070` into the dirty flags.
- It pushes `0x81E94, 6, flags & 1` and the viewport through `0x1908C0` (5558 `0x24A700`).
- It always pushes `0x41EA0` (SET_TRANSFORM_PROGRAM_START) = Address (`0x191FE8`) and stores it at
  `[dev+0x384]`.
- `retn 8`.

Caller: `D3DDevice_SetVertexShader` `0x1922F6`, right after `LoadVertexShader`, as in 5558.
**Confidence: certain.**

### D3DDevice_SetShaderConstantMode = 0x192000 (anchor)
Both builds: `ret 4, regs -, len 0x118, calls 5, k {0x41EA4, 0x1009D0, 0x100A50, 0x3F800000, 0xFFFFFDFF}`;
ratio 1.0. It writes `0x41EA4` (`0x19204A`), `0x1009D0` (`0x1920C1`) and `0x100A50` (`0x1920E8`)
and ends with `retn 4`. Its caller is the push-buffer state setup `0x195D50` (the code at
`0x195D3B`, reached through `0x195C60`), which `CDevice_Init` calls at `0x19699C`. Confirmed.

### D3DDevice_DeleteVertexShader = 0x192160
5558 `0x24C2E0`: `ret 4, regs -, len 0x1B, calls 1`; 5233: `ret 4, regs -, len 0x19, calls 1`.
All invariants held; ratio 0.737.
- `obj = handle - 1; if (--obj->ref == 0) free(obj)` (`0x192164-0x19216B`).
- 5233 tail-jumps into the allocator's free `0xCA26F` with no tag (`0x192171`, xtlid `0x20034`).
  5558 calls `0x108F3E` with tag `0x24800000`; 3925 also tail-jumps.
- The `handle - 1` marks it as the vertex-shader form; `DeletePixelShader` takes the pointer
  itself.
- `retn 4`.

Title calls: `0x155064`, `0x155074`, `0x155084`, `0x167E37`, `0x167F3C`. **Confidence: certain.**

### D3DDevice_SetVertexShader = 0x192270
| | ret, regs, len, calls, k |
| --- | --- |
| 5558 `0x24C3F0` | `ret 4, regs -, len 0x163, calls 7, k {0x4194C, 0x41950, 0x4195C, 0x41960, 0x41E94, 0x41EA0, 0x81E94}` |
| 5233 | `ret 4, regs -, len 0x152, calls 7, k {0x4194C, 0x41950, 0x4195C, 0x41960, 0x41E94, 0x41EA0, 0x81E94}` |

All invariants held; ratio 0.764.
- **Handle.** An odd handle is a program object (`object = handle - 1`). An even one is an FVF,
  built into the static shader `0x1A1C28` by `0x191620` (5558 builds into `0x266FC8` through
  `0x24B340`).
- **Dirty bits.** `0x70`, `0x400` and `0x1600`.
- **Stores.** `[dev+0x37C]`/`[dev+0x380]` (`0x1922D8`/`0x1922DE`).
- **Program with flag `0x10`.** `LoadVertexShader` and `SelectVertexShader` (`0x1922EF`,
  `0x1922F6`).
- **Otherwise.** `0x4194C/0x41950/0x4195C/0x41960` by FVF bits, then `0x41EA0, 0` with
  `0x81E94, 6` (`0x192370-0x192380`) or `0x41E94, 4` (`0x1923A3`).
- `retn 4`.

Callers: `CDevice_Init` `0x196A08` with `SetVertexShader(2)`, 5558's init order, and 18 title
sites. **Confidence: certain.**

### D3DDevice_SetPixelShader = 0x195510 (anchor)
Both builds: `ret 4, regs -, len 0x1F3, calls 5`; ratio 1.0. It writes `0x41E78` (`0x195579`),
`0x417F8` (`0x19564F`) and `0x81E74` (`0x19569E`) and ends with `retn 4`.

The signer lists three more 5558 constants: `0x200260`, `0x210000` and `0x241E40`. The
instructions carry the same values here, but those values fall in `.rdata`/`.data` in this image,
so the signer drops them as addresses. In 5558 they fall in `.text`, so they count as constants
there. Callers: `0x1940E0`, `0x194200` and `0x1954D0` (twice). Confirmed.

### D3DDevice_SetStreamSource = 0x191E90 (anchor)
Both builds: `ret 12, regs -, len 0x8C, calls 1, k {0x80000, 0xFFF80000}`; ratio 1.0. It does an
`add [vb], 80000h` AddRef (`0x191EA0`) and a `0xFFF80000` release (`0x191EC8`) and ends with
`retn 0Ch`. 17 title calls. Confirmed.

### D3DDevice_SetTransform = 0x192D80
5558 `0x244FE0`: `ret 8, regs -, len 0x118, calls 2, k {0x3F800000}`; 5233: `ret 8, regs -, len 0x10E, calls 2, k {0x3F800000}`.
All invariants held; ratio 0.907.
- `lea edi, [type*64 + dev + 810h]; mov ecx, 10h; rep movsd` (`0x192D96-0x192DA4`; 5558 `+0xC60`).
- It ORs the type's dirty mask `[0x19DAB8 + type*4]` into `[0x19F568]` (`0x192DAC-0x192DB8`).
- For the projection (type 1) it derives the W/Z floats at `[dev+0x500/0x504/0x508]` (5558
  `+0x93C/0x940/0x944`) and the `0x2` flag in `[dev+8]`.
- On that projection path only, it calls `0x18FE80` and `0x192180` (5558 `0x249AB0` and
  `0x24C300`). The other types return straight after the dirty OR (`jne 0x192E88` at `0x192DBE`).
- `retn 8` at `0x192E8B`.

Caller: `D3D_InitDefaultState` only. The title does not call it, since it draws with its own
vertex shaders. `D3d8StateSymbols` independently reported the same address. **Confidence: certain.**

### D3DDevice_SetTexture = 0x1936F0 (anchor)
Both builds: `ret 8, regs -, len 0x1A4, calls 3`, with the same 8 stable constants; ratio 1.0.
Textures are at `[dev + stage*4 + 0xB38]` (`0x193700`, `0x193739`). It writes `0x41B0C`
(`0x193754`) and `0x41B1C` (`0x1937F0`), ORs `0x4800` into the dirty flags (`0x193777`) and ends
with `retn 8`. Confirmed.

### D3DDevice_SetPalette = 0x1938A0
Both builds: `ret 8, regs -, len 0x8D, calls 2, k {0x41B20, 0x80000, 0xFFF80000}`; ratio 1.0. It
is 5558 `0x2473A0` instruction for instruction:
- The old palette at `[dev + stage*4 + 0xB48]` gets the clock stamp and loses a reference; at zero
  it is destroyed through `0x18F9B0`.
- The new palette gains a reference (`+0x80000`) and is stored.
- It pushes `0x41B20 + stage*64` (SET_TEXTURE_PALETTE) with `data | (Common >> 28)` (`0x193916`).
- `retn 8`.

Title calls: `0x1531F8`, `0x154D6C`, `0x155A25`, `0x15B338`, `0x15B346`. **Confidence: certain.**

### D3DDevice_SetRenderTarget = 0x192D60
| | ret, regs, len, calls, k |
| --- | --- |
| 5558 `0x246040` | `ret 8, regs -, len 0x274, calls 11, k {0x40100, 0x40110, 0x40130, 0x4020C, 0x40210, 0x40214, 0x4030C, 0x4032C, 0xFFFFFEFF}` |
| 5233 `0x192D60` (public entry) | `ret 8, regs -, len 0x17, calls 1, k {-}` |

`ret` and `regs` held. `calls`, `len` and `k` miss because 5233 splits the function in two; see
"Exceptions". The whole public entry:

```
0x192D60  mov eax, [esp+8]        ; pNewZStencil
0x192D64  mov ecx, [esp+4]        ; pRenderTarget
0x192D68  push 19D6D0h            ; {0, 0, 0x7FFFFFFF, 0x7FFFFFFF, 0.0, 1.0}: the whole target
0x192D6D  push eax / push ecx
0x192D6F  call 0x190BE0           ; D3D_SetRenderTargetInternal(pRT, pZ, pViewport), retn 0Ch
0x192D74  retn 8
```

`0x190BE0` holds the 5558 body. It does the following:
- **Targets.** It AddRefs the new target (`0x190E58`), releases the old one and stores the target
  at `[dev+0x15B4]` (`0x190E8A`). It does the same for the depth surface at `[dev+0x15B8]`
  (`0x190EAF`).
- **Depth scale.** It writes the depth-format maximum into `[dev+0x50C]` through `0x197850`.
- **Push tokens.** `0x40100/0x40110` waits, `0x4020C/0x40210/0x40214` (surface pitch, colour and
  zeta offsets), `0x80200` surface clip, `0x40290`, `0x4030C`/`0x4032C`, `0x40130` and `0x40208`.
- **Scale and viewport.** It stores the scale pair `[dev+0x518/0x51C]`, calls
  `SetRenderStateNotInline`, then calls `D3DDevice_SetViewport(pViewport)` (`0x191162`).
- `retn 0Ch` at `0x19117A`.

This is the right address for the host body:
- **Position.** `CDevice_Init` calls `0x192D60([dev+0x15C0], [dev+0x15CC])` at `0x196A37`, just
  before `D3D_InitDefaultState` and `Clear(0, NULL, 3, 0, 1.0f, 0)`. 5558's init calls
  `SetRenderTarget([+0x1A14], [+0x1A20])` at the same point (`0x250517`).
- **Title calls.** Two-argument calls at `0x15385A`, `0x155A87` and `0x15B9E5`.
- **ABI.** The host's `HLE_STDCALL(D3DDevice_SetRenderTarget, 2)` matches `retn 8` and does what
  the wrapper does, including resetting the viewport to the whole target.

**Never put the name on `0x190BE0`.** It takes 3 arguments, and a 2-argument host body there would
leave 4 bytes on every caller's stack. Its remaining guest callers are
`SetRenderState_MultiSampleMode` and `SetRenderState_MultiSampleRenderTargetMode`, which pass the
current viewport `&[dev+0xA90]` and are `D3d8StateSymbols`' names; `Reset`; and two flip helpers of
`Swap`. All of these are host-replaced when both D3D files are merged. **Confidence: certain.**

### D3DDevice_SetFlickerFilter = 0x192F40
Both builds: `ret 4, regs -, len 0x42, calls 0`; ratio 1.0. If the value has changed (cache
`[0x1A1D50]`/`[0x1A1D48]`), it calls `AvSendTVEncoderOption([dev+0x17C8], 0xB, value, 0)`
(`0x192F65`, import `0x1EE618` = ordinal 2) and ends with `retn 4`. Caller: `CDevice_Init`
`0x196AC9` with `SetFlickerFilter(5)`, as 5558 `0x25058B` does. **Confidence: certain.**

### D3DDevice_SetSoftDisplayFilter = 0x192F90
Both builds: `ret 4, regs -, len 0x51, calls 0`; ratio 1.0. The same structure with option `0xE`
(`0x192FBE`) and cache `[0x1A1D4C]`/`[0x1A1D44]`; `retn 4`. Caller: `CDevice_Init` `0x196AD0`
with `(0)`, as 5558 `0x250592` does. **Confidence: certain.**

### D3DDevice_GetBackBuffer2 = 0x1931F0
Both builds: `ret 4, regs -, len 0x43, calls 2`; ratio 1.0. Details under "This build's API
shape". Callers: title `0x1569C9` and `0x158242`; D3D `0x19B1ED` and `0x19B4D9` (the debug capture
reached from `Swap`). **Confidence: certain.**

### D3DDevice_CopyRects = 0x193240 (anchor)
Both builds: `ret 20, regs -, len 0x323, calls 6, k {0x86300, 0x86308, 0xC4300}`; ratio 1.0. It
writes the blit methods `0x86308` (`0x19334B`), `0x86300` (`0x193360`) and `0xC4300` (`0x1934E6`)
and ends with `retn 14h`. Title call: `0x153D12`. Confirmed.

### D3DDevice_GetDepthStencilSurface2 = 0x193570
Both builds: `ret 0, regs -, len 0x1E, calls 1`; ratio 1.0. Details under "This build's API
shape". Title call: `0x1569D4`. **Confidence: certain.**

### D3DDevice_SetViewport = 0x193590
| | ret, regs, len, calls, k |
| --- | --- |
| 5558 `0x246B40` | `ret 4, regs -, len 0x222, calls 8` |
| 5233 | `ret 4, regs -, len 0x160, calls 4` |

`ret` and `regs` held. `calls ✗` and `len ✗`: 5233 has no super-sample scaling (see
"Exceptions"). Ratio 0.556.

The body otherwise follows 5558's:
1. It picks the target, substituting the front buffer `[dev+0x15C4]` when the target is the back
   buffer `[dev+0x15C0]`, as 5558 does with `+0x1A14`/`+0x1A18` (`0x19359A-0x1935B4`).
2. It clamps X/Y/W/H to the surface size decoded from its Size/Format dwords, with the same code
   as 5558 (`0x1935BA-0x19367E`).
3. It stores X, Y, W, H, MinZ and MaxZ at `[dev+0xA90..0xAA4]` (`0x19368B-0x1936AF`; 5558
   `+0xEE0..+0xEF4`).
4. It calls `0x18FE80` (5558 calls `0x249AB0` at the same point), then **`SetScissors(0, 0, 0)`**
   (`0x1936C0`; 5558 `0x246D39`).
5. It pushes the viewport through `0x1908C0` (5558 `0x24A700`) and ORs `0x100` into the dirty
   flags (`0x1936DF`, as 5558 does).
6. `retn 4` at `0x1936ED`.

Caller: `D3D_SetRenderTargetInternal` `0x191162`. The title never calls it directly. The host body
`HLE_STDCALL(D3DDevice_SetViewport, 1)` reads the six `D3DVIEWPORT8` fields, which have the same
layout here. **Confidence: high.**

### D3DDevice_SetScissors = 0x193A60
| | ret, regs, len, calls, k |
| --- | --- |
| 5558 `0x247C40` | `ret 12, regs -, len 0x300, calls 13, k {0x402B4, 0x402C0, 0x402E0, 0x80200}` |
| 5233 | `ret 12, regs -, len 0x197, calls 5, k {0x402B4, 0x402E0}` |

`ret` and `regs` held; `k⊂`. `calls ✗` and `len ✗` are explained under "Exceptions". Ratio 0.372.
- The arguments are `(Count, Exclusive, pRects)`. With Count 0 it uses one rect, the viewport from
  `[dev+0xA90]` (`0x193A89`).
- It pushes `0x402B4` (SET_WINDOW_CLIP_TYPE) = Exclusive (`0x193AE0`).
- For each rect it pushes `0x402C0 + 4i` (horizontal) and `0x402E0 + 4i` (vertical), scaled by
  `[dev+0x518]`/`[dev+0x51C]` through the float-to-int helper `0x197550` (5558 `0x251CB0`).
- It copies the rects to `[dev+0x1720]` and stores Count and Exclusive at `[dev+0x17A0]`/`+0x17A4`.
- `retn 0Ch` at `0x193BF4`.

Callers: `D3DDevice_SetViewport` with `(0, 0, 0)`, exactly as 5558's `SetViewport` calls
`SetScissors`, and title `0x152EB0`. **Confidence: high.**

### D3DDevice_SetScreenSpaceOffset = 0x193C00
Both builds: `ret 8, regs -, len 0x49, calls 3`; ratio 0.8.
- It stores `x + 0.53125` (constant `0x19DA38`) at `[dev+0xAA8]` and `y + 0.53125` at `[dev+0xAAC]`
  (`0x193C13`, `0x193C23`; 5558 `+0xEF8`/`+0xEFC`).
- It calls `0x192180` and pushes the viewport through `0x1908C0`, as 5558 does with `0x24C300` and
  `0x24A700`.
- `retn 8`.

Caller: `D3D_InitDefaultState` `0x195EF8` with `(0, 0)`, as 5558's calls `0x2480F0`.
`D3d8StateSymbols` independently reported the same address. **Confidence: certain.**

### D3DDevice_Swap = 0x1948F0
5558 `0x2495F0`: `ret 4, regs -, len 0xE5, calls 9`; 5233: `ret 4, regs -, len 0xDB, calls 9`.
All invariants held; ratio 0.993. Details under "This build's API shape". Title calls: `0x156B1A`,
the once-a-frame call, and `0x158363`, the present-and-halt screen. **Confidence: certain.**

### D3DDevice_Clear = 0x194A90
5558 `0x248570`: `ret 24, regs -, len 0x39F, calls 10, k {0x40208, 0x81D98, 0xC1D8C, 0xFFFFFDFF}`;
5233: `len 0x394`, everything else identical. All invariants held; ratio 0.89.
- It pushes `0x40208` (`0x194AEA`, `0x194E0B`).
- Per rect it pushes `0x81D98` (SET_CLEAR_RECT_HORIZONTAL/VERTICAL, `0x194D93`) and `0xC1D8C`
  (ZSTENCIL_CLEAR_VALUE, COLOR_CLEAR_VALUE, CLEAR_SURFACE, `0x194DB6`).
- It uses the same depth-scale constants (`0xFFFFFF` clamp) and float helpers as 5558, which line
  up instruction for instruction.
- `retn 18h` at `0x194E21`.

`CDevice_Init` calls `Clear(0, NULL, 3, 0, 1.0f, 0)` at `0x196A50` and `Reset` makes the same call
at `0x1931DF`; both are 5558's positions. Title calls: `0x152735`, `0x1527DF`, `0x154FDE`,
`0x15825E`, `0x15BA05`. **Confidence: certain.**

### D3DDevice_DrawVerticesUP = 0x194F00
5558 `0x24D9E0`: `ret 16, regs -, len 0x165, calls 5, k {0x417FC, 0x40001818, 0xFFFFE7FF}`;
5233: `len 0x15D`, everything else identical. All invariants held; ratio 0.931.
1. State sync `0x1995F0` (5558 `0x2552D0`).
2. `0x417FC` (BEGIN_END) with the primitive (`0x194F26`).
3. Batches through `BeginPush` with `0x40001818 + (dwords << 18)` (inline array, `0x194FBA`).
4. `0x417FC, 0` (`0x19502C`); `SetFence(1)` under flag `0x1000` (`0x19504A`); flags
   `&= 0xFFFFE7FF`.
5. `retn 10h` at `0x19505A`.

Title calls: `0x155F4F`, `0x156168`, `0x1566CC`, `0x1568A2`. **Confidence: certain.**

### D3DDevice_DrawVertices = 0x195060 (anchor)
Both builds: `ret 12, regs -, len 0x94, calls 2, k {0x417FC, 0x40001810, 0xFF000000, 0xFFFFFEFF}`;
ratio 1.0. It writes `0x417FC` (`0x19508D`, `0x1950DB`) and `0x40001810` (`0x195093`) and ends with
`retn 0Ch`. Confirmed.

### D3DDevice_DrawIndexedVertices = 0x195100 (anchor)
Both builds: `ret 12, regs -, len 0x257, calls 4, k {0x417FC, 0x41808, 0x40001800, 0xFFFFE7FF}`;
ratio 0.953. BaseVertex is read at `[dev+0x1C]` (`0x19510E`); it writes `0x40001800` index runs
and `0x41808`, and ends with `retn 0Ch`. Confirmed.

### D3DDevice_Begin = 0x195450
Both builds: `ret 4, regs -, len 0x35, calls 2, k {0x417FC}`; ratio 1.0. It is 5558 `0x24E200`
byte for byte:
- state sync `0x1993D0`
- `0x417FC, PrimitiveType` (`0x19546C`)
- flags `|= 0x800` (`0x19547A`)
- `retn 4`

8 title calls (`0x153D8D` and others). **Confidence: certain.**

### D3DDevice_End = 0x195490
5558 `0x24E240`: `ret 0, regs -, len 0x41, calls 2, k {0x417FC, 0xFFFFE7FF}`; 5233: `len 0x3D`,
everything else identical. All invariants held; ratio 0.842.
- `0x417FC, 0` (`0x1954A3`)
- `SetFence(1)` if flag `0x1000` (`0x1954BF`)
- flags `&= 0xFFFFE7FF`
- plain `ret`

8 title calls. **Confidence: certain.**

## Exceptions to the invariants

Four emitted names miss the `calls ±1` rule, and three of them also miss the length band. I emit
them because each one's body is the 5558 function, read side by side. Each miss has a structural
cause I could point to in both images. `ret` and `regs`, the two invariants that would reveal a
changed calling convention, hold for all four.

| Name | Miss | Cause |
| --- | --- | --- |
| `D3D_BlockOnTime` `0x192960` | calls 7 vs 9; len -48 | 5558 splits the "distance to GET" computation into `0x24CF60` (read GET) and `0x24CB00` (distance), called 3 and 2 times. 5233 has one fastcall, `0x192530`, called 3 times. The other calls line up one to one: `SetFence`, the ring lookup, and the two pokes `0x1926C0`. The count drifts across builds: 3925's `BlockOnTime` (`fuzion frenzy` `0x1FB020`) measures 6 calls. |
| `D3DDevice_SetRenderTarget` `0x192D60` | calls 1 vs 11; len 0x17 vs 0x274; k empty | The public `retn 8` entry is a 2-argument wrapper around `D3D_SetRenderTargetInternal` `0x190BE0`, which takes `(pRT, pZ, pViewport)` with `retn 0Ch`. The 5558 body's tokens and calls live in `0x190BE0`. The proof is positional (`CDevice_Init` `0x196A37` against 5558 `0x250517`) plus the three 2-argument title calls. |
| `D3DDevice_SetViewport` `0x193590` | calls 4 vs 8; len -194 | 5558 scales X/Y/W/H by the super-sample factors `[dev+0x95C]`/`[dev+0x960]`. That accounts for the 4 extra `0x251CB0` float-to-int calls and the `fild/fmul/fdiv` blocks at `0x246C44-0x246CE1`, plus a `pViewport == NULL` path. 5233 has neither. The calls 5233 does make line up with 5558's: `0x18FE80`, `SetScissors(0, 0, 0)`, `MakeSpace` and the viewport push. |
| `D3DDevice_SetScissors` `0x193A60` | calls 5 vs 13; len -361; k lacks `0x402C0` and `0x80200` | 5558 has separate scaled and unscaled rect paths (8 more float-to-int calls) and also pushes SURFACE_CLIP `0x80200`. 5233 has one scaled path and computes `0x402C0 + 4i` as `esi - 0x20` from `0x402E0 + 4i` (`0x193B50`), so the signer never sees that constant. |

Length-band misses only (corroboration, not proof):
- `CDevice_KickOff` +43: `this` is reloaded from `[esp]`.
- `D3D_MakeRequestedSpace` +60: the GET read is inlined.
- `D3DDevice_SelectVertexShader` -28: no shader-mode compare.

The `k` differences are each explained in the name's section: `D3D_SetFence`, `D3D_MakeRequestedSpace`
and `D3DDevice_SetPixelShader`.

## Not emitted

The 22 names below are not linked into this image. The ranked candidates are the best 5233
functions by body similarity among those with the reference's `ret` and `regs`. Each is listed with
what it actually is.

| Name (5558 twin, measurements) | Why it is absent | Ranked candidates (ratio), and why each is not it |
| --- | --- | --- |
| `D3DDevice_BlockOnFence` (`0x2453C0`, ret 4, len 0xF, 1 call) | Its body is `push 4; push [esp+8]; call BlockOnTime; retn 4`. `D3D_BlockOnTime`'s 9 call sites are all accounted for: `MakeRequestedSpace`, `KickOffAndWaitForIdle`, `BlockOnResource` ×3, `0x192D20` ×2, `Swap` ×2. None is in a 15-byte wrapper. | `0x191460`, `0x191440`, `0x191420` (all 0.667): `retn 4` 17-byte setters that store a global and call `0x190B10`. They are `D3d8StateSymbols`' `DoNotCullUncompressed`, `RopZRead` and `RopZCmpAlwaysRead`. |
| `D3DDevice_CreatePixelShader` (`0x24E290`, ret 8, k `0x8007000E`) | It allocates `0xFC` bytes and copies `0x3C` dwords. There is no `push 0FCh`, no `mov ecx, 3Ch`, and no `retn 8` function returning `0x8007000E` in the section. The only users of `0x8007000E` are `CreateVertexShader`, `CDevice_InitPushBuffer` (twice), `InitializeFrameBuffers` and `CDevice_Init`. `D3DDevice_SetPixelShader` is called here only by D3D-internal code (`0x1940E0`, `0x194200`, `0x1954D0`). | `0x195790` (0.25): a buffer-lock helper (`Flags & 0xA0`, then `[res+4] \| 0x80000000`). `0x18FCF0` (0.25): `SetRenderStateNotInline`. `0x191F80` (0.24): `SelectVertexShader`. |
| `D3DDevice_DeletePixelShader` (`0x24E2E0`, ret 4, len 0x1D) | It needs `dec dword [eax]; jnz` and a free of the object. No `dec [eax]; jnz` exists in the section, and `CreatePixelShader` is absent. | `0x18FA90` (0.522): `D3D_InternalAddRef`. `0x1914C0` (0.435): `SetRenderState_MultiSampleRenderTargetMode`. `0x191460` (0.429): a render-state setter. |
| `D3DDevice_EnableOverlay` (`0x259700`, ret 4) | It writes PVIDEO registers `0x8100`, `0x8700`, `0x8704`, `0x8900-0x8930` and `+0x934`. None of those displacements occurs in the section. | `0x1914C0` and `0x191480` (0.258): the two MultiSample render-state handlers. `0x1912A0` (0.208): `SetRenderState_StencilFail`. |
| `D3DDevice_EndPush` (`0x24D0C0`, ret 4, len 0xF) | Its body is `[D3D_pDevice]->Push = arg`. 5558 links it just after `InsertCallback`, with a `0x1B`-byte thunk between them. In 5233, `InsertCallback` `0x1926F0` is followed directly by `CDevice_KickOff` `0x192760`. The title inlines it: `0x152FD6 mov [0x19FA10], esi`. | `0x192EF0` (0.75): stores its argument at `[dev+0x1958]`. That is `D3DDevice_SetVerticalBlankCallback`, 5558 `0x245450`, which stores `+0x1DB8`; the 0x460 shift is the same as for the VBlank event `+0x195C`/`+0x1DBC`. `0x18FC90` (0.6): `SetRenderState_PSTextureModes`. `0x1957B0` (0.5): returns `Common >> 30`. |
| `D3DDevice_FlushVertexCache` (`0x2476F0`, k `0x41710`) | The method `0x41710` does not occur in the section. | `0x195490` (0.8): `D3DDevice_End`, method `0x417FC`. `0x190B10` (0.41): a PGRAPH-poke render-state helper. `0x195C60` (0.37): a push-buffer state block. |
| `D3DDevice_GetRenderTarget2` (`0x246B00`, ret 0, len 0x1A) | It would read `[dev+0x15B4]` and AddRef it. Every reader of `+0x15B4` is something else: `SetRenderTargetInternal`, `SetViewport`, `Clear`, the teardown, the flip and debug-capture helpers `0x194380`/`0x194440` (called from `0x1945C0` and `0x1949D0`) and `0x1947A0`, the debugger callback `0x193C50`, and the render-state handlers `0x1902B0`, `0x191480` and `0x1914C0`. | `0x193570` (0.783): `GetDepthStencilSurface2`, which reads `+0x15B8`. `0x192C80` (0.375): `D3D_KickOffAndWaitForIdle`. `0x192C20` (0.375): `D3DDevice_MakeSpace`. |
| `D3DDevice_GetVertexShaderFunction` (`0x24C870`, ret 12, k `0x88760867`) | `0x88760867` does not occur in the section, and nothing copies a program back out of a shader object. | `0x191810` (0.278): the vertex-program copier (`0xB00` packets). `0x197A10` (0.189): the surface-description helper behind `0x1958E0`. `0x1949D0` (0.157): the debug-capture blit. |
| `D3DDevice_InsertFence` (`0x245790`, ret 0, len 8) | Its body is `push 0; call D3D_SetFence; ret`. None of the 8 `SetFence` call sites sits in such a wrapper: `BlockOnTime`, `MakeRequestedSpace`, `0x1948B0`, `Swap` ×2, `DrawVerticesUP`, `DrawIndexedVertices`, `End`. | `0x192C80` (0.667): `KickOffAndWaitForIdle`, which calls `BlockOnTime(t, 2)`. `0x192C20` (0.444): `MakeSpace`. `0x199830` (0.4): a 3-byte miniport stub. |
| `D3DDevice_IsFencePending` (`0x24D010`, ret 4, len 0x1E) | Its tail is `cmp eax, edx; sbb eax, eax; neg eax; retn 4`. Those bytes (`1B C0 F7 D8 C2 04 00`) do not occur in the section. 5558 links it between the GPU poke `0x24CFE0` and `InsertCallback`; here the GPU poke `0x1926C0` is followed directly by `InsertCallback` `0x1926F0`. | `0x1914C0` and `0x191480` (0.333): the two MultiSample render-state handlers. `0x192F40` (0.207): `SetFlickerFilter`. |
| `D3DDevice_LightEnable` (`0x247030`, ret 8, len 0x151) | Its only callee is `SetLight`, which is absent. No candidate scores above 0.21. | `0x190580` (0.209): `SetTextureState_TexCoordIndex`. `0x1938A0` (0.183): `SetPalette`. `0x191F20` (0.159): `LoadVertexShader`. |
| `D3DDevice_PersistDisplay` (`0x247FC0`, ret 0, k `0x80004005`) | It needs `MmPersistContiguousMemory(..., TRUE)`. The only importer of `MmPersistContiguousMemory` is `D3D_ApplyDisplayModeChange` `0x193FC0`, which persists with FALSE and frees: it drops a kept display. The only `0x80004005` user is the mode set `0x1959F8`. | `0x19B010` (0.189): the debug-capture file writer. `0x195E30` (0.171): `D3D_InitDefaultState`. `0x193570` (0.145): `GetDepthStencilSurface2`. |
| `D3DDevice_SetGammaRamp` (`0x244EC0`, ret 8, len 0x83) | It needs `repz cmpsd` over `0xC0` dwords and a copy into miniport `+0x1DC + i*0x300`. There is no `repz cmpsd` in the section. The only `mov ecx, 0C0h` is in the kernel-debugger callback `0x193C50`. The displacement `+0x7DC` occurs only in the mode set `0x1959F8`, in the texture-state sync `0x198320` (a different structure), and in the vertical-blank handler `0x199960`, which consumes a pending ramp. Nothing writes a ramp into miniport `+0x1DC` except the identity setup in `CMiniport_InitHardware`. | `0x191F20` (0.27): `LoadVertexShader`. `0x1938A0` (0.244): `SetPalette`. `0x18FCF0` (0.235): `SetRenderStateNotInline`. |
| `D3DDevice_SetIndices` (`0x247430`, ret 8, k `0x80000`, `0xFFF80000`) | The only `0x80000`/`0xFFF80000` users are `SetStreamSource`, `SetTexture`, `SetPalette`, `InternalAddRef` and `InternalRelease`. No function stores an index buffer and `D3D_IndexData`. The title passes index pointers to `DrawIndexedVertices`. | `0x1938A0` (0.386): `SetPalette`. `0x18FCF0` (0.303): `SetRenderStateNotInline`. `0x191F20` (0.278): `LoadVertexShader`. |
| `D3DDevice_SetLight` (`0x246D70`, ret 8, k `0x8007000E`) | No `retn 8` function uses `0x8007000E`; the full list of users is in the `CreatePixelShader` row. | `0x1936F0` (0.179): `SetTexture`. `0x195710` (0.125): a surface-level helper. `0x1939A0` (0.125): the no-wait tile setter. |
| `D3DDevice_SetMaterial` (`0x2451D0`, ret 4, len 0x30) | Its body is `mov ecx, 11h; rep movsd` into the device, plus dirty `0x9000`. The only `mov ecx, 11h` in the section is in `InitializeFrameBuffers` `0x196030`. | `0x190460` (0.378): `SetRenderState_BackFillMode`. `0x1904C0` (0.35): `TwoSidedLighting`. `0x1900A0` (0.324): `FogColor`. |
| `D3DDevice_SetPixelShaderConstant` (`0x24E940`, ret 12, k `0x40A60-0x40A9C`, `0xC181C`) | None of those combiner-factor methods occurs in the section. | `0x195060` (0.111): `DrawVertices`. `0x18F730` (0.106): the adapter-mode enumeration. `0x191810` (0.097): the program copier. |
| `D3DDevice_SetTile` (`0x247A20`, len 0xA: `call KickOffAndWaitForIdle; jmp SetTileNoWait`) | The no-wait tile setter here is `0x1939A0` (`retn 8`). Its only callers are the frame-buffer code `0x195F10`, `0x196290` and `0x196460`. `KickOffAndWaitForIdle`'s callers include no 10-byte wrapper. | `0x192ED0` (0.667): `D3DDevice_BlockUntilIdle`, which is `jmp D3D_KickOffAndWaitForIdle`. `0x1977A0` (0.5): a jump-table stub. `0x192EE0` (0.5): `D3DDevice_KickPushBuffer`, which is `mov ecx, D3D_pDevice; jmp CDevice_KickOff`. |
| `D3DDevice_SetVertexShaderConstant1Fast` (`0x24BA70`, len 0x49) | 5558 links `SetVertexShaderConstant1` (0x5F) and `...1Fast` (0x49) side by side. 5233 has only the 0x5F body, `0x191C60`, which is the non-Fast one instruction for instruction. | `0x18FCC0` (0.703): a 2-dword fastcall pusher, `D3d8StateSymbols`' `SetRenderState_Simple`. `0x191C60` (0.556): `SetVertexShaderConstant1`, emitted under that name. `0x191CC0` (0.431): `SetVertexShaderConstant4`. |
| `D3DDevice_SwitchTexture` (`0x245300`, fastcall, ret 4) | Its body is a 3-dword push, `mov eax, [D3D_Device]; add eax, 0Ch; cmp eax, [D3D_Device+4]`. The bytes `A1 10 FA 19 00 83 C0 0C` do not occur in the section. | `0x191D70` (0.152): `SetVertexShaderConstantNotInlineFast`. `0x191E50` (0.051): the `SetVertexShaderConstant` wrapper. No other candidate has `ecx, edx` and `retn 4`. |
| `D3DResource_BlockUntilNotBusy` (`0x244BF0`: `jmp D3D_BlockOnResource`) | `D3D_BlockOnResource` `0x192CA0` has exactly two references, both calls: `0x18F9CD` and `0x197D21`. There is no jump thunk to it. 5558 places it after `IsBusy` in the resource object; in 5233 the resource-type getter `0x18FB60` is followed directly by `0x18FBF0` (5558 `0x244BC0`) and `InternalRelease`. | `0x192ED0` (1.0): **also a 5-byte `jmp`, but it jumps to `D3D_KickOffAndWaitForIdle` `0x192C80`.** That is the `BlockUntilIdle` thunk, which the title calls at `0x167F26` and `0x168344`. The normalized ratio cannot tell the two targets apart. `0x1977A0` (0.667) and `0x192EE0` (0.667): see the `SetTile` row. |
| `D3DResource_IsBusy` (`0x244B10`, ret 4, len 0x8A) | It needs four `test ..., 780000h` and a clear of the resource fence. The only `0x780000` users are `0x18FA50`, `InternalAddRef`, `0x18FB10`, `InternalRelease`, `0x192D20`, and two routines at `0x19D38F` and `0x19D410`. 5558's `0x244B10` slot (after `0x244A80`) is empty here. | `0x18FA50` (0.492): the in-use test used by `BlockOnResource` (5558 `0x244970`, len 0x35). `0x18FC20` (0.272): `InternalRelease`. `0x18FB10` (0.26): 5558 `0x244A30`, a resource release. |

`config/game.toml` keeps 0 for all 22. That is correct: there is no guest code to replace.

## Other functions identified (not targets, renamed in IDA)

| Address | Name used | Evidence |
| --- | --- | --- |
| `0x196590` | `CDevice_Init` | `retn 4`. Its only caller is `Direct3D_CreateDevice`. It allocates the `0x60`-byte fence page, calls `CDevice_InitPushBuffer` and `CMiniport_InitHardware`, creates DMA contexts and objects (`0x19A62B`, `0x19A416`, `0x19A6FA`), and starts the push buffer (`[0x80000000]` handshake, `wbinvd`, `CDevice_KickOff`). It then runs `InitializeFrameBuffers` `0x196030`, the mode set `0x1959F8`, `SetVertexShader(2)`, `SetRenderTarget`, `D3D_InitDefaultState`, `Clear`, the debugger block (`0xABCDEF00`), `SetFlickerFilter(5)` and `SetSoftDisplayFilter(0)`. |
| `0x196AF0` | `CDevice_UnInit` | Called by `Direct3D_CreateDevice` on failure and by `Release` at count 1. It calls `KickOffAndWaitForIdle` and frees. |
| `0x192460` | `CDevice_InitPushBuffer` | Push-buffer allocation; see the boot table. |
| `0x19A93D` | `CMiniport_InitHardware` [inference for the internal name] | `KeInitializeDpc`, `CMiniport_MapRegisters`, `0x19A475`, `HalGetInterruptVector(3)`, `KeInitializeInterrupt`/`KeConnectInterrupt` (ISR `0x199840`), `HalRegisterShutdownNotification`, two identity gamma ramps of `0x300` bytes from miniport `+0x1DC`, `out 80C0h`, and two `HalReadWritePCISpace` calls. |
| `0x19A44A` | `CMiniport_MapRegisters` [inference] | The boot fault. |
| `0x190BE0` | `D3D_SetRenderTargetInternal` | See `D3DDevice_SetRenderTarget`. |
| `0x193FC0` | `D3D_ApplyDisplayModeChange` | Takes `edi` = device. `KickOffAndWaitForIdle`, then `BlockUntilVerticalBlank` and `AvSetDisplayMode` in a loop, `AvSendTVEncoderOption`, and dropping the persisted display. Called from `Swap`'s helper `0x1948B0`. |
| `0x192ED0` | `D3DDevice_BlockUntilIdle` [inference for the name] | `jmp D3D_KickOffAndWaitForIdle`. Title calls at `0x167F26` and `0x168344`; also `0x19B289`. |
| `0x192EE0` | `D3DDevice_KickPushBuffer` [inference for the name] | `mov ecx, D3D_pDevice; jmp CDevice_KickOff`. Title calls at `0x15282E` and `0x158368`. |
| `0x192EF0` | (`D3DDevice_SetVerticalBlankCallback`, not renamed) | Stores its argument at `[dev+0x1958]`. The title calls it at `0x155383` to register `0x13960`, a bare `ret`, so the host's vertical-blank thread can call it with any argument list. This was `D3d8DataLayout`'s lead, and I checked it. |
| `0x18F690`, `0x18F730` | (IDirect3D8 mode queries, not renamed) | Identical to 5558 `0x243D40` and `0x243DE0`; called by the title at `0x12A906` and `0x12A941`. |
| `0x195760`, `0x195900` | (surface-lock wrappers) | Call `Lock2DSurface`; `retn 14h` and `retn 10h`. |
| `0x191E50` | (`SetVertexShaderConstant` wrapper) | 5558 `0x24BC50`. Copies into the shadow, then `SetVertexShaderConstantNotInlineFast`. |

## Notes for the integrator

1. **`D3DDevice_InsertCallback` needs a host body in this port.** There is none in `sdk/runtime` or
   `src/`. Copy Bustin' Out's from `src/game/hooks.cpp:48`. The title waits on it through its
   render thread: case 3, and case 5's flush at `0x152829`.
2. **Merge this file together with `config/found-d3d8-data.toml`.** The layout it depends on is
   proven. The host `Direct3D_CreateDevice` is the boot fix. The guest console paths that become
   live behind a host device are covered by the other names here: `KickOff`'s NV2A write,
   `MakeRequestedSpace`'s PFIFO read, `Swap`'s flip, and `Reset`'s mode set. After the merge, expect
   the next blocker to be `InsertCallback` (item 1).
3. **`D3DDevice_BeginPush` with an inlined `EndPush`.** The title's constant writer `0x152EC0`
   takes room from the host `BeginPush`, which returns the scratch buffer, writes
   `0x41EA4, 0x8C + 3n, 0x300B80/0x600B80, matrices` and stores the end straight into `[D3D_Device]`
   (`0x152FD6`). The host walker reads that at the next draw. This is the "inline constant packets"
   case the bring-up skill describes; it needs `CDevice_Push = 0`.
4. **`D3DDevice_Present`, `D3DDevice_GetBackBuffer` and `D3DDevice_GetDepthStencilSurface`, the
   3925-form names, must not be added for this title.** XDK 5233 has the 5558 forms.
