# Kernel import coverage: The Sims (XDK 5233)

Every xboxkrnl ordinal `assets/default.xbe` imports, its name, and whether the SDK runtime registers an
implementation for it. This is static reading only. Nothing was built or run, and `tools/kernel_coverage.py`
was read but not run (the section on method below explains why it would give the same answer).

Inputs read:

- `assets/default.xbe`: 2183168 bytes, sha1 `40ab6f97e8ee3bf4102a5a7820dcb8047fc30097`, retail, base `0x00010000`.
- `sdk/runtime/kernel/*.cpp` and `*.h`: the registrations. The whole of `sdk/runtime/**` was searched too, and
  there are none anywhere else.
- `sdk/runtime/kernel/ordinals.cpp`: the names (the SDK's own table, the one it uses to report a missing import).
- `sdk/runtime/kernel/boot.cpp:142-152`: how an import is bound at boot.

## Result

| | |
| --- | --- |
| Ordinals imported | **123**, in the thunk table `0x001EE460`..`0x001EE648`, with the zero terminator at `0x001EE64C` |
| Covered by the SDK runtime | **123** |
| Not covered | **0** |
| Exports the SDK registers | 275 ordinals. This title uses 123 of them and leaves 152 unused |

**No uncovered import exists, so no kernel call is a guaranteed boot trap.** At boot, every thunk slot is
rewritten to the export's data address or synthetic thunk. `boot: kernel import <n> (<name>) has no
implementation` is logged only when `HasExport(ord)` is false (`kernel/boot.cpp:145-149`). It cannot fire
for this image.

Covered means registered, not faithful. Of the 123 imports:

- 87 have a real body.
- 22 are constant stubs, listed under "What covered does not promise" below.
- 14 are data exports.

By registration form there are 104 `KERNEL_EXPORT`, 4 `KERNEL_FASTCALL`, 14 `KERNEL_DATA` and 1 direct
`RegisterExport` (`DbgPrint`). 108 of them are in `kernel/xboxkrnl.cpp` and 15 in `kernel/files.cpp`.

## Method

**Imports.** The thunk pointer at XBE header `+0x158` is stored XOR'd with the build key. The header holds
`0x5B73A4D6`. XOR with the retail key `0x5B6D40B6` gives `0x001EE460`, the first byte of `.rdata` (file offset
`0x1DD000`). The retail entry key also gives the known entry point `0x000C7B1E`, which confirms the build type.
From there, dwords are read until the first zero. All 123 are of the form `0x8000xxxx` (import by ordinal), and
all 123 ordinals are distinct. This is the same walk as `tools/xbe_info.py` `_parse_kernel_imports`, done
independently.

**Registrations.** The macros are parsed with the regular expressions `tools/kernel_coverage.py` uses:

- `\bKERNEL_(EXPORT|FASTCALL|DATA)\s*\(\s*(0x[0-9A-Fa-f]+|\d+)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)`, skipping the
  macro definitions' own `ord`/`name`.
- `\bRegister(Export|Data)\s*\(\s*(0x[0-9A-Fa-f]+|\d+)\s*,\s*"([^"\\]+)"` for the direct calls.

The direct calls are `InterlockedCompareExchange` (51, `kernel/rtl.cpp:300`), `DbgPrint` (8,
`kernel/xboxkrnl.cpp:1131`), `RtlSnprintf` (361) and `RtlSprintf` (362, `kernel/xboxkrnl.cpp:1149-1150`). No
ordinal is registered twice. No registration sits inside an `#if`: the only conditionals in the kernel sources
are platform `#ifdef _WIN32` blocks, none in `xboxkrnl.cpp`, `rtl.cpp` or `iocp.cpp`, and the single one in
`files.cpp` is `Seek` at lines 144-148. All 275 registered names equal the `ordinals.cpp` entry for their
ordinal, 275 of 275. That is two independently typed spellings of the same mapping.

**Why the script would agree.** `tools/kernel_coverage.py` scans `sdk/runtime/kernel/*.cpp|*.h`
non-recursively with the same two expressions. Every one of the 275 registrations lives in that directory
(`xboxkrnl.cpp` 206, `rtl.cpp` 44, `files.cpp` 21, `iocp.cpp` 4). It reads imports with the same thunk walk,
and it lets a macro override a direct call for the same ordinal, which never happens here. Its paths fit this
image unchanged, and no adaptation is needed.

## Hand cross-check

The task warned to distrust a zero-overlap result. A 100 % result deserves the same suspicion, so the
intersection was checked by hand against both files.

**The XBE bytes** (`xxd -s 0x158 -l 4` and `xxd -s 0x1dd000 -l 0x1f0`):

```
00000158: d6a4 735b                                  -> 0x5B73A4D6 ^ 0x5B6D40B6 = 0x001EE460
001dd000: 3101 0080 8000 0080 9c00 0080 bb00 0080    -> 305, 128, 156, 187
001dd020: 2800 0080 db00 0080 4300 0080 d700 0080    -> 40, 219, 67, 215
001dd130: 6801 0080 7100 0080 6b00 0080 9100 0080    -> 360, 113, 107, 145
001dd170: 6401 0080 5300 0080 5700 0080 5100 0080    -> 356, 83, 87, 81
001dd1b0: b000 0080 0100 0080 0200 0080 0300 0080    -> 176, 1, 2, 3
001dd1c0: 0400 0080 2e00 0080 6400 0080 0800 0080    -> 4, 46, 100, 8
001dd1e0: 8900 0080 9900 0080 4700 0080 0000 0000    -> 137, 153, 71, terminator
```

`(0x1DD1EC - 0x1DD000) / 4 = 123` entries.

**The source lines** (`grep` of `sdk/runtime/kernel`), one per sampled ordinal:

| Ordinal | Thunk slot (file offset) | Raw | Registration found by hand |
| ---: | --- | --- | --- |
| 305 | `0x1EE460` (`0x1DD000`, first) | `31 01 00 80` | `kernel/xboxkrnl.cpp:298 KERNEL_EXPORT(305, RtlTimeToTimeFields, 2)` |
| 156 | `0x1EE468` (`0x1DD008`) | `9c 00 00 80` | `kernel/xboxkrnl.cpp:18 KERNEL_DATA(156, KeTickCount, 4)` |
| 219 | `0x1EE484` (`0x1DD024`) | `db 00 00 80` | `kernel/files.cpp:501 KERNEL_EXPORT(219, NtReadFile, 8)` |
| 360 | `0x1EE590` (`0x1DD130`) | `68 01 00 80` | `kernel/xboxkrnl.cpp:1199 KERNEL_EXPORT(360, HalInitiateShutdown, 0)` |
| 87 | `0x1EE5D8` (`0x1DD178`) | `57 00 00 80` | `kernel/xboxkrnl.cpp:1295 KERNEL_FASTCALL(87, IofCompleteRequest)` |
| 1 | `0x1EE614` (`0x1DD1B4`) | `01 00 00 80` | `kernel/xboxkrnl.cpp:1261 KERNEL_EXPORT(1, AvGetSavedDataAddress, 0)` |
| 8 | `0x1EE62C` (`0x1DD1CC`) | `08 00 00 80` | `kernel/xboxkrnl.cpp:1131 RegisterExport(8, "DbgPrint", DbgPrintEntry)` (direct form) |
| 71 | `0x1EE648` (`0x1DD1E8`, last) | `47 00 00 80` | `kernel/xboxkrnl.cpp:33 KERNEL_DATA(71, IoFileObjectType, 0x20)` |

These eight cover all four registration forms, both source files, the lowest (1) and highest (360)
ordinal, and the first and last thunk slots.

**Negative controls** (the parser can say "no"):

- Ordinals 7 `DbgLoadImageSymbols` and 9 `HalReadSMCTrayState` have no registration anywhere. `grep` finds
  none, and the parser lists both among the 91 unregistered ordinals. Neither is imported.
- Ordinal 5 `DbgBreakPoint` is registered (`kernel/xboxkrnl.cpp:1169`) but not imported. It is one of the 152
  registered-but-unused exports, not a cover for this title.

**Arithmetic tripwires:**

- 104 + 4 + 14 + 1 = 123 registrations of imported ordinals.
- 108 + 15 = 123 by file.
- 123 + 152 = 275 registered.
- 275 + 91 = 366, every ordinal of the 1..366 table.

**An independent use count.** Raw dwords equal to a thunk-slot address, counted in each code section of the
XBE bytes, match IDA's references to the 123 slots in the flat PE, section for section:

| Section | Raw dwords | IDA reference sites |
| --- | ---: | ---: |
| `.text` | 264 | 264 |
| `D3D` | 49 | 49 |
| `DSOUND` | 141 | 141 |
| `XPP` | 159 | 159 |
| `XGRPH` | 0 | 0 |
| `XMV` | 0 | 0 |

That is 613 sites in all. Every one of the 123 slots is referenced at least once, so there is no dead import
in the count. XGRPH and XMV reach the kernel only through XAPI/CRT in `.text` and through D3D/DSOUND
(`docs/xgrph-xmv-symbols.md`).

## Every imported ordinal

Names come from `kernel/ordinals.cpp`. "Referenced from" counts the instructions that read the slot, by the
section they are in (IDA, cross-checked by the raw count above).

| Ordinal | Export | Thunk slot | SDK registration | Body | Referenced from (sites) |
| ---: | --- | --- | --- | --- | --- |
| 1 | `AvGetSavedDataAddress` | `0x1EE614` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1261` | implemented | `D3D` 3 |
| 2 | `AvSendTVEncoderOption` | `0x1EE618` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1267` | implemented | `D3D` 6 |
| 3 | `AvSetDisplayMode` | `0x1EE61C` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1266` | stub: returns `0` | `D3D` 1 |
| 4 | `AvSetSavedDataAddress` | `0x1EE620` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1262` | implemented | `D3D` 1 |
| 8 | `DbgPrint` | `0x1EE62C` | `RegisterExport` `kernel/xboxkrnl.cpp:1131` | implemented | `.text` 1 |
| 15 | `ExAllocatePoolWithTag` | `0x1EE5E4` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:394` | implemented | `DSOUND` 1, `XPP` 2 |
| 16 | `ExEventObjectType` | `0x1EE554` | `KERNEL_DATA` `kernel/xboxkrnl.cpp:32` | data, 0x20 bytes | `XPP` 1 |
| 17 | `ExFreePool` | `0x1EE5E0` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:402` | implemented | `DSOUND` 1, `XPP` 1 |
| 23 | `ExQueryPoolBlockSize` | `0x1EE63C` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:406` | implemented | `DSOUND` 2 |
| 24 | `ExQueryNonVolatileSetting` | `0x1EE4EC` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1228` | implemented | `.text` 1 |
| 40 | `HalDiskCachePartitionCount` | `0x1EE480` | `KERNEL_DATA` `kernel/xboxkrnl.cpp:25` | data, 4 bytes | `.text` 2 |
| 44 | `HalGetInterruptVector` | `0x1EE5F0` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:785` | implemented | `D3D` 1, `DSOUND` 2, `XPP` 1 |
| 46 | `HalReadWritePCISpace` | `0x1EE624` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1273` | implemented | `D3D` 1 |
| 47 | `HalRegisterShutdownNotification` | `0x1EE51C` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1201` | stub: returns `0` | `.text` 1, `D3D` 2, `DSOUND` 4, `XPP` 1 |
| 49 | `HalReturnToFirmware` | `0x1EE4E8` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1179` | implemented | `.text` 2 |
| 65 | `IoCreateDevice` | `0x1EE5B0` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1282` | stub: returns `kUnsuccessful` | `XPP` 1 |
| 67 | `IoCreateSymbolicLink` | `0x1EE488` | `KERNEL_EXPORT` `kernel/files.cpp:751` | implemented | `.text` 3 |
| 71 | `IoFileObjectType` | `0x1EE648` | `KERNEL_DATA` `kernel/xboxkrnl.cpp:33` | data, 0x20 bytes | `.text` 1 |
| 74 | `IoInvalidDeviceRequest` | `0x1EE5B4` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1283` | stub: returns `0xC0000010` | `XPP` 1 |
| 81 | `IoStartNextPacket` | `0x1EE5DC` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1292` | stub: returns `0` | `XPP` 8 |
| 83 | `IoStartPacket` | `0x1EE5D4` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1291` | stub: returns `0` | `XPP` 1 |
| 87 | `IofCompleteRequest` | `0x1EE5D8` | `KERNEL_FASTCALL` `kernel/xboxkrnl.cpp:1295` | stub: returns `0` | `.text` 1, `XPP` 9 |
| 95 | `KeBugCheck` | `0x1EE5AC` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1174` | implemented: logs, then traps (the console halts here too) | `.text` 4 |
| 97 | `KeCancelTimer` | `0x1EE5C0` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:722` | implemented | `.text` 1, `DSOUND` 2, `XPP` 20 |
| 98 | `KeConnectInterrupt` | `0x1EE5F8` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:783` | stub: returns `1` | `D3D` 1, `DSOUND` 2, `XPP` 1 |
| 99 | `KeDelayExecutionThread` | `0x1EE570` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:258` | implemented | `.text` 1, `XPP` 2 |
| 100 | `KeDisconnectInterrupt` | `0x1EE628` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:784` | stub: returns `1` | `D3D` 1, `DSOUND` 2 |
| 107 | `KeInitializeDpc` | `0x1EE598` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:759` | implemented | `.text` 2, `D3D` 1, `DSOUND` 2, `XPP` 5 |
| 109 | `KeInitializeInterrupt` | `0x1EE5FC` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:782` | stub: returns `0` | `D3D` 1, `DSOUND` 2, `XPP` 1 |
| 113 | `KeInitializeTimerEx` | `0x1EE594` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:694` | implemented | `.text` 2, `DSOUND` 1, `XPP` 4 |
| 119 | `KeInsertQueueDpc` | `0x1EE60C` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:768` | implemented | `.text` 1, `D3D` 1, `DSOUND` 3, `XPP` 1 |
| 125 | `KeQueryInterruptTime` | `0x1EE588` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:219` | implemented | `.text` 2 |
| 128 | `KeQuerySystemTime` | `0x1EE464` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:225` | implemented | `.text` 4, `DSOUND` 4, `XPP` 2 |
| 129 | `KeRaiseIrqlToDpcLevel` | `0x1EE58C` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:203` | implemented | `.text` 2, `XPP` 23 |
| 137 | `KeRemoveQueueDpc` | `0x1EE640` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:776` | implemented | `DSOUND` 3 |
| 139 | `KeRestoreFloatingPointState` | `0x1EE638` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:888` | stub: returns `kSuccess` | `DSOUND` 1 |
| 142 | `KeSaveFloatingPointState` | `0x1EE634` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:889` | stub: returns `kSuccess` | `DSOUND` 1 |
| 143 | `KeSetBasePriorityThread` | `0x1EE530` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:879` | implemented | `.text` 1 |
| 144 | `KeSetDisableBoostThread` | `0x1EE53C` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:877` | stub: returns `0` | `.text` 1 |
| 145 | `KeSetEvent` | `0x1EE59C` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:670` | implemented | `.text` 4, `D3D` 2, `XPP` 4 |
| 149 | `KeSetTimer` | `0x1EE580` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:714` | implemented | `.text` 1, `DSOUND` 3, `XPP` 13 |
| 150 | `KeSetTimerEx` | `0x1EE5B8` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:704` | implemented | `.text` 2 |
| 151 | `KeStallExecutionProcessor` | `0x1EE600` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:252` | implemented | `DSOUND` 6, `XPP` 1 |
| 153 | `KeSynchronizeExecution` | `0x1EE644` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:789` | implemented | `DSOUND` 2 |
| 156 | `KeTickCount` | `0x1EE468` | `KERNEL_DATA` `kernel/xboxkrnl.cpp:18` | data, 4 bytes | `.text` 1 |
| 158 | `KeWaitForMultipleObjects` | `0x1EE5BC` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:664` | implemented | `.text` 1 |
| 159 | `KeWaitForSingleObject` | `0x1EE5A4` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:659` | implemented | `.text` 2, `D3D` 2, `XPP` 3 |
| 160 | `KfRaiseIrql` | `0x1EE5F4` | `KERNEL_FASTCALL` `kernel/xboxkrnl.cpp:192` | implemented | `DSOUND` 1, `XPP` 1 |
| 161 | `KfLowerIrql` | `0x1EE584` | `KERNEL_FASTCALL` `kernel/xboxkrnl.cpp:198` | implemented | `.text` 2, `DSOUND` 1, `XPP` 29 |
| 164 | `LaunchDataPage` | `0x1EE4E0` | `KERNEL_DATA` `kernel/xboxkrnl.cpp:19` | data, 4 bytes | `.text` 9 |
| 165 | `MmAllocateContiguousMemory` | `0x1EE4DC` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:366` | implemented | `.text` 1, `XPP` 1 |
| 166 | `MmAllocateContiguousMemoryEx` | `0x1EE5C4` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:367` | implemented | `.text` 1, `D3D` 6, `DSOUND` 1 |
| 168 | `MmClaimGpuInstanceMemory` | `0x1EE630` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:385` | implemented | `D3D` 1 |
| 171 | `MmFreeContiguousMemory` | `0x1EE4E4` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:368` | implemented | `.text` 2, `D3D` 7, `DSOUND` 1 |
| 173 | `MmGetPhysicalAddress` | `0x1EE604` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:372` | implemented | `DSOUND` 6, `XPP` 4 |
| 175 | `MmLockUnlockBufferPages` | `0x1EE608` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:374` | stub: returns `0` | `DSOUND` 6, `XPP` 4 |
| 176 | `MmLockUnlockPhysicalPage` | `0x1EE610` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:375` | stub: returns `0` | `XPP` 3 |
| 178 | `MmPersistContiguousMemory` | `0x1EE4D8` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:373` | stub: returns `0` | `.text` 1, `D3D` 1 |
| 179 | `MmQueryAddressProtect` | `0x1EE524` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:378` | stub: returns `4` | `.text` 1, `XPP` 1 |
| 180 | `MmQueryAllocationSize` | `0x1EE5C8` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:376` | implemented | `D3D` 1, `DSOUND` 2 |
| 181 | `MmQueryStatistics` | `0x1EE5CC` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:408` | implemented | `.text` 1 |
| 182 | `MmSetAddressProtect` | `0x1EE520` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:377` | stub: returns `0` | `.text` 2, `XPP` 2 |
| 184 | `NtAllocateVirtualMemory` | `0x1EE4FC` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:330` | implemented | `.text` 8 |
| 186 | `NtClearEvent` | `0x1EE55C` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:491` | implemented | `.text` 1 |
| 187 | `NtClose` | `0x1EE46C` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:449` | implemented | `.text` 20, `D3D` 2 |
| 189 | `NtCreateEvent` | `0x1EE550` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:464` | implemented | `.text` 1 |
| 190 | `NtCreateFile` | `0x1EE4A0` | `KERNEL_EXPORT` `kernel/files.cpp:326` | implemented | `.text` 7, `D3D` 2 |
| 193 | `NtCreateSemaphore` | `0x1EE564` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:531` | implemented | `.text` 1 |
| 196 | `NtDeviceIoControlFile` | `0x1EE4B4` | `KERNEL_EXPORT` `kernel/files.cpp:736` | implemented | `.text` 2 |
| 197 | `NtDuplicateObject` | `0x1EE4A4` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:451` | implemented | `.text` 1 |
| 198 | `NtFlushBuffersFile` | `0x1EE4B0` | `KERNEL_EXPORT` `kernel/files.cpp:724` | implemented | `.text` 1 |
| 199 | `NtFreeVirtualMemory` | `0x1EE4F8` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:342` | implemented | `.text` 6 |
| 200 | `NtFsControlFile` | `0x1EE498` | `KERNEL_EXPORT` `kernel/files.cpp:731` | implemented | `.text` 1 |
| 202 | `NtOpenFile` | `0x1EE474` | `KERNEL_EXPORT` `kernel/files.cpp:429` | implemented | `.text` 9 |
| 203 | `NtOpenSymbolicLinkObject` | `0x1EE490` | `KERNEL_EXPORT` `kernel/files.cpp:760` | implemented | `.text` 1 |
| 205 | `NtPulseEvent` | `0x1EE560` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:584` | implemented | `.text` 1 |
| 207 | `NtQueryDirectoryFile` | `0x1EE4D4` | `KERNEL_EXPORT` `kernel/files.cpp:655` | implemented | `.text` 2 |
| 210 | `NtQueryFullAttributesFile` | `0x1EE4D0` | `KERNEL_EXPORT` `kernel/files.cpp:704` | implemented | `.text` 1 |
| 211 | `NtQueryInformationFile` | `0x1EE4AC` | `KERNEL_EXPORT` `kernel/files.cpp:507` | implemented | `.text` 8 |
| 215 | `NtQuerySymbolicLinkObject` | `0x1EE48C` | `KERNEL_EXPORT` `kernel/files.cpp:770` | implemented | `.text` 1 |
| 217 | `NtQueryVirtualMemory` | `0x1EE508` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:352` | implemented | `.text` 1 |
| 218 | `NtQueryVolumeInformationFile` | `0x1EE470` | `KERNEL_EXPORT` `kernel/files.cpp:619` | implemented | `.text` 3 |
| 219 | `NtReadFile` | `0x1EE484` | `KERNEL_EXPORT` `kernel/files.cpp:501` | implemented | `.text` 3, `D3D` 1 |
| 222 | `NtReleaseSemaphore` | `0x1EE568` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:553` | implemented | `.text` 1 |
| 224 | `NtResumeThread` | `0x1EE544` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:806` | implemented | `.text` 1 |
| 225 | `NtSetEvent` | `0x1EE558` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:483` | implemented | `.text` 2, `DSOUND` 3 |
| 226 | `NtSetInformationFile` | `0x1EE49C` | `KERNEL_EXPORT` `kernel/files.cpp:552` | implemented | `.text` 7, `D3D` 1 |
| 231 | `NtSuspendThread` | `0x1EE540` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:820` | implemented | `.text` 1 |
| 233 | `NtWaitForSingleObject` | `0x1EE4A8` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:637` | implemented | `.text` 2 |
| 234 | `NtWaitForSingleObjectEx` | `0x1EE56C` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:643` | implemented | `.text` 1 |
| 236 | `NtWriteFile` | `0x1EE47C` | `KERNEL_EXPORT` `kernel/files.cpp:502` | implemented | `.text` 9, `D3D` 1 |
| 246 | `ObReferenceObjectByHandle` | `0x1EE534` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:672` | implemented | `.text` 3, `XPP` 1 |
| 250 | `ObfDereferenceObject` | `0x1EE52C` | `KERNEL_FASTCALL` `kernel/xboxkrnl.cpp:690` | stub: returns `0` | `.text` 3, `XPP` 1 |
| 255 | `PsCreateSystemThreadEx` | `0x1EE54C` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:793` | implemented | `.text` 1 |
| 258 | `PsTerminateSystemThread` | `0x1EE548` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:804` | implemented | `.text` 2, `D3D` 1 |
| 259 | `PsThreadObjectType` | `0x1EE538` | `KERNEL_DATA` `kernel/xboxkrnl.cpp:34` | data, 0x20 bytes | `.text` 2 |
| 269 | `RtlCompareMemoryUlong` | `0x1EE500` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:983` | implemented | `.text` 7 |
| 277 | `RtlEnterCriticalSection` | `0x1EE4F4` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:135` | implemented | `.text` 16, `DSOUND` 4 |
| 279 | `RtlEqualString` | `0x1EE574` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:976` | implemented | `.text` 1 |
| 289 | `RtlInitAnsiString` | `0x1EE478` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:893` | implemented | `.text` 15, `XPP` 1 |
| 291 | `RtlInitializeCriticalSection` | `0x1EE504` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:120` | implemented | `.text` 2, `DSOUND` 1 |
| 294 | `RtlLeaveCriticalSection` | `0x1EE4F0` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:155` | implemented | `.text` 16, `DSOUND` 71 |
| 301 | `RtlNtStatusToDosError` | `0x1EE494` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:989` | implemented | `.text` 4 |
| 302 | `RtlRaiseException` | `0x1EE50C` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1030` | implemented: dispatches the guest SEH chain | `.text` 3 |
| 305 | `RtlTimeToTimeFields` | `0x1EE460` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:298` | implemented | `.text` 1 |
| 312 | `RtlUnwind` | `0x1EE5A8` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1062` | implemented | `.text` 1 |
| 322 | `XboxHardwareInfo` | `0x1EE518` | `KERNEL_DATA` `kernel/xboxkrnl.cpp:20` | data, 8 bytes | `.text` 3, `D3D` 1, `XPP` 3 |
| 323 | `XboxHDKey` | `0x1EE4C4` | `KERNEL_DATA` `kernel/xboxkrnl.cpp:27` | data, 16 bytes | `.text` 1 |
| 324 | `XboxKrnlVersion` | `0x1EE528` | `KERNEL_DATA` `kernel/xboxkrnl.cpp:21` | data, 8 bytes | `.text` 1 |
| 325 | `XboxSignatureKey` | `0x1EE4C8` | `KERNEL_DATA` `kernel/xboxkrnl.cpp:28` | data, 16 bytes | `.text` 1 |
| 327 | `XeLoadSection` | `0x1EE578` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:424` | implemented | `.text` 1 |
| 328 | `XeUnloadSection` | `0x1EE57C` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:439` | implemented | `.text` 1 |
| 335 | `XcSHAInit` | `0x1EE4BC` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1299` | implemented | `.text` 1 |
| 336 | `XcSHAUpdate` | `0x1EE4B8` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1303` | implemented | `.text` 1 |
| 337 | `XcSHAFinal` | `0x1EE4C0` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1307` | implemented | `.text` 1 |
| 344 | `XcVerifyPKCS1Signature` | `0x1EE510` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1332` | stub: returns `1` | `.text` 1 |
| 354 | `XboxAlternateSignatureKeys` | `0x1EE4CC` | `KERNEL_DATA` `kernel/xboxkrnl.cpp:30` | data, 16 * 16 bytes | `.text` 1 |
| 355 | `XePublicKeyData` | `0x1EE514` | `KERNEL_DATA` `kernel/xboxkrnl.cpp:31` | data, 284 bytes | `.text` 1 |
| 356 | `HalBootSMCVideoMode` | `0x1EE5D0` | `KERNEL_DATA` `kernel/xboxkrnl.cpp:26` | data, 4 bytes | `.text` 1 |
| 357 | `IdexChannelObject` | `0x1EE5A0` | `KERNEL_DATA` `kernel/xboxkrnl.cpp:35` | data, 0x40 bytes | `.text` 4 |
| 358 | `HalIsResetOrShutdownPending` | `0x1EE5EC` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1200` | stub: returns `0` | `XPP` 1 |
| 359 | `IoMarkIrpMustComplete` | `0x1EE5E8` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1293` | stub: returns `0` | `XPP` 1 |
| 360 | `HalInitiateShutdown` | `0x1EE590` | `KERNEL_EXPORT` `kernel/xboxkrnl.cpp:1199` | implemented | `.text` 1 |

## Uncovered imports

**None.** No import of this XBE lacks a registration, so no import is a guaranteed boot trap.

## What "covered" does not promise

Each of these 22 imports is registered, so it binds and never traps, but it returns a constant:
`kSuccess` = 0, `kUnsuccessful` = `0xC0000001`, and `0xC0000010` is `STATUS_INVALID_DEVICE_REQUEST`. A stub is
safe only while the guest code that calls it either tolerates the constant or never runs.

| Ordinal | Export | Stub returns | Referenced from (sites) |
| ---: | --- | --- | --- |
| 3 | `AvSetDisplayMode` | `0` | `D3D` 1 |
| 47 | `HalRegisterShutdownNotification` | `0` | `.text` 1, `D3D` 2, `DSOUND` 4, `XPP` 1 |
| 65 | `IoCreateDevice` | `kUnsuccessful` | `XPP` 1 |
| 74 | `IoInvalidDeviceRequest` | `0xC0000010` | `XPP` 1 |
| 81 | `IoStartNextPacket` | `0` | `XPP` 8 |
| 83 | `IoStartPacket` | `0` | `XPP` 1 |
| 87 | `IofCompleteRequest` | `0` | `.text` 1, `XPP` 9 |
| 98 | `KeConnectInterrupt` | `1` | `D3D` 1, `DSOUND` 2, `XPP` 1 |
| 100 | `KeDisconnectInterrupt` | `1` | `D3D` 1, `DSOUND` 2 |
| 109 | `KeInitializeInterrupt` | `0` | `D3D` 1, `DSOUND` 2, `XPP` 1 |
| 139 | `KeRestoreFloatingPointState` | `kSuccess` | `DSOUND` 1 |
| 142 | `KeSaveFloatingPointState` | `kSuccess` | `DSOUND` 1 |
| 144 | `KeSetDisableBoostThread` | `0` | `.text` 1 |
| 175 | `MmLockUnlockBufferPages` | `0` | `DSOUND` 6, `XPP` 4 |
| 176 | `MmLockUnlockPhysicalPage` | `0` | `XPP` 3 |
| 178 | `MmPersistContiguousMemory` | `0` | `.text` 1, `D3D` 1 |
| 179 | `MmQueryAddressProtect` | `4` | `.text` 1, `XPP` 1 |
| 182 | `MmSetAddressProtect` | `0` | `.text` 2, `XPP` 2 |
| 250 | `ObfDereferenceObject` | `0` | `.text` 3, `XPP` 1 |
| 344 | `XcVerifyPKCS1Signature` | `1` | `.text` 1 |
| 358 | `HalIsResetOrShutdownPending` | `0` | `XPP` 1 |
| 359 | `IoMarkIrpMustComplete` | `0` | `XPP` 1 |

- **Interrupts and IRPs.** The interrupt imports 98, 100 and 109 are referenced only from `D3D`, `DSOUND` and
  `XPP`, the libraries' own hardware drivers. The IRP/device imports 65, 74, 81, 83, 87 and 359 come only from
  `XPP` (plus one `.text` call of 87). `KeConnectInterrupt` returns 1 without connecting anything, so an ISR
  those drivers install is never called. These are sound only because the host replaces the library entry
  points above them. That is the `[symbols]` work of the D3D, DSOUND and XPP slices, not a kernel gap.
- **`XcVerifyPKCS1Signature` returns 1** (signature valid). It has a single `.text` caller.
- Two bodies trap on purpose: `KeBugCheck` (95), as the console would, and `RtlRaiseException` (302). The
  latter is the guest SEH dispatcher, which traps only when no frame handles the exception.

## The movie path's kernel reach

The title's movies are five XMV streams inside `movies.arc` (`docs/xgrph-xmv-symbols.md`). Take the static
direct-call closure that starts from the six XMV entry points and the game's movie class: `0x15BD60`,
`0x15BEA0`, `0x15BF10`, `0x15C040`, the packet callbacks it hands XMV (`0x15BF90`, `0x15BF50`) and its read
helpers (`0x15BBD0`, `0x15BC60`). The closure follows XAPI, CRT, D3D and DSOUND guest code. It spans 440
functions and references 44 thunk slots:

15 `ExAllocatePoolWithTag`, 17 `ExFreePool`, 23 `ExQueryPoolBlockSize`, 24 `ExQueryNonVolatileSetting`, 44 `HalGetInterruptVector`, 47 `HalRegisterShutdownNotification`, 95 `KeBugCheck`, 98 `KeConnectInterrupt`, 99 `KeDelayExecutionThread`, 100 `KeDisconnectInterrupt`, 107 `KeInitializeDpc`, 109 `KeInitializeInterrupt`, 113 `KeInitializeTimerEx`, 119 `KeInsertQueueDpc`, 128 `KeQuerySystemTime`, 137 `KeRemoveQueueDpc`, 139 `KeRestoreFloatingPointState`, 142 `KeSaveFloatingPointState`, 151 `KeStallExecutionProcessor`, 159 `KeWaitForSingleObject`, 160 `KfRaiseIrql`, 161 `KfLowerIrql`, 166 `MmAllocateContiguousMemoryEx`, 171 `MmFreeContiguousMemory`, 173 `MmGetPhysicalAddress`, 175 `MmLockUnlockBufferPages`, 180 `MmQueryAllocationSize`, 184 `NtAllocateVirtualMemory`, 186 `NtClearEvent`, 187 `NtClose`, 190 `NtCreateFile`, 193 `NtCreateSemaphore`, 199 `NtFreeVirtualMemory`, 219 `NtReadFile`, 225 `NtSetEvent`, 233 `NtWaitForSingleObject`, 234 `NtWaitForSingleObjectEx`, 269 `RtlCompareMemoryUlong`, 277 `RtlEnterCriticalSection`, 289 `RtlInitAnsiString`, 294 `RtlLeaveCriticalSection`, 301 `RtlNtStatusToDosError`, 302 `RtlRaiseException`, 356 `HalBootSMCVideoMode`.

All 44 are covered. Inside this closure, the interrupt and DPC ones (44, 98, 100, 107, 109, 113, 119, 137) are
referenced only from DSOUND's own APU code (`0x1B84A3`, `0x1B9A4E`, `0x1BDBDD`, `0x1BDC68`). Image-wide, most of
them also have D3D, XPP or `.text` callers (see the table). Static reach is not run-time reach. That DSOUND code
runs only when XMV's DSOUND calls land on console bodies, which is the case while `DirectSoundCreate`,
`DirectSoundCreateStream` and the rest stay unmatched in `config/game.toml`. Once the DSOUND slice's names merge,
the host bodies take those calls instead.
