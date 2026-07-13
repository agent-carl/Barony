#!/bin/bash
# Project Umbra — cross-compile a Windows x64 build from Linux with MinGW-w64,
# staging prebuilt Windows libraries from the MSYS2 mingw64 repository.
# Produces build-win/umbra.exe (+ editor.exe) and a dist/ folder with the
# full DLL closure. No Visual Studio, no vcpkg, no Windows machine needed.
#
# Usage: tools/build-windows-cross.sh
# Prereqs (Debian/Ubuntu): mingw-w64 g++-mingw-w64 zstd cmake curl
#   sudo apt-get install -y mingw-w64 g++-mingw-w64 zstd cmake curl
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SYSROOT="${UMBRA_MINGW_SYSROOT:-$HOME/mingw-sysroot}"
MIRROR="https://repo.msys2.org/mingw/mingw64"
PKGDIR="$SYSROOT/pkgs"
mkdir -p "$PKGDIR" "$SYSROOT/mingw64"

# --- 1. stage prebuilt Windows libraries from MSYS2 --------------------------
LIST="$PKGDIR/.listing.html"
[ -s "$LIST" ] || curl -sS --max-time 60 "$MIRROR/" -o "$LIST"

fetch() {
  local base file
  base="$1"
  file="$(grep -oiE "mingw-w64-x86_64-$base-[0-9][^\"]*-any\.pkg\.tar\.zst" "$LIST" \
          | grep -viE -- '-debug-' | sort -V | tail -1)"
  [ -z "$file" ] && { echo "  !! not found: $base"; return 0; }
  [ -s "$PKGDIR/$file" ] || curl -sS --max-time 120 "$MIRROR/$file" -o "$PKGDIR/$file"
  tar --use-compress-program=unzstd -xf "$PKGDIR/$file" -C "$SYSROOT" 2>/dev/null
}

echo ">> staging Windows libraries into $SYSROOT"
for p in gcc-libs libwinpthread-git SDL2 SDL2_image SDL2_net SDL2_ttf physfs \
         openal libpng zlib libogg libvorbis glew freetype harfbuzz brotli \
         bzip2 graphite2 glib2 libiconv gettext pcre2 libjpeg-turbo libtiff \
         libwebp zstd xz libdeflate lerc libavif aom dav1d rav1e svt-av1 \
         libyuv libjxl lcms2 highway giflib jbigkit rapidjson; do
  fetch "$p"
done

# case-alias headers: MinGW headers are lowercase; the legacy source includes
# some with Windows-style capitalization (harmless on a case-insensitive FS).
INC="$SYSROOT/mingw64/include"
for pair in Dbghelp.h:dbghelp.h WinSock2.h:winsock2.h Windows.h:windows.h; do
  printf '#include <%s>\n' "${pair##*:}" > "$INC/${pair%%:*}"
done

# --- 2. configure + build ----------------------------------------------------
echo ">> configuring"
rm -rf "$REPO/build-win" && mkdir "$REPO/build-win"
cd "$REPO/build-win"
cmake .. \
  -DCMAKE_TOOLCHAIN_FILE="$REPO/cmake/mingw-w64-toolchain.cmake" \
  -DUMBRA_MINGW_SYSROOT="$SYSROOT/mingw64" \
  -DFMOD_ENABLED=OFF -DOPENAL_ENABLED=ON \
  -DSTEAMWORKS_ENABLED=0 -DEOS_ENABLED=0 -DPLAYFAB_ENABLED=0 \
  -DCMAKE_BUILD_TYPE=Release
echo ">> building"
cmake --build . -j"$(nproc)"

# --- 3. collect the DLL closure ----------------------------------------------
echo ">> collecting DLLs into dist/"
DIST="$REPO/build-win/dist"
BIN="$SYSROOT/mingw64/bin"
rm -rf "$DIST"; mkdir -p "$DIST/lang"
cp umbra.exe editor.exe "$DIST/"
cp "$REPO/lang/en.txt" "$DIST/lang/"
python3 - "$BIN" "$DIST" umbra.exe << 'PY'
import os, sys, subprocess, shutil
bindir, out, exe = sys.argv[1], sys.argv[2], sys.argv[3]
system = {x.lower() for x in ("kernel32.dll user32.dll shell32.dll opengl32.dll "
 "gdi32.dll advapi32.dll ole32.dll oleaut32.dll ws2_32.dll wsock32.dll msvcrt.dll "
 "winmm.dll imm32.dll version.dll setupapi.dll rpcrt4.dll comdlg32.dll dwmapi.dll "
 "shlwapi.dll cfgmgr32.dll hid.dll ntdll.dll secur32.dll iphlpapi.dll crypt32.dll "
 "bcrypt.dll userenv.dll dbghelp.dll glu32.dll usp10.dll dwrite.dll").split()}
def deps(p):
    try:
        o = subprocess.check_output(["x86_64-w64-mingw32-objdump","-p",p],
                                    stderr=subprocess.DEVNULL).decode()
    except Exception: return []
    return [l.split()[-1] for l in o.splitlines() if "DLL Name:" in l]
seen=set(); q=deps(exe)
while q:
    d=q.pop(); dl=d.lower()
    if dl in seen or dl in system or dl.startswith("api-ms-"): continue
    seen.add(dl); src=os.path.join(bindir,d)
    if os.path.exists(src):
        shutil.copy(src,out); q+=deps(src)
print("shipped DLLs:", sum(f.lower().endswith('.dll') for f in os.listdir(out)))
PY

echo ">> done: $DIST/umbra.exe + $(ls "$DIST"/*.dll | wc -l) DLLs"
