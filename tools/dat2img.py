"""Rebuild a raw ext4 image from an OTA block payload (the "sdat2img" transform).

A block-based OTA zip ships system.new.dat(.br) plus system.transfer.list. The
transfer list says which 4096-byte block ranges of the target partition each
chunk of the .dat stream belongs to. This writes those chunks at the right
offsets and pads the result to the highest block referenced, so the output can
be dd'd straight onto the partition.

Decompress a .dat.br first:  brotli -d -o system.new.dat system.new.dat.br

Supports the erase/new/zero commands used by full (non-incremental) OTAs.

Usage: python dat2img.py <system.transfer.list> <system.new.dat> <system.img>
"""

import sys

BLOCK_SIZE = 4096


def parse_rangeset(text):
    nums = [int(n) for n in text.split(",")]
    if len(nums) != nums[0] + 1:
        raise ValueError("bad rangeset: %s" % text)
    return [(nums[i], nums[i + 1]) for i in range(1, len(nums), 2)]


def convert(list_path, dat_path, out_path):
    with open(list_path) as f:
        lines = f.read().splitlines()

    version = int(lines[0])
    total_blocks = int(lines[1])
    body = lines[4:] if version >= 2 else lines[2:]

    commands = []
    for line in body:
        if not line.strip():
            continue
        parts = line.split(" ")
        cmd = parts[0]
        if cmd in ("erase", "new", "zero"):
            commands.append((cmd, parse_rangeset(parts[1])))
        elif not cmd[0].isdigit():
            raise ValueError("unsupported command (incremental OTA?): %s" % cmd)

    max_block = max(end for _cmd, ranges in commands for _begin, end in ranges)

    print("transfer list v%d, %d blocks declared, highest block %d"
          % (version, total_blocks, max_block))
    print("output size: %d bytes (%.3f GiB)"
          % (max_block * BLOCK_SIZE, max_block * BLOCK_SIZE / 1024 ** 3))

    written = 0
    with open(out_path, "wb") as out, open(dat_path, "rb") as dat:
        for cmd, ranges in commands:
            if cmd != "new":
                continue
            for begin, end in ranges:
                out.seek(begin * BLOCK_SIZE)
                remaining = end - begin
                while remaining > 0:
                    take = min(remaining, 1024)
                    chunk = dat.read(take * BLOCK_SIZE)
                    if not chunk:
                        raise IOError("dat stream ended early at block %d" % begin)
                    out.write(chunk)
                    remaining -= take
                    written += take
        out.truncate(max_block * BLOCK_SIZE)

    print("wrote %d blocks (%d bytes) of real data -> %s"
          % (written, written * BLOCK_SIZE, out_path))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    convert(sys.argv[1], sys.argv[2], sys.argv[3])
