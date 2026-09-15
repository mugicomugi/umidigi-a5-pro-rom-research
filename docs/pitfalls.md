# Pitfalls

Problems hit while installing LineageOS 20 and EvolutionX 4.4 on the UMIDIGI A5
Pro, what caused them, and what worked. Windows driver issues are in
[windows.md](windows.md).

## TWRP 3.7.0 cannot receive large files over adb

**Symptom.** With `TWRP_3.7.0_9_20231020_Hadenix-breeze.img`, `adb push` of a
ROM zip sits at 0% indefinitely. `adb sideload` stops at `(~0%)`. The adb client
uses almost no CPU, and `adb shell` commands started meanwhile hang too.

**Measurements** in TWRP (single push each):

| Size | Result |
|---:|---|
| 100 KB | ok, 81 ms |
| 1 MB | ok, 140 ms |
| 2 MB | stalled |
| 5 MB | stalled |
| 15 MB | stalled, also when pushed to `/tmp` (tmpfs) |
| 812 MB | stalled (push and sideload) |

Changes that did **not** help: platform-tools 37.0.1 versus r30.0.5 (with the
old adb server actually restarted), USB 2.0 versus USB 3.0 port, disabling
Windows USB selective suspend, pushing to `/tmp` instead of `/sdcard`, and
binding WinUSB to the MTP interface shown with Code 28.

**What works:**

1. **Push while Android is booted, then reboot to TWRP.** Booted-system adb over
   the same cable and port: 24 MB in 1.65 s, 812 MB in 48 s, 1.04 GB in 66 s,
   3 GB in 90 s. This is the reliable path.
2. **800 KB chunks** with [`tools/push_chunks.ps1`](../tools/push_chunks.ps1),
   reassembled on the device with `cat`. In a fresh TWRP session, after
   flashing and before Android had ever booted, this pushed an 812 MB ROM as
   992/992 chunks with no failures, and the md5 of the reassembled file matched.
   In later TWRP sessions the same method broke down: pushes ended with
   `adb: error: failed to read copy response` and the device went `offline`.
   Restarting the adb server did not bring it back; only replugging the cable
   did. The cause was not pinned down.
3. **Download on the phone over Wi-Fi** in Android, then install from `/sdcard`
   in TWRP.

## EvolutionX 4.4 zip refuses to install (E3004)

```text
E3004: This package is for device: A5_Pro; this device is breeze.
Updater process ended with ERROR: 7
```

The 2020 build asserts the old codename `A5_Pro`; TWRP 3.7.0 reports `breeze`.
`setprop ro.product.device A5_Pro` in TWRP fails with error `0xb`. Workaround:
write the zip's payload by hand, as described in
[evolutionx-4.4.md](evolutionx-4.4.md).

## MindTheGapps: `Could not mount /mnt/system! Aborting`

**Symptom.** `MindTheGapps-13.0.0-arm64-20231028.zip` on LineageOS 20:

```text
Mounting partitions
mount: : need -t
Could not mount /mnt/system! Aborting
Updater process ended with ERROR: 1
```

Rebooting TWRP and flashing again gives the same error.

**Cause**, from the zip's `META-INF/com/google/android/update-binary`:

1. `get_block_for_mount_point` searches `/etc/recovery.fstab` with
   `grep "[[:blank:]]$1[[:blank:]]"`. In this TWRP's fstab the mount point is the
   first column (`/system  ext4  /dev/block/platform/bootdevice/by-name/system ...`),
   so there is no leading blank and the pattern never matches.
2. The fallback for non-dynamic devices is
   `BLK_PATH=/dev/block/bootdevice/by-name`. This device only has
   `/dev/block/platform/bootdevice/by-name`.
3. `[ -b "$dev" ]` fails, `SYSTEM_BLOCK` stays empty, and `mount -o rw "" /mnt/system`
   fails with `need -t`.

**Fix.** Create the expected path in TWRP, then install:

```powershell
adb shell "ln -s /dev/block/platform/bootdevice /dev/block/bootdevice"
adb shell "twrp install /sdcard/Download/MindTheGapps-13.0.0-arm64-20231028.zip"
```

```text
Mounting partitions
/mnt/system mounted
...
Done!
```

The symlink lives in TWRP's RAM-backed `/dev`, so recreate it after every TWRP
reboot.

## fastboot cannot boot recovery

- `fastboot reboot recovery` does not reach recovery.
- `fastboot boot twrp.img` prints `OKAY` and stays in fastboot.

Write a Bootloader Control Block to the misc partition, `para` on this device:

```bash
python tools/make_bcb.py bcb_recovery.img
fastboot flash para bcb_recovery.img
fastboot reboot
```

This booted TWRP from fastboot mode (used once, successfully).

## The stock ROM puts back its own recovery

After `fastboot flash recovery TWRP...img`, the phone booted the stock Android 9
system. The next recovery boot showed the stock recovery instead of TWRP. That
fits the stock ROM restoring its recovery during boot. Get into TWRP before
the stock system boots even once: flash TWRP, then use the BCB method above
instead of rebooting normally. (On the test unit the BCB method was only
discovered later, so this exact sequence is untested, but the mechanism is the
same.)

Button combinations seen on the test unit: holding Volume Up + Power while the
phone rebooted from fastboot opened MediaTek **Factory Mode**, not recovery.
Volume Down + Power from powered off just booted Android normally.

## TWRP busybox `dd` rejects `bs=4M`

```text
dd: block size `4M': illegal number
```

Use a byte count: `bs=1048576`.

## Git Bash rewrites Android paths

Running adb from Git Bash:

```text
adb: error: failed to copy 'x' to 'C:/Program Files/Git/sdcard/x': remote secure_mkdirs failed
```

MSYS converted the `/sdcard/...` argument into a Windows path. Run `adb` from
PowerShell or cmd.

## `wipe data` versus `format data`

| TWRP command | Internal storage (`/data/media`) |
|---|---|
| `twrp wipe data` | kept: prints `Wiping data without wiping /data/media` |
| `twrp format data` | erased |

Use `wipe data` to keep ROM zips and images on `/sdcard` for later or for a
rollback.

## Files staged right after `format data` disappeared

A zip reassembled on `/sdcard` in TWRP directly after `twrp format data` was
gone once LineageOS had booted for the first time. Files placed on `/sdcard`
after Android's first boot survived later `twrp wipe data` runs. Cause not
confirmed. Stage files after the first boot.

## Status bar clock clipped on LineageOS 20 (unresolved)

On LineageOS 20 the status bar clock is cut off at the screen edge; the owner
describes it as a long-standing issue with this model. Values read with
`dumpsys window displays`:

- display cutout: one top cutout, bounding rect `Rect(488, 0 - 593, 63)`, top inset 63 px
- rounded corners: radius 0 on all four corners
- status bar inset frame `[0,0][1080,66]`
- `wm density`: physical 420, and a fresh install came up with override 378

These did **not** fix it:

| Change | Result |
|---|---|
| `wm density reset` (378 → 420) | no change |
| `settings put secure clock_seconds 0` | no change |
| `cmd overlay enable com.android.internal.display.cutout.emulation.corner` | no change (it models a corner camera; this one is centred) |
| 3-button navigation | the navigation bar was never affected |

`wm size 1040x2230` was set but reverted before it could be judged, because
lowering the resolution was not acceptable. A per-resource
`cmd overlay fabricate` on SystemUI status bar padding dimens was not tried.
Whether EvolutionX has the same problem has not been checked yet.
