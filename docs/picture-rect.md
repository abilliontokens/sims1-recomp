# Picture rectangle: 640x432 at row 24, inside a 640x480 back buffer

Conclusion: `app::kGame.picture_top = 24`, `picture_height = 432` in `src/common/game_info.cpp`.
The title asks Direct3D for a 640x480 back buffer and draws a 640x432 picture in rows 24..455 of
it; rows 0..23 and 456..479 are never drawn (a TV's overscan hid them). The host now presents those
432 rows, scaled to the output, so the black bars are gone and the 4:3 projection the title built
for the band is shown at 4:3. This is **not** the sibling Bustin' Out's 640x448 at row 16.

Recorded 2026-10-20. Static evidence is from `out/game.exe` (the flat PE of `default.xbe`, guest
addresses 1:1). The on-screen measurements are the native Linux release build, windowed 1280x960
(2.000 render scale), `fps_cap = 60`, runs `pic_before` (fields 0/0) and `pic_after` (24/432);
screenshots under `out/shots/`, F3 captures under `out/build/linux-release/cap_pic/` (both
gitignored, kept on disk).

## 1. The title states its band: the renderer's picture size and offset

The renderer is the static object at `0x323CE8` (vtable `0x1F9530`; `dword_323CE0` points at it,
set at `0x12A894`). Its init (vtable slot 3, `sub_0012A8D0`) builds the one video mode and, just
before it creates the device, stores a picture size and offset beside it:

```asm
12A979  mov   [eax], ecx                     ; mode.Width  = 640 ([esi+0C0h], set at 0x12A880)
12A97B  mov   dword ptr [eax+4], 1E0h        ; mode.Height = 480
12A9BC  mov   [esi+8], ecx                   ; renderer+8   = 640          picture width
12A9BF  mov   edx, [eax+4]
12A9C2  sub   edx, 30h                       ;              480 - 48
12A9CB  mov   [esi+0Ch], edx                 ; renderer+0Ch = 432          picture height
12A9CE  mov   [esi+0B8h], edi                ; renderer+0B8h = 0.0         picture x offset
12A9D4  mov   dword ptr [esi+0BCh], 41C00000h; renderer+0BCh = 24.0        picture y offset
12A9DE  call  _sub_00156900                  ; create the device with that mode
```

`sub_00156900` fills the presentation parameters with the mode: BackBufferWidth 640
(`0x15693E`), BackBufferHeight **480** (`0x156944`), and calls `Direct3D_CreateDevice` at
`0x1569BE` (the run log agrees: `d3d: CreateDevice 640x480 ...`). Nothing writes `renderer+8` /
`+0Ch` again, and game code reads the height 291 times and the width 125 times. The enumerated
adapter mode list is overwritten with this one mode (`0x12A979`-`0x12A9A4`); there is no 720x480
or 1280x720 path.

## 2. Every back-buffer transform adds the 24

- **The offset helper** `sub_0012ABC0` makes the screen offset `(x, y) = (0 + 0.0 + 0.53125,
  0 + 24.0 + 0.53125)` (`fadd [ecx+0BCh]` at `0x12ABF6`, the 0.53125 pixel-centre bias at
  `0x1F2318`), and is applied whenever the render target is the back buffer.
- **2-D:** the UI view's matrix maps normalised coordinates to `{0, 0, 640, 432}` (the
  renderer's rect, vtable slot +0x24 `sub_0014A9E0`), and the title's own constant upload
  (`sub_00153050`, and `sub_00155100` at device setup: `fild dword_323CF0` / `fild dword_323CF4`
  at `0x1553AB` / `0x1553C2`) appends that offset. The 2-D transform is the vertex-shader
  constant c20 =

  ```
  [ 640      0        0         0 ]
  [ 0        432      0         0 ]
  [ 0        0        16777215  0 ]
  [ 0.53125  24.53125 0         1 ]      (row-vector form)
  ```

  so `y_pixel = v * 432 + 24.53` and the UI covers rows 24.5..456.5.
- **3-D:** the viewport builder `sub_0014AD70` makes `sy = -216, oy = 216` for the full-screen
  rect, and the title's viewport command (`sub_00152B30`) adds the same offset
  (`sub_0012ABC0` at `0x152BC2`), so clip y +1..-1 lands on rows 24.5..456.5, centred on 240.5.
- **Scissor:** `sub_00152CB0` turns the UI rect into `{0, 24, 640, 456}` for
  `D3DDevice_SetScissors`.
- **Clear:** the frame clear blacks the whole buffer (`D3DDevice_Clear` at `0x152735`) and fills
  only `{1, 25, 638, 454}` with the background colour (`0x1527DF`).
- **UI arithmetic** divides y by the run-time picture height (`fild [eax+0Ch]` then
  `fdivr flt_1EF780` (24.0) at `0x387CB`, likewise `0x3871C`, `0x18ED5`) and x by the one 1/640
  constant (`0x3ACCCCCD` at `0x1EFC74`, `fmul` at `0x453C9` / `0x4632B`).
- **Projection:** the aspect is always 4/3 (`fld flt_1F29F0` at `0x12A8B0`; camera default
  `mov [edx+3Ch], 3FAAAAABh` at `0x133264`) and the vertical FOV is scaled by 432/640
  (`fild` of the height at `0x122F4`, `fidiv` of the width at `0x122FE`), projected into the
  640x432 viewport: the scene is undistorted only when the 432-row band is shown at 4:3.

A whole-image scan of every section for the constants a 448 or 480 band would need found none:
no 1/448 (`0x3B124925`), 1/480 (`0x3B088889`), 2/448, 2/480, -2/448, -2/480, 448.0, 480.0, 640.0,
640/448 or 16/9. The band is computed from the mode height, not from a reciprocal.

## 3. Measured on screen and in the frame

**F3 frame captures (the back buffer itself).** Every capture lights exactly rows 24..455 of 480:

| capture | screen | `frame.txt` lines (draws) | BMP | black rows top / bottom | lit rows |
| --- | --- | ---: | --- | ---: | --- |
| `cap_pic/144635` (fields 0/0) | main menu | 23 | `0023_83110000.bmp`, `final.bmp` 640x480 | 24 / 24 | 24..455 |
| `cap_pic/144727` (fields 0/0) | live mode | 1236 | `1236_83110000.bmp`, `final.bmp` 640x480 | 24 / 24 | 24..455 |
| `cap_pic/145020` (fields 24/432) | live mode | 1235 | `1235_8323C000.bmp`, `final.bmp` 640x480 | 24 / 24 | 24..455 |

(A row is black when no pixel's R+G+B exceeds 30.)

**The presented window, before and after** (client area 1280x960 at 2.000 scale, so one guest row
is two window rows; a row is black when no pixel's R+G+B exceeds 40, 12 columns in from each side):

| screen | fields 0/0: black rows top / bottom | fields 24/432: black rows top / bottom |
| --- | --- | --- |
| main menu (`pic_before_menu.png` / `pic_after_menu.png`) | 49 / 48 (24.5 / 24 guest rows) | 1 / 0 |
| live mode (`pic_before_live.png` / `pic_after_live.png`) | 48 / 48 (24 / 24) | 0 / 0 |
| Create a Sim (`probe60_cas3.png` / `pic_after_cas.png`) | 48 / 48 | 0 / 0 |
| intro movie, The Sims logo (`pic_after_movie13.png`) | - | 0 / 0 |

The present line confirms the host now samples the band:

```
before: vulkan: present 5580 ... guest 640x480 target 1280x960 ... srcPx (0,0 1280x960) srcUv (0,0.000)-(1,1.000) dst (0,0 1280x960)
after:  vulkan: present 5640 ... guest 640x480 target 1280x960 ... srcPx (0,48 1280x864) srcUv (0,0.050)-(1,0.900) dst (0,0 1280x960)
```

`0.050 = 24/480` and `0.900 = 432/480`. The one remaining top row on the main menu is the 0.53
pixel-centre bias: the menu's backdrop quad starts at y = 24.53, so guest row 24 is half lit there.

## 4. The full-screen movies

The movies in `assets/movies.arc` are five XMV streams: four 640x480 and one 320x240 (none is
640x448 or 640x432). The title copies a movie frame raw to the back buffer at (0, 0) with
`D3DDevice_CopyRects` (`0x153D12`); its centring arithmetic divides by twice the buffer size and
always comes out 0 (`0x153CB2`-`0x153CD4`), so a full-screen movie covers all 480 rows and the crop
trims 24 rows from its top and bottom. Those rows were overscan on a TV as well, and the movies are
authored for it: the attract movie's captured gameplay is itself letterboxed to rows 24..456, the
in-game cutscene to rows 39..434, and the help movie is placed at (16, 96). The Sims logo movie
after the crop is `out/shots/pic_after_movie13.png` (the logo whole, nothing of it lost).

## 5. Host overlays

The host draws only the F1 settings and F2 performance panels (`src/common/overlay.cpp`), anchored
to the window (centred, and the top-right corner), not to fractions of the guest frame, so the crop
needs no remapping there.
