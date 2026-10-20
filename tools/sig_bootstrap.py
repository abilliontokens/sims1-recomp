#!/usr/bin/env python3
"""Seed an XDK signature set for a build the SDK does not ship yet.

Usage, from the repo root (all paths have these defaults):

    python3 tools/sig_bootstrap.py [--xbe assets/default.xbe]
                                   [--ref sdk/xdk/5558/signatures.toml]
                                   [--out sdk/xdk/<build>/signatures.toml]

Why: xbe_symbols picks sdk/xdk/<build>/signatures.toml by the XBE's D3D8 (else
XAPILIB, else any library) build number. This title, The Sims (USA, title id
4541002F), is XDK 5233 for every library (XAPILIB, XBOXKRNL, LIBCMT, D3D8,
XGRAPHC, DSOUND and XMV all 5233), and the SDK ships sdk/xdk/3925,
sdk/xdk/5558 and sdk/xdk/5849 but nothing for 5233, so the scanner exits 1
with "no signatures for these library builds" and writes no config/game.toml
at all. The default reference is the 5558 set: 5233 is far closer to 5558
than to 5849 (or 3925), so its sec/k/ret/regs records describe code much
nearer to this title's; --ref can name 5849 instead.

What carries over between XDK builds, and what does not:

  * Byte signatures do NOT. len/hash/calls (and the count/nth/deep qualifiers of
    a byte match) describe 5558 code bytes; the same function recompiled for
    5233 has different bytes, so copying them would make the scanner hunt for
    foreign hashes and could claim a wrong function whose bytes collide.
    Every seeded record therefore drops len, hash, calls, count, nth and deep.
    With no len the record is the documented no-signature form (see the header
    of sdk/xdk/5849/signatures.toml and WriteSig in sdk/tools/symbols/main.cpp):
    the byte matcher skips it and the name stays 0 unless another line below
    finds it. Nothing is invented.
  * .XTLID export ids do, and in this XBE they name functions directly. An
    xtlid is the API identity .XTLID lists an address under, stable across
    builds, so a name whose id the image exports is named from the address
    .XTLID gives it (the scanner's "found by .XTLID" fallback). Unlike the
    3925 sibling port's image, which has no such section, this XBE does have
    one (.XTLID at 0x344280, 656 bytes, beside .text, D3D, XGRPH, DSOUND, XMV,
    XPP, .rdata, .data, DOLBY and $$XTIMAGE), so the xtlid channel resolves
    names here. The id is copied for every reference name that has one, and
    the XBE is parsed to report how many of them it actually exports.
  * Constant sets mostly do. k (sorted immediates/displacements), ret (stack
    bytes popped) and regs (registers read before written) survive a rebuild
    far better than bytes, so sec, k, ret and regs are copied verbatim. With
    sec present the scanner's constant matcher can place a function .XTLID
    does not name in its library section and score its constants against
    unclaimed starts.
  * [anchors] keep no signature ({}): they exist only as byte signatures for
    finding [data], and their 5558 bytes say nothing about 5233.
  * [data] is copied verbatim. Its xtlid entries resolve from .XTLID alone, so
    in this XBE they can resolve; its in/insn entries only resolve once the
    named function is found by its bytes, which a seeded file never is, so
    those data stay 0 for now. That is the scanner's own guard against
    trusting a foreign instruction index.

The output is a starting point, not a signed set: once a 5233 config names
enough functions by .XTLID and constants, `xbe_symbols --sign` on it produces
real 5233 byte signatures to replace this seed.

Standard library only.
"""

from __future__ import annotations

import argparse
import struct
import sys
import tomllib
from collections import Counter
from pathlib import Path

ENTRY_KEYS = (0xA8FC57AB, 0x94859D4B)  # retail, debug
THUNK_KEYS = (0x5B6D40B6, 0xEFB1F152)


def u32(data: bytes, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


class Xbe:
    """The parts of an XBE this bootstrap needs: header, sections, libraries, .XTLID."""

    def __init__(self, path: Path) -> None:
        self.path = path
        d = self.data = path.read_bytes()
        if len(d) < 0x180 or d[:4] != b"XBEH":
            raise SystemExit(f"{path}: not an XBE")
        self.base = u32(d, 0x104)
        self.header_size = u32(d, 0x108)
        self.image_size = u32(d, 0x10C)
        cert = u32(d, 0x118)
        self.title_id = u32(d, cert - self.base + 8)
        ep, kt = u32(d, 0x128), u32(d, 0x158)
        for ek, tk in zip(ENTRY_KEYS, THUNK_KEYS):
            if self.base <= (ep ^ ek) < self.base + self.image_size:
                self.entry, self.kernel_thunk = ep ^ ek, kt ^ tk
                break
        else:
            raise SystemExit(f"{path}: entry point key not recognised")
        self.sections: list[dict] = []
        sec_addr = u32(d, 0x120)
        for i in range(u32(d, 0x11C)):
            o = sec_addr - self.base + i * 56
            flags, va, vsize, raw, rsize = struct.unpack_from("<IIIII", d, o)
            name_at = u32(d, o + 20) - self.base
            name = d[name_at : d.index(b"\0", name_at)].decode()
            self.sections.append(
                {"name": name, "flags": flags, "va": va, "vsize": vsize, "raw": raw, "rsize": rsize}
            )
        self.libraries: list[dict] = []
        lib_addr = u32(d, 0x164)
        for i in range(u32(d, 0x160)):
            o = lib_addr - self.base + i * 16
            major, minor, build, flags = struct.unpack_from("<HHHH", d, o + 8)
            self.libraries.append(
                {"name": d[o : o + 8].rstrip(b"\0").decode(), "major": major,
                 "minor": minor, "build": build, "flags": flags}
            )
        # .XTLID: 8-byte (export id, address) pairs, as in xbe_symbols' Exports(). Not every
        # XBE has the section (this one does: 0x344280, 656 bytes; some 3925 images have none):
        # has_xtlid tells "no section" apart from "a section that lists no id we know".
        self.has_xtlid = any(s["name"] == ".XTLID" for s in self.sections)
        self.xtlid: dict[int, int] = {}
        for s in self.sections:
            if s["name"] != ".XTLID":
                continue
            for o in range(s["raw"], s["raw"] + min(s["vsize"], s["rsize"]) - 7, 8):
                export_id, addr = struct.unpack_from("<II", d, o)
                self.xtlid.setdefault(export_id, addr)

    def build(self) -> int:
        """The build xbe_symbols would pick: D3D8/D3D8LTCG/XAPILIB first, then any library."""
        for pick in ("D3D8", "D3D8LTCG", "XAPILIB"):
            for lib in self.libraries:
                if lib["name"] == pick:
                    return lib["build"]
        return self.libraries[0]["build"]

    def section_at(self, va: int) -> str:
        for s in self.sections:
            if s["va"] <= va < s["va"] + s["vsize"]:
                return s["name"]
        return "?"


def hx(v: int) -> str:
    return f"0x{v:X}"


def seeded_symbol(name: str, ref: dict, xbe: Xbe, stats: Counter) -> str:
    """One [symbols] line: the reference record with its byte signature removed."""
    parts: list[str] = []
    sec = ref.get("sec")
    if sec:
        parts.append(f'sec = "{sec}"')
    xtlid = ref.get("xtlid")
    if xtlid is not None:
        parts.append(f"xtlid = {hx(xtlid)}")
        stats["xtlid_kept"] += 1
        if xtlid in xbe.xtlid:
            stats["xtlid_in_xbe"] += 1
    k = ref.get("k") or []
    if k:
        parts.append("k = [" + ", ".join(hx(v) for v in k) + "]")
        if len(k) >= 3:  # the scanner's kMinConstants: matchable by constants
            stats["constants_candidates"] += 1
    ret = ref.get("ret")
    if isinstance(ret, list):
        if len(ret) == 1:
            parts.append(f"ret = {ret[0]}")
        elif ret:
            parts.append("ret = [" + ", ".join(str(v) for v in ret) + "]")
    elif ret is not None:
        parts.append(f"ret = {ret}")
    if "regs" in ref:
        regs = ", ".join(f'"{r}"' for r in ref["regs"])
        parts.append(f"regs = [{regs}]")
    if not parts:
        stats["empty"] += 1
    return f"{name} = {{{', '.join(parts)}}}"


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description="Seed XDK signatures for an unshipped build from a shipped one")
    ap.add_argument("--xbe", type=Path, default=root / "assets/default.xbe")
    ap.add_argument("--ref", type=Path, default=root / "sdk/xdk/5558/signatures.toml")
    ap.add_argument("--out", type=Path, default=None, help="default: sdk/xdk/<build>/signatures.toml")
    args = ap.parse_args(argv)

    xbe = Xbe(args.xbe)
    build = xbe.build()
    out = args.out or root / f"sdk/xdk/{build}/signatures.toml"
    ref = tomllib.loads(args.ref.read_text())
    ref_symbols: dict = ref.get("symbols", {})
    ref_anchors: dict = ref.get("anchors", {})
    ref_data: dict = ref.get("data", {})

    stats: Counter = Counter()
    def shown(p: Path) -> str:
        try:
            return str(p.resolve().relative_to(root))
        except ValueError:
            return p.name

    if xbe.has_xtlid:
        against = f"against {args.xbe.name}'s .XTLID."
        xtlid_note = "# a rebuild: xtlid (the .XTLID export id, named directly when this image exports it),"
        data_note = "# resolve from .XTLID, in/insn entries only once that function is found by its bytes."
    else:
        against = f"against {args.xbe.name}, which has no .XTLID section."
        xtlid_note = "# a rebuild: xtlid (kept for other titles of this build; it names nothing in this image),"
        data_note = "# stay 0 here (no .XTLID), in/insn entries only once that function is found by its bytes."
    lines = [
        f"# XDK {build} library signatures, seeded by tools/sig_bootstrap.py from",
        f"# {shown(args.ref)} (the reference build) {against}",
        f"# No {build} byte signatures exist yet, so no record carries len, hash or calls: with no",
        "# length a record is the documented no-signature form and the byte matcher skips it",
        "# instead of hunting for the reference build's hashes. What is copied is what survives",
        xtlid_note,
        "# sec, k (constant set), ret (stack bytes popped) and regs (registers read before",
        "# written), which the scanner's constant matcher scores against unclaimed starts.",
        "# [anchors] stay {} (byte-only in the reference). [data] is verbatim: xtlid entries",
        data_note,
        "# Replace this seed with real signatures from `xbe_symbols --sign` when convenient.",
        "",
        "[symbols]",
    ]
    for name in sorted(ref_symbols, key=str.lower):
        lines.append(seeded_symbol(name, ref_symbols[name], xbe, stats))
    lines += ["", "[anchors]"]
    for name in sorted(ref_anchors, key=str.lower):
        lines.append(f"{name} = {{}}")
    lines += ["", "[data]"]
    for name in sorted(ref_data, key=str.lower):
        d = ref_data[name]
        parts = []
        if d.get("in"):
            parts.append(f'in = "{d["in"]}", insn = {d["insn"]}, op = "{d["op"]}"')
        if d.get("xtlid") is not None:
            parts.append(f"xtlid = {hx(d['xtlid'])}")
        lines.append(f"{name} = {{{', '.join(parts)}}}")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")

    libs = " ".join(f"{l['name']} {l['major']}.{l['minor']}.{l['build']}" for l in xbe.libraries)
    print(f"{args.xbe}: title {xbe.title_id:08X}, entry {hx(xbe.entry)}, libraries: {libs}", file=sys.stderr)
    sections = ", ".join(f"{s['name']}@{hx(s['va'])}" for s in xbe.sections)
    if xbe.has_xtlid:
        print(f".XTLID: {len(xbe.xtlid)} exports; sections: {sections}", file=sys.stderr)
        named = (f"{stats['xtlid_in_xbe']} named by a .XTLID id this XBE exports "
                 f"({stats['xtlid_kept']} ids kept)")
    else:
        print(f".XTLID: this XBE has no .XTLID section, so no symbol is named by export id and the "
              f"seed rests on sec/k/ret/regs alone; sections: {sections}", file=sys.stderr)
        named = (f"none named by .XTLID (no section; {stats['xtlid_kept']} ids kept for other "
                 f"XDK {build} titles)")
    print(f"{out}: {len(ref_symbols)} symbols seeded for XDK {build}: {named}, "
          f"{stats['constants_candidates']} with k >= 3 for the "
          f"constant matcher, {stats['empty']} with nothing portable (stay 0); "
          f"{len(ref_anchors)} anchors unsigned, {len(ref_data)} data copied", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
