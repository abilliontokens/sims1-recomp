# Toolchain

## Development machine (Linux)

Installed on this machine, and what each piece is for:

| tool | version | used for |
|---|---|---|
| clang / clang++ | 23.1.3 | compiler for the host tools, the runtime and the generated guest code (`CMakePresets.json` sets `CMAKE_C_COMPILER=clang`, `CMAKE_CXX_COMPILER=clang++`, `-march=x86-64-v2`); its `clang-cl` and `lld-link` drive the Windows cross build |
| cmake | 4.4.4 | configure and build, through the presets below (`CMakePresets.json` requires 3.25+) |
| ninja | 1.13.2 | the generator every preset uses |
| git | 2.56.0 | source control; the SDK's CMake also fetches its dependencies (zydis, toml++, imgui, SDL3) with `FetchContent` |
| python3 | 3.14.8 | the stdlib-only tools: `tools/xiso_extract.py`, `tools/xbe_info.py`, `tools/sig_bootstrap.py`, `sdk/tools/symbols/xbe2pe.py` |
| SDL3 | 3.4.18 | installed system library. **[inference]** the build does not link it: `sdk/cmake/XbeRecomp.cmake` declares SDL `release-3.4.16` with `FetchContent` (no `find_package` fallback) and builds it static (`SDL_STATIC ON`) for window, input and audio; not checked against a built binary, since none exists |
| Vulkan loader | working | rendering of the Linux build |

## Targets

**Linux is the primary target**: native Vulkan rendering and SDL3 for window, input and audio,
built and run directly on Linux. No Wine is involved.

**The Windows x64 target is cross-compiled from Linux**: `clang-cl` + `lld-link`, through
`cmake/windows-cross.cmake` and the `windows-cross` preset. `xbe_recomp` runs during the build,
so the cross build does not build it for Windows; it takes the Linux binary from the
`host-tools` preset via `XBE_HOST_TOOLS_DIR` (the preset sets it to
`${sourceDir}/out/build/host-tools`, and `sdk/cmake/XbeRecomp.cmake` stops with a fatal error if
no `xbe_recomp` is there):

```
cmake --preset host-tools && cmake --build --preset host-tools
cmake --preset windows-cross && cmake --build --preset windows-cross
```

The Windows cross build has not been run for this port.

## Presets

`cmake --list-presets` on this machine reports exactly these configure presets:

| preset | what it is |
|---|---|
| `linux-debug` | Debug |
| `linux-release` | Release |
| `linux-relwithdebinfo` | RelWithDebInfo |
| `linux-verbose` | RelWithDebInfo with `CMAKE_CXX_FLAGS_RELWITHDEBINFO=-O2 -g` (and the same for C): no `NDEBUG` |
| `host-tools` | Release, `XBE_HOST_TOOLS_ONLY=ON`: builds only `xbe_symbols` and `xbe_recomp` |
| `windows-cross` | Windows x64 Release, toolchain file `cmake/windows-cross.cmake`, `XBE_HOST_TOOLS_DIR=out/build/host-tools` |

`CMakePresets.json` also defines `debug`, `release` and `relwithdebinfo`; they carry a
`hostSystemName == Windows` condition, which is why they are not listed here. Every preset
builds into `out/build/<preset>`.

## Verified build facts

- `host-tools` configures and builds `xbe_symbols` and `xbe_recomp` in about **24 seconds** on
  this machine. Both binaries are in `out/build/host-tools/`; they produced every scan and
  recompilation number in [`xbe-analysis.md`](xbe-analysis.md).
- **The full game target (`Sims1`) builds and links.** `cmake --preset linux-release` configures
  in 61.4 s and `cmake --build --preset linux-release` completes 494 targets in **125 seconds**
  on this machine, producing `out/build/linux-release/Sims1`, 16202696 bytes. It starts, reads
  its settings, opens the Wayland display, maps the guest space, resolves every kernel import
  and runs guest code; it does not yet reach a frame (see `docs/boot-crash.md`).

## The logging trap

The sibling ports all hit this, and it costs a day each time.

`sdk/runtime/core/log.h` sets `logx::kVerbose = false` when `NDEBUG` is defined. With
`kVerbose` false, `logx::Write` drops every line below `Error` (`sdk/runtime/core/log.cpp`), so
`LOGD`, `LOGI` and `LOGW` vanish and only `LOGE`/`LOGR` reach the log. Release *and*
RelWithDebInfo, with CMake's default flags, define `NDEBUG`. The result: the log holds the boot
preamble and then nothing, and a healthy run looks identical to a hung one. The `XBE_PERF`
lines are `LOGI` too (`sdk/runtime/gpu/vulkan.cpp`), so they disappear with it.

The `linux-verbose` preset exists for exactly this: `RelWithDebInfo` with
`CMAKE_CXX_FLAGS_RELWITHDEBINFO=-O2 -g` (and `CMAKE_C_FLAGS_RELWITHDEBINFO=-O2 -g`), no
`NDEBUG`, so the build is optimised and still verbose.

In this tree, `sdk/cmake/XbeRecomp.cmake` (lines 17–31) also strips `-DNDEBUG` from the Release
and RelWithDebInfo flags at configure time, for the same reason. **This is confirmed by a run:**
the `linux-release` build of `Sims1` logs its `[info]` preamble, settings, boot, dispatch and
file-system lines, so `linux-release` is verbose here and `linux-verbose` is not needed merely
to get `LOGI` out.

## Runtime switches

- `XBE_PERF=1` — once a second, logs perf lines: frames per second, host time split, and per-frame
  draw counts (`draws`, `skipped`, `nopipeline`, uploads, clears, copies)
  (`sdk/runtime/core/diag.h`, `sdk/runtime/gpu/vulkan.cpp`). These are `LOGI` lines: they need a
  verbose build (see above).
- `XBE_CAPTURE_DIR=cap` plus **F3** — dumps a frame into a time-stamped folder under `cap/`
  beside the executable: `frame.txt` (every clear and draw, each naming its render target and
  vertex shader) and a BMP of each render target. The D3D12 backend also writes each translated
  shader there as an `.hlsl` file; the Vulkan backend lists the shader handle in `frame.txt` but
  writes no shader files (`sdk/runtime/gpu/d3d12.cpp`, `sdk/runtime/gpu/vulkan.cpp`). Without
  `XBE_CAPTURE_DIR`, F3 does not capture.
- **F3 thread dumps work even in Release**: F3 also walks every guest thread
  (`DumpThreads` in `sdk/runtime/app/main_sdl.cpp` and `main.cpp`), and the register line and
  guest stack words are logged at error level (`LOGE` in `kernel::LogGuestStack`,
  `sdk/runtime/cpu/dispatch.cpp`), so they survive a non-verbose build. Only the
  `thread <id>` header line before each thread is `LOGI` and is dropped there.

`XBE_PERF=1` was set on the first boot run, but the title faults before it completes a second of
rendering, so no perf line has been observed yet. F3 and `XBE_CAPTURE_DIR` have not been
exercised on this port.
