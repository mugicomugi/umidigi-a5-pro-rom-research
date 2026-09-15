"""Unpack and repack Android boot images (header v0/v1/v2).

Tested on the UMIDIGI A5 Pro images: unpack + repack of the EvolutionX 4.4
boot.img (header v0) reproduces the original byte for byte. For the LineageOS
20 boot.img (header v1) every byte matches except the 20-byte SHA1 id field at
offset 576, i.e. that build computed the id differently.

Usage:
  python bootimg.py unpack <boot.img> <outdir>
  python bootimg.py repack <outdir> <newboot.img> [options]

Repack options:
  --header-version N     write this header version (default: keep template's)
  --ramdisk FILE         use this ramdisk ("" or 'none' for no ramdisk)
  --kernel FILE          use this kernel (default: the unpacked one)
  --cmdline "..."        replace the kernel command line
"""

import hashlib
import os
import struct
import sys

MAGIC = b"ANDROID!"


def pad_to(n, page):
    rem = n % page
    return 0 if rem == 0 else page - rem


def unpack(img_path, outdir):
    with open(img_path, "rb") as f:
        data = f.read()
    if data[:8] != MAGIC:
        raise SystemExit("not an Android boot image")

    (kernel_size, kernel_addr, ramdisk_size, ramdisk_addr,
     second_size, second_addr, tags_addr, page_size,
     header_version, os_version) = struct.unpack("<10I", data[8:48])
    name = data[48:64]
    cmdline = data[64:576]
    extra_cmdline = data[608:1632]

    os.makedirs(outdir, exist_ok=True)

    off = page_size
    kernel = data[off:off + kernel_size]
    off += kernel_size + pad_to(kernel_size, page_size)
    ramdisk = data[off:off + ramdisk_size]
    off += ramdisk_size + pad_to(ramdisk_size, page_size)
    second = data[off:off + second_size]

    open(os.path.join(outdir, "kernel"), "wb").write(kernel)
    if ramdisk_size:
        open(os.path.join(outdir, "ramdisk"), "wb").write(ramdisk)
    if second_size:
        open(os.path.join(outdir, "second"), "wb").write(second)

    meta = {
        "kernel_addr": kernel_addr,
        "ramdisk_addr": ramdisk_addr,
        "second_addr": second_addr,
        "tags_addr": tags_addr,
        "page_size": page_size,
        "header_version": header_version,
        "os_version": os_version,
        "name": name.rstrip(b"\x00").decode("utf-8", "replace"),
        "cmdline": cmdline.rstrip(b"\x00").decode("utf-8", "replace"),
        "extra_cmdline": extra_cmdline.rstrip(b"\x00").decode("utf-8", "replace"),
    }
    with open(os.path.join(outdir, "meta.txt"), "w") as f:
        for k, v in meta.items():
            if isinstance(v, int):
                f.write("%s=0x%x\n" % (k, v))
            else:
                f.write("%s=%s\n" % (k, v))

    print("unpacked %s -> %s" % (img_path, outdir))
    for k, v in meta.items():
        print("  %-16s %s" % (k, ("0x%x" % v) if isinstance(v, int) else v))
    print("  kernel_size      %d" % kernel_size)
    print("  ramdisk_size     %d" % ramdisk_size)
    return meta


def read_meta(outdir):
    meta = {}
    for line in open(os.path.join(outdir, "meta.txt")):
        line = line.rstrip("\n")
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if v.startswith("0x"):
            meta[k] = int(v, 16)
        else:
            meta[k] = v
    return meta


def repack(outdir, newimg, header_version=None, ramdisk_path=None,
           kernel_path=None, cmdline=None):
    meta = read_meta(outdir)
    page = meta["page_size"]
    hv = meta["header_version"] if header_version is None else header_version

    kp = kernel_path or os.path.join(outdir, "kernel")
    kernel = open(kp, "rb").read()

    if ramdisk_path in ("none", ""):
        ramdisk = b""
    elif ramdisk_path:
        ramdisk = open(ramdisk_path, "rb").read()
    else:
        rp = os.path.join(outdir, "ramdisk")
        ramdisk = open(rp, "rb").read() if os.path.exists(rp) else b""

    sp = os.path.join(outdir, "second")
    second = open(sp, "rb").read() if os.path.exists(sp) else b""

    cl = meta.get("cmdline", "") if cmdline is None else cmdline
    cl_b = cl.encode("utf-8")
    if len(cl_b) > 511:
        raise SystemExit("cmdline too long for the 512-byte field")

    hdr = bytearray(page)
    hdr[0:8] = MAGIC
    struct.pack_into("<10I", hdr, 8,
                     len(kernel), meta["kernel_addr"],
                     len(ramdisk), meta["ramdisk_addr"],
                     len(second), meta["second_addr"],
                     meta["tags_addr"], page, hv, meta["os_version"])
    hdr[48:64] = meta.get("name", "").encode("utf-8")[:16].ljust(16, b"\x00")
    hdr[64:576] = cl_b.ljust(512, b"\x00")

    # id field: SHA1 over each section followed by its little-endian length.
    # mkbootimg built with v1 support always folds in a fourth (recovery_dtbo)
    # section even when writing a v0 header, so include it to stay bit-exact.
    sha = hashlib.sha1()
    for section in (kernel, ramdisk, second, b""):
        sha.update(section)
        sha.update(struct.pack("<I", len(section)))
    digest = sha.digest()
    hdr[576:576 + len(digest)] = digest

    hdr[608:1632] = meta.get("extra_cmdline", "").encode("utf-8")[:1024].ljust(1024, b"\x00")
    if hv >= 1:
        struct.pack_into("<IQI", hdr, 1632, 0, 0, 1648)   # recovery_dtbo_size/offset, header_size
    if hv >= 2:
        struct.pack_into("<IQ", hdr, 1648, 0, 0)          # dtb_size, dtb_addr

    with open(newimg, "wb") as f:
        f.write(hdr)
        f.write(kernel)
        f.write(b"\x00" * pad_to(len(kernel), page))
        if ramdisk:
            f.write(ramdisk)
            f.write(b"\x00" * pad_to(len(ramdisk), page))
        if second:
            f.write(second)
            f.write(b"\x00" * pad_to(len(second), page))

    print("wrote %s" % newimg)
    print("  header_version %d" % hv)
    print("  kernel  %d bytes" % len(kernel))
    print("  ramdisk %d bytes" % len(ramdisk))
    print("  cmdline %s" % cl)
    print("  total   %d bytes" % os.path.getsize(newimg))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    mode = sys.argv[1]
    if mode == "unpack":
        unpack(sys.argv[2], sys.argv[3])
    elif mode == "repack":
        outdir = sys.argv[2]
        newimg = sys.argv[3]
        kw = {}
        args = sys.argv[4:]
        i = 0
        while i < len(args):
            if args[i] == "--header-version":
                kw["header_version"] = int(args[i + 1]); i += 2
            elif args[i] == "--ramdisk":
                kw["ramdisk_path"] = args[i + 1]; i += 2
            elif args[i] == "--kernel":
                kw["kernel_path"] = args[i + 1]; i += 2
            elif args[i] == "--cmdline":
                kw["cmdline"] = args[i + 1]; i += 2
            else:
                raise SystemExit("unknown option %s" % args[i])
        repack(outdir, newimg, **kw)
    else:
        raise SystemExit(__doc__)
