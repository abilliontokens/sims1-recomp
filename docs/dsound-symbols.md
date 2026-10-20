# DSOUND symbols in The Sims (XDK 5233)

Target image: `out/game.exe`, a flat PE of `assets/default.xbe` with guest addresses 1:1. The `DSOUND` section is
`0x1B5380-0x1BF060` (40132 bytes). Every library in this image is XDK build 5233.

Reference image: `out/sims5558.exe`, The Sims: Bustin' Out, XDK 5558, with its names applied. All 13 of its
sections are byte-identical to `simsbustinout/assets/default.xbe`. Its DSOUND section is `0x28B680-0x2B19F4`.

Target list: every `[symbols]` key of `sdk/xdk/5558/signatures.toml` tagged `sec = "DSOUND"`. That is 77 names.
The two `[anchors]` rows are not targets.

**Result: 33 of the 77 names are proven, plus the 2 `[data]` stream vtables. All are in `config/found-dsound.toml`,
unstaged. The other 44 names have no code in this image, so they are correct zeros. No name is left unproven.**

Every one of the 33 matches its 5558 namesake exactly on all five invariants: `ret`, `regs`, `len`, `calls` and `k`.
Each body is also byte-identical to its namesake once rel32 displacements and image addresses are masked. That
includes `DirectSoundCreate`, the one anchor that differed on the 3925 port. Where several 5558 functions share
one body, the callee chain decides the name (section 7).

## 1. Verdict: `CDirectSoundStream` IS linked in this title

This is the opposite of Fuzion Frenzy. On Fuzion Frenzy all 21 `CDirectSoundStream_*` names were correct zeros.
Here they are real targets: **12 of the 21 are proven and in the toml. The other 9 have no code in this image and
stay 0.**

| Proven (12) | Address | How the guest reaches it |
|---|---|---|
| `CDirectSoundStream_AddRef` | `0x1B5C0F` | vtable slot 0; the +4 adjustor `0x1B5F3A` |
| `CDirectSoundStream_Release` | `0x1B5C56` | vtable slot 1; the +4 adjustor `0x1B5F44` |
| `CDirectSoundStream_GetInfo` | `0x1B5CA4` | vtable slot 2 |
| `CDirectSoundStream_GetStatus` | `0x1B5DA3` | vtable slot 3 |
| `CDirectSoundStream_Process` | `0x1B5DF4` | vtable slot 4 (XMV `call [ecx+10h]` at `0x1BF84A`) |
| `CDirectSoundStream_Discontinuity` | `0x1B5D0B` | vtable slot 5 (XMV `call [ecx+14h]` at `0x1BF875` and `0x1BFCF9`) |
| `CDirectSoundStream_Flush` | `0x1B5D58` | vtable slot 6 |
| `CDirectSoundStream_FlushEx` | `0x1B5EBC` | forwarder `0x1B628D` (IDirectSoundStream_FlushEx), called by XMV at `0x1BF3A4` |
| `CDirectSoundStream_Pause` | `0x1B5E6B` | thunk `0x1B6288` (IDirectSoundStream_Pause): game ×4, XMV ×1 |
| `CDirectSoundStream_SetVolume` | `0x1B6038` | thunk `0x1B6279` (IDirectSoundStream_SetVolume): game ×2 |
| `CDirectSoundStream_SetMixBins` | `0x1B608A` | thunk `0x1B627E` (IDirectSoundStream_SetMixBins): game ×1 |
| `CDirectSoundStream_SetMixBinVolumes` | `0x1B60DC` | thunk `0x1B6283` (IDirectSoundStream_SetMixBinVolumes): game ×1 |

**Still 0, because this image has no code for them (9):** `SetFilter`, `SetFormat`, `SetFrequency`, `SetHeadroom`,
`SetI3DL2Source`, `SetMaxDistance`, `SetMinDistance`, `SetPosition` and `SetVelocity`. In 5558 each of these is
reached only through its own `IDirectSoundStream_*` entry. For SetFilter, SetHeadroom, SetFrequency, SetI3DL2Source
and SetFormat that entry is a 5-byte `jmp` thunk. For the four 3D setters it is a float-marshalling forwarder
(`0x29006C`, `0x290084`, `0x2900A1`, `0x2900CA`). This image has four stream thunks and one forwarder, listed in
section 4c, and none of them leads to these nine. Each of the nine would also be a lock-and-forward shim carrying
the `0x80004005` constant. The census in section 4b assigns every such shim in DSOUND, and none is left over.
The five 3D ones also need the DS3D engine, which is not linked at all (section 4d).

Related names:

- `DirectSoundCreateStream = 0x1B70C7` is proven. It is the stream factory API.
- `DSound_StreamVtable = 0x2004C4` and `DSound_StreamVtable2 = 0x2004B8` are proven and sit in the toml's `[data]`.
- `IDirectSoundStream_SetEG` is absent (section 4c).

### 1a. Evidence

1. **The vtables.** `.rdata` holds a 7-slot XMediaObject table and, just before it, the 3-slot secondary table of
   the object's `+4` base. The rets are 4, 4, 8, 8, 12, 4 and 4: AddRef, Release, GetInfo, GetStatus, Process,
   Discontinuity, Flush. That is the 5558 stream vtable `0x2F9038` slot for slot.

   | Address | Slot | Points to | 5558 at the same slot |
   |---|---|---|---|
   | `0x2004B8` | vtable2[0] | `0x1B6603` scalar-deleting dtor (calls `0x1B5BCE`, then frees through `0x1B724C` when `[esp+8]&1`) | `0x231947` (adjustor to the sdtor) |
   | `0x2004BC` | vtable2[1] | `0x1B5F3A` `sub dword [esp+4],4; jmp 0x1B5C0F` | `0x28D67A` (same adjustor to AddRef) |
   | `0x2004C0` | vtable2[2] | `0x1B5F44` `sub dword [esp+4],4; jmp 0x1B5C56` | `0x28D684` (same adjustor to Release) |
   | `0x2004C4` | vtable[0] | `0x1B5C0F` AddRef, ret 4 | `0x28CDBC` CDirectSoundStream_AddRef |
   | `0x2004C8` | vtable[1] | `0x1B5C56` Release, ret 4 | `0x28CE03` |
   | `0x2004CC` | vtable[2] | `0x1B5CA4` GetInfo, ret 8 | `0x28CE51` |
   | `0x2004D0` | vtable[3] | `0x1B5DA3` GetStatus, ret 8 | `0x28CF50` |
   | `0x2004D4` | vtable[4] | `0x1B5DF4` Process, ret 12 | `0x28CFA1` |
   | `0x2004D8` | vtable[5] | `0x1B5D0B` Discontinuity, ret 4 | `0x28CEB8` |
   | `0x2004DC` | vtable[6] | `0x1B5D58` Flush, ret 4 | `0x28CF05` |

   The 5558 secondary table `0x2F9028` has a fourth slot, the CRefCount final release `0x28B7D4`. In this build
   every refcounted DSOUND base has three slots (section 2), like 3925, so `vtable2` is `0xC` bytes below `vtable`.
   In 5558 the gap is `0x10`.

2. **The constructor `0x1B6AD1`** is a byte twin of the 5558 stream constructor `0x29048D`, ret 4. It builds the
   `+4` base with `0x1B6440`, the CDirectSoundVoice base constructor and a twin of 5558 `0x28EA7F`, then writes both
   tables:

   ```
   1b6ad1  push esi
   1b6ad2  mov  esi,ecx
   1b6ad4  push edi
   1b6ad5  push dword [esp+0Ch]
   1b6ad9  lea  edi,[esi+4]
   1b6adc  mov  ecx,edi
   1b6ade  call 1B6440                 ; CDirectSoundVoice base ctor on this+4 (stores 0x2004A0, overwritten below)
   1b6ae3  mov  dword [edi],2004B8h    ; [stream+4] = DSound_StreamVtable2
   1b6ae9  pop  edi
   1b6aea  mov  dword [esi],2004C4h    ; [stream+0] = DSound_StreamVtable
   1b6af0  mov  eax,esi
   1b6af2  pop  esi
   1b6af3  retn 4
   ```

   The 5558 constructor is the same instructions with `0x2F9028`/`0x2F9038`.

3. **The destructor `0x1B5BCE`** is the second witness for both values. It is entered with `ecx` = the `+4`
   subobject, restores both tables, and then releases the two attached objects at `+0x20`/`+0x1C` of the subobject:

   ```
   1b5bce  push esi
   1b5bcf  mov  esi,ecx                ; esi = stream+4
   1b5bd1  mov  eax,[esi+20h]
   1b5bd4  test eax,eax
   1b5bd6  mov  dword [esi-4],2004C4h  ; [stream+0] = DSound_StreamVtable
   1b5bdd  mov  dword [esi],2004B8h    ; [stream+4] = DSound_StreamVtable2
   ...
   1b5c0a  jmp  1B57A0                 ; base dtor
   ```

   Its only caller is the scalar-deleting dtor `0x1B6603`, which is `vtable2[0]`. The 5558 anchor function
   `DSound_StreamVtable_ref` is a 62-byte destructor entered with the object base. This one is 65 bytes and entered
   with `+4`, so the anchor's `insn 6`/`insn 7` rule cannot find these values in 5233 bytes. That is why they are
   proven by hand here.

4. **The factory.** `0x1B6BC0` is a byte twin of 5558 `0x290D63`, CDirectSound::CreateSoundStream, ret 16. It takes
   the DSOUND lock, allocates `0x28` bytes through `0x1B539F`, runs the constructor `0x1B6AD1` and initializes the
   stream through `0x1B6AF6` (5558 `0x290C05`, 170 bytes in both). It returns the stream through `arg 3`, and
   `E_OUTOFMEMORY` comes from the `0x7FF8FFF2`/`0x8007000E` idiom. Its only caller is `0x1B70F5` inside
   `DirectSoundCreateStream`.

5. **The API.** `DirectSoundCreateStream = 0x1B70C7` is called from two places:
   - **The game** at `0x163592`, in its stream setup `0x1634C0`. It first builds a PCM or ADPCM WAVEFORMATEX with
     the thunks `0x1B5558`/`0x1B555D`. It then passes `DSSTREAMDESC {dwFlags 0, dwMaxAttachedPackets 5,
     lpwfxFormat &wfx, lpfnCallback 0, lpvContext 0, lpMixBins 0}`; the stores are at `0x16357A`, `0x163586`
     and `0x16358E`. Next it calls `IDirectSoundStream_SetMixBins` at `0x16363D` and
     `IDirectSoundStream_SetMixBinVolumes` at `0x16364A`, both with `DSMIXBINS {8, 0x334A48}`. Last it calls
     `IDirectSoundStream_SetVolume(stream, 0)` at `0x163654`.
   - **XMV** at `0x1BF5F1`, in `0x1BF4C6`, with a descriptor at `[ebp-2Ch]`. It stores the stream in the array at
     `[xmv+0x134]`. `0x1BF6C9` then uses that array:
     - `call [ecx+10h]`, Process, at `0x1BF84A`;
     - `call [ecx+14h]`, Discontinuity, at `0x1BF875` and `0x1BFCF9`;
     - `IDirectSoundStream_Pause(stream, 2)`, DSSTREAMPAUSE_SYNCHPLAYBACK, at `0x1BF7E8`;
     - `DirectSoundCreate`, `IDirectSound_SynchPlayback` and `IDirectSound_Release` at `0x1BFB72`, `0x1BFB82` and
       `0x1BFB8D`.

6. **The game streams through it.** Besides the setup above, the game calls `IDirectSoundStream_Pause` with 0 at
   `0x163B7F` and `0x163EBD` and with 1 at `0x163E7D`. It calls `IDirectSoundStream_SetVolume` at `0x163E44` with a
   value from its volume table `0x20DD30`.

On Fuzion Frenzy the class was absent because 3925's DSOUND had no vtable, no factory and no allocation for it, and
nothing in the game created one. Here all four exist, and both the game and the XMV movie player create streams.

## 2. Facts about the 5233 DSOUND section

- **Extent.** Code runs `0x1B5380-0x1BE02F`, 36016 bytes and 390 function starts: 389 from the recompiler
  inventory, plus `0x1B7280`, which only the signer's start rule finds.
  - Four of the addresses named here are reached only through `jmp` thunks, so the recompiler did not list them:
    `0x1B5E6B`, `0x1B6038`, `0x1B608A` and `0x1B60DC`. Section 6 covers what that means for the build.
  - `0x1BE030-0x1BF060` is 4116 bytes of data: static WAVEFORMATEXs at `0x1BE030` (PCM, 48000 Hz), the silence
    block, the DSOUND lock and globals.
  - The inventory starts `0x1BE030`, `0x1BE0EF`, `0x1BE3A1`, `0x1BE6B1` and `0x1BEAD5` lie in that data and are
    not code.
- **Lock.** The API bodies take the DSOUND lock through `0x1B5471`, a twin of 5558 `0x28B973`. That function calls
  `RtlEnterCriticalSection(0x1BE810)` unless IRQL is already raised. The unlock is `push 1BE810h;
  call [1EE4F0h]`, xboxkrnl ordinal 294 `RtlLeaveCriticalSection`. The one exception found is
  CDirectSound::SynchPlayback `0x1B5686`, which calls the APU without the lock; its 5558 counterpart takes it
  (section 7.1).
- **Interface handles** match 5558 and 3925:
  - an `IDirectSound*` is `CDirectSound + 8`, and `DirectSoundCreate` returns `this+8`;
  - an `IDirectSoundBuffer*` is `CDirectSoundBuffer + 0x1C`;
  - every interface wrapper converts back with exactly one `lea ecx,[eax-8]`, `add eax,-8`, `lea ecx,[eax-1Ch]` or
    `add eax,-1Ch`.
- **Singleton.** The CDirectSound constructor `0x1B5584`, a twin of 5558 `0x28BE0B`, stores vtable `0x200488` and
  refcount 2 and publishes `this` in `0x1BEE90`. `DirectSoundDoWork` reads that global.
- **Refcount base: 3 slots, as in 3925; 5558 has 4.** Each table below is sdtor, AddRef, Release:

  | Class | Table | Slots |
  |---|---|---|
  | base | `0x200478` | `0x1B6786`, `0x1B543D`, `0x1B544A` |
  | CDirectSound | `0x200488` | `0x1B632E`, `0x1B55A1`, `0x1B67A2` |
  | CDirectSoundVoice | `0x2004A0` | `0x1B646A`, `0x1B543D`, `0x1B544A` |
  | CDirectSoundBuffer | `0x2004AC` | `0x1B6568`, `0x1B55A1`, `0x1B5964` |

  Slot 2 (`[vtbl+8]`) is Release in every class, and it is what both `*_Release` wrappers call:
  - `0x1B67A2` is a twin of 5558 CDirectSound::Release `0x290148`;
  - `0x1B5964` is a twin of 5558 CDirectSoundBuffer::Release `0x28C872`.

  With one slot fewer in the base, every later virtual slot sits 4 bytes lower than in 5558. Two near-twins
  differ in exactly that way: `call [eax+10h]` against `+14h` in `0x1B64C4`/`0x2902E4`, and `call [eax+18h]`
  against `+1Ch` in `0x1BB5D3`/`0x2995CE`.
- **No DSOUND `.XTLID` ids.** `.XTLID` at `0x344280` has 82 entries: 35 ids of the form `0x1xxxx`, 46 of `0x2xxxx`
  and one `0`. None has the DSOUND library id `0xB`, so the strongest proof, an xtlid, exists for no name here.
  Every name below rests on the invariants plus the callee chain.

### What a 40132-byte section implies

| Image | DSOUND section | Code | Function starts |
|---|---|---|---|
| Fuzion Frenzy (3925) | 110272 bytes, `0x206980-0x221840` | 33021 bytes, `0x206980-0x20EA7D` | 343, plus 6 fragments |
| **The Sims (5233)** | **40132 bytes** | **36016 bytes** | **390** |
| Bustin' Out (5558) | 156532 bytes | to `0x2B1472` | 1023 |

The size gap to Fuzion Frenzy is almost all data, not code. About 77 KB of Fuzion Frenzy's section is HRTF
coefficient tables and other data; this section carries 4 KB. The code sizes are comparable, 36016 bytes against
33021. This title has the stream class that Fuzion Frenzy lacks, and lacks the DS3D and HRTF code that Fuzion
Frenzy has.

Against the 5558 library this title links about 38% of the function count. What it links:

- the 2D buffer path (14 wrappers);
- the stream path (12 methods; the game's streamed audio and the XMV movie soundtrack);
- device create, release, DoWork and SynchPlayback;
- the effects-image download;
- PCM and ADPCM format helpers (`0x1B7280`, `0x1B72CA`) and a file media-object factory (`0x1B62CE`), none of
  them in the target list;
- the CMcpx APU, voice, buffer and stream engine under all of the above.

What it does not link, each checked in section 4:

- any DS3D code: no listener or voice 3D setter, no 3D commit, no DS3DBUFFER defaults;
- I3DL2;
- the HRTF installers and their tables;
- effect-data access;
- output meters;
- speaker-config and headphone calls;
- `Lock`/`Unlock`;
- `StopEx`;
- `XAudioDownloadEffectsImage`.

That is why 44 of the 77 target names are correct zeros.

## 3. Method

- **Reference validation.** The decoder in `tools/align_symbols.py` reproduces what `xbe_symbols` records. Run over
  `out/sims5558.exe`, it gives exactly the `len`, `ret`, `regs`, `k` and `calls` count that
  `sdk/xdk/5558/signatures.toml` records for **77 of 77** DSOUND names.
- **Twin.** Two functions are twins when their bytes are equal after masking every rel32 displacement and every
  operand in `0x10000-0x4000000`, the image addresses.
  - 248 of this section's functions have an exact twin in 5558 DSOUND.
  - Where 5558 has several functions with one body, the table in section 7 gives the count in the "share" column.
    Examples: 17 for the 28-byte buffer wrappers and 8 for the 82-byte stream shims. The callee chain then
    decides, read down to the level where the 5558 candidates differ.
- **Invariants.** `ret` and `regs` must match exactly, `calls` within ±1. For all 33 names, `len`, `calls` and `k`
  also match exactly.
- Every emission was read in the disassembly, and its game or XMV call site was checked for argument shape and
  meaning.
- All 33 names, the two vtables, the four stream thunks, the FlushEx forwarder, and the stream ctor, dtor and factory
  are renamed or labelled in the shared IDB.

## 4. Completeness inventories: why the 44 absent names are absent

### 4a. Interface wrappers: 18 exist, and all 18 are named

A raw byte scan of all DSOUND code (`0x1B5380-0x1BE02F`) for the four handle-adjust encodings finds 18 sites. They
are `8D 48 F8` and `83 C0 F8` for `IDirectSound*`, and `8D 48 E4` and `83 C0 E4` for `IDirectSoundBuffer*`. Every
site is at an instruction boundary, and each lies in a different function. In 5558, 47 of the 49 `IDirectSound*`
target names carry exactly one of these four instructions. The two that do not are `IDirectSoundBuffer_Unlock` and
`IDirectSoundStream_SetEG`.

- **IDirectSound (4):** `Release 0x1B54E1`, `DownloadEffectsImage 0x1B612E`, `SynchPlayback 0x1B6155`,
  `CreateSoundBuffer 0x1B6EB6`.
- **IDirectSoundBuffer (14):**
  - ret 4: `Release 0x1B54F7`, `Stop 0x1B6209`;
  - ret 8: `SetVolume 0x1B616D`, `SetMixBins 0x1B6189`, `SetMixBinVolumes 0x1B61A5`, `Pause 0x1B6221`,
    `GetStatus 0x1B625D`, `SetFormat 0x1B66BE`, `SetFrequency 0x1B66DA`;
  - ret 12: `SetLoopRegion 0x1B623D`, `SetPlayRegion 0x1B66F6`, `SetBufferData 0x1B6BA0`;
  - ret 16: `Play 0x1B61C1`, `PlayEx 0x1B61E5`.

So these 15 IDirectSound names have no wrapper:

- `CommitDeferredSettings`, `CommitEffectData`, `EnableHeadphones`
- `GetEffectData`, `GetOutputLevels`, `GetSpeakerConfig`
- `SetDistanceFactor`, `SetDopplerFactor`, `SetEffectData`
- `SetI3DL2Listener`, `SetMixBinHeadroom`, `SetOrientation`
- `SetPosition`, `SetRolloffFactor`, `SetVelocity`

And these 13 IDirectSoundBuffer names have none:

- `GetCurrentPosition`, `SetAllParameters`, `SetCurrentPosition`
- `SetFilter`, `SetHeadroom`, `SetI3DL2Source`
- `SetMaxDistance`, `SetMinDistance`, `SetOutputBuffer`
- `SetPosition`, `SetRolloffCurve`, `SetVelocity`
- `StopEx`

`Lock` and `Unlock` are handled in 4d.

### 4b. Lock-and-forward shims (`k` contains `0x80004005`): every one is assigned

These are all 38 DSOUND functions whose constants include E_FAIL:

| Function | Role |
|---|---|
| `0x1B55A1` | shared AddRef, slot 1 of CDirectSound and CDirectSoundBuffer |
| `0x1B5964` | CDirectSoundBuffer::Release |
| `0x1B67A2` | CDirectSound::Release |
| `0x1B5622` | CDirectSound::DownloadEffectsImage |
| `0x1B59AE` | Play impl |
| `0x1B59FF` | PlayEx impl |
| `0x1B5A58` | Stop impl |
| `0x1B5AA7` | Pause impl |
| `0x1B5AF8` | GetStatus impl |
| `0x1B5B49` | SetLoopRegion impl |
| `0x1B5F4E`, `0x1B5F9C`, `0x1B5FEA` | buffer SetVolume, SetMixBins, SetMixBinVolumes impls |
| `0x1B6583` | SetPlayRegion impl |
| `0x1B6622` | SetFormat impl |
| `0x1B6670` | SetFrequency impl |
| `0x1B69EA` | SetBufferData impl |
| `0x1B6BC0` | CreateSoundStream |
| `0x1B6CF6` | buffer init |
| `0x1B6DFF` | CreateSoundBuffer |
| `0x1B5C0F` to `0x1B5EBC` | the 9 stream methods of section 1 that are not setters |
| `0x1B6038`, `0x1B608A`, `0x1B60DC` | the 3 stream setters |
| `0x1B84A3` | called from DSOUND init `0x1B6EDA` |
| `0x1B92BE` | stream pause engine |
| `0x1BAE76` | buffer pause engine |
| `0x1BBD4B` | slot of the media-object vtable at `0x2005AC` |
| `0x1BD5B6` | internal helper (5558 `0x29C48C`) |
| `0x1BDC68` | internal helper (5558 `0x29CC76`) |

None is a further stream setter, a `SetEG`, a `StopEx` or an effect-data shim.

### 4c. jmp thunks: 7 exist

| Thunk | Target | Meaning | 5558 equivalent |
|---|---|---|---|
| `0x1B5558` | `0x1B7280` | PCM WAVEFORMATEX builder, ret 16: `wFormatTag = 1` | — (not a target) |
| `0x1B555D` | `0x1B72CA` | ADPCM WAVEFORMATEX builder, ret 12: `wFormatTag = 0x69`, `wBitsPerSample = 4`, `cbSize = 2`, 64 samples per block | — (not a target) |
| `0x1B6279` | `0x1B6038` | IDirectSoundStream_SetVolume | `0x28E17E` → `0x28DA06` |
| `0x1B627E` | `0x1B608A` | IDirectSoundStream_SetMixBins | `0x29002F` → `0x28F835` |
| `0x1B6283` | `0x1B60DC` | IDirectSoundStream_SetMixBinVolumes | `0x28E19C` → `0x28DBA0` |
| `0x1B6288` | `0x1B5E6B` | IDirectSoundStream_Pause | `0x28E1A1` → `0x28D018` |
| `0x1B75FD` | `0x1B73CB` | internal; called from the media object at `0x1BB9DC` | `0x292D54`, `0x292D8C`, `0x29304F` → `0x291C07` |

Among 5558's DSOUND function starts are 34 such thunks. They include `IDirectSoundStream_SetEG` (`0x28E18D` →
`0x28DAAA`) and the thunks to five of the nine absent stream setters: SetFilter `0x28E192`, SetHeadroom `0x28E197`,
SetFrequency `0x290025`, SetI3DL2Source `0x290140` and SetFormat `0x2907CE`. The four 3D setters are reached through
the forwarders named in section 1.

**`IDirectSoundStream_SetEG` is absent.** No fifth stream thunk exists here, and no DSOUND function carries the
envelope-register constants `0x0F000000`/`0x0FFFFFFF`. Those belong to 5558's envelope writer `0x2979BE`, which
SetEG's shim reaches through `0x28C534`.

### 4d. Other scans

- **`IDirectSoundBuffer_Unlock`.** The 5558 body, and the 3925 one, is `xor eax,eax; retn 14h`. The byte string
  `33 C0 C2 14 00` occurs nowhere in the whole image.
- **`IDirectSoundBuffer_Lock`.** No DSOUND function pops 32 bytes. Over the 396 code entries (the 390 starts plus
  the six thunk targets the recompiler did not list), the ret census is ret 4: 133, ret 0: 108, ret 8: 74,
  ret 12: 32, ret 16: 23, leaves by `jmp`: 22, ret 20: 4. Both the 5558 wrapper and its impl `0x28CBE3` are
  `retn 20h`.
- **`DirectSoundUseFullHRTF` and `DirectSoundUseLightHRTF`.**
  - Of the 36 functions that take the DSOUND lock, the only one with ret 0 is `DirectSoundDoWork`. The 5558 HRTF
    entries are lock, call, unlock, ret 0, 31 bytes.
  - No DSOUND function stores more than one code pointer. 5558's installers `0x293D0A` and `0x293D79` each store
    10. The only single-pointer stores are four 11-byte static initializers listed in `.data` (`0x20A72C`-`0x20A738`).
  - The data area is too small to hold the HRTF tables.
- **The 3D path.** None of these constants occurs in any DSOUND function:
  - 3D commit: `0x08420002`, `0x18400044`, `0x18000000`, `0x40000000`;
  - the DS3DBUFFER default `flMaxDistance` 1e9 (`0x4E6E6B28`), not even as raw bytes.

  Neither the 5558 3D deferred helper `0x28C59A` nor the 3D commit `0x2904B2` has a twin. So the listener and
  buffer 3D setters are absent, and so are `CommitDeferredSettings` and the five 3D stream setters.
- **`XAudioDownloadEffectsImage`.** The 5558 body (514 bytes) calls CDirectSound::DownloadEffectsImage `0x28BF62`.
  - Its twin here, `0x1B5622`, has exactly one caller: the IDirectSound wrapper at `0x1B614C`.
  - No DSOUND function carries `0x88780032` together with `0x80070000`.
  - The game does the job itself in `0x140C80`. It opens `d:\dsstdfx.bin` with CreateFile (`0xC75E1`), sizes it
    with `0xC7355`, reads it with `0xC6EE7`, and calls `IDirectSound_DownloadEffectsImage` at `0x140D8E`.
- **`DirectSoundCreateBuffer`.** Its 5558 body is byte-identical to `DirectSoundCreateStream`, and here only
  `0x1B70C7` has that body. That function calls the stream factory `0x1B6BC0`. The buffer factory `0x1B6DFF`, a twin
  of 5558 `0x290CC7`, has two callers only: `0x1B6ED2` in `IDirectSound_CreateSoundBuffer`, and `0x1B6FDA` in DSOUND
  init.

**Linked-out or never in 5233?** For none of the 44 can this image tell whether XDK 5233 had the API at all. None of
them is called, and an uncalled API leaves no code whichever XDK provides it. Either way the config value is 0. What
the image does show is that every API the title uses was already in 5233, including `SetPlayRegion`, `PlayEx`,
`SynchPlayback` and the stream `FlushEx`.

## 5. The boot list: what the guest calls, and the runtime warning

`sdk/runtime/xdk/dsound.cpp` prints `dsound: exports running their original code:` from `AuditExports()`. **On this
title that warning is blind, and its silence proves nothing.**

- The audit only lists `.XTLID` entries whose id has library id `0xB` (`id >> 16 != 0xB` skips the rest). This
  image's `.XTLID` has none (section 2).
- It runs only inside the host `DirectSoundCreate`, so it never ran while that name was 0.

The equivalent list comes from a raw scan of every `E8`/`E9 rel32` and every absolute pointer into DSOUND code.
Calls from `.text` and from XMV land on 29 distinct DSOUND addresses. One of them, `0x1B82C3`, is reached only from
the `.text` adjustor `0x181053` (`sub ecx,8; jmp`). That adjustor is the only slot of the secondary table
`0x200508`, which the object built by `0x1B79B4` keeps at `+8`. DSOUND init `0x1B6EDA` builds that object, the APU.
This is the same pattern as Fuzion Frenzy's `0x34711`, so it is not a game API call. The other 28 are below, plus the
stream vtable slots that XMV calls indirectly.

| Entry | Called from | After this merge |
|---|---|---|
| `DirectSoundCreate 0x1B7080` | game `0x140DED` (init `0x140DE0`), XMV `0x1BFB72` | host |
| `IDirectSound_DownloadEffectsImage 0x1B612E` | game `0x140D8E` | host |
| `IDirectSound_Release 0x1B54E1` | game `0x140F14`, XMV `0x1BFB8D` | host |
| `DirectSoundDoWork 0x1B62A5` | game `0x140705` (per frame), XMV `0x1BF3DA`, `0x1BFC40` | host |
| `IDirectSound_SynchPlayback 0x1B6155` | XMV `0x1BFB82` | host |
| `IDirectSound_CreateSoundBuffer 0x1B6EB6` | game `0x162C3A` | host |
| `IDirectSoundBuffer_SetVolume 0x1B616D` | game `0x162C45`, `0x1630D6`, `0x16317B`, `0x163219` | host |
| `IDirectSoundBuffer_Release 0x1B54F7` | game `0x162C9D` | host |
| `IDirectSoundBuffer_Pause 0x1B6221` | game `0x162CE9`, `0x16304B` | host |
| `IDirectSoundBuffer_SetFrequency 0x1B66DA` | game `0x162D4A`, `0x162D93`, `0x162DBD`, `0x1630AB`, `0x163150` | host |
| `IDirectSoundBuffer_GetStatus 0x1B625D` | game `0x162E0C`, `0x163059`, `0x163398` | host |
| `IDirectSoundBuffer_SetMixBins 0x1B6189` | game `0x162F10` | host |
| `IDirectSoundBuffer_SetMixBinVolumes 0x1B61A5` | game `0x162F1A` | host |
| `IDirectSoundBuffer_SetBufferData 0x1B6BA0` | game `0x162FFC` | host |
| `IDirectSoundBuffer_SetFormat 0x1B66BE` | game `0x16300C` | host |
| `IDirectSoundBuffer_SetPlayRegion 0x1B66F6` | game `0x1630BB`, `0x163160` | host |
| `IDirectSoundBuffer_SetLoopRegion 0x1B623D` | game `0x1630CB`, `0x163170` | host |
| `IDirectSoundBuffer_PlayEx 0x1B61E5` | game `0x162B04` (forwarder `0x162AF0`) | host |
| `IDirectSoundBuffer_Stop 0x1B6209` | game `0x163229` | host |
| `DirectSoundCreateStream 0x1B70C7` | game `0x163592`, XMV `0x1BF5F1` | host, needs the `[data]` vtables |
| thunk `0x1B6279` → `CDirectSoundStream_SetVolume` | game `0x163654`, `0x163E44` (tail jmp) | thunk is guest, jumps to host |
| thunk `0x1B627E` → `CDirectSoundStream_SetMixBins` | game `0x16363D` | thunk is guest, jumps to host |
| thunk `0x1B6283` → `CDirectSoundStream_SetMixBinVolumes` | game `0x16364A` | thunk is guest, jumps to host |
| thunk `0x1B6288` → `CDirectSoundStream_Pause` | game `0x163B7F`, `0x163DBF`, `0x163E7D`, `0x163EBD`, XMV `0x1BF7E8` | thunk is guest, jumps to host |
| forwarder `0x1B628D` → `CDirectSoundStream_FlushEx` | XMV `0x1BF3A4` | forwarder is guest, calls host |
| stream vtable slots 0-6 | XMV `0x1BF84A`, `0x1BF875`, `0x1BFCF9` (indirect) | host, through the guest vtable the host object carries |
| thunk `0x1B5558` → `0x1B7280` (PCM format) | game `0x163536` | guest |
| thunk `0x1B555D` → `0x1B72CA` (ADPCM format) | game `0x163555`, `0x163CBB` | guest |
| `0x1B62CE` (media-object factory, ret 12) | game `0x163661` | guest |

**What still runs original DSOUND code after the merge is harmless.** I followed direct calls from the three guest
entries and from the thunks and forwarder, stopping at named functions. I also followed the media object's 13 vtable
slots at `0x200590`-`0x2005C0`. The union is 52 functions. None of them touches an MCPX register (no `0xFE82xxxx`
constant), and none takes the DSOUND lock `0x1B5471`. The media object uses its own critical section, initialised in
its constructor `0x1BBCE8` through ordinal 291, and reads files through XAPI.

Without this file, guest `DirectSoundCreate` runs the CDirectSound and CMcpxAPU initialisation `0x1B6EDA` at
`0x140DED` on the first boot path. That is the "console code touches hardware the host never built" failure.

## 6. Host-body preconditions, checked

- **`DirectSoundCreateStream`** has `XDK_REQUIRE(CDirectSoundStream_Vtable, CDirectSoundStream_Vtable2,
  DSound_StreamVtable, DSound_StreamVtable2)`.
  - The two layout keys are already in `sdk/xdk/5233/layout.toml` as `0x0` and `0x4`, and they are right for 5233:
    constructor `0x1B6AD1` and destructor `0x1B5BCE` (section 1a). The file's comments cite the 5558 addresses
    `0x29048D`; the 5233 constructor is `0x1B6AD1`.
  - The two data symbols are in this file's `[data]`.
  - If `[data]` were not merged, the first stream creation would abort, naming the missing key. It would never
    corrupt memory silently. So nothing is staged, as agreed with Main.
- **`IDirectSound_DownloadEffectsImage`** has `XDK_REQUIRE(EffectsImage_Skip0, EffectsImage_Skip1,
  EffectsImage_Desc)`. Those are `0x804`, `0x80C` and `0x818` in `sdk/xdk/5233/layout.toml`, and they hold here. The
  5233 effects-image walker `0x1B7710` is an exact twin of 5558 `0x294000`, the function those layout comments
  cite:
  - `0x1B7723` `mov eax,[ebx+80Ch]`;
  - `0x1B7729` `add eax,[ebx+804h]`;
  - `0x1B7732` `lea esi,[ebx+eax*4+818h]`.

  The title discards the descriptor anyway: `&desc` at `0x140C80` is a dead local.
- **The buffer and stream bodies** read DSBUFFERDESC (`+4` flags, `+8` bytes, `+0xC` format, `+0x10` mix bins),
  DSSTREAMDESC (`+0`, `+4`, `+8`, `+0xC`, `+0x10`, `+0x14`) and DSMIXBINS (`{count, pairs}`). That is exactly the
  game's layout at `0x162B10`, `0x1634C0` and `0x162EB0`. They need no layout key.
- **Recompiler entry points.** `0x1B5E6B`, `0x1B6038`, `0x1B608A` and `0x1B60DC` are not in
  `generated/game/x86_func_mapping.cpp`; the recompiler folded each into the thunk that jumps to it.
  `sdk/tools/recomp/main.cpp` (lines 166-167) adds every non-zero `[symbols]` address to the entry points, so the
  re-run after the merge makes them functions. The thunks' `jmp` then reaches the host body. The runtime's own
  rule, "a jmp to a host version is covered by it", already assumes this.

## 7. Per-name evidence (33 names and 2 data symbols)

Invariants, reference / measured. The 5558 reference values are the `sdk/xdk/5558/signatures.toml` rows, reproduced
on `out/sims5558.exe`. `k` lists the constants ≥ `0x10000`. "Share" is the number of 5558 DSOUND functions with this
exact masked body. For all 33 rows, ret, regs, len and k are identical and calls are equal.

| Name | Address | 5558 | ret | regs | len | calls | k | share |
|---|---|---|---|---|---|---|---|---|
| `IDirectSound_Release` | `0x1B54E1` | `0x28BAE1` | 4 / 4 | [] / [] | 22 / 22 | 0 / 0 | - / - | 1 |
| `IDirectSoundBuffer_Release` | `0x1B54F7` | `0x28BB17` | 4 / 4 | [] / [] | 22 / 22 | 0 / 0 | - / - | 1 |
| `CDirectSoundStream_AddRef` | `0x1B5C0F` | `0x28CDBC` | 4 / 4 | [] / [] | 71 / 71 | 1 / 1 | 0x80004005 / 0x80004005 | 2 |
| `CDirectSoundStream_Release` | `0x1B5C56` | `0x28CE03` | 4 / 4 | [] / [] | 78 / 78 | 2 / 2 | 0x80004005 / 0x80004005 | 2 |
| `CDirectSoundStream_GetInfo` | `0x1B5CA4` | `0x28CE51` | 8 / 8 | [] / [] | 103 / 103 | 2 / 2 | 0x80004005 / 0x80004005 | 1 |
| `CDirectSoundStream_Discontinuity` | `0x1B5D0B` | `0x28CEB8` | 4 / 4 | [] / [] | 77 / 77 | 2 / 2 | 0x80004005 / 0x80004005 | 1 |
| `CDirectSoundStream_Flush` | `0x1B5D58` | `0x28CF05` | 4 / 4 | [] / [] | 75 / 75 | 2 / 2 | 0x80004005 / 0x80004005 | 1 |
| `CDirectSoundStream_GetStatus` | `0x1B5DA3` | `0x28CF50` | 8 / 8 | [] / [] | 81 / 81 | 2 / 2 | 0x80004005 / 0x80004005 | 2 |
| `CDirectSoundStream_Process` | `0x1B5DF4` | `0x28CFA1` | 12 / 12 | [] / [] | 119 / 119 | 3 / 3 | 0x80004005, 0x88780032 / same | 1 |
| `CDirectSoundStream_Pause` | `0x1B5E6B` | `0x28D018` | 8 / 8 | [] / [] | 81 / 81 | 2 / 2 | 0x80004005 / 0x80004005 | 2 |
| `CDirectSoundStream_FlushEx` | `0x1B5EBC` | `0x28D0C2` | 16 / 16 | [] / [] | 106 / 106 | 3 / 3 | 0x80004005 / 0x80004005 | 1 |
| `CDirectSoundStream_SetVolume` | `0x1B6038` | `0x28DA06` | 8 / 8 | [] / [] | 82 / 82 | 2 / 2 | 0x80004005 / 0x80004005 | 8 |
| `CDirectSoundStream_SetMixBins` | `0x1B608A` | `0x28F835` | 8 / 8 | [] / [] | 82 / 82 | 2 / 2 | 0x80004005 / 0x80004005 | 8 |
| `CDirectSoundStream_SetMixBinVolumes` | `0x1B60DC` | `0x28DBA0` | 8 / 8 | [] / [] | 82 / 82 | 2 / 2 | 0x80004005 / 0x80004005 | 8 |
| `IDirectSound_DownloadEffectsImage` | `0x1B612E` | `0x28DD4C` | 20 / 20 | [] / [] | 39 / 39 | 1 / 1 | - / - | 2 |
| `IDirectSound_SynchPlayback` | `0x1B6155` | `0x28DE54` | 4 / 4 | [] / [] | 24 / 24 | 1 / 1 | - / - | 3 |
| `IDirectSoundBuffer_SetVolume` | `0x1B616D` | `0x28DEDA` | 8 / 8 | [] / [] | 28 / 28 | 1 / 1 | - / - | 17 |
| `IDirectSoundBuffer_SetMixBins` | `0x1B6189` | `0x28FDCE` | 8 / 8 | [] / [] | 28 / 28 | 1 / 1 | - / - | 17 |
| `IDirectSoundBuffer_SetMixBinVolumes` | `0x1B61A5` | `0x28DF82` | 8 / 8 | [] / [] | 28 / 28 | 1 / 1 | - / - | 17 |
| `IDirectSoundBuffer_Play` | `0x1B61C1` | `0x28DF9E` | 16 / 16 | [] / [] | 36 / 36 | 1 / 1 | - / - | 6 |
| `IDirectSoundBuffer_PlayEx` | `0x1B61E5` | `0x28DFC2` | 16 / 16 | [] / [] | 36 / 36 | 1 / 1 | - / - | 6 |
| `IDirectSoundBuffer_Stop` | `0x1B6209` | `0x28DFE6` | 4 / 4 | [] / [] | 24 / 24 | 1 / 1 | - / - | 1 |
| `IDirectSoundBuffer_Pause` | `0x1B6221` | `0x28E022` | 8 / 8 | [] / [] | 28 / 28 | 1 / 1 | - / - | 17 |
| `IDirectSoundBuffer_SetLoopRegion` | `0x1B623D` | `0x28E062` | 12 / 12 | [] / [] | 32 / 32 | 1 / 1 | - / - | 9 |
| `IDirectSoundBuffer_GetStatus` | `0x1B625D` | `0x28E082` | 8 / 8 | [] / [] | 28 / 28 | 1 / 1 | - / - | 17 |
| `DirectSoundDoWork` | `0x1B62A5` | `0x28E214` | 0 / 0 | [] / [] | 41 / 41 | 2 / 2 | - / - | 1 |
| `IDirectSoundBuffer_SetFormat` | `0x1B66BE` | `0x290792` | 8 / 8 | [] / [] | 28 / 28 | 1 / 1 | - / - | 17 |
| `IDirectSoundBuffer_SetFrequency` | `0x1B66DA` | `0x28FD96` | 8 / 8 | [] / [] | 28 / 28 | 1 / 1 | - / - | 17 |
| `IDirectSoundBuffer_SetPlayRegion` | `0x1B66F6` | `0x290005` | 12 / 12 | [] / [] | 32 / 32 | 1 / 1 | - / - | 9 |
| `IDirectSoundBuffer_SetBufferData` | `0x1B6BA0` | `0x2907AE` | 12 / 12 | [] / [] | 32 / 32 | 1 / 1 | - / - | 9 |
| `IDirectSound_CreateSoundBuffer` | `0x1B6EB6` | `0x29128C` | 16 / 16 | [] / [] | 36 / 36 | 1 / 1 | - / - | 3 |
| `DirectSoundCreate` | `0x1B7080` | `0x2915DA` | 12 / 12 | [] / [] | 71 / 71 | 2 / 2 | - / - | 1 |
| `DirectSoundCreateStream` | `0x1B70C7` | `0x291678` | 8 / 8 | [] / [] | 87 / 87 | 3 / 3 | - / - | 2 |

In the chains below, "≡" means an exact masked twin and "~" means the same length, the same constants and the same
callee structure, differing only in a few structure-field displacements. Every body reads its arguments from the
stack only.

### 7.1 Device and free functions

#### DirectSoundCreate = 0x1B7080

- **Invariants.** 5558 `0x2915DA`: ret 12, regs [], len 71, calls 2, no k. Measured: ret 12, regs [], len 71,
  calls 2, no k. All hold, and the body is a unique twin. On the 3925 port this was the one non-twin anchor.
- **Chain.**
  - DSOUND lock `0x1B5471` ≡ `0x28B973`.
  - Get-or-create singleton `0x1B7013` ≡ `0x29156D`. It calls the allocator `0x1B539F` ≡ `0x28B6D9` and the
    constructor `0x1B5584` ≡ `0x28BE0B` (vtable `0x200488`, singleton `0x1BEE90`).
  - It then calls the initializer `0x1B6EDA` ~ `0x291434`: 313/313 bytes, the same `0x7FF8FFF2`/`0x8007000E`
    constants. That initializer creates the silence buffer through `0x1B6DFF`, `0x1B6BA0` and `0x1B61C1`, as 5558
    does through `0x290CC7`, `0x2907AE` and `0x28DF9E`.
  - It writes `this+8` to `*arg2`.
- **Callers.**
  - Game sound init `0x140DE0` at `0x140DED`: `DirectSoundCreate(0, &g_pDS = 0x32BB48, 0)`.
  - XMV `0x1BFB72`: `DirectSoundCreate(0, &pDS, 0)`, with `ebx = 0` pushed at `0x1BFB6C` and `0x1BFB71`.

#### DirectSoundCreateStream = 0x1B70C7

- **Invariants.** 5558 `0x291678`: ret 8, regs [], len 87, calls 3, no k. Measured the same.
- **The bytes are shared.** In 5558, `DirectSoundCreateBuffer` `0x291621` has the same body; here only `0x1B70C7`
  has it.
- **Chain: the third callee decides.**
  - The callees are lock `0x1B5471`, singleton `0x1B7013` ≡ `0x29156D`, then `0x1B6BC0` ≡ `0x290D63`.
  - `0x1B6BC0` is CDirectSound::CreateSoundStream. It allocates `0x28` bytes and runs the stream constructor
    `0x1B6AD1` ≡ `0x29048D` (section 1a).
  - DirectSoundCreateBuffer would call the buffer factory `0x1B6DFF` instead.
  - The body Releases its temporary CDirectSound reference with `call [eax+8]` at `0x1B7103`.
- **Callers.**
  - Game `0x163592` with `DSSTREAMDESC {0, 5, &wfx, 0, 0, 0}`.
  - XMV `0x1BF5F1`.

#### DirectSoundDoWork = 0x1B62A5

- **Invariants.** 5558 `0x28E214`: ret 0, regs [], len 41, calls 2. Measured the same. Unique twin.
- **Chain.** It takes the lock and reads the singleton `[0x1BEE90]`. If that is set, it calls `0x1B5695` ≡
  `0x28C291`, which takes the lock again and runs the APU work routine `0x1B7EAF` ~ `0x294946` (149/146 bytes, same
  callees). Then it unlocks.
- **Callers.** Game per-frame update `0x140700` at `0x140705`; XMV `0x1BF3DA` and `0x1BFC40`.

#### IDirectSound_Release = 0x1B54E1

- **Invariants.** 5558 `0x28BAE1`: ret 4, regs [], len 22, calls 0. Measured the same. Unique twin.
- **Body.** `mov eax,[esp+4]; lea ecx,[eax-8]; neg eax; sbb eax,eax; and eax,ecx; mov ecx,[eax]; push eax;
  call [ecx+8]; retn 4`. That is slot 2 of CDirectSound's table `0x200488`, `0x1B67A2` ≡ 5558 CDirectSound::Release
  `0x290148`.
- **Callers.** Game shutdown `0x140EC0` at `0x140F14` on `g_pDS`; XMV `0x1BFB8D`, right after SynchPlayback.

#### IDirectSound_CreateSoundBuffer = 0x1B6EB6

- **Invariants.** 5558 `0x29128C`: ret 16, regs [], len 36, calls 1. Measured the same. Three 5558 functions share
  the body.
- **Chain.** It calls `0x1B6DFF` ≡ `0x290CC7`, CDirectSound::CreateSoundBuffer, which carries k `0x7FF8FFF2`,
  `0x80004005` and `0x8007000E`. That function calls the allocator, the buffer constructor `0x1B6550` ≡ `0x28F0F7`
  (vtable `0x2004AC`), and the buffer init `0x1B6CF6` ~ `0x290AC4` (232/231 bytes).
- **Caller.** Game `0x162B10` at `0x162C3A`, run 48 times. It passes `(g_pDS, &DSBUFFERDESC, &buffer, NULL)`. The
  descriptor holds a PCM mono 44100 Hz 16-bit WAVEFORMATEX and a DSMIXBINS `{8, pairs}`. Each call is followed by
  `SetVolume(buffer, 0)`.

#### IDirectSound_DownloadEffectsImage = 0x1B612E

- **Invariants.** 5558 `0x28DD4C`: ret 20, regs [], len 39, calls 1. Measured the same.
- **The bytes are shared** with GetEffectData `0x28DD73`.
- **Chain: the callee decides.**
  - `0x1B5622` is a unique twin of `0x28BF62`, CDirectSound::DownloadEffectsImage.
  - Below it, `0x1B548F` (47/47) calls `0x1B78F1` ~ `0x29426D` (153/153, k `0xFFFFF7E8`). That function calls the
    image walker `0x1B7710` ≡ `0x294000` (section 6).
  - GetEffectData's callee `0x28C028` is a 95-byte effect-memory reader through `0x2943AF`. Nothing like it exists
    here.
- **Caller.** Game `0x140C80` at `0x140D8E`. It passes `(g_pDS, image, size, &DSEFFECTIMAGELOC {0, 1}, &desc)`,
  after reading `d:\dsstdfx.bin` itself.

#### IDirectSound_SynchPlayback = 0x1B6155

- **Invariants.** 5558 `0x28DE54`: ret 4, regs [], len 24, calls 1. Measured the same.
- **The bytes are shared** with CommitDeferredSettings and CommitEffectData.
- **Chain.**
  - The callee `0x1B5686` is `mov eax,[esp+4]; mov ecx,[eax+0Ch]; call 1B7FF8h; retn 4`: CDirectSound::SynchPlayback
    forwarding to the APU at `this+0xC`.
  - 5558's `0x28C18B` makes the same call inside the DSOUND lock.
  - The APU routine `0x1B7FF8` ~ `0x294AE5` is 319/319 bytes and 97/97 instructions. Its constant set is identical:
    `0x7FF8FFF2`, `0x8007000E`, `0xFE820010`, `0xFE820140`, `0xFE8202F8`, `0xFE8202FC` ×2 and `0xFFFF0000`. Only 4
    APU field displacements differ.
- **The other two candidates do not fit.** CommitDeferredSettings would reach the 3D commit (`0x2904B2`, absent).
  CommitEffectData would reach the DSP effect copy `0x29419C`.
- **Caller.** XMV `0x1BF6C9`. It first pauses its streams with `IDirectSoundStream_Pause(stream, 2)`, which is
  DSSTREAMPAUSE_SYNCHPLAYBACK, at `0x1BF7E8`. Then it calls `DirectSoundCreate`, `SynchPlayback(pDS)` at
  `0x1BFB82`, and `Release`. This is the documented synchronized start.

### 7.2 IDirectSoundBuffer wrappers

All 14 are byte twins of their namesakes.

#### IDirectSoundBuffer_Release = 0x1B54F7

- **Invariants.** 5558 `0x28BB17`: 4 / [] / 22 / 0. Measured the same. Unique twin.
- **Body.** `lea ecx,[eax-1Ch]` then `call [ecx+8]`: slot 2 of the CDirectSoundBuffer table `0x2004AC`. That slot
  holds `0x1B5964` ≡ CDirectSoundBuffer::Release `0x28C872`.
- **Callers.** Game `0x162C9D`, the loop over its 48 buffers in `0x162C88`; DSOUND's CDirectSound::Release at
  `0x1B6827`.

#### IDirectSoundBuffer_SetVolume = 0x1B616D

- **Invariants.** 5558 `0x28DEDA`: 8 / [] / 28 / 1. Measured the same. 17 bodies share these bytes.
- **Chain, strict twins three levels down.** `0x1B5F4E` ≡ `0x28D6AA`, then `0x1B5806` ≡ `0x28C505`, which is
  CDirectSoundVoice::SetVolume. That calls `0x1BA3BB` ≡ `0x29814D`, which writes SET_VOICE_TAR_VOLA/B/C at
  `0xFE820360/364/368`.
- **Callers.** `0x162C45` passes 0 after create; `0x1630D6` and `0x16317B` pass 0; `0x163219` passes -10000,
  DSBVOLUME_MIN, just before Stop.

#### IDirectSoundBuffer_SetMixBins = 0x1B6189

- **Invariants.** 5558 `0x28FDCE`: 8 / [] / 28 / 1. Measured the same.
- **Chain.** `0x1B5F9C` ≡ `0x28F26C`, then `0x1B5822`. Its leaves are `0x1B56EB` ~ `0x28E8E1` and `0x1BA2FA` ≡
  `0x29808C`, the mix-bin routing writer with `0xFE820300`/`0xFE820304`.
- **Why not MixBinVolumes.** `0x1B5822` shares its bytes with both 5558 `0x28EBD3` (SetMixBins) and `0x28C57D`
  (SetMixBinVolumes). The routing writer as leaf picks SetMixBins.
- **Caller.** `0x162EB0` at `0x162F10` with DSMIXBINS `{count, pairs}` at `0x3348A8 + 8*n`.

#### IDirectSoundBuffer_SetMixBinVolumes = 0x1B61A5

- **Invariants.** 5558 `0x28DF82`: 8 / [] / 28 / 1. Measured the same.
- **Chain.** `0x1B5FEA` ≡ `0x28D87E`, then `0x1B583F`. Its leaves are `0x1B56C6` ≡ `0x28C3FA` and the volume writer
  `0x1BA3BB` ≡ `0x29814D`.
- **Caller.** `0x162F1A`, immediately after SetMixBins and with the same DSMIXBINS.

#### IDirectSoundBuffer_Play = 0x1B61C1

- **Invariants.** 5558 `0x28DF9E`: 16 / [] / 36 / 1. Measured the same.
- **Chain.** `0x1B59AE` ≡ `0x28C8BC`, CDirectSoundBuffer::Play, a unique body. It calls the play engine `0x1BB347`
  ~ `0x29924C`: 176/176 bytes, k `0x182000`. The engine's own callees match position for position, among them
  `0x1B9D78` ≡ `0x29763A`, `0x1BA915` ~ `0x29876C` and `0x1BACF7` ~ `0x298B5A`.
- **Caller.** Only DSOUND's initializer `0x1B6EDA`, at `0x1B6FFC`. It plays the silence buffer right after
  `SetBufferData` at `0x1B6FEC`, exactly as 5558 `0x291434` does. The game never calls Play; it uses PlayEx.

#### IDirectSoundBuffer_PlayEx = 0x1B61E5

- **Invariants.** 5558 `0x28DFC2`: 16 / [] / 36 / 1. Measured the same.
- **Chain.** `0x1B59FF` ≡ `0x28C90D`, a body StopEx's `0x28C9B5` shares, then `0x1BB5D3` ~ `0x2995CE`.
- **Why PlayEx and not StopEx.** `0x1BB5D3` is the same 57 bytes as `0x2995CE` except `call [eax+18h]` against
  `+1Ch`, the vtable shift of section 2. It posts event **3** and falls back to the **play** engine `0x1BB347`.
  StopEx's `0x299607` posts 4 and calls the stop engine.
- **Caller.** Game forwarder `0x162AF0` at `0x162B04`. The routine `0x162FA0` calls it with `(buffer, 0, 0, 3)` or
  `(buffer, 0, 0, 2)`: a zero time stamp, DSBPLAY_FROMSTART, and DSBPLAY_LOOPING when looping.

#### IDirectSoundBuffer_Stop = 0x1B6209

- **Invariants.** 5558 `0x28DFE6`: 4 / [] / 24 / 1. Measured the same. Unique twin.
- **Chain.** `0x1B5A58` ≡ `0x28C966`, then the stop engine `0x1BB460` ~ `0x299365` (144/144 bytes, k `0x182000`).
- **Callers.** Game `0x163229`, after SetVolume(-10000); CDirectSound::Release at `0x1B67F5`.

#### IDirectSoundBuffer_Pause = 0x1B6221

- **Invariants.** 5558 `0x28E022`: 8 / [] / 28 / 1. Measured the same.
- **Chain.** `0x1B5AA7` ≡ `0x28CA0E`, then `0x1BAE76` ≡ `0x298CD9`, then `0x1B9D78` ≡ `0x29763A`, which writes the
  voice on/off register `0xFE820140`.
- **Callers.**
  - `0x162CE9` passes 1, DSBPAUSE_PAUSE.
  - `0x16304B` passes 0, resume, in a loop with GetStatus until the playing bit appears.

#### IDirectSoundBuffer_GetStatus = 0x1B625D

- **Invariants.** 5558 `0x28E082`: 8 / [] / 28 / 1. Measured the same.
- **Chain.** Strict twin five levels down: `0x1B5AF8` ≡ `0x28CAB8`, then `0x1BAEE9` ≡ `0x298D85`.
- **Callers.** `0x162E0C`, `0x163059` and `0x163398` test `status & 3` or `status & 1`; DSOUND calls it at `0x1B6811`.

#### IDirectSoundBuffer_SetLoopRegion = 0x1B623D

- **Invariants.** 5558 `0x28E062`: 12 / [] / 32 / 1. Measured the same. 9 bodies share these bytes.
- **Chain.**
  - `0x1B5B49` ~ `0x28CB09`: 133/133 bytes, 43/43 instructions, the same k (`0x80004005`, `0x88780032`, that is
    E_FAIL and DSERR_INVALIDCALL).
  - The only differences are 3 field displacements: `+0xC4/+0xC8/+0xCC` here against `+0xC8/+0xCC/+0xD0`.
  - It calls `0x1BB442` ≡ `0x299347`, which calls the play engine.
- **Callers.** `0x1630CB` and `0x163170`, as `SetLoopRegion(buffer, 0, size)`.

#### IDirectSoundBuffer_SetFormat = 0x1B66BE

- **Invariants.** 5558 `0x290792`: 8 / [] / 28 / 1. Measured the same.
- **Chain.**
  - `0x1B6622` ≡ `0x2906F2`, then `0x1B64C4` ~ `0x2902E4`.
  - `0x1B64C4` is 68/68 bytes and 24/24 instructions. Its only difference is `call [eax+10h]` against `+14h`.
  - Its four callees match position for position:
    - `0x1B6349` ~ `0x29025E`;
    - `0x1B56EB` ~ `0x28E8E1`;
    - `0x1BA2FA` ≡ `0x29808C`;
    - `0x1BA453` ~ `0x2981E5`: 146/146 bytes, k `0x182000` and `0xFE82037C`, SET_VOICE_TAR_PITCH.
- **Caller.** `0x16300C`, with `sample+8`, a WAVEFORMATEX, right after SetBufferData.

#### IDirectSoundBuffer_SetFrequency = 0x1B66DA

- **Invariants.** 5558 `0x28FD96`: 8 / [] / 28 / 1. Measured the same.
- **Chain.** `0x1B6670` ≡ `0x28F1D0`, then `0x1B6508` ≡ `0x28EB5B`. Its leaves are the Hz-to-pitch converter
  `0x1B550D` ~ `0x28BC1A` (75/74 bytes) and `0x1B57ED` ≡ `0x28C4EC`, which leads to the pitch writer.
- **Callers.** Five sites.
  - `0x162FA0` passes **188**, DSBFREQUENCY_MIN, when its pitch scale is 0.0 (`flt_1EE9D8` = 0.0).
  - Otherwise it passes a value from the sample header (`+4`) times that scale.

#### IDirectSoundBuffer_SetPlayRegion = 0x1B66F6

- **Invariants.** 5558 `0x290005`: 12 / [] / 32 / 1. Measured the same.
- **Chain.**
  - `0x1B6583` ~ `0x28F12A`: 128/128 bytes, 42/42 instructions, the same k, and 2 displacement differences
    (`+0xBC` against `+0xC0`).
  - It calls `0x1B652C` (36) and `0x1BB3F7` (75), which match `0x28F0D3` (36) and `0x2992FC` (75).
  - `0x1BB3F7` then calls `0x1BAAFE` ~ `0x298964` and the play engine.
- **Callers.** `0x1630BB` and `0x163160`, as `SetPlayRegion(buffer, 0, size)`, each immediately before
  SetLoopRegion.

#### IDirectSoundBuffer_SetBufferData = 0x1B6BA0

- **Invariants.** 5558 `0x2907AE`: 12 / [] / 32 / 1. Measured the same.
- **Chain.**
  - `0x1B69EA` ~ `0x2903C4`: 174/174 bytes, 60/60 instructions, 2 displacement differences.
  - Its callees match position for position:
    - `0x1BB664` ~ `0x299698`;
    - `0x1B695E` ~ `0x290338`: k `0x7FF8FFF2`, `0x80000000` and `0x8007000E`, with the pool allocator `0x1B71E4` ≡
      `0x2917F6` and the free `0x1B724C` ≡ `0x29185E`;
    - `0x1BB514` ~ `0x29950F`.
- **Callers.**
  - Game `0x162FFC`, as `(buffer, sample+24, *sample)`.
  - DSOUND init `0x1B6FEC`, for the silence buffer, as in 5558.

### 7.3 CDirectSoundStream methods

All 12 take the stream object itself as `this`. Each is a byte twin of its namesake and runs the DSOUND lock
`0x1B5471` ≡ `0x28B973` first.

#### CDirectSoundStream_AddRef = 0x1B5C0F

- **Invariants.** 5558 `0x28CDBC`: 4 / [] / 71 / 1, k `0x80004005`. Measured the same.
- **Evidence.** Strict twin five levels down. It is vtable slot 0 at `0x2004C4`, and the target of the `+4`
  adjustor `0x1B5F3A`.
- 5558 has a second function with these bytes, `0x29ADEC`. It belongs to a class that is not linked here, and this
  body is unique in 5233.

#### CDirectSoundStream_Release = 0x1B5C56

- **Invariants.** 5558 `0x28CE03`: 4 / [] / 78 / 2, k `0x80004005`. Measured the same.
- **Evidence.** Vtable slot 1, and the target of the adjustor `0x1B5F44`. The second callee is the shared CRefCount
  release `0x1B544A`, 35 bytes against 5558's 33.

#### CDirectSoundStream_GetInfo = 0x1B5CA4

- **Invariants.** 5558 `0x28CE51`: 8 / [] / 103 / 2, k `0x80004005`. Measured the same.
- **Evidence.** Unique twin; vtable slot 2.

#### CDirectSoundStream_GetStatus = 0x1B5DA3

- **Invariants.** 5558 `0x28CF50`: 8 / [] / 81 / 2, k `0x80004005`. Measured the same.
- **Evidence.**
  - Pause has the same 81 bytes.
  - GetStatus is fixed by vtable slot 3 and by its callee `0x1B87CF` ~ `0x2953A7`, the stream status engine (90/90
    bytes, k `0x40000`).
  - Pause's callee is the 142-byte pause engine.

#### CDirectSoundStream_Process = 0x1B5DF4

- **Invariants.** 5558 `0x28CFA1`: 12 / [] / 119 / 3, k `0x80004005` and `0x88780032`. Measured the same.
- **Evidence.**
  - Unique twin; vtable slot 4.
  - Its callees are `0x1B87CF` ~ `0x2953A7` and `0x1B91F0` ~ `0x295DD1` (206/206 bytes, k `0x8000000A` = E_PENDING
    and `0xFFFFF7FF`).
  - XMV calls it through `call [ecx+10h]` at `0x1BF84A`.

#### CDirectSoundStream_Discontinuity = 0x1B5D0B

- **Invariants.** 5558 `0x28CEB8`: 4 / [] / 77 / 2, k `0x80004005`. Measured the same.
- **Evidence.** Unique twin; vtable slot 5. XMV calls it through `call [ecx+14h]` at `0x1BF875` and `0x1BFCF9`.

#### CDirectSoundStream_Flush = 0x1B5D58

- **Invariants.** 5558 `0x28CF05`: 4 / [] / 75 / 2, k `0x80004005`. Measured the same.
- **Evidence.** Unique twin; vtable slot 6. Its callee is `0x1B8E47` ~ `0x295A29` (225/224 bytes). The callee's
  constants are `0x80004004` and `0xFFFFCFFF`. `0x80004004` is E_ABORT, the status the host also gives flushed
  packets.

#### CDirectSoundStream_FlushEx = 0x1B5EBC

- **Invariants.** 5558 `0x28D0C2`: 16 / [] / 106 / 3, k `0x80004005`. Measured the same.
- **Evidence.**
  - Unique twin.
  - Its only caller is the 24-byte forwarder `0x1B628D`. That forwarder is a twin of 5558 `0x28E1BE`, which
    forwards to `0x28D0C2`.
  - XMV calls the forwarder at `0x1BF3A4`.

#### CDirectSoundStream_Pause = 0x1B5E6B

- **Invariants.** 5558 `0x28D018`: 8 / [] / 81 / 2, k `0x80004005`. Measured the same.
- **Chain.** Its callee is `0x1B92BE` ≡ `0x295E9F`, the stream pause engine. That calls `0x1B8F38` ~ `0x295B19` and
  then `0x1B9D78` ≡ `0x29763A` twice.
- **How the guest reaches it.** Only through the thunk `0x1B6288`, as 5558's thunk `0x28E1A1` does.
- **Arguments at the call sites.**
  - 0, resume, at `0x163B7F` and `0x163EBD`.
  - 1, pause, at `0x163E7D`.
  - 2, synchronized start, at XMV `0x1BF7E8`.

#### CDirectSoundStream_SetVolume = 0x1B6038

- **Invariants.** 5558 `0x28DA06`: 8 / [] / 82 / 2, k `0x80004005`. Measured the same. 8 bodies share these bytes.
- **Chain.**
  - The callee is `0x1B5806` ≡ `0x28C505`. That is the same CDirectSoundVoice::SetVolume the buffer SetVolume uses,
    and it leads to `0x1BA3BB` ≡ `0x29814D`.
  - The look-alike SetHeadroom passes through `0x28C55A` (35 bytes) instead.
- **How the guest reaches it.** Only through the thunk `0x1B6279`, as 5558's `0x28E17E` does.
- **Callers.** Game `0x163654` passes 0 after create; `0x163E10` tail-jumps at `0x163E44` with a value from its
  volume table.

#### CDirectSoundStream_SetMixBins = 0x1B608A

- **Invariants.** 5558 `0x28F835`: 8 / [] / 82 / 2, k `0x80004005`. Measured the same.
- **Chain.** The callee is `0x1B5822`, whose leaves are `0x1B56EB` and the routing writer `0x1BA2FA` ≡ `0x29808C`.
  This is the chain of the 5558 stream and buffer SetMixBins.
- **How the guest reaches it.** Only through the thunk `0x1B627E`, as 5558's `0x29002F` does.
- **Caller.** Game `0x16363D` with `DSMIXBINS {8, 0x334A48}`.

#### CDirectSoundStream_SetMixBinVolumes = 0x1B60DC

- **Invariants.** 5558 `0x28DBA0`: 8 / [] / 82 / 2, k `0x80004005`. Measured the same.
- **Chain.** The callee is `0x1B583F`, whose leaves are `0x1B56C6` ≡ `0x28C3FA` and `0x1BA3BB` ≡ `0x29814D`.
- **How the guest reaches it.** Only through the thunk `0x1B6283`, as 5558's `0x28E19C` does.
- **Caller.** Game `0x16364A` with the same DSMIXBINS.

### 7.4 Data

#### DSound_StreamVtable = 0x2004C4

- **What it is.** The 7-slot XMediaObject table of section 1a. The 5558 counterpart is `0x2F9038`.
- **First witness.** The constructor `0x1B6AD1` stores it to `[stream+0]` at `0x1B6AEA`
  (`mov dword [esi],2004C4h`).
- **Second witness.** The destructor `0x1B5BCE` stores it at `0x1B5BD6` (`mov dword [esi-4],2004C4h`, with
  `esi = stream+4`).
- **Use.** The host `DirectSoundCreateStream` writes it to `obj + XDK_CDirectSoundStream_Vtable`, which is `+0`.
  Guest vtable calls then reach the named slot functions:
  - XMV's Process at `0x1BF84A`;
  - XMV's Discontinuity at `0x1BF875` and `0x1BFCF9`.

#### DSound_StreamVtable2 = 0x2004B8

- **What it is.** The 3-slot table of the `+4` subobject of section 1a. The 5558 counterpart is `0x2F9028`.
- **First witness.** The constructor `0x1B6AD1` stores it to `[stream+4]` at `0x1B6AE3` (`mov dword [edi],2004B8h`,
  with `edi = stream+4`).
- **Second witness.** The destructor `0x1B5BCE` stores it at `0x1B5BDD` (`mov dword [esi],2004B8h`).
- **Use.** The host writes it to `obj + XDK_CDirectSoundStream_Vtable2`, which is `+4`.

Both values are reached from the game through `DirectSoundCreateStream` (`0x163592`), then
`CDirectSound::CreateSoundStream` (`0x1B70F5` → `0x1B6BC0`), then the constructor (`0x1B6BFC` → `0x1B6AD1`). XMV
reaches them by the same path from `0x1BF5F1`.

## 8. Every target name

77 names: 33 proven, 44 absent from this build, 0 unproven.

| Name | Status | Address / reason |
|---|---|---|
| `CDirectSoundStream_AddRef` | proven | `0x1B5C0F` |
| `CDirectSoundStream_Discontinuity` | proven | `0x1B5D0B` |
| `CDirectSoundStream_Flush` | proven | `0x1B5D58` |
| `CDirectSoundStream_FlushEx` | proven | `0x1B5EBC` |
| `CDirectSoundStream_GetInfo` | proven | `0x1B5CA4` |
| `CDirectSoundStream_GetStatus` | proven | `0x1B5DA3` |
| `CDirectSoundStream_Pause` | proven | `0x1B5E6B` |
| `CDirectSoundStream_Process` | proven | `0x1B5DF4` |
| `CDirectSoundStream_Release` | proven | `0x1B5C56` |
| `CDirectSoundStream_SetFilter` | absent | no stream thunk or shim leads to a filter writer (4b, 4c) |
| `CDirectSoundStream_SetFormat` | absent | no stream thunk or shim; the format chain `0x1B64C4` is reached only from buffer SetFormat (4b, 4c) |
| `CDirectSoundStream_SetFrequency` | absent | no stream thunk or shim (4b, 4c) |
| `CDirectSoundStream_SetHeadroom` | absent | no stream thunk or shim (4b, 4c) |
| `CDirectSoundStream_SetI3DL2Source` | absent | no I3DL2 or 3D code (4d) |
| `CDirectSoundStream_SetMaxDistance` | absent | no 3D code (4d) |
| `CDirectSoundStream_SetMinDistance` | absent | no 3D code (4d) |
| `CDirectSoundStream_SetMixBins` | proven | `0x1B608A` |
| `CDirectSoundStream_SetMixBinVolumes` | proven | `0x1B60DC` |
| `CDirectSoundStream_SetPosition` | absent | no 3D code (4d) |
| `CDirectSoundStream_SetVelocity` | absent | no 3D code (4d) |
| `CDirectSoundStream_SetVolume` | proven | `0x1B6038` |
| `DirectSoundCreate` | proven | `0x1B7080` |
| `DirectSoundCreateBuffer` | absent | the only body of that shape is DirectSoundCreateStream; the buffer factory has no such caller (4d) |
| `DirectSoundCreateStream` | proven | `0x1B70C7` |
| `DirectSoundDoWork` | proven | `0x1B62A5` |
| `DirectSoundUseFullHRTF` | absent | no HRTF installer, no HRTF tables (4d) |
| `DirectSoundUseLightHRTF` | absent | same (4d) |
| `IDirectSoundBuffer_GetCurrentPosition` | absent | the three ret-12 buffer wrappers are SetLoopRegion, SetPlayRegion and SetBufferData (4a) |
| `IDirectSoundBuffer_GetStatus` | proven | `0x1B625D` |
| `IDirectSoundBuffer_Lock` | absent | no ret-32 function in DSOUND (4d) |
| `IDirectSoundBuffer_Pause` | proven | `0x1B6221` |
| `IDirectSoundBuffer_Play` | proven | `0x1B61C1` |
| `IDirectSoundBuffer_PlayEx` | proven | `0x1B61E5` |
| `IDirectSoundBuffer_Release` | proven | `0x1B54F7` |
| `IDirectSoundBuffer_SetAllParameters` | absent | no wrapper (4a); no 3D code (4d) |
| `IDirectSoundBuffer_SetBufferData` | proven | `0x1B6BA0` |
| `IDirectSoundBuffer_SetCurrentPosition` | absent | all seven ret-8 buffer wrappers carry other names (4a) |
| `IDirectSoundBuffer_SetFilter` | absent | same (4a) |
| `IDirectSoundBuffer_SetFormat` | proven | `0x1B66BE` |
| `IDirectSoundBuffer_SetFrequency` | proven | `0x1B66DA` |
| `IDirectSoundBuffer_SetHeadroom` | absent | all ret-8 buffer wrappers carry other names (4a) |
| `IDirectSoundBuffer_SetI3DL2Source` | absent | no wrapper (4a); no I3DL2 code (4d) |
| `IDirectSoundBuffer_SetLoopRegion` | proven | `0x1B623D` |
| `IDirectSoundBuffer_SetMaxDistance` | absent | no wrapper (4a); no 3D code (4d) |
| `IDirectSoundBuffer_SetMinDistance` | absent | no wrapper (4a); no 3D code (4d) |
| `IDirectSoundBuffer_SetMixBins` | proven | `0x1B6189` |
| `IDirectSoundBuffer_SetMixBinVolumes` | proven | `0x1B61A5` |
| `IDirectSoundBuffer_SetOutputBuffer` | absent | all ret-8 buffer wrappers carry other names (4a) |
| `IDirectSoundBuffer_SetPlayRegion` | proven | `0x1B66F6` |
| `IDirectSoundBuffer_SetPosition` | absent | no wrapper (4a); no 3D code (4d) |
| `IDirectSoundBuffer_SetRolloffCurve` | absent | the two ret-16 wrappers are Play and PlayEx (4a); no 3D code (4d) |
| `IDirectSoundBuffer_SetVelocity` | absent | no wrapper (4a); no 3D code (4d) |
| `IDirectSoundBuffer_SetVolume` | proven | `0x1B616D` |
| `IDirectSoundBuffer_Stop` | proven | `0x1B6209` |
| `IDirectSoundBuffer_StopEx` | absent | the two ret-16 wrappers are Play and PlayEx; the stop engine `0x1BB460` has no 57-byte StopEx caller (4a) |
| `IDirectSoundBuffer_Unlock` | absent | `33 C0 C2 14 00` occurs nowhere in the image (4d) |
| `IDirectSoundStream_SetEG` | absent | no SetEG thunk, no envelope writer (4c) |
| `IDirectSound_CommitDeferredSettings` | absent | the only ret-4 IDirectSound wrapper besides Release is SynchPlayback (4a); no 3D commit (4d) |
| `IDirectSound_CommitEffectData` | absent | same wrapper census (4a) |
| `IDirectSound_CreateSoundBuffer` | proven | `0x1B6EB6` |
| `IDirectSound_DownloadEffectsImage` | proven | `0x1B612E` |
| `IDirectSound_EnableHeadphones` | absent | the only four IDirectSound wrappers carry other names (4a) |
| `IDirectSound_GetEffectData` | absent | the only ret-20 IDirectSound wrapper is DownloadEffectsImage (4a) |
| `IDirectSound_GetOutputLevels` | absent | no wrapper (4a) |
| `IDirectSound_GetSpeakerConfig` | absent | no wrapper (4a) |
| `IDirectSound_Release` | proven | `0x1B54E1` |
| `IDirectSound_SetDistanceFactor` | absent | no wrapper (4a); no 3D code (4d) |
| `IDirectSound_SetDopplerFactor` | absent | no wrapper (4a); no 3D code (4d) |
| `IDirectSound_SetEffectData` | absent | no wrapper (4a) |
| `IDirectSound_SetI3DL2Listener` | absent | no wrapper (4a); no I3DL2 code (4d) |
| `IDirectSound_SetMixBinHeadroom` | absent | no wrapper (4a) |
| `IDirectSound_SetOrientation` | absent | no wrapper (4a); no 3D code (4d) |
| `IDirectSound_SetPosition` | absent | no wrapper (4a); no 3D code (4d) |
| `IDirectSound_SetRolloffFactor` | absent | no wrapper (4a); no 3D code (4d) |
| `IDirectSound_SetVelocity` | absent | no wrapper (4a); no 3D code (4d) |
| `IDirectSound_SynchPlayback` | proven | `0x1B6155` |
| `XAudioDownloadEffectsImage` | absent | the CDirectSound::DownloadEffectsImage twin has only the wrapper as caller; the game loads `dsstdfx.bin` itself (4d) |

## 9. Notes for the other agents

- **XMV, for the XGRPH/XMV owner.** These call sites into DSOUND are all proven above:
  - `0x1BF377` calls FlushEx through the forwarder at `0x1BF3A4` and DoWork at `0x1BF3DA`.
  - `0x1BF4C6` calls DirectSoundCreateStream at `0x1BF5F1`.
  - `0x1BF6C9` calls:
    - Pause(stream, 2) through the thunk at `0x1BF7E8`;
    - stream Process at `0x1BF84A` and Discontinuity at `0x1BF875` and `0x1BFCF9`, through the vtable;
    - DirectSoundCreate, SynchPlayback and Release at `0x1BFB72`, `0x1BFB82` and `0x1BFB8D`;
    - DoWork at `0x1BFC40`.

  Its stream pointers live in the array at `[xmv+0x134]`.
- **`sdk/xdk/5233/layout.toml`.** The DSOUND values hold for 5233, but the comments still cite 5558 addresses. The
  5233 equivalents are the stream constructor `0x1B6AD1` (5558 `0x29048D`) and the effects-image walker `0x1B7710`
  (5558 `0x294000`; it reads at `0x1B7723`, `0x1B7729` and `0x1B7732`). Changing them is for that file's owner.
- **The shared IDB** carries all 33 names and these labels: `DSound_StreamVtable`, `DSound_StreamVtable2`,
  `IDirectSoundStream_SetVolume`, `IDirectSoundStream_SetMixBins`, `IDirectSoundStream_SetMixBinVolumes`,
  `IDirectSoundStream_Pause`, `IDirectSoundStream_FlushEx`, `CDirectSoundStream_ctor`, `CDirectSoundStream_dtor` and
  `CDirectSound_CreateSoundStream`.
