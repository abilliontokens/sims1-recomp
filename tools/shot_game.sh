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
# presses the next key. A press a transition swallows is retried, and the script
# refuses to advance until the expected screen is showing. The walk is the one
# docs/playtest.md records and proved screen by screen with draw counts (the probe60
# run, then 17 of 17 runs to live mode), driven through the same SIMS1_STEP pad
# tokens:
#   intro movies (end by themselves) -> title "Please press START to begin": START
#   -> "Loading, please wait..." -> main menu (Get a Life highlighted): A
#   -> Get a Life (Start a Life highlighted): A
#   -> Create a Sim, last name (default NEWBIE, cursor on Done): A
#   -> only once a NEWBIE save exists on hdd/ (any run that answered YES has
#      written one): "Warning! There is already a 'Get a Life' save game of the
#      name NEWBIE ... Press (A) to proceed": A (proceeding writes nothing)
#   -> first name (default PAT): A
#   -> Create a Sim with Pat at the mirror, focus on DONE: A
#   -> loading -> the logo with "(A) Start house": A
#   -> "Would you like to save before starting this house?" YES highlighted:
#      DOWN to NO, then A (nothing is written to hdd/)
#   -> the household, with tutorial dialogues: A dismisses each as it comes up
#      (Welcome to The Sims, then Pat's first lines and more, some 20 s apart)
#   -> live mode, HUD up, clock running.
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
screen() { # classify a fresh screenshot -> state word on stdout
    shot probe
    python3 tools/classify_screen.py "out/shots/${TAG}_probe.png" 2>/dev/null || echo unknown
}
# keep the screenshot the last state was read from, as the stage's own
keep() { cp -f "out/shots/${TAG}_probe.png" "out/shots/${TAG}_$1.png"; }

# Wait until classify says one of the given states (re-screenshotting), or give up.
# The state seen is left in SEEN.
SEEN=""
wait_for() {
    local want="$1" tries="${2:-40}" s i
    for ((i = 0; i < tries; i++)); do
        alive || { echo "died while waiting for $want"; return 1; }
        s="$(screen)"
        SEEN="$s"
        case " $want " in *" $s "*) echo "screen: $s"; return 0 ;; esac
        sleep 3
    done
    echo "timed out waiting for $want (last seen: $s)"
    return 1
}

# Press a key until the screen becomes one of the given states.
press_until() {
    local key="$1" want="$2" tries="${3:-6}" i
    for ((i = 0; i < tries; i++)); do
        press "$key"
        if wait_for "$want" 8; then return 0; fi
        echo "press $key ($((i + 1))/$tries) did not reach $want, retrying"
    done
    echo "could not reach $want with $key"
    return 1
}

# 1. intro movies (about 27 s, they end by themselves) -> title
wait_for "title" 40 || exit 1
keep title

# 2. title -> "Loading, please wait..." -> main menu
press_until START "loading menu" || exit 1
[ "$SEEN" = loading ] && keep loading
wait_for "menu" 20 || exit 1
keep menu

# 3. main menu -> Get a Life -> Create a Sim's last name -> first name -> Create a Sim
#    (A x5 in all, the fifth below at Create a Sim)
press_until A "getalife" || exit 1
keep getalife
press_until A "lastname" || exit 1
keep lastname
press_until A "firstname overwrite" || exit 1
if [ "$SEEN" = overwrite ]; then  # only with a NEWBIE save already on hdd/
    keep overwrite
    press_until A "firstname" || exit 1
fi
keep firstname
press_until A "cas" || exit 1
keep cas

# 4. Create a Sim -> loading -> "(A) Start house". The "(A) Start house" line blinks,
#    and its off phase is the bare logo, which classifies as "loading" (the 4 known
#    misreads in classify_screen.py), so wait on until a lit frame is caught.
press_until A "loading starthouse" || exit 1
[ "$SEEN" = loading ] && keep loading2
wait_for "starthouse" 40 || exit 1
keep starthouse

# 5. the save question: DOWN to NO, A (nothing is saved)
press_until A "question" || exit 1
keep question
press_until DOWN "questionno" || exit 1
keep questionno
press_until A "dialogue house" || exit 1

# 6. the household: A dismisses each tutorial dialogue as it comes up; they arrive up
#    to ~25 s apart (docs/playtest.md), so live mode is only called reached after 45 s
#    of household with no dialogue. A is never pressed without a dialogue up: in live
#    mode it opens the pie menu or walks Pat somewhere.
n=0 quiet_since=$SECONDS
while ((SECONDS - quiet_since < 45)); do
    alive || { echo "died in the household"; exit 1; }
    s="$(screen)"
    case "$s" in
        dialogue)
            n=$((n + 1)); keep "dialogue$n"; echo "screen: dialogue ($n), A"
            press A; quiet_since=$SECONDS ;;
        house) sleep 3 ;;
        *) echo "screen: $s in the household"; sleep 3 ;;
    esac
    if ((n > 12)); then echo "more than 12 dialogues: A is not dismissing them"; exit 1; fi
done
wait_for "house" 5 || exit 1
keep house
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
grep -o 'per frame [0-9]* draws' "$LOG" | sort -k3 -n | tail -1 | sed 's/^/peak: /'
echo "--- present geometry ---"
grep -o 'vulkan: present .*' "$LOG" | tail -1
