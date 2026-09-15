"""Poll libusb and log the instant a MediaTek device appears or disappears.

MediaTek BROM (0e8d:0003) and preloader (0e8d:2000) mode only advertise
themselves for a few seconds per power cycle. On the UMIDIGI A5 Pro the BROM
was visible for about 3.7 s. This makes that window observable so you know
which button combination actually works before starting mtkclient.

Needs pyusb and a libusb-1.0.dll (the one bundled in the `libusb` pip package
works). This only enumerates devices, so no WinUSB binding is required.

Usage: python mtkwatch.py [--dll path\\to\\libusb-1.0.dll] [--seconds 300]
       (or set MTK_LIBUSB_DLL instead of --dll)
"""

import argparse
import os
import time

import usb.backend.libusb1
import usb.core

MTK_VID = 0x0E8D
MODES = {
    0x0003: "BROM (boot ROM)",
    0x2000: "preloader",
    0x201C: "fastboot",
    0x201D: "adb",
    0x2008: "mtp",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dll", default=os.environ.get("MTK_LIBUSB_DLL"))
    ap.add_argument("--seconds", type=int, default=300)
    args = ap.parse_args()

    if args.dll:
        backend = usb.backend.libusb1.get_backend(find_library=lambda _x: args.dll)
    else:
        backend = usb.backend.libusb1.get_backend()
    if backend is None:
        raise SystemExit("no libusb backend - pass --dll or set MTK_LIBUSB_DLL")

    print("watching for 0e8d devices for %ds - plug the phone in now" % args.seconds, flush=True)
    seen = set()
    start = time.time()
    while time.time() - start < args.seconds:
        now = {d.idProduct for d in usb.core.find(find_all=True, backend=backend, idVendor=MTK_VID)}
        for pid in sorted(now - seen):
            print("[%7.2fs] appeared 0e8d:%04x  %s"
                  % (time.time() - start, pid, MODES.get(pid, "unknown")), flush=True)
        for pid in sorted(seen - now):
            print("[%7.2fs] gone     0e8d:%04x" % (time.time() - start, pid), flush=True)
        seen = now
        time.sleep(0.15)


if __name__ == "__main__":
    main()
