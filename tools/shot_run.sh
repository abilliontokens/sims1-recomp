#!/usr/bin/env bash
# Launch the native Linux build on the live Wayland session, screenshot it at fixed
# times, and shut it down. Proof for a change that is only visible on screen.
#
#   tools/shot_run.sh <tag> [build dir] [seconds at which to shoot ...]
#
# Screens land in out/shots/<tag>_<seconds>s.png, the game's stdout in out/shots/<tag>.log.
set -uo pipefail
cd "$(dirname "$0")/.."

TAG="${1:?usage: shot_run.sh <tag> [build-dir] [seconds...]}"
BUILD="${2:-out/build/linux-release}"
shift 2 2>/dev/null || shift 1
TIMES=("$@")
[ "${#TIMES[@]}" -gt 0 ] || TIMES=(14 20 26 34)

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
export DISPLAY="${DISPLAY:-:0}"
if [ -z "${XAUTHORITY:-}" ]; then
    for x in /run/user/$(id -u)/xauth_*; do [ -e "$x" ] && export XAUTHORITY="$x" && break; done
fi

mkdir -p out/shots
[ -e "$BUILD/assets" ] || ln -sfn ../../../assets "$BUILD/assets"

LOG="out/shots/${TAG}.log"
: > "$LOG"
"./$BUILD/Sims1" >> "$LOG" 2>&1 &
PID=$!
echo "launched $BUILD/Sims1 as pid $PID"

prev=0
for t in "${TIMES[@]}"; do
    sleep "$((t - prev))"
    prev=$t
    if ! kill -0 "$PID" 2>/dev/null; then echo "exited before ${t}s"; break; fi
    spectacle -b -n -f -o "out/shots/${TAG}_${t}s.png" >/dev/null 2>&1
    echo "shot at ${t}s -> out/shots/${TAG}_${t}s.png"
done

kill -TERM "$PID" 2>/dev/null
sleep 2
kill -KILL "$PID" 2>/dev/null
wait "$PID" 2>/dev/null
echo "--- log tail ---"
grep -vE '\[esp\+' "$LOG" | tail -12
