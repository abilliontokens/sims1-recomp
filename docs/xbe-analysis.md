# XBE analysis — The Sims (USA), XDK 5233 bootstrap

Image: `assets/default.xbe`, extracted from `Sims, The (USA).xiso.iso` (see
[`iso-extract.md`](iso-extract.md)). Everything below was read from this image on Linux with
`tools/xbe_info.py`, the host tools from the `host-tools` preset
(`out/build/host-tools/xbe_symbols`, `out/build/host-tools/xbe_recomp`) and
`tools/sig_bootstrap.py`.

This file is written by hand. `tools/xbe_info.py`'s own usage text suggests
`--markdown docs/xbe-analysis.md`; that option opens the path for writing and would replace this
document with the generated header report. Write the generated report somewhere else.

## Header

Measured by `python3 tools/xbe_info.py assets/default.xbe`:

| field | value |
|---|---|
| size | 2,183,168 bytes |
| sha1 | `40ab6f97e8ee3bf4102a5a7820dcb8047fc30097` |
| magic | `XBEH` |
| title | `The Sims\u2122` (The Sims™) |
| title id | `0x4541002F` (EA-47) |
| region | `north_america` |
| media | `dvd_x2` |
| build type | retail |
| base | `0x00010000` |
| entry | `0x000C7B1E` |
| image size | 3,360,032 bytes |
| headers | 2,476 bytes |
| built | 2003-03-11T05:08:23+00:00 |
| certificate | 2003-03-13T21:55:15+00:00 |
| debug name | `C:\\eor\\src2\\games\\sims\\ESRC\\Sims___Xbox_Xbox_Console_Release\\Sims.exe` |
| kernel thunk | `0x001EE460` |
| kernel imports | 123 |

## Sections

Exactly as `xbe_info.py` prints them:

| section | vaddr | vsize | raw | raw size | flags |
|---|---|---|---|---|---|
| `.text` | `0x00011000` | 1566320 | `0x00001000` | 1566320 | preload,executable,head_page_read_only |
| `D3D` | `0x0018F680` | 75552 | `0x00180000` | 62132 | writable,preload,executable |
| `XGRPH` | `0x001A1DA0` | 79328 | `0x00190000` | 76132 | writable,preload,executable |
| `DSOUND` | `0x001B5380` | 40132 | `0x001A3000` | 39548 | writable,preload,executable |
| `XMV` | `0x001BF060` | 162700 | `0x001AD000` | 162684 | writable,preload,executable |
| `XPP` | `0x001E6C00` | 30812 | `0x001D5000` | 30812 | writable,preload,executable |
| `.rdata` | `0x001EE460` | 114132 | `0x001DD000` | 114116 | preload,executable |
| `.data` | `0x0020A240` | 1246908 | `0x001F9000` | 62168 | writable,preload,executable |
| `DOLBY` | `0x0033A900` | 29056 | `0x00209000` | 29036 | preload,executable,tail_page_read_only |
| `$$XTIMAGE` | `0x00341A80` | 10240 | `0x00211000` | 10240 | inserted_file,head_page_read_only,tail_page_read_only |
| `.XTLID` | `0x00344280` | 656 | `0x00214000` | 656 | inserted_file,head_page_read_only,tail_page_read_only |

The kernel thunk table (`0x001EE460`) sits at the start of `.rdata`.

## Libraries

Every library is **XDK build 5233**, qfe 1, approved:

| library | build | qfe |
|---|---|---|
| `XAPILIB` | 5233 | 1 |
| `XBOXKRNL` | 5233 | 1 |
| `LIBCMT` | 5233 | 1 |
| `D3D8` | 5233 | 1 |
| `XGRAPHC` | 5233 | 1 |
| `DSOUND` | 5233 | 1 |
| `XMV` | 5233 | 1 |

There is no `XNET`, `XONLINE` or `BINK` section. Names that the 5849 reference set tags to those
libraries are therefore correct zeros in this image, not identification gaps.

## Consequence 1: XDK 5233 had to be seeded

The SDK (`sdk/xdk/`) ships signature sets for **3925, 5558 and 5849 only**. `xbe_symbols` picks
`sdk/xdk/<build>/signatures.toml` by the D3D8 or XAPILIB build, then by any library's build
(`SignatureDir` in `sdk/tools/symbols/main.cpp`); every library here is 5233, so it found no set
at all. `tools/sig_bootstrap.py`
wrote `sdk/xdk/5233/signatures.toml` from the 5558 set, deliberately carrying `sec`, `k`, `ret`,
`regs` and `xtlid` but **no byte signatures**: 5558 bytes would mis-identify 5233 code, so a
copied hash would hunt for foreign bytes. Its own report:

```
242 symbols seeded for XDK 5233: 5 named by a .XTLID id this XBE exports (65 ids kept),
54 with k >= 3 for the constant matcher, 48 with nothing portable (stay 0);
2 anchors unsigned, 12 data copied
```

A record with no byte length is the no-signature form: the byte matcher skips it, and the name
stays 0 unless `.XTLID` or the constant matcher finds it.

## Consequence 2: the first scan found 24 of 242

The first `xbe_symbols` scan against that set found **24 of 242 functions and 0 of 12 data**.

By `.XTLID` export id (exact — an export id is an API identity):

| name | xtlid |
|---|---|
| `XInputClose` | `0x10037` |
| `XInputGetState` | `0x10038` |
| `XInputOpen` | `0x10036` |
| `XInputSetState` | `0x1003A` |
| `XMountUtilityDrive` | `0x10049` |

By the constant matcher (address, score):

| name | address | score |
|---|---|---|
| `D3DDevice_CopyRects` | `0x193240` | 0.85 |
| `D3DDevice_CreateVertexShader` | `0x191B20` | 1.00 |
| `D3DDevice_DrawIndexedVertices` | `0x195100` | 1.00 |
| `D3DDevice_DrawVertices` | `0x195060` | 1.00 |
| `D3DDevice_InsertCallback` | `0x1926F0` | 1.00 |
| `D3DDevice_SetPixelShader` | `0x195510` | 0.64 |
| `D3DDevice_SetRenderState_CullMode` | `0x1900F0` | 1.00 |
| `D3DDevice_SetRenderState_FogColor` | `0x1900A0` | 1.00 |
| `D3DDevice_SetRenderState_LineWidth` | `0x190240` | 0.60 |
| `D3DDevice_SetRenderState_StencilEnable` | `0x191210` | 0.60 |
| `D3DDevice_SetRenderState_StencilFail` | `0x1912A0` | 1.00 |
| `D3DDevice_SetShaderConstantMode` | `0x192000` | 0.91 |
| `D3DDevice_SetStreamSource` | `0x191E90` | 1.00 |
| `D3DDevice_SetTexture` | `0x1936F0` | 0.76 |
| `D3DDevice_SetTextureState_TexCoordIndex` | `0x190580` | 0.65 |
| `D3DDevice_SetVertexShaderConstantNotInlineFast` | `0x191D70` | 1.00 |
| `D3D_InternalAddRef` | `0x18FA90` | 1.00 |
| `D3D_InternalRelease` | `0x18FC20` | 1.00 |
| `crt_pow` | `0x17714C` | 1.00 |

5 by `.XTLID` + 19 by constants = 24. Every constant-matched D3D name falls inside the `D3D`
section (`0x0018F680`–`0x001A1DA0`); `crt_pow` falls in `.text`. Scores below 1.00 are the
matcher's own confidence and have not been confirmed by disassembly in this document.

## Consequence 3: `.XTLID` is present and mostly unmatched

This XBE **has** a `.XTLID` section: 656 bytes, 82 entries of 8 bytes (`u32 id, u32 address`).
Measured distribution of the addresses:

| where | entries |
|---|---|
| `.text` | 73 |
| `XPP` | 8 |
| null row (`id=0 addr=0x1471`) | 1 |
| **total** | **82** |

Only 5 ids matched the ids recorded in the SDK reference sets (the five XInput/XMount names
above). The other 76 non-null entries are an open lead, worked in
[`xtlid-and-xapi.md`](xtlid-and-xapi.md).

## Recompilation

Measured by `xbe_recomp config/game.toml --xdk sdk/xdk`:

```
direct: 241 functions, 14662 instructions
pointer seeds: 5561 accepted, 1169 rejected
gap fill: 2164 functions
c++ eh: 1 catch blocks, 1 continuations
late pointer seeds: 1
overlapping decodes: 3780
total: 12883 functions, 541952 instructions, 1741548 code bytes of 1954908, 225 jump tables, 4 callback entries
```

1,741,548 of 1,954,908 code bytes is **89.1%** coverage.

The recompiler also reported these unimplemented x86 opcodes. They are recorded here so that a
later change in the counts is visible as a regression:

| opcode | count |
|---|---|
| `arpl` | 12 |
| `bound` | 17 |
| `daa` | 6 |
| `das` | 5 |
| `enter` | 4 |
| `int1` | 7 |
| `into` | 1 |
| `lds` | 10 |
| `les` | 83 |
| `lss` | 1 |
| `outsb` | 2 |
| `outsd` | 1 |

**[inference]** These are overwhelmingly data decoded as code: they are legacy 16-bit/segment,
BCD and port-I/O opcodes that MSVC does not emit for 32-bit Xbox code, and the run also reports
3,780 overlapping decodes. Not measured: no individual site has been checked.

## Flat PE for static analysis

`out/game.exe` was written by `sdk/tools/symbols/xbe2pe.py` from `config/game.toml` and exports
**12883** functions at guest addresses 1:1 (the `total` function count above).

It is the artefact every symbol-naming agent reads: IDA or Ghidra (the script's own header names
Ghidra) opens it with the image at its load address and the recompiler's functions and the
config's names as exports, so an address read there goes straight into `config/game.toml`. Its
export names come from `config/game.toml`, so it is stale as soon as names are merged into that
file and **must be regenerated after each merge into `config/game.toml`**:

```
python3 sdk/tools/symbols/xbe2pe.py config/game.toml out/game.exe
```
