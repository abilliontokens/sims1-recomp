# `.XTLID`, XAPI, XPP and CRT-math symbols in The Sims (XDK 5233)

Target: `out/game.exe`, the xbe2pe flat PE of `assets/default.xbe`, with guest addresses 1:1. Every address
below is this image's unless it is labelled with a sibling. Sources:

- `simsbustinout/assets/default.xbe` + `config/game.toml`: Bustin' Out, XDK 5558, `.XTLID` 479 rows.
- `urbz-recomp` and `sims2-recomp` `assets/default.xbe` + `config/game.toml`: The Urbz and The Sims 2, XDK 5849,
  174 and 173 rows.
- `sdk/xdk/{3925,5558,5849}/signatures.toml` and `config/ref/5558-signed.toml`.

## Result

| Name | Address | File | Strongest evidence | Status |
|---|---|---|---|---|
| `XMountUtilityDrive` | `0x0C64AB` | found-xtlid | `.XTLID` 0x10049; masked bytes identical to 5558/5849 | confirms config |
| `XInputOpen` | `0x1E7B7C` | found-xtlid | `.XTLID` 0x10036; masked bytes identical to 5558/5849 | confirms config |
| `XInputClose` | `0x1E7BD2` | found-xtlid | `.XTLID` 0x10037; masked bytes identical to 5558/5849 | confirms config |
| `XInputGetState` | `0x1E7DBC` | found-xtlid | `.XTLID` 0x10038; ret, regs, calls equal, k minus one 5558-only constant | confirms config |
| `XInputSetState` | `0x1E7E28` | found-xtlid | `.XTLID` 0x1003A; len, ret, regs, calls, k equal | confirms config |
| `XInitDevices` | `0x1E70D5` | found-xapi-crt | `.XTLID` 0x10031 is its thunk `jmp 0x1E70D5`; len, ret, regs, calls, k equal | **new** |
| `XLaunchNewImageA` | `0x0C796D` | found-xapi-crt | ret, regs, calls equal; same body as the 3911 API and the 5558 wrapper plus internal; the game's dashboard launch | **new** |
| `_CIacos` | `0x1759F4` | found-xapi-crt | 5849/5558 masked hash and the whole callee tree | **new** |
| `_CIasin` | `0x176F60` | found-xapi-crt | 5849/5558 masked hash and the whole callee tree | **new** |
| `crt_acos` | `0x175A11` | found-xapi-crt | unique 5849/5558 masked hash, whole callee tree, `fsqrt`/`fpatan`, OP 0xD + "acos" | **new** |
| `crt_asin` | `0x176F7D` | found-xapi-crt | unique 5849/5558 masked hash, whole callee tree, `fsqrt`/`fpatan`, OP 0xE + "asin" | **new** |
| `crt_pow` | `0x17714C` | found-xapi-crt | unique 5849/5558 masked hash, `fyl2x`, OP 0x1D + "pow" | confirms config |
| `[data] XPP_GamepadType` | `0x1E6C30` | found-xapi-crt | the type the game hands to every XInput/XGetDevices call; XInputOpen's own XID table points at it | **new** |
| `[data] XPP_MemoryUnitType` | `0x1E6CE0` | found-xapi-crt | the game's second XInitDevices type; the MU driver init pushes it, as the 5558 instruction does | **new** |

That is 6 new `[symbols]`, 2 new `[data]` and 6 confirmations. In this area, 7 names stay at 0: `crt_sin`,
`crt_cos`, `crt_tan`, `crt_atan`, `crt_log`, `crt_log10` and `crt_sqrt`. None of the seven is linked into this
image (see "Not emitted").

No contradiction was found. Every one of the 81 ids matches the function Bustin' Out publishes under the same id
in `ret` and `regs`, and so does every id that Urbz and Sims 2 publish (78 of 81). So no id-matched address
has a different calling convention from its sibling.

Every emitted name corroborates its reference record:

- `ret` and `regs` are equal to the 5558, 5849 and 3925 records for all 12 names.
- `calls` is equal for 11 names. `XLaunchNewImageA` has 2 calls against the reference's 1, which is within the
  ±1 band; its section explains why.

## Method

**`.XTLID`.** The section holds 8-byte `u32 id, u32 address` rows. Here it is at raw `0x214000`, virtual
`0x344280`, 656 bytes, 82 rows. I parsed it from each XBE's section table, as `xbe_symbols` `Exports()` does.

**Measuring tool.** I reimplemented the measurement part of `sdk/tools/symbols/main.cpp` in Python with capstone
5.0.7:

- **Sweep.** A linear sweep of the six code sections. A zero byte at an instruction start counts as one byte.
  Decoding is then restarted at rel32 call targets the sweep missed.
- **Masked FNV hash.** As in `SweepInstruction`/`MaskAddresses`.
- **`Extent`.** Branches are followed, bounded by the next rel32 call target or nonzero config symbol. These are
  the scanner's `Bounds`.
- **`Trace`.** Records registers read before written. A call writes eax, ecx and edx. `xor`/`sub`/`sbb r,r` and
  `push r` read nothing. It also records the `ret` immediates and `k`. `k` takes immediates and displacements
  of instructions that do not use the stack, between 0x40 and 0xFFFFFF00, that are not image addresses. imm8 is
  sign-extended as Zydis does.
- **`calls`.** The scanner's `ExternalTargets`: rel32 call/jump targets that leave the extent.

**Validation.** I ran the tool on Bustin' Out with its own config. For all **194 of 194** named functions it
reproduces the `config/ref/5558-signed.toml` record exactly, in each of `len`, `hash`, `ret`, `regs`, the
`calls` count and `k`. The numbers below are the SDK's own measure, not an approximation of it. Kernel import
slots come from `tools/xbe_info.py` (`Xbe.imports`) and `sdk/runtime/kernel/ordinals.cpp`.

## The 82 `.XTLID` rows

- **Row 0 is not a function.** It is `id 0, value 0x1471`, and 0x1471 is 5233, the XDK build. Bustin' Out's row 0
  holds 0x15B6 (5558) and Urbz's and Sims 2's hold 0x16D9 (5849). The value lies below the image base and in no
  section, so the row is discounted.
- **Rows 1-81 are 81 distinct ids:** 73 in `.text` and 8 in `XPP`, as measured.

**What the ids are.** Each identification below is read from this image's body (kernel ordinals, constants,
strings, argument count), not taken from a sibling.

- The 35 `0x1xxxx` ids are the Xbox half of XAPILIB: save games, signatures, sections, settings, physical memory,
  XInput and XPP.
- The 46 `0x2xxxx` ids are XAPILIB's Win32 surface over xboxkrnl: `CloseHandle`, `ReadFile`, `CreateThread`,
  `GetLastError`, `HeapFree` and so on. **None of them is a C-runtime routine.**
- No C-runtime function in this image has an id. Every one of the 81 addresses is an XAPI body; none is
  `strrchr`, `_CIacos`, `crt_acos`, `crt_asin`, `_CIpow` or `crt_pow`. In the siblings it is the same: their
  configs' `crt_pow`, `crt_acos`, `crt_asin`, `_CIacos` and `_CIasin` addresses appear in none of the Bustin' Out,
  Urbz or Sims 2 tables.
- This image publishes no `0x8xxxx` (D3D8), `0xBxxxx` (DSOUND), `0xDxxxx` (XGRAPHC) or `0xExxxx` (XMV) id at all,
  although Bustin' Out publishes 64, 168, 26 and 17 of them. **The `.XTLID` channel is empty for every D3D and
  DSOUND name in this build.**

**Siblings.** Bustin' Out publishes all 81 ids. Urbz and Sims 2 publish 78; they lack `0x20176` (`SetRect`),
`0x2017D` (`OffsetRect`) and `0x1002E` (`XGetGameRegion`).

Agreement with Bustin' Out at the same id:

| Measure | Agrees |
|---|---|
| `ret` | 81/81 |
| `regs` | 81/81 |
| `calls` | 78/81 equal, 80/81 within ±1 |
| length | 72/81 |
| masked bytes | 67/81 identical |

The one `calls` outlier is `0x10073` (`XCalculateSignatureEnd`): 4 calls here, 2 in 5558. 5558 rewrote it as a
dispatcher on the signature type, with `ret 8` and `regs []` unchanged. It is not a config name.

Urbz and Sims 2 agree on `ret` and `regs` for 78/78 ids each; 63/78 are byte-identical.

**What the siblings call the 76 other addresses.** Nothing. Every sibling config names exactly the five addresses
of rows 3, 74, 75, 77 and 78, plus the thunk target of row 79. Each of the other 76 addresses is an unnamed
`sub_` in all three siblings.

**Which ids reach a name the host replaces.** I checked the config `[symbols]` keys against
`sdk/runtime/xdk/xapi.cpp` and `crt_math.cpp`. The only keys any id can reach are `XMountUtilityDrive`,
`XInputOpen`, `XInputClose`, `XInputGetState`, `XInputSetState` and `XInitDevices`. `XLaunchNewImageA` is a key
with a host wrapper, but its id `0x1005A` is not in this image's table.

None of the other identified functions (`CloseHandle`, `XGetDevices`, `XInputGetCapabilities`, ...) is a config
key or has a host body, so they resolve to nothing and are not emitted. All 81 are renamed in the shared IDA
database, each with an `xtlid 0x....` comment.

Columns: *here* is this image's `len · ret (stack bytes) · regs · calls`. "same bytes" means the masked byte hash
over the whole extent is equal.

| # | id | address | sec | here: len · ret · regs · calls | Bustin' Out 5558, same id | Urbz · Sims 2 5849, same id | sibling config name | identified as (this image's body) | config key / host body → result |
|---|---|---|---|---|---|---|---|---|---|
| 0 | `0x00000` | `0x001471` | none | — | `0x0015B6` | `0x0016D9` · `0x0016D9` | — | header row: id 0 carries the XDK build, 0x1471 = 5233 (5558 = 0x15B6, 5849 = 0x16D9); below the image base, in no section | not a function → discounted |
| 1 | `0x200A5` | `0x0C6120` | .text | 0x64 · 0x4 · – · 0 | `0x1007F5` same bytes | `0x1F0D6E` same bytes · `0x21BE61` same bytes | unnamed | `GetSystemTime`: KeQuerySystemTime + RtlTimeToTimeFields into a SYSTEMTIME, no bias | no config key, no host body → nothing to emit |
| 2 | `0x200B5` | `0x0C6184` | .text | 0x8 · 0 · – · 0 | `0x100859` same bytes | `0x1F0DD2` same bytes · `0x21BEC5` same bytes | unnamed | `GetTickCount`: returns *KeTickCount | no config key, no host body → nothing to emit |
| 3 | `0x10049` | `0x0C64AB` | .text | 0x105 · 0x4 · – · 7 | `0x1035AF` same bytes | `0x1F2955` same bytes · `0x21B58B` same bytes | XMountUtilityDrive | `XMountUtilityDrive`: `\Device\Harddisk0\Partition%d\`, IoCreateSymbolicLink; byte-identical to 5558/5849 | key with host body → **found-xtlid** (confirms config) |
| 4 | `0x10008` | `0x0C6AA6` | .text | 0x263 · 0x18 · – · 14 | `0x22B60F` ret, regs equal; same length | `0x238BAD` ret, regs equal · `0x26144D` ret, regs equal | unnamed | `XCreateSaveGame`: NtCreateFile, `\SaveMeta.xbx`, `%lc%ls%lc%ls%ls` | no config key, no host body → nothing to emit |
| 5 | `0x1000A` | `0x0C6D09` | .text | 0x107 · 0x8 · – · 11 | `0x22B942` ret, regs equal; len 0x10A | `0x238EE0` ret, regs equal; len 0x10A · `0x261780` ret, regs equal; len 0x10A | unnamed | `XFindFirstSaveGame`: NtOpenFile + NtQueryDirectoryFile over save dirs, reads SaveMeta.xbx `Name` | no config key, no host body → nothing to emit |
| 6 | `0x1000B` | `0x0C6E10` | .text | 0x47 · 0x8 · – · 3 | `0x22BA4C` same bytes | `0x238FEA` same bytes · `0x26188A` same bytes | unnamed | `XFindNextSaveGame`: NtQueryDirectoryFile continuation of the 0x1000A handle | no config key, no host body → nothing to emit |
| 7 | `0x1000C` | `0x0C6E57` | .text | 0x4C · 0x4 · – · 3 | `0x22BA93` ret, regs equal; len 0x56 | `0x239031` ret, regs equal; len 0x56 · `0x2618D1` ret, regs equal; len 0x56 | unnamed | `XFindClose`: switches on find-handle tags 0x434F4E54/0x4E49434B/0x53425645/0xBE4BEA00, NtClose + LocalFree | no config key, no host body → nothing to emit |
| 8 | `0x200A1` | `0x0C6EA3` | .text | 0x1E · 0x4 · – · 1 | `0x101D04` same bytes | `0x1F0AE5` same bytes · `0x21BBD8` same bytes | unnamed | `CloseHandle`: NtClose, status to SetLastError | no config key, no host body → nothing to emit |
| 9 | `0x200A2` | `0x0C6EC1` | .text | 0x26 · 0x1C · – · 1 | `0x101D22` same bytes | `0x1F0B03` same bytes · `0x21BBF6` same bytes | unnamed | `DuplicateHandle`: NtDuplicateObject | no config key, no host body → nothing to emit |
| 10 | `0x20099` | `0x0C6EE7` | .text | 0xED · 0x14 · – · 1 | `0x107242` same bytes | `0x1F063C` same bytes · `0x21B72F` same bytes | unnamed | `ReadFile`: NtReadFile + NtWaitForSingleObject on STATUS_PENDING | no config key, no host body → nothing to emit |
| 11 | `0x20098` | `0x0C6FD4` | .text | 0xD6 · 0x14 · – · 1 | `0x10732F` same bytes | `0x1F0729` same bytes · `0x21B81C` same bytes | unnamed | `WriteFile`: NtWriteFile + NtWaitForSingleObject | no config key, no host body → nothing to emit |
| 12 | `0x2009C` | `0x0C70AA` | .text | 0x84 · 0x4 · – · 2 | `0x107405` same bytes | `0x1F07FF` same bytes · `0x21B8F2` same bytes | unnamed | `SetEndOfFile`: NtQueryInformationFile(FilePositionInformation 0xE) then NtSetInformationFile end-of-file | no config key, no host body → nothing to emit |
| 13 | `0x2009D` | `0x0C712E` | .text | 0xFA · 0x10 · – · 4 | `0x107489` same bytes | `0x1F0883` same bytes · `0x21B976` same bytes | unnamed | `SetFilePointer`: NtQueryInformationFile/NtSetInformationFile position, high-dword pointer | no config key, no host body → nothing to emit |
| 14 | `0x2009E` | `0x0C7228` | .text | 0xC8 · 0x14 · – · 2 | `0x107583` same bytes | `0x1F097D` same bytes · `0x21BA70` same bytes | unnamed | `SetFilePointerEx`: same with a LARGE_INTEGER distance and new-pointer out | no config key, no host body → nothing to emit |
| 15 | `0x2009A` | `0x0C72F0` | .text | 0x27 · 0x4 · – · 1 | `0x1077FC` same bytes | `0x1F0A45` same bytes · `0x21BB38` same bytes | unnamed | `FlushFileBuffers`: NtFlushBuffersFile | no config key, no host body → nothing to emit |
| 16 | `0x20097` | `0x0C7317` | .text | 0x3E · 0x8 · – · 1 | `0x107823` same bytes | `0x1F0A6C` same bytes · `0x21BB5F` same bytes | unnamed | `GetFileSizeEx`: NtQueryInformationFile class 0x22 (FileNetworkOpenInformation), copies EndOfFile | no config key, no host body → nothing to emit |
| 17 | `0x20096` | `0x0C7355` | .text | 0x3B · 0x8 · – · 2 | `0x107C6B` same bytes | `0x1F0AAA` same bytes · `0x21BB9D` same bytes | unnamed | `GetFileSize`: calls 0x20097, stores the high dword, SetLastError(0) on 0xFFFFFFFF | no config key, no host body → nothing to emit |
| 18 | `0x10071` | `0x0C74D9` | .text | 0x7D · 0x8 · – · 3 | `0x109739` ret, regs equal; len 0x41 | `0x1F5BDE` ret, regs equal; len 0x41 · `0x220871` ret, regs equal; len 0x41 | unnamed | `XCalculateSignatureBeginEx`: LocalAlloc(0x7C) context keyed by XboxSignatureKey/XboxAlternateSignatureKeys and a title id | no config key, no host body → nothing to emit |
| 19 | `0x10072` | `0x0C7556` | .text | 0x1A · 0xC · – · 1 | `0x10978E` ret, regs equal; len 0x4E, calls 2 | `0x1F5C33` ret, regs equal; len 0x4E, calls 2 · `0x2208C6` ret, regs equal; len 0x4E, calls 2 | unnamed | `XCalculateSignatureUpdate`: XcSHAUpdate(context+8, data, size) | no config key, no host body → nothing to emit |
| 20 | `0x10073` | `0x0C7570` | .text | 0x5D · 0x8 · – · 4 | `0x1097DC` ret, regs equal; len 0x45, calls 2 | `0x1F5C81` ret, regs equal; len 0x45, calls 2 · `0x220914` ret, regs equal; len 0x45, calls 2 | unnamed | `XCalculateSignatureEnd`: finishes the HMAC with XboxHDKey, frees the context | no config key, no host body → nothing to emit |
| 21 | `0x10070` | `0x0C75CD` | .text | 0x14 · 0x4 · – · 1 | `0x10977A` same bytes | `0x1F5C1F` same bytes · `0x2208B2` same bytes | unnamed | `XCalculateSignatureBegin`: calls 0x10071(flags, certificate TitleID [0x10118]+8) | no config key, no host body → nothing to emit |
| 22 | `0x10030` | `0x0C7B90` | .text | 0x22 · 0x14 · – · 1 | `0x101197` same bytes | `0x1F100D` same bytes · `0x21CBAB` same bytes | unnamed | `XQueryValue`: ExQueryNonVolatileSetting(5 args) + RtlNtStatusToDosError | no config key, no host body → nothing to emit |
| 23 | `0x20072` | `0x0C7BB2` | .text | 0x28 · 0 · – · 0 | `0x100F43` ret, regs equal; same length | `0x1F0EE5` ret, regs equal · `0x21BFD8` ret, regs equal | unnamed | `GetLastError`: reads the TLS error slot | no config key, no host body → nothing to emit |
| 24 | `0x20073` | `0x0C7BDA` | .text | 0x2E · 0x4 · – · 0 | `0x100F6B` ret, regs equal; same length | `0x1F0F0D` ret, regs equal · `0x21C000` ret, regs equal | unnamed | `SetLastError`: writes the TLS error slot (+4 here, +8 in 5558) | no config key, no host body → nothing to emit |
| 25 | `0x20075` | `0x0C7C1F` | .text | 0x65 · 0x10 · – · 3 | `0x1010DC` same bytes | `0x1F0F52` same bytes · `0x21C045` same bytes | unnamed | `GetOverlappedResult`: STATUS_PENDING 0x103 check, WaitForSingleObject, ERROR_IO_INCOMPLETE 0x3E4 | no config key, no host body → nothing to emit |
| 26 | `0x20046` | `0x0CA235` | .text | 0x17 · 0xC · – · 1 | `0x103BE2` same bytes | `0x1F2AF9` same bytes · `0x21D0A6` same bytes | unnamed | `HeapFree`: RtlFreeHeap(heap, flags, mem), BOOL from al | no config key, no host body → nothing to emit |
| 27 | `0x2002D` | `0x0CA252` | .text | 0x1D · 0x8 · – · 1 | `0x103BFF` same bytes | `0x1F2B16` same bytes · `0x21D0C3` same bytes | unnamed | `LocalAlloc`: RtlAllocateHeap(process heap [0x33A558], (uFlags>>3)&8 = HEAP_ZERO_MEMORY, size). [INFERENCE] GlobalAlloc would be the same body; `XMemAlloc` calls this one | no config key, no host body → nothing to emit |
| 28 | `0x20034` | `0x0CA26F` | .text | 0x1E · 0x4 · – · 1 | `0x103C5C` same bytes | `0x1F2B33` same bytes · `0x21D0E0` same bytes | unnamed | `LocalFree`: RtlFreeHeap(process heap, 0, mem), NULL on success. [INFERENCE] GlobalFree would be the same body; `XMemFree` calls this one | no config key, no host body → nothing to emit |
| 29 | `0x200BE` | `0x0CB028` | .text | 0x65 · 0xC · ebp · 2 | `0x102467` ret, regs equal; same length | `0x1F1CC9` ret, regs equal · `0x21D279` ret, regs equal | unnamed | `lstrcpynA`: SEH-guarded bounded byte copy (__SEH_prolog 0x175F20) | no config key, no host body → nothing to emit |
| 30 | `0x2006A` | `0x0CB3C2` | .text | 0x52 · 0x8 · – · 1 | `0x101D80` same bytes | `0x1F18DE` same bytes · `0x21CDB0` same bytes | unnamed | `SetThreadPriority`: ObReferenceObjectByHandle(PsThreadObjectType) + KeSetBasePriorityThread, 15/-15 saturate to 16/-16 | no config key, no host body → nothing to emit |
| 31 | `0x2006B` | `0x0CB414` | .text | 0x46 · 0x8 · – · 1 | `0x101E26` same bytes | `0x1F1930` same bytes · `0x21CE02` same bytes | unnamed | `SetThreadPriorityBoost`: ObReferenceObjectByHandle + KeSetDisableBoostThread | no config key, no host body → nothing to emit |
| 32 | `0x2007C` | `0x0CB45A` | .text | 0x26 · 0x4 · – · 1 | `0x101EAD` same bytes | `0x1F1976` same bytes · `0x21CE48` same bytes | unnamed | `SuspendThread`: NtSuspendThread | no config key, no host body → nothing to emit |
| 33 | `0x2007D` | `0x0CB480` | .text | 0x26 · 0x4 · – · 1 | `0x101ED3` same bytes | `0x1F199C` same bytes · `0x21CE6E` same bytes | unnamed | `ResumeThread`: NtResumeThread | no config key, no host body → nothing to emit |
| 34 | `0x2005C` | `0x0CB4A6` | .text | 0x56 · 0x10 · – · 0 | `0x101EF9` same bytes | `0x1F19C2` same bytes · `0x21CE94` same bytes | unnamed | `RaiseException`: builds an EXCEPTION_RECORD, RtlRaiseException | no config key, no host body → nothing to emit |
| 35 | `0x2006F` | `0x0CB4FC` | .text | 0x12 · none · – · 1 | `0x101F92` same bytes | `0x1F1A18` same bytes · `0x21CEEA` same bytes | unnamed | `ExitThread`: thread-notify callout 0xCB38A then PsTerminateSystemThread, int3; no return | no config key, no host body → nothing to emit |
| 36 | `0x2005E` | `0x0CB50E` | .text | 0x12 · 0x4 · – · 0 | `0x101FF0` same bytes | `0x1F1A2A` same bytes · `0x21CEFC` same bytes | unnamed | `SetUnhandledExceptionFilter`: swaps the filter global 0x33A550 | no config key, no host body → nothing to emit |
| 37 | `0x1005D` | `0x0CB520` | .text | 0x49 · 0x8 · – · 0 | `0x1020A2` same bytes | `0x1F1A3C` same bytes · `0x21CF0E` same bytes | unnamed | `XRegisterThreadNotifyRoutine`: links/unlinks a notify record on list 0x20B720 under critical section 0x20B704 | no config key, no host body → nothing to emit |
| 38 | `0x2005D` | `0x0CB569` | .text | 0x3C · 0x4 · – · 0 | `0x10214B` same bytes | `0x1F1A85` same bytes · `0x21CF57` same bytes | unnamed | `UnhandledExceptionFilter`: debugger hook (fs:[0x20]+0x250) then the 0x33A550 filter | no config key, no host body → nothing to emit |
| 39 | `0x20064` | `0x0CB63D` | .text | 0x6E · 0x18 · – · 1 | `0x10221F` same bytes | `0x1F1B59` same bytes · `0x21D02B` same bytes | unnamed | `CreateThread`: PsCreateSystemThreadEx | no config key, no host body → nothing to emit |
| 40 | `0x20066` | `0x0CB6AB` | .text | 0xD · 0 · – · 0 | `0x10228D` same bytes | `0x1F1BC7` same bytes · `0x21D099` same bytes | unnamed | `GetCurrentThreadId`: KTHREAD (fs:[0x28]) +0x12C | no config key, no host body → nothing to emit |
| 41 | `0x20089` | `0x0CB76F` | .text | 0x20 · 0x4 · – · 1 | `0x100200` same bytes | `0x1F04C7` same bytes · `0x21B0D7` same bytes | unnamed | `SetEvent`: NtSetEvent | no config key, no host body → nothing to emit |
| 42 | `0x2008A` | `0x0CB78F` | .text | 0x1E · 0x4 · – · 1 | `0x100220` same bytes | `0x1F04E7` same bytes · `0x21B0F7` same bytes | unnamed | `ResetEvent`: NtClearEvent | no config key, no host body → nothing to emit |
| 43 | `0x2008C` | `0x0CB808` | .text | 0x26 · 0xC · – · 1 | `0x100315` same bytes | `0x1F0560` same bytes · `0x21B170` same bytes | unnamed | `ReleaseSemaphore`: NtReleaseSemaphore | no config key, no host body → nothing to emit |
| 44 | `0x200D5` | `0x0CB82E` | .text | 0x44 · 0xC · – · 2 | `0x10040F` same bytes | `0x1F0586` same bytes · `0x21B196` same bytes | unnamed | `WaitForSingleObjectEx`: NtWaitForSingleObjectEx | no config key, no host body → nothing to emit |
| 45 | `0x200D4` | `0x0CB872` | .text | 0x52 · 0x8 · – · 1 | `0x10051A` same bytes | `0x1F05CA` same bytes · `0x21B1DA` same bytes | unnamed | `SleepEx`: KeDelayExecutionThread | no config key, no host body → nothing to emit |
| 46 | `0x2008E` | `0x0CB8C4` | .text | 0x12 · 0x8 · – · 1 | `0x10068C` same bytes | `0x1F061C` same bytes · `0x21B22C` same bytes | unnamed | `WaitForSingleObject`: calls 0x200D5(h, ms, FALSE) | no config key, no host body → nothing to emit |
| 47 | `0x20090` | `0x0CB8D6` | .text | 0xE · 0x4 · – · 1 | `0x1006B8` same bytes | `0x1F062E` same bytes · `0x21B23E` same bytes | unnamed | `Sleep`: calls 0x200D4(ms, FALSE) | no config key, no host body → nothing to emit |
| 48 | `0x10004` | `0x0CB95B` | .text | 0x21 · 0x4 · – · 1 | `0x102301` same bytes | `0x1F1C3B` same bytes · `0x21D1EB` same bytes | unnamed | `XLoadSectionByHandle`: XeLoadSection(h), returns section VA [h+4] | no config key, no host body → nothing to emit |
| 49 | `0x10005` | `0x0CB97C` | .text | 0x1E · 0x4 · – · 1 | `0x102322` same bytes | `0x1F1C5C` same bytes · `0x21D20C` same bytes | unnamed | `XFreeSectionByHandle`: XeUnloadSection(h) | no config key, no host body → nothing to emit |
| 50 | `0x10006` | `0x0CB99A` | .text | 0xA · 0x4 · – · 0 | `0x102376` same bytes | `0x1F1C7A` same bytes · `0x21D22A` same bytes | unnamed | `XGetSectionSize`: returns [h+8] (section virtual size) | no config key, no host body → nothing to emit |
| 51 | `0x1002D` | `0x0CB9A4` | .text | 0x25 · 0 · – · 1 | `0x103014` same bytes | `0x1F25F1` same bytes · `0x21DBA1` same bytes | unnamed | `XGetParentalControlSetting`: ExQueryNonVolatileSetting(XC_PARENTAL_CONTROL_GAMES 0xA) | no config key, no host body → nothing to emit |
| 52 | `0x10054` | `0x0CB9C9` | .text | 0x1B · 0 · – · 0 | `0x106F24` same bytes | `0x1F50A8` same bytes · `0x22011D` same bytes | unnamed | `XAutoPowerDownResetTimer`: KeSetTimer with a 6-hour due time (0xFFFFFFCD_B5659000) | no config key, no host body → nothing to emit |
| 53 | `0x20176` | `0x17EDF0` | .text | 0x24 · 0x14 · – · 0 | `0x22BD84` same bytes | not published · not published | unnamed | `SetRect`: stores left/top/right/bottom, returns TRUE | no config key, no host body → nothing to emit |
| 54 | `0x2017D` | `0x17EE14` | .text | 0x1D · 0xC · – · 0 | `0x22BDEE` same bytes | not published · not published | unnamed | `OffsetRect`: adds dx to left/right and dy to top/bottom, returns TRUE | no config key, no host body → nothing to emit |
| 55 | `0x20161` | `0x17EE31` | .text | 0x11 · 0x4 · – · 0 | `0x22AC60` same bytes | `0x1F0DDA` same bytes · `0x21BECD` same bytes | unnamed | `QueryPerformanceCounter`: rdtsc into the LARGE_INTEGER | no config key, no host body → nothing to emit |
| 56 | `0x20162` | `0x17EE42` | .text | 0x14 · 0x4 · – · 0 | `0x22AC71` same bytes | `0x1F0DEB` same bytes · `0x21BEDE` same bytes | unnamed | `QueryPerformanceFrequency`: stores 733333333 (0x2BB5C755) | no config key, no host body → nothing to emit |
| 57 | `0x1002B` | `0x17EE56` | .text | 0x49 · 0 · – · 3 | `0x22AC85` same bytes | `0x238371` same bytes · `0x260BC2` same bytes | unnamed | `XGetVideoFlags`: ExQueryNonVolatileSetting(XC_VIDEO_FLAGS 8) >>16 & 0x5F, masked by XGetAVPack/XGetVideoStandard | no config key, no host body → nothing to emit |
| 58 | `0x10064` | `0x17F223` | .text | 0x43 · 0x10 · – · 1 | `0x109FEF` same bytes | `0x1F5EB2` same bytes · `0x21D0FE` same bytes | unnamed | `XPhysicalAlloc`: MmAllocateContiguousMemoryEx | no config key, no host body → nothing to emit |
| 59 | `0x10066` | `0x17F266` | .text | 0x10 · 0xC · – · 0 | `0x10A065` same bytes | `0x1F5F22` same bytes · `0x21D16E` same bytes | unnamed | `XPhysicalProtect`: MmSetAddressProtect | no config key, no host body → nothing to emit |
| 60 | `0x10067` | `0x17F276` | .text | 0x6 · none · – · 0 | `0x10A075` same bytes | `0x1F5F32` same bytes · `0x21D17E` same bytes | unnamed | `XPhysicalFree`: jmp [MmFreeContiguousMemory] | no config key, no host body → nothing to emit |
| 61 | `0x2002B` | `0x17F27C` | .text | 0x4F · 0x4 · – · 0 | `0x22B172` same bytes | `0x238322` same bytes · `0x260C0B` same bytes | unnamed | `GlobalMemoryStatus`: MmQueryStatistics into a MEMORYSTATUS (dwLength 0x20, 0x7FFE0000 virtual) | no config key, no host body → nothing to emit |
| 62 | `0x10028` | `0x17F2CB` | .text | 0x3A · 0 · – · 2 | `0x22BD4A` same bytes | `0x23934B` ret, regs equal; len 0x2D, calls 1 · `0x261BEB` ret, regs equal; len 0x2D, calls 1 | unnamed | `XGetLanguage`: ExQueryNonVolatileSetting(XC_LANGUAGE 7), >9 falls back by XGetGameRegion | no config key, no host body → nothing to emit |
| 63 | `0x200F0` | `0x17F305` | .text | 0x2E · none · – · 0 | `0x22C147` same bytes | `0x2382F0` same bytes · `0x260B90` same bytes | unnamed | `OutputDebugStringA`: builds an ANSI_STRING, int 2Dh | no config key, no host body → nothing to emit |
| 64 | `0x20140` | `0x17F337` | .text | 0x65 · 0x8 · ebp · 2 | `0x22C179` same bytes | `0x239378` same bytes · `0x26575F` same bytes | unnamed | `IsBadReadPtr`: SEH-guarded read probe of every page in [p, p+n) | no config key, no host body → nothing to emit |
| 65 | `0x20141` | `0x17F39C` | .text | 0x69 · 0x8 · ebp · 2 | `0x22C1DE` same bytes | `0x2393DD` same bytes · `0x2657C4` same bytes | unnamed | `IsBadWritePtr`: SEH-guarded read-write probe of every page | no config key, no host body → nothing to emit |
| 66 | `0x20144` | `0x17F405` | .text | 0xE · 0x4 · – · 1 | `0x22C247` same bytes | `0x239446` same bytes · `0x26582D` same bytes | unnamed | `IsBadCodePtr`: calls 0x20140(p, 1) | no config key, no host body → nothing to emit |
| 67 | `0x1002A` | `0x17F413` | .text | 0x29 · 0 · – · 1 | `0x22C312` same bytes | `0x239454` same bytes · `0x261C18` same bytes | unnamed | `XGetVideoStandard`: byte 1 of ExQueryNonVolatileSetting(XC_FACTORY_AV_REGION 0x103) | no config key, no host body → nothing to emit |
| 68 | `0x10029` | `0x17F43C` | .text | 0x8 · 0 · – · 0 | `0x22C33B` same bytes | `0x23947D` same bytes · `0x261C41` same bytes | unnamed | `XGetAVPack`: returns *HalBootSMCVideoMode | no config key, no host body → nothing to emit |
| 69 | `0x1002E` | `0x17F444` | .text | 0x28 · 0 · – · 1 | `0x22C43D` same bytes | not published · not published | unnamed | `XGetGameRegion`: ExQueryNonVolatileSetting(XC_FACTORY_GAME_REGION 0x104) | no config key, no host body → nothing to emit |
| 70 | `0x1002C` | `0x1812C8` | .text | 0x42 · 0 · – · 2 | `0x232BD5` same bytes | `0x23B474` same bytes · `0x26562D` same bytes | unnamed | `XGetAudioFlags`: ExQueryNonVolatileSetting(XC_AUDIO_FLAGS 9), adjusted for AV packs 3 and 6 | no config key, no host body → nothing to emit |
| 71 | `0x2013D` | `0x181331` | .text | 0xCF · 0x4 · – · 1 | `0x232C3E` ret, regs equal; len 0xC9 | `0x23B4DD` ret, regs equal; len 0xC9 · `0x265696` ret, regs equal; len 0xC9 | unnamed | `CancelIo`: ObReferenceObjectByHandle(IoFileObjectType), walks the IdexChannelObject queue with a DPC | no config key, no host body → nothing to emit |
| 72 | `0x10069` | `0x181400` | .text | 0x6F · 0x8 · – · 2 | `0x108E9E` ret, regs equal; len 0xA0, calls 3 | `0x1F554F` ret, regs equal; len 0xA0, calls 3 · `0x21C100` ret, regs equal; len 0xA0, calls 3 | unnamed | `XMemAlloc`: default XMemAlloc: high attribute bit -> XPhysicalAlloc (0x10064) with page alignment/protect from the attributes, else LocalAlloc (0x2002D) | no config key, no host body → nothing to emit |
| 73 | `0x1006A` | `0x18146F` | .text | 0x1A · 0x8 · – · 2 | `0x108F3E` same bytes | `0x1F55EF` same bytes · `0x21C1A0` same bytes | unnamed | `XMemFree`: default XMemFree: XPhysicalFree (0x10067) or LocalFree (0x20034) by attribute bit 31 | no config key, no host body → nothing to emit |
| 74 | `0x10036` | `0x1E7B7C` | XPP | 0x56 · 0x10 · – · 4 | `0x2DAC65` same bytes | `0x2B1536` same bytes · `0x2D8336` same bytes | XInputOpen | `XInputOpen`: XID type lookup over 0x1E6C04..0x1E6C0C, SetLastError(0x57) on an unknown type; byte-identical to 5558/5849 | key with host body → **found-xtlid** (confirms config) |
| 75 | `0x10037` | `0x1E7BD2` | XPP | 0xC · 0x4 · – · 1 | `0x2DACBB` same bytes | `0x2B158C` same bytes · `0x2D838C` same bytes | XInputClose | `XInputClose`: `mov ecx,[esp+4]; call 0x1E8826; ret 4`; byte-identical to 5558/5849 | key with host body → **found-xtlid** (confirms config) |
| 76 | `0x1003B` | `0x1E7BDE` | XPP | 0x1DE · 0x8 · – · 5 | `0x2DACC7` ret, regs equal; len 0x1D8 | `0x2B1598` ret, regs equal; len 0x1D8 · `0x2D8398` ret, regs equal; len 0x1D8 | unnamed | `XInputGetCapabilities`: zeroes the XINPUT_CAPABILITIES out-buffer, sends XID control request 0xC1/1/wValue 0x0200, 0x48F when detached; game caller 0x12B623 | no config key, no host body → nothing to emit |
| 77 | `0x10038` | `0x1E7DBC` | XPP | 0x6C · 0x8 · – · 0 | `0x2DAE9F` ret, regs equal; len 0x73 | `0x2B1770` ret, regs equal; len 0x73 · `0x2D8570` ret, regs equal; len 0x73 | XInputGetState | `XInputGetState`: 0x57 on a wrong type, 0x48F detached, copies dwPacketNumber and the report; 5558 adds one `and byte [h+0A2h],0EFh` | key with host body → **found-xtlid** (confirms config) |
| 78 | `0x1003A` | `0x1E7E28` | XPP | 0x33 · 0x8 · – · 1 | `0x2DAF12` ret, regs equal; same length | `0x2B17E3` ret, regs equal · `0x2D85E3` ret, regs equal | XInputSetState | `XInputSetState`: k 0x40/0x41/0xA3 = reference; only `and`/`mov byte [fb+40h],0` encoding differs from 5558 | key with host body → **found-xtlid** (confirms config) |
| 79 | `0x10031` | `0x1E7EDF` | XPP | 0x5 · none · – · 1 | `0x2DB05E` same bytes | `0x2B1AB1` same bytes · `0x2D88B1` same bytes | thunk; its jmp target is `XInitDevices` in all three configs (0x2DA1B3, 0x2B0EC8, 0x2D7CC8) | `XInitDevices (public thunk)`: 5-byte `jmp 0x1E70D5`; in sbo the same id is `jmp 0x2DA1B3`, sbo config XInitDevices | key `XInitDevices` with host body → **found-xapi-crt** at the jmp target `0x1E70D5` |
| 80 | `0x10032` | `0x1E7EE4` | XPP | 0x22 · 0x4 · – · 0 | `0x2DB063` same bytes | `0x2B1AB6` same bytes · `0x2D88B6` same bytes | unnamed | `XGetDevices`: raises IRQL, returns [rec+0], clears [rec+4], [rec+8] = [rec+0] | no config key, no host body → nothing to emit |
| 81 | `0x10033` | `0x1E7F06` | XPP | 0x6D · 0xC · – · 0 | `0x2DB085` same bytes | `0x2B1AD8` same bytes · `0x2D88D8` same bytes | unnamed | `XGetDeviceChanges`: insertions/removals from Current/Previous/Changed, clears Changed | no config key, no host body → nothing to emit |

## Evidence per emitted name

Reference values are quoted as `len / hash / ret / regs / calls / k`. 3925 records carry only `ret`, `regs` and `k`.

### `XMountUtilityDrive = 0x0C64AB` (found-xtlid, confirms config)
- **Id.** `.XTLID` row 3 publishes id 0x10049 at this address. All three siblings publish the same id at their
  config's `XMountUtilityDrive`: Bustin' Out `0x1035AF`, Urbz `0x1F2955`, Sims 2 `0x21B58B`.
- **Reference.** 5558 and 5849: `0x105 / 0xAE7D3CB029BED347 / 4 / [] / 7 / [0x4000, 0xFFFFFEEC x3]`.
  3925: `ret 4`, `regs []`, the same k.
- **Measured.** `0x105 / 0xAE7D3CB029BED347 / 4 / [] / 7 / [0x4000, 0xFFFFFEEC x3]`. Every field is equal,
  including the masked hash, so the function is byte-identical (addresses masked) to 5558 and 5849.
- **Disassembly.**
  - `sub esp,114h`, then `push 1F38D4h` ("\Device\Harddisk0\Partition%d\") at `0x0C64EE` into `[ebp-114h]`.
    Its three `[ebp-114h]` operands are the k `0xFFFFFEEC` x3.
  - `mov esi,4000h` at `0x0C6501`.
  - RtlInitAnsiString (ordinal 289) loaded at `0x0C650E`; IoCreateSymbolicLink (ordinal 67) at `0x0C6587`.
  - `ret 4`.
- **Caller.** The XAPI startup routine `0x0CAA6B` (at `0x0CAB77`), which also reads LaunchDataPage.

### `XInputOpen = 0x1E7B7C` (found-xtlid, confirms config)
- **Id.** Row 74 publishes id 0x10036. The siblings' config `XInputOpen` carries the same id: Bustin' Out
  `0x2DAC65`, Urbz `0x2B1536`, Sims 2 `0x2D8336`.
- **Reference.** 5558 and 5849: `0x56 / 0xADCB23E069376F62 / 16 / [] / 4`. 3925: `ret 16`, `regs []`.
- **Measured.** `0x56 / 0xADCB23E069376F62 / 16 / [] / 4 / k []`. Byte-identical.
- **Disassembly.**
  - The type lookup `0x1E7E92` walks the XID class table `0x1E6C04..0x1E6C0C`, comparing `[entry+4]` with the type.
  - An unknown type calls `SetLastError(0x57)` (`0x0C7BDA`, id 0x20073) and returns NULL.
  - A NULL polling-parameter pointer takes the class default `[class+10h]`.
  - `cmp [ebp+10h],1; mov edx,[ebp+0Ch]; jne; add edx,10h` (bottom slot = port + 16), then the open in
    `0x1E8B9B`, then `ret 10h`.
- **Callers.** The game opens the gamepad with it at `0x12B99D` and `0x12BA91`, as `push 1E6C30h` (the gamepad
  type) then `call`.

### `XInputClose = 0x1E7BD2` (found-xtlid, confirms config)
- **Id.** Row 75 publishes id 0x10037. Siblings: `0x2DACBB`, `0x2B158C`, `0x2D838C`, each its config's
  `XInputClose`.
- **Reference.** 5558 and 5849: `0xC / 0xE51B784F4912F43 / 4 / [] / 1`. 3925: `ret 4`, `regs []`.
- **Measured.** Equal in every field, including the hash.
- **Disassembly.** `mov ecx,[esp+4]; call 1E8826h; ret 4`.
  - The same 12-byte shape also occurs at `0x1E7604`, XInitDevices' third callee. The id is what tells them apart.
  - The callee `0x1E8826` is 0x97 bytes against the reference callee's 0x94.
- **Caller.** The game at `0x12BA67`.

### `XInputGetState = 0x1E7DBC` (found-xtlid, confirms config)
- **Id.** Row 77 publishes id 0x10038. Siblings: `0x2DAE9F`, `0x2B1770`, `0x2D8570`, each its config's
  `XInputGetState`.
- **Reference.** 5558 and 5849: `0x73 / 0xE17394FE8915A614 / 8 / [] / 0 / [0xA2, 0xA3, 0xA3, 0x48F]`.
  3925: `ret 8`, `regs []`, the same k.
- **Measured.** `0x6C / 0x98446252EABD21A9 / 8 / [] / 0 / [0xA3, 0xA3, 0x48F]`. ret, regs and calls are equal.
  The length is inside the band: 7 bytes, 6%.
- **Disassembly.** Instruction for instruction 5558 `0x2DAE9F`, except that 5558 adds
  `and byte [edx+0A2h],0EFh`. That instruction is the 7 bytes and the 5558-only constant 0xA2. The body:
  - `KeRaiseIrqlToDpcLevel`.
  - `test byte [[h+0A3h]+28h],10h` returns 0x57 on a wrong type; a detached device gives 0x48F.
  - It copies `dwPacketNumber` from `[h+8]` and the report from `h+14h` with `rep movsd/movsb`.
  - `KfLowerIrql`, then `ret 8`.
- **Caller.** The game at `0x12B779`.

### `XInputSetState = 0x1E7E28` (found-xtlid, confirms config)
- **Id.** Row 78 publishes id 0x1003A. Siblings: `0x2DAF12`, `0x2B17E3`, `0x2D85E3`, each its config's
  `XInputSetState`.
- **Reference.** 5558 and 5849: `0x33 / 0xB8A1EA30C6441E92 / 8 / [] / 1 / [0x40, 0x41, 0xA3]`.
  3925: `ret 8`, `regs []`, the same k.
- **Measured.** `0x33 / 0xA53050801CDCDD50 / 8 / [] / 1 / [0x40, 0x41, 0xA3]`. Equal except the hash.
- **Disassembly.** The only difference from 5558 `0x2DAF12` is `and byte [edx+40h],0` here against
  `mov byte [edx+40h],0`: same length, same effect. The callee `0x1E88BD` (0x12E bytes) has the 5849 callee hash
  `0x8CC2092C9971EA6C`.
- **Callers.** The game at `0x12B71B` and `0x12BA5B`.

### `XInitDevices = 0x1E70D5` (found-xapi-crt, new)
- **Id.** Row 79 publishes id 0x10031 at `0x1E7EDF`, a 5-byte `jmp 1E70D5h`. The same id is a 5-byte thunk in
  every sibling, and each thunk jumps to that title's config `XInitDevices`:

  | Title | thunk | jmp target = config `XInitDevices` |
  |---|---|---|
  | Bustin' Out | `0x2DB05E` | `0x2DA1B3` |
  | Urbz | `0x2B1AB1` | `0x2B0EC8` |
  | Sims 2 | `0x2D88B1` | `0x2D7CC8` |

  The id therefore names the API's public entry, and all three siblings name the body.
- **Reference.** 5558 and 5849: `0x79 / 0x8FBA4792BD64DE2A / 8 / [] / 5 / [0x5C, 0x5D, 0x60, 0x70]`.
  3925: `ret 8`, `regs []`, the same k.
- **Measured at `0x1E70D5`.** `0x79 / 0xED9C76E38100264 / 8 / [] / 5 / [0x5C, 0x5D, 0x60, 0x70]`.
  - len, ret, regs, calls and k are all equal.
  - The callee lengths are in the same order: `0x5A, 0x151, 0xC, 0xA3, 0x42` here against
    `0x5A, 0x149, 0xC, 0xA3, 0x42`.
  - Three callees are byte-identical to the 5849 callees: `0x1E7604` (0xC, `0xE51B784F4912F43`), `0x1E7561`
    (0xA3, `0xAA0B4FA1D141A9FB`) and `0x1E7610` (0x42, `0x57440CC2F164E4C6`).
- **Disassembly.**
  - `push ebp; lea ebp,[esp-70h]; sub esp,0B4h` builds the 0xB4-byte resource structure on the stack, as 5558 does.
  - `0x1E94D5(ecx=struct, dwPreallocTypeCount, PreallocTypes)` fills it.
  - A loop over the class-driver table `0x1E6C14..0x1E6C24` calls `[entry+4](struct)`.
  - Then `0x1E7410(struct)`, `0x1E7604(&[ebp+60h])`, `0x1E7561(ecx=33A270h, byte [ebp+5Ch], byte [ebp+5Dh])`,
    `and byte [33A268h],0`, `0x1E7610()`, then `leave; ret 8`.
  - The k 0x5C, 0x5D and 0x60 are those frame operands; 0x70 is the frame bias.
- **Neighbour order.** The body sits 0xAA7 bytes before `XInputOpen` here and 0xAB2 bytes before it in Bustin'
  Out. The XPP anchors are in the same order in both images.
- **Callers.** Only the thunk. The game calls the thunk once, at `0x12B968`, as
  `XInitDevices(2, {{0x1E6C30, 8}, {0x1E6CE0, 8}})`.
- **Why the body.** It matches the siblings' configs and the signature records, which describe the body.
  `sdk/tools/recomp/main.cpp:166-167` turns every nonzero `[symbols]` address into a function entry.
  - Today `0x1E70D5` is not in `generated/game/x86_func_mapping.cpp`; it is a chunk of `sub_001E7EDF`, which
    xbe2pe exported as `_sub_001E7EDF_0`.
  - After the merge and a regeneration, the thunk's `jmp` becomes a tail call into the host body. That is how
    Fuzion Frenzy's `XInitDevices` works.
- **Host.** `HLE_STDCALL(XInitDevices, 2)` pops 8 bytes, which matches `ret 8`. It `XDK_REQUIRE`s:
  - `XPP_GamepadType`: proven below and emitted in the same file.
  - `XPP_Current`/`XPP_Changed`/`XPP_Previous`: `sdk/xdk/5233/layout.toml` has 0x0, 0x4 and 0x8.
    `XGetDevices` `0x1E7EE4` (id 0x10032) returns `[edx]` (`0x1E7EEF`), clears `[edx+4]` (`0x1E7EF1`) and stores
    Current into `[edx+8]` (`0x1E7EF7`). `XGetDeviceChanges` `0x1E7F06` (id 0x10033) tests `[esi+4]` (`0x1E7F0F`)
    and clears it (`0x1E7F50`).

  Nothing is missing, so the file is not staged.

### `XLaunchNewImageA = 0x0C796D` (found-xapi-crt, new)
- **No id here.** This image's `.XTLID` has no 0x1005A row. The siblings publish 0x1005A at their config's
  `XLaunchNewImageA` (`0x102564`, `0x1F1D2E`, `0x21D2DE`), so the name comes from the body and the convention.
- **Reference.** 5558 and 5849: `0x42 / 0x900544F31DC8414C / 8 / [] / 1`, a wrapper. 3925: `ret 8`, `regs []`.
- **Measured.** `0x13D / 0x7E3E1628B4F6DB6F / 8 / [] / 2`. k holds the path characters 0x44/0x5C/0x64
  (`D`, `\`, `d`), OBJ_CASE_INSENSITIVE 0x40, the 0x208/0x168 buffer sizes and the frame displacements
  `0xFFFFFE84` x4 and `0xFFFFFC7C` x2. The reference wrapper has no k to compare.
  - ret and regs are equal, and calls is within ±1.
  - The length is outside the band. 5233 implements the API in one function, as 3911 does in Fuzion Frenzy
    (`fuzion frenzy/docs/xapi-crt-symbols.md`: "3911 implements the API in one function, where 5849 has a 0x42-byte
    wrapper").
- **Disassembly.** In order, this one function is the 5558 public wrapper's code followed by the body of the 5558
  internal:
  - **Hook table.** It walks the one-slot launch-hook table `0x20A778..0x20A77C` and calls `[slot](path, ld)` when
    the slot is set. The 5558 wrapper `0x102564` starts with the same walk over `0x30877C..0x308780`.
  - **Path parse.** A non-NULL path must be `D`/`d` (`0x0C79A0`/`0x0C79A4`), then `:` (`0x0C79A8`), then `\`
    (`0x0C79AE`). Otherwise `push 57h; pop eax` (ERROR_INVALID_PARAMETER) at `0x0C79B4`.
  - **NULL path.** It pushes the certificate TitleID `[[0x10118]+8]` and `pLaunchData != NULL ? 1 : -1`
    (`setne al; lea eax,[eax+eax-1]`, `0x0C79D9`/`0x0C79DC`), then calls `0x0C7926`.
  - **Current D: device.**
    - NtOpenSymbolicLinkObject (ordinal 203) at `0x0C7A07`, on the ANSI_STRING `0x1F3A64` = "\??\D:".
    - NtQuerySymbolicLinkObject (215) at `0x0C7A2D`, with a 0x208-byte buffer.
    - NtClose (187) at `0x0C7A38`.
    - On failure it copies "\Device\Cdrom0" (`0x1F3A6C`).
  - **Reboot.** `0x0C7926` (`ret 14h`, XWriteTitleInfoAndReboot-shaped, as Fuzion Frenzy's `0x305BE`):
    - Writes the launch data page through `0x0C7845` (LaunchDataPage 164, MmPersistContiguousMemory 178).
    - Then `HalReturnToFirmware(2)` (ordinal 49) at `0x0C795C`, and RtlNtStatusToDosError on failure.
  - `ret 8`.
- **Callers.**
  - The game at `0x0B5110` and `0x0B5369`. `esi` is zeroed at `0x0B4FF1`, and no instruction on either path
    (`0x0B50A3`/`0x0B50B1` -> `0x0B5336`) writes it again. The calls pass
    `(NULL, &LAUNCH_DATA{dwReason = 2, dwParameter1 = 0x55 'U'})`. That is the dashboard "memory" launch for drive
    U:, reached after the game's free-space check on `T:\` (`0x0B5007`) and `T:\config.data`.
  - The XAPI helper `0x0CA775` (3 arguments) builds a zeroed 0xC00-byte LAUNCH_DATA and calls `(NULL, &ld)` at
    `0x0CA7C7`, falling back to HalReturnToFirmware at `0x0CA7D3`.
- **Host.** The `GUEST(XLaunchNewImageA)` wrapper reads the path at `esp+4`. It either runs this original body or
  returns with `Return(ctx, 2, 2)`, popping 2 arguments, which matches `ret 8`.

### CRT x87 math (LIBCMT 5233, `.text`)

The three x87 workers this CRT links (acos, asin, pow) and the two `_CI` wrappers are byte-for-byte the 5558/5849
code: their masked hashes are unique in `.text` and equal to the 5849 and 5558 records. Each worker takes `x` in
`st(0)`. Its loader (`0x179E94` for `_CI` callers, `0x179E51` for cdecl callers) leaves the exponent bits of the
high dword in `eax`, or the whole high dword when the exponent is 0x7FF, and the ZF of that compare; that is why
`regs = [eax]`. It reports errors with `mov edx, OP_<fn>` plus `lea ecx, "<fn>"`. The names are in `.data`:
"acos" `0x2172B4`, "asin" `0x2172D0`, "pow" `0x2172E0`.

Each function is laid out as follows. `crt_math.cpp`'s host bodies expect exactly this: `x` in st0, result in
st0, and `ret` popping only the return address.

- The `_CI` form: `sub esp,0Ch; fst qword [esp]; call 179E94h; call crt_<fn>; add esp,0Ch; ret`.
- The cdecl entry: `lea edx,[esp+4]; call 179E51h`, falling through into the worker.
- The worker.

Link order agrees with Bustin' Out:

| | `_CIacos` | `crt_acos` | `_CIasin` | `crt_asin` | `crt_pow` |
|---|---|---|---|---|---|
| here | `0x1759F4` | `0x175A11` | `0x176F60` | `0x176F7D` | `0x17714C` |
| Bustin' Out | `0x21EAD4` | `0x21EAF1` | `0x22085C` | `0x220879` | `0x220A24` |

`crt_X` sits at `_CIX + 0x1D` in both images. Every hash below was found by hashing **every byte offset** of
`.text` with each reference length.

#### `_CIacos = 0x1759F4`
- **Reference.** 5558 and 5849: `0x14 / 0x242CEA3CB8F35082 / 0 / [] / 2`. 3925: `ret 0`, `regs []`.
- **Measured.** Equal in every field. The hash has exactly two hits in `.text`, `0x1759F4` and `0x176F60`. The
  second callee decides between them: here it is `0x175A11`, `crt_acos`.
- **Callee tree.** The full two-level tree matches 5849 and 5558: the loader `0x179E94` and `crt_acos`.
- **Callers.** The game calls it 12 times, e.g. `0x0A8C5E`, `0x128C9A`, `0x1439C7`.

#### `_CIasin = 0x176F60`
- **Reference and measured.** As `_CIacos`. The second callee is `0x176F7D` (`crt_asin`), and the 5849/5558
  `_CIasin` callee tree matches in full.
- **Callers.** No caller: no rel32 call or jump, and no pointer in any section. It is linked dead code. Naming it is
  harmless and keeps the CRT object fully named.

#### `crt_acos = 0x175A11` (`0x175A11-0x175ABF`)
- **Reference.** 5558 and 5849: `0xAE / 0xECA88B2666FCEC33 / 0 / [eax] / 6 / [0x3FF00000, 0x80000000]`.
  3925: `ret 0`, `[eax]`, the same k.
- **Measured.** Equal in every field. The hash is unique in `.text`. The full callee tree matches 5849 and 5558:
  `0x179E21`, `0x179EAA` (twice), `0x179EB7`, `0x179E38` and `0x179DCF`.
- **Disassembly.**
  - `cmp eax,3FF00000h` at `0x175A25`.
  - `fsqrt` at `0x175A36` and `fpatan` at `0x175A3A`: atan2(sqrt((1+x)(1-x)), x).
  - `mov edx,0Dh` (OP_ACOS) at `0x175A49`/`0x175AAD` and `lea ecx,"acos"` at `0x175A4E`/`0x175AB2`.
  - `and ecx,80000000h` at `0x175A6C` and `fldpi` at `0x175A76`.
- **Callers.** Only `_CIacos` calls it (`0x1759FF`). The cdecl entry `0x175A08` falls through into it, but nothing
  calls that entry.

#### `crt_asin = 0x176F7D` (`0x176F7D-0x17702B`)
- **Reference.** 5558 and 5849: `0xAE / 0x67B152AC9353F8E6 / 0 / [eax] / 6 / [0x3FF00000, 0x80000000]`.
  3925: `ret 0`, `[eax]`, the same k.
- **Measured.** Equal in every field. The hash is unique, and the full callee tree matches.
- **Disassembly.**
  - `cmp eax,3FF00000h` at `0x176F91`.
  - `fsqrt` at `0x176FA2`, then `fpatan` at `0x176FA4` with no `fxch`: atan2(x, sqrt(...)).
  - `mov edx,0Eh` (OP_ASIN) at `0x176FB3`/`0x177019` and `lea ecx,"asin"` at `0x176FB8`/`0x17701E`.
  - `and ecx,80000000h` at `0x176FD6` and `fchs` at `0x176FE6`.
- **Callers.** Called only from `_CIasin`.

#### `crt_pow = 0x17714C` (confirms config)
- **Reference.** 5558 and 5849:
  `0x1C5 / 0x1FBDF1CEC7DD4478 / 0 / [eax] / 16 / [0x7FF00000 x5, 0x7FFFFFFF]`. 3925: `ret 0`, `[eax]`,
  the same k.
- **Measured.** Equal in every field. The hash is unique. All 16 first-level callees match. One second-level
  callee (0x61 bytes against 0x65) does not. Fuzion Frenzy's `crt_pow` also differs from 5849 in exactly one
  second-level callee.
- **Disassembly.**
  - `and/cmp ecx,7FF00000h` at `0x177160`/`0x17716A`.
  - `fyl2x` at `0x177199`.
  - `lea ecx,"pow"` with `mov edx,1Dh` (OP_POW) at `0x1771B4`/`0x1771BA` and `0x1771D1`/`0x1771D7`.
- **Caller.** Its `_CI` form `_CIpow` `0x177128` (`fxch; fstp [esp]; fst [esp+8]; call crt_pow`), which the game
  calls once, at `0x167888`. `_CIpow` is not a config name.

### `[data] XPP_GamepadType = 0x1E6C30` (found-xapi-crt, new)
- **The game uses it as the gamepad type everywhere.**

  | Call | Site |
  |---|---|
  | `XGetDevices` | `0x12B96D` |
  | `XInputOpen` | `0x12B998`, `0x12BA8C` |
  | `XGetDeviceChanges` | `0x12BA05` |
  | `XInitDevices` preallocation, first entry | `0x12B958` |

  Those are the only code references.
- **The library points at it.** `XInputOpen`'s XID class lookup reads the table `0x1E6C04` = `{0x1E6C68, 0x1E6CB0}`.
  The class at `0x1E6C68` has `+4 = 0x1E6C30`, the field the lookup compares with the type argument. The other
  XID class (`0x1E6CB0`) points at `0x1E6C94`.
- **The record has the right shape.** At `0x1E6C30` sit three zero dwords: Current, Changed and Previous, which
  `XGetDevices` reads and writes at +0, +4 and +8.
- **The sibling agrees.** The first 0x1A0 bytes of XPP have the same layout as Bustin' Out's:
  - 70 dwords are equal.
  - 18 are data pointers displaced by exactly 0xF30E0 (`0x1E6C00` here, `0x2D9CE0` there).
  - The other 16 are code pointers, or pointers packed after a byte.

  Bustin' Out's XTLID 0x1007C, its `XPP_GamepadType`, is `0x2D9D10`: the same `+0x30` from the section start.
- **Host.** `xapi.cpp` uses it as `kGamepadType`.
  `generated/game/image_symbols.h` currently has `SYM_XPP_GamepadType 00000000`, so the host `XInputOpen`,
  which is already named, rejects the game's `0x1E6C30`. See the observations below.

### `[data] XPP_MemoryUnitType = 0x1E6CE0` (found-xapi-crt, new)
- **The game passes it to `XInitDevices`.** It is the second preallocation entry, `{0x1E6CE0, 8}`, at
  `0x12B960`.
- **The memory-unit driver's init uses it.** It does `push 1E6CE0h; call 1E71CBh` at `0x1E6E0C`, the preallocation
  count lookup, before naming its devices "\Device\MU_0". That is the same instruction sequence as Bustin' Out
  `0x2D9EEC`, `push 2D9DC0h (XPP_MemoryUnitType); call 2DA2A9h`.
- **Its pointer is followed by a mass-storage descriptor.** The record's pointer at `0x1E6CEC` is followed by the
  descriptor `82 08 FF FF` (USB class 8, mass storage) at `0x1E6CF0`. Bustin' Out has the same at `0x2D9DD0`.
- **The sibling agrees.** It sits at offset `+0xE0` here, as Bustin' Out's XTLID 0x1007E record `0x2D9DC0` does.
- **Host.** `XInitDevices` clears it when `HAS_XPP_MemoryUnitType`.

`config/found-d3d8-data.toml` reaches the same two addresses independently, so the duplicate is not a conflict.

## Not emitted

### `crt_sin`, `crt_cos`, `crt_tan`, `crt_atan`, `crt_log`, `crt_log10`, `crt_sqrt`: not linked
Four independent searches each find nothing:

1. **Byte hash.** No offset of `.text` hashes to any of the 5849 records:

   | Name | 5849 `len` |
   |---|---|
   | `crt_sin` | 0x91 |
   | `crt_cos` | 0x91 |
   | `crt_tan` | 0x95 |
   | `crt_atan` | 0x82 |
   | `crt_log` | 0xB8 |
   | `crt_log10` | 0xB8 |
   | `crt_sqrt` | 0x9D |

   The 0x14-byte `_CI` wrapper hash has only the two hits above, so there is no `_CIsin`, `_CIcos` or other `_CI`
   wrapper.
2. **Error-report idiom.** Every worker reports its errors with `lea ecx,<name>` beside `mov edx,<OP>`.
   Enumerating that pair across `.text` finds exactly six sites: acos x2, asin x2 and pow x2. There are none for
   OP_SIN 0x1E, OP_COS 0x12, OP_TAN 0x20, OP_ATAN 0x0F, OP_LOG 0x1A, OP_LOG10 0x1B or OP_SQRT 5.
3. **Name strings.** "sin", "cos", "tan", "atan", "log", "log10" and "sqrt" stand alone only in the `.rdata` name
   table `0x1FE53C-0x1FE5E0`. That table is referenced only from the data table `0x217444-0x2174F4`, never from
   code. Every other occurrence is the tail of a longer string ("asin", "acos", "atan", "save_story_dialog", ...),
   and none of them is referenced from code.
4. **Worker shape.** I took every rel32 call target in `.text` with `ret 0`, `regs [eax]` and an x87
   transcendental. That gives exactly `crt_acos`, `crt_asin` and `crt_pow`. A `crt_sqrt`-shaped search
   (`fsqrt`, `ret 0`) finds only game functions: thiscall with `regs [ecx]`, or `0x0E86F0`, a lazily computed
   constant.

The game's sin, cos, tan and sqrt are inline compiler intrinsics:

| Instruction | Count | Functions |
|---|---|---|
| `fsqrt` | 121 | 64 |
| `fsin` | 48 | 37 |
| `fcos` | 27 | 23 |
| `fptan` | 6 | 5 |

None of those functions has the worker shape. LIBCMT's shared x87 object does contain log/log10 *handler*
fragments (`fldln2`/`fldlg2; fxch; fyl2x; ret` at `0x17C53A`, `0x17C569`, `0x17C56D`). They are not workers:

- They run on a dispatcher's `[ebp-90h]` frame.
- They have no OP/name report.
- No call, jump or pointer from outside the fragments reaches them. The only branch to them is the log10
  fragment's own `jmp 17C56Fh` at `0x17C56B`.

The only old-style dispatch tables (length-prefixed name, then nargs and OP) in `.data` are:

| Table | Name at | OP | Note |
|---|---|---|---|
| exp | `0x2179FA` | 0x14 at `0x217A08` | points at `0x17C4D1` |
| fmod | `0x217264` | 0x16 | 2 arguments |
| sinh | `0x21936A` | 0x1F | |
| cosh | `0x21938A` | 0x13 | |
| tanh | `0x2193AA` | 0x21 | |

None of those is a config name. All seven names are **absent from this build**, and 0 is their correct value.

### Names an id might have been expected to reach
- **`XLaunchNewImageA`** (0x1005A), **`XPP_GamepadType`** (0x1007C) and **`XPP_MemoryUnitType`** (0x1007E): all three
  siblings publish these ids, this image does not. All three are proven above by other means.
- **`XAudioDownloadEffectsImage`** (5558 xtlid 0xB00A6) and every D3D8 and DSOUND name: this image publishes no
  `0x8xxxx` or `0xBxxxx` id. They are outside this file set (DSOUND and D3D agents), and the `.XTLID` channel
  cannot help them here.
- **Socket, `WSA*`, `XNet*`, `XOnline*`, `Bink*`:** there is no XNET, XONLINE or BINK section, and no network or
  Bink id in `.XTLID`. Their zeros are correct.

## Observations for the port
- **Controllers cannot work until `XPP_GamepadType` is merged.**
  - The host `XInputOpen` returns 0 unless `type == SYM(XPP_GamepadType)`, and that symbol is 0 today.
  - The game also calls `XInitDevices` through `0x1E7EDF`, and that still runs the guest body: the USB
    host-controller and class-driver initialisation.
  - Merging `found-xapi-crt.toml` fixes both.
- **`XInputGetCapabilities` (id 0x1003B, `0x1E7BDE`) has no config key and no host body, so its guest code runs
  on host handles.**
  - It is safe: `mem::AllocSystem` zero-fills the 16-byte handle, so it reads a NULL device and returns 0x48F.
  - On that path it clears only the Reserved word at `caps+1`. The game's check at `0x12B628`/`0x12B630` then
    reads `Out.Rumble.wLeftMotorSpeed`/`wRightMotorSpeed` at `caps+0x15`/`+0x17` from an uninitialised stack
    buffer. Only the game's "rumble supported" flag is affected.
- **`XGetDevices`/`XGetDeviceChanges` (ids 0x10032/0x10033) run as guest code on the record the host's
  `UpdatePorts` writes.** This is the SDK's design and needs the layout keys above. They hold.
- **The `0x2xxxx` ids are XAPI's Win32 functions, not LIBCMT.** There is no id-based route to any CRT name; the
  CRT names come only from bytes.
- **IDA.** The shared database `out/game.exe` now names all 81 id targets and the six new functions. It also names
  `_CIpow`, the two x87 loaders and both XPP records, each with an evidence comment.
