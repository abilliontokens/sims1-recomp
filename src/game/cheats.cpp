// The game's own cheat codes, entered the game's own way (common/cheats.h, offered in the F1 panel).
// docs/cheats.md has the whole derivation; in short:
//
// The Sims takes its codes as text, not as pad sequences. The main menu's update sub_00075FE0
// (vtable 0x1F1A5C slot 1, called each frame while the main menu is the front end's current screen)
// opens a keyboard dialog titled "Enter Cheat" when nothing is open over the menu - its dialog byte
// [menu+0x69] clear (0x76025 / 0x76117) and the developer menu closed, [[0x21A294]+0x101] clear
// (0x76120 / 0x76125) - and both triggers are held (sub_001306B0 with action 12 at 0x7613A; action
// 12 is the mask 0x0C, L + R, in the action table at 0x20A7E8). When the player picks Done, it copies
// the typed text into a 32-character buffer on its stack (sub_000B9A20 at 0x760AE) and hands it to
// the recogniser: sub_0005E6A0(this = the game object 0x21A1E8, const wchar_t* text) (mov ecx at
// 0x760B8, call at 0x760BD - the recogniser's only caller; retn 4 at 0x5EB37).
//
// The recogniser compares the text with each code by wcsncmp over the code's length (sub_001758B5,
// case-sensitive, a prefix match) and sets a byte of that object:
//   FREEALL   toggles [0x21A2AD] (+0xC5, 0x5E6FF)  - purchases skip the funds check and the charge
//   FISH EYE  toggles [0x21A2B7] (+0xCF, 0x5E746)  - Black switches live mode to first person
//   SIMS      sets    [0x21A2B1] (+0xC9, 0x5E794)  - Play The Sims on the main menu; never cleared
//   MIDAS     toggles [0x21A2AF] (+0xC7, 0x5E7CF)  - every locked item and level counts as unlocked
//   PARTY M   toggles [0x21A2B0] (+0xC8, 0x5E818)  - the Party Motel two-player level
// SHALL, WE, PLAY, A and GAME, each entered on its own in that order, step the byte at 0x219590
// from 0 to 5 (0x5E861-0x5E984); any other entry puts it back to 0 (0x5EA72). At 5, GARGAMEL toggles
// [0x21A2BB] and [0x21A2B9] together (+0xD3 / +0xD1, 0x5E9C8-0x5E9F5: a skin tint and a bone scale)
// and PICTURES toggles [0x219591] (0x5EA39, a branch of the credits); both leave the 5 in place. The
// recogniser plays its own hit or miss sound (0x5EA59 / 0x5EA60). None of the bytes is saved: the
// static constructor zeroes them at boot and nothing serialises them.
//
// So the host enters a code the way the dialog does: the same call, from the same function, under
// the same conditions. The override of sub_00075FE0 below calls sub_0005E6A0(0x21A1E8, text) for
// every code the F1 panel asked for, with the text in a 64-byte buffer on the guest stack as the
// dialog's is, at the top of the main menu's update and only while the menu would open the dialog
// itself (both gates above). What the dialog does around the call needs no copy: its other writes
// are made at open and undone at close (the dialog byte and pointer, player 0's pad binding, the
// layout targets at [mgr+0x5E0]), and byte_21A34A, which it sets while open, has no reader.
#include <atomic>
#include <chrono>
#include <cstdint>

#include "common/cheats.h"
#include "core/log.h"
#include "cpu/x86_ops.h"
#include "kernel/kernel.h"
#include "xdk/hle.h"

namespace {

// the game object the recogniser runs on (mov ecx, offset dword_21A1E8 at 0x760B8)
constexpr uint32_t kGameObject = 0x21A1E8u;
// [kGameObject+0xAC]: the developer variable registry; its byte +0x101 is set while the developer
// menu is open, which keeps the cheat dialog shut (0x76120 / 0x76125)
constexpr uint32_t kRegistry = 0x21A294u;
// the SHALL WE PLAY A GAME progress, 0 to 5 (only sub_0005E6A0 reads or writes it)
constexpr uint32_t kChain = 0x219590u;

// sub_0005E6A0: the game object in ecx, the entered text as its one stack argument (retn 4)
constexpr uint32_t kEnterCode = 0x5E6A0u;
constexpr hle::Map kEnterAbi = hle::Make({hle::ecx, hle::stack});

struct CodeRow {
    const char16_t* text;  // as the keyboard types it: upper case, the spaces in place
    uint32_t flag;         // the byte that says the code is on
    bool chained;          // only taken once SHALL WE PLAY A GAME has been entered
    const char* name;
};
constexpr CodeRow kCodes[cheats::kCount] = {
    {u"FREEALL", 0x21A2ADu, false, "FREEALL"},
    {u"MIDAS", 0x21A2AFu, false, "MIDAS"},
    {u"PARTY M", 0x21A2B0u, false, "PARTY M"},
    {u"SIMS", 0x21A2B1u, false, "SIMS"},
    {u"FISH EYE", 0x21A2B7u, false, "FISH EYE"},
    {u"GARGAMEL", 0x21A2BBu, true, "GARGAMEL"},
    {u"PICTURES", 0x219591u, true, "PICTURES"},
};
constexpr const char16_t* kChainWords[] = {u"SHALL", u"WE", u"PLAY", u"A", u"GAME"};

// codes the panel asked to enter, one bit each; a second click before the title thread takes the
// first cancels it, as entering the code twice would
std::atomic<uint32_t> g_toggle{0};
// when the main menu last ran with nothing open over it, steady-clock milliseconds; 0 never
std::atomic<int64_t> g_menu_ms{0};
constexpr int64_t kMenuFreshMs = 250;  // a menu frame older than this is a menu that has gone

int64_t NowMs() {
    using namespace std::chrono;
    return duration_cast<milliseconds>(steady_clock::now().time_since_epoch()).count();
}

// the game's bytes are only there once the image has been loaded
bool Byte(uint32_t va) { return kernel::g_base != nullptr && kernel::G<uint8_t>(va) != 0; }

// One entry, as the dialog's Done makes it: the text in a buffer on the guest stack, then the
// recogniser. The dialog's buffer is 32 characters on its own stack (0x760A9 / 0x760B3).
void Enter(X86Context& ctx, const char16_t* text) {
    constexpr uint32_t kBuffer = 0x40;
    ctx.esp -= kBuffer;
    const uint32_t buffer = ctx.esp;
    uint32_t i = 0;
    for (; text[i] && i < kBuffer / 2 - 1; i++) kernel::W16(buffer + 2 * i, uint16_t(text[i]));
    kernel::W16(buffer + 2 * i, 0);
    hle::Call(ctx, kEnterCode, kEnterAbi, {kGameObject, buffer});
    ctx.esp += kBuffer;
}

// The title thread, at the top of the main menu's update, with the menu taking codes: enter what
// the panel asked for. The plain codes go first, because any of them resets the chain.
void EnterPending(X86Context& ctx) {
    const uint32_t pending = g_toggle.exchange(0, std::memory_order_relaxed);
    if (!pending) return;
    // flags are live only across tail calls, but the update reads them on entry: keep them as found
    const uint32_t cf = ctx.cf, zf = ctx.zf, sf = ctx.sf, of = ctx.of, pf = ctx.pf, df = ctx.df;
    for (int c = 0; c < cheats::kCount; c++) {
        if (!(pending & (1u << c))) continue;
        const CodeRow& row = kCodes[c];
        if (row.chained && kernel::G<uint8_t>(kChain) != 5) {
            // a chain left part way accepts no first word: one entry out of order puts it back to 0
            if (kernel::G<uint8_t>(kChain) != 0) Enter(ctx, kChainWords[0]);
            for (const char16_t* word : kChainWords) Enter(ctx, word);
        }
        Enter(ctx, row.text);
        LOGI("cheats: entered %s on the main menu: %s", row.name, Byte(row.flag) ? "on" : "off");
    }
    ctx.cf = cf;
    ctx.zf = zf;
    ctx.sf = sf;
    ctx.of = of;
    ctx.pf = pf;
    ctx.df = df;
}

}  // namespace

namespace cheats {

bool OnMainMenu() {
    const int64_t seen = g_menu_ms.load(std::memory_order_relaxed);
    return seen != 0 && NowMs() - seen < kMenuFreshMs;
}

bool On(Code c) {
    const bool queued = (g_toggle.load(std::memory_order_relaxed) >> c) & 1u;
    return Byte(kCodes[c].flag) != queued;
}

void Toggle(Code c) {
    if (!OnMainMenu()) return;
    // the recogniser only ever sets the SIMS byte (0x5E794): entering it again leaves it on
    if (c == kPlayTheSims && Byte(kCodes[c].flag)) return;
    g_toggle.fetch_xor(1u << c, std::memory_order_relaxed);
}

}  // namespace cheats

X86_FUNC(__imp__sub_00075FE0);

// sub_00075FE0: the main menu's update (this in ecx, plain ret), the one function that opens the
// cheat dialog and hands its text to the recogniser. Pending codes are entered at its top, under the
// two conditions it checks before it opens the dialog (0x76117 / 0x76125).
X86_FUNC(sub_00075FE0) {
    LOG_FIRST(1, "cheats: main menu hook reached");
    const uint32_t menu = ctx.ecx;
    const uint32_t registry = kernel::R32(kRegistry);
    const bool takes_codes = kernel::G<uint8_t>(menu + 0x69u) == 0 && registry != 0 &&
                             kernel::G<uint8_t>(registry + 0x101u) == 0;
    g_menu_ms.store(takes_codes ? NowMs() : 0, std::memory_order_relaxed);
    if (takes_codes && g_toggle.load(std::memory_order_relaxed)) EnterPending(ctx);
    __imp__sub_00075FE0(ctx, base);
}
