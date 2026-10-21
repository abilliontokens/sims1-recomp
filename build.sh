#!/usr/bin/env bash
# The Sims - native Linux build (Vulkan + SDL3, no Wine).
# Mirrors build.bat: configure, build xbe_symbols and write config/game.toml
# from assets/default.xbe on first run, then build the game.
set -euo pipefail

PRESET="${1:-linux-release}"
cd "$(dirname "$0")"

GAME_XBE="default.xbe"
GAME_EXE="Sims1"
OUT="out/build/${PRESET}"

echo
echo "  The Sims - build (${PRESET})"
echo "  ================================================"
echo

# The port itself runs straight from a disc image in assets. The build needs the XBE as a file:
# CMake hashes it and the recompiler reads its sections, so take that one file out of the image.
if [ ! -f "assets/${GAME_XBE}" ]; then
    ISO=$(ls -1 assets/*.iso assets/*.ISO 2>/dev/null | head -n 1 || true)
    if [ -n "${ISO:-}" ] && command -v python3 >/dev/null 2>&1; then
        echo "      taking ${GAME_XBE} out of ${ISO}"
        python3 tools/xiso_extract.py extract "${ISO}" assets --only "${GAME_XBE}"
    elif [ -n "${ISO:-}" ]; then
        echo "  ${ISO} is here but python3 is not, so ${GAME_XBE} cannot be taken out of it." >&2
    fi
fi

if [ ! -f "assets/${GAME_XBE}" ]; then
    echo "  Put the game in the assets folder first:" >&2
    echo "    $(pwd)/assets" >&2
    echo "  Either the disc image as a .iso, or ${GAME_XBE} with the game's files beside it." >&2
    exit 1
fi

# toolchain
echo "[1/3] Toolchain"
MISSING=""
for tool in clang clang++ cmake ninja; do
    command -v "$tool" >/dev/null 2>&1 || MISSING="${MISSING} ${tool}"
done
if [ -n "$MISSING" ]; then
    echo "  missing:${MISSING}" >&2
    echo "  Install clang, cmake and ninja, then run this again." >&2
    exit 1
fi
clang++ --version | head -n 1

# symbols
echo "[2/3] XDK symbols"
cmake --preset "${PRESET}" > /dev/null
if [ -f config/game.toml ]; then
    echo "      config/game.toml already present"
else
    cmake --build --preset "${PRESET}" --target xbe_symbols > /dev/null
    mkdir -p config
    "${OUT}/xbe_symbols" "assets/${GAME_XBE}" sdk/xdk --out config/game.toml
fi

# game
echo "[3/3] Game code"
echo "      first build recompiles ${GAME_XBE}, expect a long build ..."
cmake --build --preset "${PRESET}"

echo
echo "  The Sims built."
echo "  ${OUT}/${GAME_EXE}"
echo
