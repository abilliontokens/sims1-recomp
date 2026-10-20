#!/usr/bin/env bash
# Bring-up loop for the native Linux build.
#
# The recompiler finds functions by following direct calls, code pointers and the gaps between known
# functions. An indirect call the analysis never saw lands on no recompiled function and the runtime
# traps with "add 0x<addr> to [functions]". This runs the game, reads that address out of the log,
# appends it to config/game.toml's [functions] table and rebuilds, until the game stops asking or the
# round limit is reached. Every round's log is kept under out/bringup/.
#
# CAVEAT — false pass: the run only reaches what something drives it to. SIMS1_AUTOSTART's
# blind Start/Up/A cycle came over from the sibling Sims port, where it never finished name
# entry; nobody has yet checked how far it gets through The Sims' menus. A trap point
# past where the drive stalls is never reached unattended, and this loop can then report "no
# missing entry point, error lines: 0" having proven nothing about it. The loop only proves
# something when the drive is known to pass the trap point.
#
#   tools/bringup_loop.sh [rounds] [seconds per run]
set -euo pipefail
cd "$(dirname "$0")/.."

ROUNDS="${1:-10}"
SECONDS_PER_RUN="${2:-45}"
PRESET=linux-release
OUT="out/build/${PRESET}"
EXE="${OUT}/Sims1"
LOGS="out/bringup"
mkdir -p "$LOGS"

# the game is found beside the exe
[ -e "${OUT}/assets" ] || ln -sfn ../../../assets "${OUT}/assets"

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
[ -n "${XAUTHORITY:-}" ] || for x in /run/user/$(id -u)/xauth_*; do [ -e "$x" ] && export XAUTHORITY="$x"; done

for round in $(seq 1 "$ROUNDS"); do
    echo "=== round ${round}: build"
    cmake --build --preset "$PRESET" -j "$(nproc)" > "${LOGS}/build_${round}.log" 2>&1 || {
        echo "build failed, see ${LOGS}/build_${round}.log"; exit 1; }

    echo "=== round ${round}: run (${SECONDS_PER_RUN}s)"
    rm -rf "${OUT}/logs"
    timeout "$SECONDS_PER_RUN" "./${EXE}" > "${LOGS}/run_${round}.log" 2>&1 || true

    # every address the runtime asked for this round, in order, deduplicated
    mapfile -t want < <(grep -ho 'add 0x[0-9A-Fa-f]\+ to \[functions\]' "${LOGS}/run_${round}.log" |
                        grep -o '0x[0-9A-Fa-f]\+' | sort -u)
    if [ "${#want[@]}" -eq 0 ]; then
        echo "=== round ${round}: no missing entry point reported"
        grep -c '^\[.*\] error:' "${LOGS}/run_${round}.log" | sed 's/^/    error lines: /' || true
        exit 0
    fi

    echo "    adding ${#want[@]}: ${want[*]}"
    python3 - "${want[@]}" <<'PY'
import pathlib, re, sys
cfg = pathlib.Path('config/game.toml')
text = cfg.read_text()
add = [a for a in sys.argv[1:] if f'"{a.upper()}"' not in text.upper()]
if not add:
    sys.exit(0)
lines = '\n'.join(f'"{a}" = ""' for a in add)
text = re.sub(r'^\[functions\]\n', '[functions]\n' + lines + '\n', text, count=1, flags=re.M)
cfg.write_text(text)
print(f'    config/game.toml: {len(add)} entry point(s) added')
PY
done
echo "=== ${ROUNDS} rounds used, still asking for entry points"
exit 1
