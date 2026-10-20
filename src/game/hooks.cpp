// Hooks for default.xbe. A strong definition replaces the recompiled function at that address.
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <cstring>

#include "cpu/x86_ops.h"
#include "xdk/hle.h"

namespace {
// Each wrapper can be switched off for the run, so a defect can be bisected against the stock
// behaviour without a rebuild. Off means the recompiled function runs exactly as the image wrote it.
bool HookOff(const char* name) {
    const char* v = std::getenv(name);
    return v && v[0] && std::strcmp(v, "0") != 0;
}

// SIMS1_NO_STEP: both frame-step wrappers below run the image's own functions untouched
bool StepOff() {
    static const bool off = HookOff("SIMS1_NO_STEP");
    return off;
}

// the frame step's globals (docs/frame-rate.md)
constexpr uint32_t kTickSize = 0x324220u;   // float, seconds per tick: 1/60 (0x12FA01) or 0.02 (0x12F9F5)
constexpr uint32_t kTickCount = 0x20C14Cu;  // dword, the quantiser's tick count (0x12F6C3 / 0x12F6FA)
constexpr uint32_t kTickTotal = 0x324230u;  // dword, the running total of ticks (0x12F6FF)
}  // namespace

// D3DDevice_InsertCallback(Flags, pCallback, Context) at 0x1926F0.
//
// Confirmed against this image's guest body, not assumed: 0x19270B writes the push token
// 0x00081D8C, and the function is retn 0Ch. The title calls it at 0x156B01 (its render thread,
// beside the per-frame D3DDevice_Swap at 0x156B1A) and at 0x152829.
//
// On the console this writes a callback token into the push buffer; the D3D interrupt handler
// runs pCallback(Context) once the GPU reaches it. The SDK has no push-buffer callback path -
// the tokens land in a buffer the renderer walks for draws only - so the callback would never
// run and an engine thread waiting on the semaphore that callback releases would idle-wait
// forever: the title creates its device, locks its startup surfaces, opens d:\DATASETS.ARC and
// then completes no frame at all (0 presents in a 23-second run).
//
// The host renderer has no GPU timeline the guest can be behind, so the callback is run
// immediately: by the time this returns, everything queued before it has been handed to the
// render thread. SIMS1_NO_CALLBACK=1 bisects this off without a rebuild; with it off the
// wedge returns, which is the proof this body is what unblocks the first frame.
HLE_STDCALL(D3DDevice_InsertCallback, 3) {
    uint32_t callback = a[1], context = a[2];
    if (callback != 0) ::kernel::CallGuest(ctx, callback, {context});
    return 0;
}

// The frame step: the quantiser sub_0012F640 (this in ecx, float elapsed seconds on the stack,
// retn 4 at 0x12F705), called once a frame from the frame tick sub_0012FB80 at 0x12FC41, its only
// call site. docs/frame-rate.md has the whole derivation; in short:
//
// The engine measures real time in whole milliseconds and then quantises it away. The clock object
// at 0x20C9DC (published through dword_33220C) reads GetTickCount (sub_000C6184, *KeTickCount): its
// elapsed vfunc sub_0015EBD0 (vtable 0x1FBDF8 +0x10) returns (GetTickCount() - stamp) / 1000.0f
// (fdiv flt_20C9D8 = 1000.0 at 0x15EBED). The frame tick takes that elapsed (call at 0x12FC17,
// fstp to a float at 0x12FC1A) and restamps (0x12FC27), so successive elapsed values telescope to
// the real time that passed, to the millisecond.
//
// The tick then makes the one delta the rest of the engine multiplies by, at [0x20C150] (fstp at
// 0x12FCE0; 205 read xrefs in 112 functions against three writes - this one and a scoped
// save / restore pair at 0x113312 / 0x112E16). Which delta depends on the frame object's byte at
// this+5 (test at 0x12FC46):
//   - clear, which is the state in play (the subclass init sub_00151D20 clears it at 0x151D65 after
//     the constructor sub_0012F9B0 set it at 0x12F9E9; read 0 at run time on every screen): the
//     elapsed is clamped to [tick size, 15 x tick size] (fcom [0x324220] at 0x12FC64, fmul by the
//     15.0 at [0x1EF674] at 0x12FC81) and averaged with the two previous clamped values (fmul by
//     the 1/3 at [0x1F2614] at 0x12FCCA). The tick size [0x324220] is 1/60 s (0x12FA01), so a
//     frame shorter than 16.7 ms still advances the world by 16.7 ms;
//   - set: ticks * tick size (fild [0x20C14C] at 0x12FC4F, fmul [0x324220] at 0x12FC55), from the
//     tick count the quantiser stores at [0x20C14C].
// At 144 fps the clamp makes 144 x 1/60 = 2.4 s of game time per real second, and at the 60 fps
// cap the frames the host delivers early are floored too.
//
// The fix replaces only the quantisation: the step is the frame's real length, the engine's
// ceiling kept (15 ticks of 1/60 s = 250 ms), handed to the frame tick's product path (see
// sub_0012FB80 below) as a whole-millisecond tick count, stored at [0x20C14C] and added to the
// running total at [0x324230] as the quantiser does (0x12F6FA / 0x12F6FF) and returned in eax,
// times a tick size of step / count written into [0x324220], so the caller's count x size is the
// step to the float.
//
// The step is measured on the host's steady clock, the clock the guest's KeTickCount is made from
// (sdk/runtime/kernel/xboxkrnl.cpp), at its full resolution, between successive calls - one per
// frame, from the same point in the frame tick as the engine's own reading. The engine's reading is
// that same interval rounded to whole milliseconds, which telescopes correctly but cannot carry a
// frame shorter than 1 ms: the front end runs at about 1500 fps uncapped, most of its frames read
// 0 ms, and a one-tick floor of 1 ms measured 1.50 s of game time per real second there
// (docs/frame-rate.md). The engine's reading is only used for the first frame, which has no
// previous call.
X86_FUNC(__imp__sub_0012F640);
X86_FUNC(sub_0012F640) {
    if (StepOff()) {
        __imp__sub_0012F640(ctx, base);
        return;
    }
    constexpr double kTick = 0.001;  // seconds per counted tick, 1/60 before this
    constexpr int kMaxTicks = 250;   // 0.25 s, the engine's own ceiling of 15 ticks of 1/60 s
    using clock = std::chrono::steady_clock;
    static clock::time_point last{};  // title thread only
    const clock::time_point now = clock::now();
    const double real = last == clock::time_point{} ? double(X86_MEMF32(ctx.esp + 0x4u))
                                                    : std::chrono::duration<double>(now - last).count();
    last = now;
    // not (real > 0): a NaN or negative first reading takes the smallest step, as the clamp did
    const double dt = real > 0.0 ? std::min(real, kMaxTicks * kTick) : kTick;
    const int ticks = std::clamp(int(dt / kTick + 0.5), 1, kMaxTicks);
    X86_MEMF32(kTickSize) = float(dt / ticks);  // ticks * this == the time that really passed
    X86_MEM32(kTickCount) = uint32_t(ticks);
    X86_MEM32(kTickTotal) = X86_MEM32(kTickTotal) + uint32_t(ticks);
    ctx.eax = uint32_t(ticks);
    ctx.esp += 8;  // retn 4
}

// The frame tick, sub_0012FB80 'EEngine::PreFrameUpdate' (this in ecx, no stack arguments; slot
// +0x18 of the engine frame vtable 0x1F9990, and of the game's frame subclass 0x1FB030 through the
// thunk sub_00151D70). It writes nothing of its own: it sets the frame object's fixed-step byte at
// this+5 for the duration of the original call so the tick makes its delta by its own product path
// (0x12FC4F / 0x12FC55) out of the quantiser's count and tick size above, instead of the clamped
// three-frame average, and puts the byte and the engine's tick size back afterwards.
//
// Neither is read by anything else during the tick. The byte's other readers are the quantiser's
// own test (0x12F640, replaced above) and the tick-count getter sub_0012F710 (returns 1 while the
// byte is clear), whose only caller sub_0014B350 is the application's vtable slot +0x14
// (0x1F9544 / 0x1FAB5C), called from the post-frame update sub_0012FD80 at 0x12FDDE - after this
// returns, so it sees the restored byte. The tick size's other readers are two debug displays
// (the profiler print sub_00141220 at 0x14122D and the 'CPU:' overlay sub_0014AE50 at 0x14AFD6),
// and they see the engine's 1/60 again.
X86_FUNC(__imp__sub_0012FB80);
X86_FUNC(sub_0012FB80) {
    if (StepOff()) {
        __imp__sub_0012FB80(ctx, base);
        return;
    }
    const uint32_t frame = ctx.ecx;
    const uint8_t fixed_step = X86_MEM8(frame + 0x5u);
    const float tick_size = X86_MEMF32(kTickSize);
    X86_MEM8(frame + 0x5u) = 1;
    __imp__sub_0012FB80(ctx, base);  // pops its own return
    X86_MEM8(frame + 0x5u) = fixed_step;
    X86_MEMF32(kTickSize) = tick_size;
}
