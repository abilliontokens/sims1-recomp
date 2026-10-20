// Hooks for default.xbe. A strong definition replaces the recompiled function at that address.
#include <atomic>
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
