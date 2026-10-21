#!/usr/bin/env bash
# Package the native Linux build, and the cross-built Windows exe when one is present.
#
#   out: Sims1-linux-x64.tar.zst, Sims1-win64.zip
#
# The Linux binary needs a shader compiler at run time: the Vulkan backend translates the
# title's shaders to SPIR-V through glslang (sdk/runtime/gpu/spirv.cpp), so glslang, SPIRV
# and SPIRV-Tools are real runtime dependencies. Arch ships no static SPIRV-Tools, so they
# cannot be linked in; they travel in lib/ beside the binary and are found through an
# $ORIGIN rpath. Everything else (SDL3, toml++, Dear ImGui) is already static, and the
# Vulkan loader is expected from the system like any other Vulkan application.
set -euo pipefail

BUILD="${1:-out/build/linux-release}"
EXE="Sims1"
STAGE="out/package/linux"
TARBALL="$EXE-linux-x64.tar.zst"

[ -x "$BUILD/$EXE" ] || { echo "no $BUILD/$EXE - build first: cmake --build --preset linux-release"; exit 1; }

# Relink with an rpath that looks beside the binary. CMAKE_BUILD_RPATH, not a raw -Wl,-rpath
# in CMAKE_EXE_LINKER_FLAGS: Ninja treats $ as its own escape character, so a literal $ORIGIN
# in a flag string reaches the linker as an empty string and the rpath silently becomes
# "/lib", which resolves against the system libraries and defeats the point. CMake's own rpath
# variables are escaped by the generator, so $ORIGIN survives into the ELF.
# CMAKE_EXE_LINKER_FLAGS carries --disable-new-dtags and is otherwise reset. A previous
# configure of this build directory may have left a stale -Wl,-rpath in it, and rpath entries
# concatenate, so it would sit in front of $ORIGIN/lib and keep winning. And the default
# new-style RUNPATH applies ONLY to the binary's own direct dependencies, not to theirs:
# libglslang pulls in libSPIRV-Tools, and with RUNPATH that lookup skips $ORIGIN/lib and falls
# through to the system copy, so the package breaks on any machine that lacks it.
# --disable-new-dtags emits the old DT_RPATH, which the whole dependency chain inherits.
cmake --preset linux-release -DCMAKE_BUILD_RPATH='$ORIGIN/lib' \
      -DCMAKE_EXE_LINKER_FLAGS=-Wl,--disable-new-dtags >/dev/null
cmake --build --preset linux-release >/dev/null

rm -rf "$STAGE"
mkdir -p "$STAGE/lib" "$STAGE/assets"
cp "$BUILD/$EXE" "$STAGE/"

# every non-system shared object the binary resolves, by what it actually links
ldd "$BUILD/$EXE" | awk '/=> \//{print $3}' |
    grep -E 'glslang|SPIRV' |
    while read -r so; do cp -L "$so" "$STAGE/lib/"; done

cp README.md "$STAGE/"
[ -f sdk/THIRD_PARTY.txt ] && cp sdk/THIRD_PARTY.txt "$STAGE/"
cat > "$STAGE/assets/PUT_YOUR_GAME_HERE.txt" <<'EOF'
Put your own legally acquired copy of The Sims (original Xbox, USA) in this
folder. The short way is the disc image itself: drop it in here as a .iso and
start the game. It is mounted as the console's disc and read as the game asks
for each file, so nothing is unpacked and nothing else has to be done. The 14
extracted disc files (default.xbe and its siblings) work just as well.

This port ships no game data of its own. It expects sha1
40ab6f97e8ee3bf4102a5a7820dcb8047fc30097 for default.xbe.
EOF

rm -f "$TARBALL"
tar --zstd -C "$STAGE/.." -cf "$TARBALL" linux --transform "s,^linux,$EXE-linux-x64,"
echo "wrote $TARBALL ($(du -h "$TARBALL" | cut -f1))"

# The cross-built Windows exe, when one is present. It is packaged from here rather than
# from a release.bat because this machine has no Windows: the exe is produced by the
# windows-cross preset (clang-cl + lld-link against an xwin MSVC/Windows SDK cache).
WINEXE="out/build/windows-cross/$EXE.exe"
if [ -f "$WINEXE" ]; then
    WINSTAGE="out/package/$EXE-win64"
    rm -rf "$WINSTAGE"
    mkdir -p "$WINSTAGE/assets"
    cp "$WINEXE" "$WINSTAGE/"
    cp README.md "$WINSTAGE/"
    [ -f sdk/THIRD_PARTY.txt ] && cp sdk/THIRD_PARTY.txt "$WINSTAGE/"
    cp "$STAGE/assets/PUT_YOUR_GAME_HERE.txt" "$WINSTAGE/assets/"
    # Imports MSVCP140.dll and VCRUNTIME140.dll: the CRT is dynamic, so a clean Windows needs
    # the Visual C++ redistributable. Everything else it imports (d3d12, dxgi, D3DCOMPILER_47,
    # the api-ms-win-crt-* UCRT set) ships with Windows 10 and later.
    cat > "$WINSTAGE/READ_ME_FIRST.txt" <<'EOF'
Needs the Microsoft Visual C++ Redistributable (2015-2022, x64) if you do not
already have it: https://aka.ms/vs/17/release/vc_redist.x64.exe

Put your own copy of the game in assets\ - see assets\PUT_YOUR_GAME_HERE.txt.
The disc image alone is enough: drop the .iso in there and run the exe.

A controller is read through SDL3: Xbox, PlayStation and Switch pads, hot
plugged. Keyboard and mouse drive controller port 0 as well.
EOF
    rm -f "$EXE-win64.zip"
    (cd "$WINSTAGE/.." && 7z a -tzip -bso0 -bsp0 "../../$EXE-win64.zip" "$EXE-win64" >/dev/null)
    echo "wrote $EXE-win64.zip ($(du -h "$EXE-win64.zip" | cut -f1))"
fi
