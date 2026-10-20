#!/usr/bin/env python3
"""Merge hand-proven [symbols] from config/found-*.toml into config/game.toml.

    python3 tools/merge_symbols.py [--config config/game.toml] [--apply] [found.toml ...]

Default inputs are every config/found-*.toml. Without --apply nothing is written; the
report is printed and the exit status is 1 if any conflict was found, so this doubles as
a gate.

Why a separate tool rather than editing game.toml by hand: several analysts work on
disjoint name sets at the same time, and the two ways their results can be wrong are both
silent in a hand merge.

  * Two names claiming one address. Only one of them can be right. The host replaces a
    named guest function wholesale, so the loser's calls would be dispatched to a host
    body with a different signature. Always a conflict.
  * One name claiming two addresses. Two analysts disagreed. Always a conflict.

Both abort the merge. A name already non-zero in game.toml that a found file re-states at
the same address is agreement, not a conflict, and is reported as confirmation. A name
already non-zero that a found file moves is a conflict: xbe_symbols wrote the old value
and something has to give, so a human decides.

Addresses are also bounds-checked against the XBE's own sections, read out of the config's
[xbe] path, and against the expected section for the name where sdk/xdk/5849/signatures.toml
gives one. This XBE's library sections are D3D, XGRPH, DSOUND, XMV and XPP (beside .text,
.rdata, .data, DOLBY, $$XTIMAGE and .XTLID), so D3D names must land in D3D, DSOUND names in
DSOUND, XPP names in XPP. An address outside the image, or in the wrong library section, is
refused: it cannot be what the name claims it is.

Standard library only.
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
import tomllib
from collections import defaultdict
from pathlib import Path

ENTRY_KEYS = (0xA8FC57AB, 0x94859D4B, 0x40B5C16E)  # retail, debug, chihiro
# XBE section header, 0x38 bytes: flags, virtual address, virtual size, raw address, raw size,
# section name address, ... The virtual pair at +0x04/+0x08 is what a guest address is compared
# against; +0x0C/+0x10 is the file-backed pair and is a different number in every section here.
SECTION_VADDR = 0x04
SECTION_NAME = 0x14


def xbe_sections(path: Path) -> list[tuple[str, int, int]]:
    """[(name, virtual_address, virtual_size)] from the XBE header."""
    data = path.read_bytes()
    base = struct.unpack_from("<I", data, 0x104)[0]
    count = struct.unpack_from("<I", data, 0x11C)[0]
    addr = struct.unpack_from("<I", data, 0x120)[0] - base
    out = []
    for i in range(count):
        rec = addr + i * 0x38
        vaddr, vsize = struct.unpack_from("<II", data, rec + SECTION_VADDR)
        name_ptr = struct.unpack_from("<I", data, rec + SECTION_NAME)[0] - base
        end = data.index(b"\0", name_ptr)
        out.append((data[name_ptr:end].decode("latin-1"), vaddr, vsize))
    return out


def expected_sections(sig_path: Path) -> dict[str, str]:
    if not sig_path.exists():
        return {}
    syms = tomllib.loads(sig_path.read_text()).get("symbols", {})
    return {n: v["sec"] for n, v in syms.items() if isinstance(v, dict) and "sec" in v}


def read_found(path: Path, table_name: str = "symbols") -> dict[str, int]:
    table = tomllib.loads(path.read_text()).get(table_name, {})
    out: dict[str, int] = {}
    for name, value in table.items():
        if isinstance(value, int) and value:
            out[name] = value
        elif value:
            raise SystemExit(f"{path}: [{table_name}] {name} is not an integer address: {value!r}")
    return out


def merge_data(cfg_text: str, current: dict[str, int], found_files: list[Path],
               sections: list[tuple[str, int, int]], xbe: Path) -> tuple[str, list[str], int]:
    """[data] addresses, merged by the same rules as [symbols] minus the section expectation:
    a data symbol legitimately lives in .data or .rdata, and nothing in the signature set says
    which. Two names at one address IS allowed here (a pointer and its alias can coincide), so
    only a name claimed at two addresses, an unknown name, an address outside the image, and a
    disagreement with the existing config are refused."""
    claims: dict[str, list[tuple[Path, int]]] = defaultdict(list)
    for f in found_files:
        for name, addr in read_found(f, "data").items():
            claims[name].append((f, addr))
    conflicts: list[str] = []
    additions: dict[str, int] = {}
    for name, entries in sorted(claims.items()):
        addrs = {a for _, a in entries}
        if len(addrs) > 1:
            where = ", ".join(f"{f.name}=0x{a:X}" for f, a in entries)
            conflicts.append(f"[data] {name}: claimed at {len(addrs)} different addresses ({where})")
            continue
        addr = addrs.pop()
        if name not in current:
            conflicts.append(f"[data] {name}: not a name the scanner knows")
            continue
        if sections and not any(s[1] <= addr < s[1] + s[2] for s in sections):
            conflicts.append(f"[data] {name}: 0x{addr:X} is outside every section of {xbe}")
            continue
        if current[name] and current[name] != addr:
            conflicts.append(
                f"[data] {name}: config already has 0x{current[name]:X}, "
                f"{entries[0][0].name} says 0x{addr:X}"
            )
            continue
        if current[name] != addr:
            additions[name] = addr
    for name, addr in additions.items():
        pattern = re.compile(rf"^(?P<pad>{re.escape(name)}\s*=\s*)0$", re.MULTILINE)
        cfg_text, n = pattern.subn(lambda m: f"{m.group('pad')}0x{addr:X}", cfg_text, count=1)
        if n != 1:
            raise SystemExit(f"could not find a '[data] {name} = 0' line to replace")
    return cfg_text, conflicts, len(additions)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("found", nargs="*", type=Path)
    ap.add_argument("--config", type=Path, default=Path("config/game.toml"))
    ap.add_argument("--signatures", type=Path, default=Path("sdk/xdk/5849/signatures.toml"))
    ap.add_argument("--apply", action="store_true", help="rewrite the config in place")
    args = ap.parse_args()

    found_files = args.found or sorted(args.config.parent.glob("found-*.toml"))
    if not found_files:
        print("no config/found-*.toml to merge")
        return 0
    # A file that declares `staged = true` has a precondition the runtime does not meet yet - merging
    # it would be harmful, not merely premature. It is skipped by the default glob and only merged
    # when named explicitly on the command line, so no bare run can pull it in by accident.
    if not args.found:
        held = [f for f in found_files if tomllib.loads(f.read_text()).get("staged") is True]
        for f in held:
            print(f"holding {f.name}: it declares staged = true; name it explicitly to merge it")
        found_files = [f for f in found_files if f not in held]
        if not found_files:
            print("nothing left to merge")
            return 0

    cfg_text = args.config.read_text()
    cfg = tomllib.loads(cfg_text)
    current: dict[str, int] = dict(cfg.get("symbols", {}))

    xbe = Path(cfg["xbe"]["path"])
    sections = xbe_sections(xbe) if xbe.exists() else []
    want_sec = expected_sections(args.signatures)
    # [data] is merged on the same text, before [symbols] rewrites it, so one --apply writes both
    cfg_text, data_conflicts, data_added = merge_data(
        cfg_text, dict(cfg.get("data", {})), found_files, sections, xbe
    )


    claims: dict[str, list[tuple[Path, int]]] = defaultdict(list)
    for f in found_files:
        for name, addr in read_found(f).items():
            claims[name].append((f, addr))

    conflicts: list[str] = []
    confirmations: list[str] = []
    additions: dict[str, int] = {}

    for name, entries in sorted(claims.items()):
        addrs = {a for _, a in entries}
        if len(addrs) > 1:
            where = ", ".join(f"{f.name}=0x{a:X}" for f, a in entries)
            conflicts.append(f"{name}: claimed at {len(addrs)} different addresses ({where})")
            continue
        addr = addrs.pop()
        if name not in current:
            conflicts.append(f"{name}: not a name the scanner knows; it would never be consulted")
            continue
        if sections:
            hit = next((s for s in sections if s[1] <= addr < s[1] + s[2]), None)
            if hit is None:
                conflicts.append(f"{name}: 0x{addr:X} is outside every section of {xbe}")
                continue
            # The expected section only means anything when this image has a section by that name.
            # This XBE has no BINK, XNET or XONLINE section, so the 5849 set's names with those
            # sec values can never match here; a library linked into .text instead of its own
            # section would otherwise be refused for landing where it actually lives.
            names = {s[0] for s in sections}
            if (sec := want_sec.get(name)) and sec in names and sec != hit[0] and sec != ".text":
                conflicts.append(
                    f"{name}: 0x{addr:X} is in section {hit[0]}, but this name's code lives in {sec}"
                )
                continue
        if current[name] and current[name] != addr:
            conflicts.append(
                f"{name}: config already has 0x{current[name]:X}, {entries[0][0].name} says 0x{addr:X}"
            )
            continue
        if current[name] == addr:
            confirmations.append(f"{name} = 0x{addr:X}")
        else:
            additions[name] = addr

    by_addr: dict[int, list[str]] = defaultdict(list)
    for name, addr in {**{k: v for k, v in current.items() if v}, **additions}.items():
        by_addr[addr].append(name)
    for addr, names in sorted(by_addr.items()):
        if len(names) > 1:
            conflicts.append(f"0x{addr:X}: claimed by {len(names)} names ({', '.join(sorted(names))})")

    conflicts.extend(data_conflicts)

    print(f"inputs: {', '.join(f.name for f in found_files)}")
    print(f"already named in {args.config}: {sum(1 for v in current.values() if v)} of {len(current)}")
    print(f"confirmed (same address): {len(confirmations)}")
    print(f"new [symbols] to add: {len(additions)}")
    for name, addr in sorted(additions.items()):
        print(f"  + {name} = 0x{addr:X}")
    print(f"new [data] to add: {data_added}")
    if conflicts:
        print(f"\nCONFLICTS ({len(conflicts)}) - nothing was written:")
        for c in conflicts:
            print(f"  ! {c}")
        return 1
    if not args.apply:
        print("\n--apply writes these into the config")
        return 0

    out = cfg_text
    for name, addr in additions.items():
        pattern = re.compile(rf"^(?P<pad>{re.escape(name)}\s*=\s*)0$", re.MULTILINE)
        out, n = pattern.subn(lambda m: f"{m.group('pad')}0x{addr:X}", out, count=1)
        if n != 1:
            raise SystemExit(f"{args.config}: could not find a '{name} = 0' line to replace")
    args.config.write_text(out)
    named = sum(1 for v in current.values() if v) + len(additions)
    print(f"\nwrote {args.config}: {named} of {len(current)} names now have an address")
    return 0


if __name__ == "__main__":
    sys.exit(main())
