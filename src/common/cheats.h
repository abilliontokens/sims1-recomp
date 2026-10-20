#pragma once

// The game's own cheat codes, offered in the F1 panel (overlay.cpp). The Sims takes them as text: on
// the main menu the player holds both triggers, types a code on the on-screen keyboard and picks
// Done. Each row here is entered exactly that way (src/game/cheats.cpp): the same recogniser, called
// from the main menu's own update under the same conditions, so what a code does is the game's.
// Nothing here is a setting and nothing is saved - the game itself forgets every code at a restart -
// and nothing happens until the player clicks.
namespace cheats {

// The codes the recogniser sub_0005E6A0 knows, each with the byte it sets (docs/cheats.md).
enum Code : int {
    kFreeAll,      // FREEALL: buying and building cost nothing (bills and services are still paid)
    kMidas,        // MIDAS: every locked object, Create-a-Sim item and two-player level unlocked
    kPartyMotel,   // PARTY M: the Party Motel two-player level
    kPlayTheSims,  // SIMS: Play The Sims on the main menu; the game cannot turn it off again
    kFishEye,      // FISH EYE: in live mode Black switches to a first-person view and back
    kGargamel,     // SHALL, WE, PLAY, A, GAME, then GARGAMEL: bigger heads and blue skin
    kPictures,     // SHALL, WE, PLAY, A, GAME, then PICTURES: an extra picture sequence in the credits
    kCount
};

// any thread: the main menu is up with nothing open over it, the one place the game takes a code
bool OnMainMenu();
// any thread: the code is on - the game's own byte, with a click the title thread has not taken yet
// already counted, so a checkbox shows what was asked for
bool On(Code c);
// render thread: enter the code again on the main menu's next frame, as typing it would: on <-> off,
// except SIMS, which the game can only turn on (a click on it while it is on does nothing)
void Toggle(Code c);

}  // namespace cheats
