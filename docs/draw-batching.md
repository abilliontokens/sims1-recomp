# Draw batching in live mode: the measurement, the decision, and what the frame waits on

Recorded 2026-10-20. Every run is the native Linux release build at the owner's configuration -
borderless 3440x1440, `render_percent 100` (render scale 3.000, target 1920x1440), `fps_cap 0`,
`vsync false`, `XBE_PERF=1 XBE_MUTE=1` - in the starter household reached by the `docs/playtest.md`
walk, with `out/build/linux-release/hdd` wiped before every run. "Zoomed out" is the camera held at
zoom-out (`F`, the right stick's Y) for 6 s; that it landed is shown by the screenshots of each run
(`out/shots/<run>_default.png` against `<run>_zoomed.png`) and by the draw count rising from 1396 to
1720. Logs, screenshots and F3 captures are kept on disk under `out/` (gitignored). Run names below
are those files' names.

## Result

1. **Merging is legal for about 40% of draws, and is a dead end here because the render thread is
   never the critical path.** In both camera positions roughly 40% of the draws carry exactly the
   state of the draw before them, another 45-50% differ from it only in a per-object transform held in
   vertex constants, and the rest differ in something else. A merge removes work from the render
   thread - and the title thread, which sets the frame rate, never once waited for the render thread
   (0.00 ms, 0 waits, in every run), which is itself busy only 4-6 ms of a 17-25 ms frame. On the title
   thread a merge can save only what follows the state comparison that decides whether two draws may
   merge: about 0.4 ms a frame. No batching code was landed. The same reasoning holds in any port of
   this SDK whose render thread is never waited on: look at `waiting` in the `perf: title thread` line
   before spending time on draw counts.
2. **The title thread spends about 45% of every frame asleep, not drawing and not computing.** At the
   default camera it is on a CPU for 55.7% of the wall time and zoomed out for 54.9%, with 46,700 and
   66,400 voluntary context switches a second (about 800 and 1,660 a frame). Nearly all of its
   blocked samples are inside the host kernel's object dispatcher (`kernel::Wait`, on the global
   `g_dispatch` mutex or the global `g_cv` condition variable), reached from one guest lock built on a
   semaphore. That, not the draw count, is the lever, and it lives in `sdk/runtime/kernel/objects.cpp`,
   outside this document's files; its measured outcome is in the last section.
3. **The XDK's state calls are not where the time goes.** Every one of the 76 entry points in
   `sdk/runtime/xdk/d3d8.cpp` together costs the title thread 2.3 ms of a 19.3 ms frame at the default
   camera and 2.9 ms of 28.0 ms zoomed out, of it 1.8-2.2 ms in the draw calls themselves.

## Phase 1: what consecutive draws agree on

Measured on two F3 captures of a probe build (`cap_batch/205314`, default camera, and
`cap_batch/205414`, zoomed out, both from run `pA`), whose `frame.txt` carried for every draw a hash
of each piece of state below and the list of vertex-constant registers that changed since the draw
before. A run is what the earlier analysis of `cap_pic/144727` called one: consecutive draws on one
render target with one primitive type and one vertex shader. The default-camera capture has the same
shape as that one - 1393 draws in **73 runs**, the longest **424** draws of shader `B01D5341` - so the
numbers below describe the frame the merge was proposed for.

| | default camera | zoomed out |
| --- | ---: | ---: |
| draws / vertices / vertices per draw | 1393 / 35,217 / 25.3 | 1723 / 51,689 / 30.0 |
| draws of at most 6 vertices | 645 (46%) | 827 (48%) |
| runs (rt, primitive, shader); longest | 73; 424, 182, 150, 100 | 94; 486, 162, 150, 75 |
| transitions inside runs (a draw after a draw of its run) | 1320 | 1629 |
| ... vertex constants (all 192 registers) equal | 661 (50.1%) | 721 (44.3%) |
| ... textures equal (headers and the bound image) | 1267 (96.0%) | 1563 (95.9%) |
| ... samplers equal | 1223 (92.7%) | 1528 (93.8%) |
| ... texture-stage state equal | 1316 (99.7%) | 1625 (99.8%) |
| ... blend equal | 1310 (99.2%) | 1620 (99.4%) |
| ... alpha test equal | 1302 (98.6%) | 1610 (98.8%) |
| ... depth/stencil equal | 1318 (99.8%) | 1628 (99.9%) |
| ... all render state equal (every simple state and D3DRS) | 1300 (98.5%) | 1608 (98.7%) |
| ... scissor and viewport equal | 1319 (99.9%) | 1628 (99.9%) |
| ... pixel shader and its constants equal | 1319 (99.9%) | 1628 (99.9%) |
| ... the renderer's per-draw constants (`DrawConstants`) equal | 1284 (97.3%) | 1585 (97.3%) |
| ... pipeline equal | 1303 (98.7%) | 1611 (98.9%) |
| **transitions where everything is equal (trivially mergeable)** | **559** | **612** |
| **... where only the vertex constants differ** | **616** | **858** |
| ... where something else differs | 145 | 159 |
| of those, only the sampler | 82 | 82 |
| draws a merge of the identical runs removes | **559 (40.1%)** | **612 (35.5%)** |
| draws it would remove if constants could be folded too | 1175 (84.4%) | 1470 (85.3%) |

Every change of vertex constants inside a run touched registers the draw's own program reads (0 of
the 616 and 858 changes were confined to unread registers), so none of them is harmless to ignore.
The changed registers are almost always `c[124..127]` (D3D `c28`-`c31`, the object's
world-view-projection rows) with one or more of `c[140..142]` (`c44`-`c46`, its world rows): **a
per-object transform**. The "only the sampler" cases are the renderer's own choice of clamp or wrap
from whether a draw's 2-component texture coordinates lie in [0, 1] (`UnitTexcoordsOf`), which
differs between neighbouring pieces of one object; merging across it would change sampling at the
edges. The renderer's existing constants cache, the cheapest probe, agrees: over 58 s at the default
camera it hit on 680 of 1443 draws a frame (47%), zoomed out on 731 of 1722 (42%).

The same split held over whole seconds, not only in the captured frame: run `pA` counted it on every
draw for 58 s (default) and 46 s (zoomed out) and found 567 and 613 draws a frame identical to the
one before, 651 and 856 differing only in vertex constants (`probe:` lines in `out/shots/pA.log`).

### The 424-draw run: shader `B01D5341`

`d3d: vertex shader B01D5341, 9 decl tokens, 13 instructions, type 2078` in every log; the capture
wrote its microcode and translation (`cap_batch/205314/vs_B01D5341.txt`). It is a **world-space
shader, not a UI or sprite one**:

- `oPos = v0 . c[124..127]`, then `oPos.xyz *= c[97]`, `oPos.xyz = oPos.xyz / oPos.w + c[98]`: the
  object's transform, then the engine's viewport fold - the path `d3d8.cpp` calls "world" (the 2-D and
  HUD programs read only `c[121..124]`).
- `R2 = v0 . c[140..142]` (world position), then `oT0.x = R2 . c[136] + w`, `oT0.y = R2 . c[137]`:
  texture coordinates generated from the world position, a planar projection.
- `oD0 = 1`; of its four inputs (position, packed normal, colour, a 2-D coordinate) it reads only the
  position.

Its 424 draws are 181 of 4 vertices and the rest of 6 to 18, from 284 different vertex sources, with
79 different constant blocks, 9 textures, 2 samplers and 2 pipelines between them; their screen
boxes are a few tens of target pixels across. Of the 423 transitions inside the run, **305** change
nothing, **70** change only the transform (`c[124..127]` with `c[140]` or `c[141]`) and **48**
something else (41 of them the sampler). So most of its draws do share one transform - runs of up to
77 draws are bit-identical in state - but they are not one transform for the whole run.

Folding the transform into the vertices was not pursued: on the CPU it changes the floating-point
order of the position maths (the translation is `precise` dp4s for a reason: equal-depth passes need
bit-exact positions), and the shader route (a per-vertex transform index into a constant array)
changes every generated program. Neither is worth it for the reason below.

## Where a merge would save time

Both threads' costs per draw, run `pA` (probe build, so slightly high) and run `pB4` (probe-free):

| | default camera | zoomed out |
| --- | ---: | ---: |
| fps / ms per frame (`pB4`, probe-free) | 58.4 / 17.1 | 39.9 / 25.1 |
| draws per frame / ms per 1000 draws (`pB4`) | 1397 / 12.3 | 1721 / 14.6 |
| render thread busy per frame (`host`, `pB4`) | 4.2 ms | 6.0 ms |
| title thread waited for the render thread | 0.00 ms, 0 waits | 0.00 ms, 0 waits |
| title thread inside the XDK draw calls (`in XDK draws`, `pB4`) | 1.66 ms | 2.06 ms |
| ... of it recording for the render thread (`recording`) | 1.27 ms | 1.53 ms |
| ... of that, comparing and copying state (`sendstate`) | 0.89 ms | 1.07 ms |

(`in XDK draws` already contains `recording`: the recorder runs inside the draw calls' timing
scope. Only the clears' and presents' recording is outside it.)

A merge of consecutive draws can remove only two things:

- **render-thread work** - assembly, binding, descriptor sets, the draw itself - which the title
  thread never waits for, so the frame rate cannot move from it;
- **the recorder's per-draw residue after `sendstate`** - pushing one command and noting its
  resources - about 0.4 ms a frame at most (`recording` less `sendstate`), because whether a draw can
  join the one before it is only known after the state comparison that `sendstate` already is. The
  guest's own calls (`Walk`, `SyncDeferred`, every `SetStreamSource`) happen per draw whatever the
  host does with them afterwards.

The ceiling of draw batching here is therefore about 0.4 ms of a 17-25 ms frame, under the 5% that
two runs of this scene can resolve.

## What the title thread is doing instead

Run `pA` timed every entry point in `d3d8.cpp` (all 76, by wrapping the HLE body macro) and took the
title thread's CPU time and context switches at every present (probe build; per frame):

| | default camera | zoomed out |
| --- | ---: | ---: |
| wall | 19.29 ms | 27.99 ms |
| title thread on a CPU | 10.38 ms (54%) | 14.77 ms (53%) |
| voluntary context switches | 1245 | 1889 |
| all XDK entry points (outermost, inclusive) | 2.29 ms in 7129 calls | 2.89 ms in 8613 calls |
| `DrawVertices` | 782 calls, 0.93 ms | 860 calls, 1.05 ms |
| `DrawIndexedVertices` | 440 calls, 0.51 ms | 639 calls, 0.73 ms |
| `End` (immediate mode) | 196 calls, 0.37 ms | 198 calls, 0.46 ms |
| `SetStreamSource` | 4227 calls, 0.34 ms | 4925 calls, 0.39 ms |
| `SetPixelShader`, `SetVertexShader`, `SetRenderState_Simple`, `SetTexture`, `SetPalette` | 0.12 ms together | 0.14 ms together |

`SetVertexShaderConstant*`, `SetTransform` and `SetTextureState*` are never called: the title writes
constants and texture-stage state inline into the push buffer, which `Walk` reads inside the draw
calls.

Run `pB4` (probe-free binary) then sampled every busy thread from a parent process, which may read
`/proc/<tid>/syscall`, `schedstat` and the blocked thread's stack (`out/shots/pB4_*.sample.txt`;
`pB3` the same with a second binary run). Per thread, zoomed out (default camera in brackets):

| thread | on a CPU | waiting for a CPU | voluntary switches/s | blocked in |
| --- | ---: | ---: | ---: | --- |
| guest 24 - the title thread (`Threaded::Draw` in its stacks) | 54.9% (55.7%) | 0.3% (7.7%) | 66,434 (46,739) | `g_dispatch` mutex 8.2%, `g_cv` 6.6% of samples |
| guest 18 | 91.8% (84.0%) | 0.2% (8.1%) | 14,883 (10,894) | almost never |
| guest 1C, 30, 34 | 43.5-43.9% each (32-33%) | 0.3% (20-22%) | ~84,000 each (~61,500) | `g_dispatch` ~10.8%, `g_cv` ~9.9% |
| guest 2C | 44.2% (33.5%) | 0.3% (19.7%) | 83,198 (61,649) | the same, through `KeWaitForMultipleObjects` |
| render | 25.9% (37.7%) | 0.0% (4.0%) | 208 (310) | its own queue (idle) |

The title thread's blocked stacks are one path: `kernel::Wait` <- `NtWaitForSingleObjectEx` <- guest
`sub_000CB82E` (the XAPI `WaitForSingleObjectEx`) <- `sub_001463D0` <- `sub_00164B30`.
`sub_001463D0` is a **lock built on a semaphore** - `WaitForSingleObjectEx(this->semaphore, timeout,
alertable)`, retried on an APC - whose unlock `sub_00146410` is `ReleaseSemaphore(semaphore, 1)`. The
host's `kernel::ReleaseSemaphore` wakes **every** parked guest thread on every release
(`g_cv.notify_all()` on one condition variable for all objects), and every wait and release takes the
one `g_dispatch` mutex: between them the six guest threads are put to sleep and woken some 416,000
times a second zoomed out. Waiting for a CPU is negligible zoomed out (0.3%), so there the lost time
is sleeping, not starvation; at the default camera the same threads also queued for a CPU (title
thread 7.7%, workers 20-22%), not explained here.

**How it was found, and why the first instruments missed it.** Every in-process timer measures time
spent *doing* something - inside a draw call, inside the recorder - and is silent while the thread
sleeps, so the title thread's frame looked like "unattributed game logic". What exposed it was asking
the operating system instead: the thread's own CPU time against the wall clock
(`CLOCK_THREAD_CPUTIME_ID`), its voluntary switches (`getrusage(RUSAGE_THREAD)`), then `schedstat`'s
run-queue time and the blocking syscall, futex address (resolved against the binary's symbols) and
stack of each sleeping thread, read from `/proc` by a parent process (Yama's `ptrace_scope 1` lets a
parent read its child's `syscall` and `mem`; `perf` is absent and `gdb` cannot attach). Any port of
this SDK can be checked the same way in one run.

## Decision

- **No draw batching.** It is legal for about 40% of draws and worth about 0.4 ms a frame at most;
  the measured state is recorded above so it need not be re-derived.
- **The work belongs to the kernel object dispatcher**, not to the renderer: targeted wakeups (a
  release wakes only the threads parked on that object) and fewer passes through the global mutex.

## Not reached

- A merge was not implemented, so there is no before/after of one, no `XBE_NO_DRAW_BATCH`, and no
  pixel comparison of one: nothing in the renderer's output changed.
- `B01D5341`'s draws were identified by their program and constants, not by matching them to a
  picture element; "walls, floors and furniture pieces" is not established.
- What guest 18 (92% of a core, almost never blocking) computes was not attributed; no sampler of a
  running thread's program counter was used.
