#!/usr/bin/env bash
# Launch the port, drive it from the title into the loaded household, and screenshot
# the real game - not the intro. The intro is one 2-D quad and proves almost nothing
# about the renderer; every ultrawide, HUD or aspect question has to be answered on a
# 3-D scene with the HUD up.
#
#   tools/shot_game.sh <tag> [build dir]
#
# Screens land in out/shots/<tag>_<what>.png, the game's stdout in out/shots/<tag>.log.
#
# The drive is per screen, not on a timer: after every press the script screenshots,
# classifies what is actually on screen (tools/classify_screen.py), and only then
# presses the next key. Menu transitions swallow presses (seen twice in attended
# runs), so a fixed schedule drifts; this loop retries the press that a transition
# ate and refuses to advance until the expected screen is showing. The walk itself
# is the one the sibling Sims: Bustin' Out port's docs/playtest.md records: START
# (title -> main menu), A (Continue or Bust Out -> Select Save), A (saved Sim ->
# Customize, or an empty slot -> name entry -> A accepts each default name ->
# Create-a-Sim), RIGHT x3 (confirm icon), A (save question), A (YES) -> household,
# A dismisses the greeting dialogue.
#
# CAVEAT: that walk, and the screen states classify_screen.py tells apart, came over
# from the sibling unchanged. Neither has been measured on The Sims' screens
# yet, so until both are redone for this title the drive stops at the first wait it
# cannot satisfy; the screenshots it took up to there are still valid.
set -uo pipefail
cd "$(dirname "$0")/.."

TAG="${1:?usage: shot_game.sh <tag> [build-dir]}"
BUILD="${2:-out/build/linux-release}"

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
export DISPLAY="${DISPLAY:-:0}"
if [ -z "${XAUTHORITY:-}" ]; then
    for x in /run/user/$(id -u)/xauth_*; do [ -e "$x" ] && export XAUTHORITY="$x" && break; done
fi
export XBE_PERF=1 XBE_MUTE=1

mkdir -p out/shots
# A packaged tree (release.sh) is given by absolute path and already carries its
# own assets; only a relative in-tree build dir gets the symlink back to assets/.
case "$BUILD" in
    /*) ;;
    *) [ -e "$BUILD/assets" ] || ln -sfn ../../../assets "$BUILD/assets" ;;
esac

STEP="$(mktemp /tmp/sims1-step.XXXXXX)"
export SIMS1_STEP="$STEP"
LOG="out/shots/${TAG}.log"
: > "$LOG"
# "./$BUILD/..." breaks the moment $BUILD is absolute: it becomes ".//tmp/...".
"$(cd "$BUILD" && pwd)/Sims1" >> "$LOG" 2>&1 &
PID=$!
cleanup() { kill -KILL "$PID" 2>/dev/null; rm -f "$STEP"; }
trap cleanup EXIT
echo "launched pid $PID (step file $STEP)"

# The game window, not the desktop. A full-desktop shot forces the classifier to
# find the picture inside it, which works only while the game is borderless and
# the desktop around it is black; windowed on a bright wallpaper it found the
# wallpaper instead and called a loaded household "intro" for six retries. The
# game holds focus for the whole drive (the keys are synthetic, nothing else is
# clicked), so the active window is the game.
shot() { spectacle -b -n -a -o "out/shots/${TAG}_$1.png" >/dev/null 2>&1; }
alive() { kill -0 "$PID" 2>/dev/null; }
press() { printf '%s' "$1" > "$STEP"; sleep 2; printf 'NONE' > "$STEP"; }
screen() { # classify the newest screenshot -> state word on stdout
    shot probe
    python3 tools/classify_screen.py "out/shots/${TAG}_probe.png" 2>/dev/null || echo unknown
}

# Wait until classify says one of the given states (re-screenshotting), or give up.
wait_for() {
    local want="$1" tries="${2:-40}" s i
    for ((i = 0; i < tries; i++)); do
        alive || { echo "died while waiting for $want"; return 1; }
        s="$(screen)"
        case " $want " in *" $s "*) echo "screen: $s"; return 0 ;; esac
        sleep 3
    done
    echo "timed out waiting for $want (last seen: $s)"
    return 1
}

# Press a key until the screen becomes one of the given states.
press_until() {
    local key="$1" want="$2" tries="${3:-6}" s i
    for ((i = 0; i < tries; i++)); do
        press "$key"
        if wait_for "$want" 8; then return 0; fi
        echo "press $key ($((i + 1))/$tries) did not reach $want, retrying"
    done
    echo "could not reach $want with $key"
    return 1
}

# 1. intro movies (skippable with START) -> title -> main menu
wait_for "intro blue" 30 || exit 1
press_until START "blue" || exit 1
shot menu

# 2. main menu -> Select Save (Continue when a save exists, else Bust Out; both
#    land on Select Save with the first slot highlighted)
press_until A "name cas" || exit 1

# 3. Select Save -> name entry (empty slot) or straight to Create-a-Sim (saved Sim)
s="$(screen)"
if [ "$s" = name ]; then
    shot name
    press_until A "name cas" || exit 1   # last name accepted (cursor starts on ENTER)
    press_until A "cas" || exit 1        # first name accepted
fi
wait_for "cas" 20 || exit 1
shot cas

# 4. Create-a-Sim: RIGHT x3 to the confirm icon, A, then A (YES) -> household
press RIGHTx3
wait_for "cas" 6 || exit 1
press_until A "question" || exit 1
shot question
press_until A "house dialogue loading" || exit 1

# 5. the household load takes a while; a greeting dialogue may be up first
wait_for "house dialogue" 40 || exit 1
if [ "$(screen)" = dialogue ]; then
    shot dialogue
    press A
    wait_for "house" 15 || exit 1
fi
shot house
sleep 8; shot house2

# KEEP=1 leaves the game up and in the household, so the owner can take it over
# from the state the drive reached instead of starting the walk again by hand.
if [ -n "${KEEP:-}" ]; then
    trap - EXIT; rm -f "$STEP"
    echo "left running in game as pid $PID (KEEP=1)"
else
    kill -TERM "$PID" 2>/dev/null; sleep 2
    trap - EXIT; cleanup
fi
echo "--- draws/frame seen ---"
grep -o 'per frame [0-9]* draws.*stalealloc [0-9]*' "$LOG" | tail -2
echo "--- present geometry ---"
grep -o 'vulkan: present .*' "$LOG" | tail -1
