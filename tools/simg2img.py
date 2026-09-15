"""Expand an Android sparse image into a raw image.

Stock MediaTek firmware ships vendor.img/system.img in the Android sparse
container format (magic 0xed26ff3a), which cannot be dd'd to a partition
directly - it has to be expanded first.

Usage: python simg2img.py <sparse.img> <raw.img>
"""

import struct
import sys

SPARSE_MAGIC = 0xED26FF3A
CHUNK_RAW = 0xCAC1
CHUNK_FILL = 0xCAC2
CHUNK_DONT_CARE = 0xCAC3
CHUNK_CRC32 = 0xCAC4


def expand(src_path, dst_path):
    with open(src_path, "rb") as src, open(dst_path, "wb") as dst:
        header = src.read(28)
        (magic, major, minor, file_hdr_sz, chunk_hdr_sz, blk_sz,
         total_blks, total_chunks, _crc) = struct.unpack("<I4H4I", header)

        if magic != SPARSE_MAGIC:
            raise SystemExit("not an Android sparse image (magic 0x%08x)" % magic)

        print("sparse v%d.%d  block size %d  blocks %d  chunks %d"
              % (major, minor, blk_sz, total_blks, total_chunks))
        print("expected raw size: %d bytes (%.3f GiB)"
              % (total_blks * blk_sz, total_blks * blk_sz / 1024 ** 3))

        if file_hdr_sz > 28:
            src.read(file_hdr_sz - 28)

        written_blocks = 0
        for _ in range(total_chunks):
            chunk_header = src.read(chunk_hdr_sz)
            chunk_type, _reserved, chunk_blks, total_sz = struct.unpack("<2H2I", chunk_header[:12])
            data_sz = total_sz - chunk_hdr_sz

            if chunk_type == CHUNK_RAW:
                remaining = data_sz
                while remaining > 0:
                    buf = src.read(min(remaining, 8 * 1024 * 1024))
                    if not buf:
                        raise SystemExit("unexpected end of sparse data")
                    dst.write(buf)
                    remaining -= len(buf)
            elif chunk_type == CHUNK_FILL:
                fill = src.read(4)
                dst.write(fill * (chunk_blks * blk_sz // 4))
            elif chunk_type == CHUNK_DONT_CARE:
                dst.write(b"\x00" * (chunk_blks * blk_sz))
            elif chunk_type == CHUNK_CRC32:
                src.read(4)
            else:
                raise SystemExit("unknown chunk type 0x%04x" % chunk_type)

            written_blocks += chunk_blks

        dst.flush()

    print("wrote %s (%d blocks)" % (dst_path, written_blocks))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    expand(sys.argv[1], sys.argv[2])
