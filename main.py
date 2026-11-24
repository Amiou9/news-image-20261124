#!/usr/bin/env python3
"""Tuesday 24 November 2026, in one picture.

The picture beside this file, entry.png, is version A (Klasik): a
dense broadsheet front page on cream paper, with a serif masthead
reading "Tuesday, 24 November 2026", summing up the world's news
of that day. Its three lead stories are the COP31 climate talks
collapsing in Antalya with no deal, the United States blacklisting
Megaspeed on the same day Nvidia reinstated Jensen Huang as chief
executive, and Zelensky urging four-party talks between Ukraine,
Russia, the United States and Europe at once. Thirty-two further
stories, each with its own drawn illustration, and a world map with
every story numbered on it, fill the rest of the page.

This program does nothing but hand that picture over. It reads the
bytes, proves the PNG is complete by checking every chunk's
checksum in turn, confirms the picture fits the competition's size
limits, and writes an exact copy where the grader asks for it.
Only the standard library is used, nothing touches the network,
and a second run writes the same bytes as the first.
"""

import os
import struct
import sys
import zlib
from pathlib import Path

PICTURE = "entry.png"
MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1_048_576
MAX_SIDE = 1024
TAIL = b"\x00\x00\x00\x00IEND\xaeB`\x82"


def stop(why):
    raise SystemExit(f"{PICTURE}: {why}")


def scan(raw):
    """Walk the chunks in order, checking each checksum as we go.

    Returns the (width, height) from the IHDR chunk. Any cut-short
    header, any chunk running past the end of the file, any bad
    checksum, or any bytes after IEND, stops the run.
    """
    if raw[:8] != MAGIC:
        stop("does not begin with a PNG signature")
    cursor = 8
    header_seen = end_seen = False
    width = height = None
    while cursor < len(raw):
        if cursor + 8 > len(raw):
            stop("a chunk header is cut short")
        (length,) = struct.unpack(">I", raw[cursor:cursor + 4])
        kind = raw[cursor + 4:cursor + 8]
        stop_at = cursor + 12 + length
        if stop_at > len(raw):
            stop(f"the {kind.decode('latin-1')} chunk runs past the end of the file")
        payload = raw[cursor + 8:cursor + 8 + length]
        (kept,) = struct.unpack(">I", raw[cursor + 8 + length:stop_at])
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != kept:
            stop(f"the {kind.decode('latin-1')} chunk fails its checksum")
        if not header_seen and kind != b"IHDR":
            stop("the first chunk is not IHDR")
        header_seen = True
        if kind == b"IHDR":
            width, height = struct.unpack(">II", payload[:8])
        if kind == b"IEND":
            end_seen = True
            if stop_at != len(raw):
                stop("bytes follow the IEND chunk")
        cursor = stop_at
    if not header_seen or not end_seen:
        stop("the picture has no IHDR or no IEND chunk")
    return width, height


def check(raw):
    """Confirm the picture fits the competition's limits."""
    if len(raw) > MAX_BYTES:
        stop(f"is {len(raw)} bytes, over the 1 MiB limit")
    width, height = scan(raw)
    if width is None:
        stop("has no IHDR chunk")
    if width > MAX_SIDE or height > MAX_SIDE:
        stop(f"is {width}x{height}, over the 1024x1024 limit")
    if not raw.endswith(TAIL):
        stop("does not end with a whole IEND chunk")
    return width, height


def deliver(raw, width, height):
    """Write the exact bytes to the grader's output folder."""
    folder = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / PICTURE
    target.write_bytes(raw)
    if target.read_bytes() != raw:
        stop("the output copy does not match the source picture")
    print(f"wrote {target} -- {width}x{height}, {len(raw)} bytes")


def main():
    here = Path(__file__).resolve().parent
    raw = (here / PICTURE).read_bytes()
    width, height = check(raw)
    deliver(raw, width, height)


if __name__ == "__main__":
    main()
