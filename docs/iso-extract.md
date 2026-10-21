# ISO Extraction Record

## Image

`Sims, The (USA).xiso.iso`, 413,532,160 bytes, in `assets/`.

The port does not need any of this at run time: `app::FindGame` (SDK `runtime/app/game_files.cpp`)
scans `assets/` for `*.iso`, opens the image with `kernel::Disc`, reads only the `default.xbe`
entry out of it to check the sha1, and mounts the rest as the console's `D:`, streaming each file
as the guest opens it. Dropping the image in `assets/` is the whole user-facing setup; extraction
below is a build and analysis step (CMake hashes `assets/default.xbe` and the recompiler reads its
sections), which `build.sh` and `build.bat` now do themselves with `--only default.xbe`.

## Tool

`tools/xiso_extract.py` — a stdlib-only XDVDFS reader with subcommands `info`, `list`, and `extract`.

## Reproduce

```
python3 tools/xiso_extract.py info "assets/Sims, The (USA).xiso.iso"
python3 tools/xiso_extract.py list "assets/Sims, The (USA).xiso.iso"
python3 tools/xiso_extract.py extract "assets/Sims, The (USA).xiso.iso" assets
```

## Volume geometry

Measured by `python3 tools/xiso_extract.py info`:

| field | value |
|---|---|
| image size | 413,532,160 bytes |
| partition base | `0x00000000` |
| root sector | 264 (offset `0x84000`) |
| root table size | 372 bytes |
| volume filetime | `0x01C2E90956CD0750` |
| files | 14 |
| file bytes | 412,924,266 (393.8 MiB) |

- Partition base `0x00000000`: this is a trimmed image, the bare game partition rather than a
  full dual-layer dump.
- 14 files, 412,924,266 bytes of file data; the remaining 608,894 bytes of the image are the
  volume structures and padding.

## Contents

The complete file list (14 files, 412,924,266 bytes), all in the root directory:

| Path | Size (bytes) |
|---|---|
| `audiostr.arc` | 45,060 |
| `audiostr.xwb` | 146,106,368 |
| `chall.ngh` | 622,592 |
| `datasets.arc` | 65,136,665 |
| `default.ngh` | 352,256 |
| `default.xbe` | 2,183,168 |
| `dsstdfx.bin` | 24,936 |
| `index.ind` | 122,720 |
| `models.arc` | 13,025,802 |
| `movies.arc` | 59,074,560 |
| `quickdat.arc` | 7,731,732 |
| `rletextu.arc` | 6,042,070 |
| `samples.arc` | 111,936,145 |
| `story.ngh` | 520,192 |

## Extraction

`python3 tools/xiso_extract.py extract "Sims, The (USA).xiso.iso" assets` was run and verified
complete:

```
14/14 files, 393.8 MiB written
```

and the single-file form the build scripts use, against the image in `assets/`:

```
1/1 files, 2.1 MiB written
default.xbe      2183168 bytes, magic b'XBEH', sha1 40ab6f97e8ee3bf4102a5a7820dcb8047fc30097
```

`assets/default.xbe` is 2,183,168 bytes, the size the `list` reports. The XBE itself is analysed in
[`xbe-analysis.md`](xbe-analysis.md).

## Notable files for the port

Only sizes and names are measured here. Nothing below has been confirmed by parsing the file
formats; every statement about what a file *contains* is marked **[inference]**.

- `default.xbe` (2,183,168 bytes) — the executable that is recompiled. Measured; see
  [`xbe-analysis.md`](xbe-analysis.md).
- `movies.arc` (59,074,560 bytes, ~59 MB) — the movie data the XBE's `XMV` library decodes.
  **[inference]**: unlike Bustin' Out, this disc carries no loose `*.xmv` files, so the movies
  must live inside an archive, and `movies.arc` is the one so named. The archive layout and the
  number of movies in it have not been read.
- `audiostr.xwb` (146,106,368 bytes, ~146 MB, the largest file) — the streamed audio bank.
  **[inference]** from the `.xwb` extension (XACT wave bank) and the `audiostr` (audio stream)
  name; `audiostr.arc` (45,060 bytes) is **[inference]** its index or companion table. The wave
  bank header has not been parsed.
- `*.arc` (`audiostr`, `datasets`, `models`, `movies`, `quickdat`, `rletextu`, `samples`) — the
  game's packed archives. **[inference]** from the names: `models` 3-D models, `rletextu`
  run-length-encoded textures, `samples` sound samples, `datasets` and `quickdat` game data. No
  archive directory has been decoded.
- `*.ngh` (`default`, `chall`, `story`) — neighbourhood saves/templates. **[inference]** from
  the names; the same three names appear on the Bustin' Out disc. Not parsed.
- `dsstdfx.bin` (24,936 bytes) — **[inference]** the DirectSound standard effects (DSP) image
  the title downloads at startup, by the XDK's conventional file name. Not verified.
- `index.ind` (122,720 bytes) — purpose unknown; not examined.

## Legal hygiene

Bring your own disc. The port ships no game data: the user supplies their own copy of the disc and
drops the image into `assets/`, where it stays — nothing has to leave it.

`.gitignore` ignores `/assets/`, `/generated/`, `/out/`, `*.iso` and `*.xbe`. The disc image, the
XBE and every file extracted from it, and the recompiled code derived from the XBE, are never
committed or distributed.
