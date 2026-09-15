"""Write a Bootloader Control Block that makes the next boot enter recovery.

On the UMIDIGI A5 Pro, `fastboot reboot recovery` does not reach recovery and
`fastboot boot <img>` is a no-op. What does work from fastboot mode is writing
"boot-recovery" into the command field of the misc partition, which this device
names "para", then rebooting:

    python make_bcb.py bcb_recovery.img
    fastboot flash para bcb_recovery.img
    fastboot reboot

Recovery clears the request itself once it has booted.

Usage: python make_bcb.py <out.img>
"""

import sys

BCB_SIZE = 2048          # command[32] + status[32] + recovery[768] + stage[32] + reserved
COMMAND = b"boot-recovery"


def main(path):
    bcb = bytearray(BCB_SIZE)
    bcb[0:len(COMMAND)] = COMMAND
    with open(path, "wb") as f:
        f.write(bytes(bcb))
    print("wrote %s (%d bytes, command=%s)" % (path, BCB_SIZE, COMMAND.decode()))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
