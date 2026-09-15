# Investigation log: why EvolutionX 4.4 would not boot

A record of what was tried, what each attempt showed, and which conclusions
turned out to be wrong. The wrong turns are kept on purpose: two plausible
theories were tested and failed before the real cause was found, and one of
them soft-bricked the phone.

Starting point: LineageOS 20 installed and working
([lineageos-20.md](lineageos-20.md)). Goal: run EvolutionX.

## 1. What exists

Only one EvolutionX build targets this device:
`EvolutionX_4.4_A5_Pro-10.0-20200622-2341-UNOFFICIAL.zip`, Android 10, from 2020.
The Evolution-X GitHub organisation has no device tree for `breeze`, `A5_Pro`
or `mt6763`. Its `updater-script` writes to
`/dev/block/platform/bootdevice/by-name/{system,boot}`, the path this device
uses, so it is a genuine device build and not a GSI.

## 2. The zip will not install

TWRP 3.7.0 reports `breeze`; the zip asserts `A5_Pro` (`E3004`). Read-only
properties cannot be changed in TWRP. The payload was written by hand instead:
brotli decompress, rebuild `system.img` from the transfer list, `dd` system and
boot, and apply the script's one `sed` edit.

## 3. It drops to fastboot

Every boot landed in FASTBOOT mode.

Comparing `boot.img` headers suggested a structural difference:

| | EvolutionX 4.4 | LineageOS 20 |
|---|---|---|
| header version | 0 | 1 |
| ramdisk | 0 bytes | 1,430,670 bytes |

The LineageOS zip also contains `lk.img`, `dtbo.img` and `tee.img`.

### Hypothesis A: LineageOS installed a bootloader that rejects ramdisk-less images

Test: repack the EvolutionX kernel as header v1, with no ramdisk (variant A)
and with LineageOS's ramdisk (variant C).

Both still dropped to fastboot. Header version and ramdisk presence were not
what decided the outcome.

Later confirmed wrong from two directions: the **stock** V2.0 `boot.img` is
also ramdisk-less (header v1, ramdisk 0 bytes), and LineageOS's `lk.img`
differs from stock by only 100 bytes.

### Control experiment

LineageOS 20's own `boot.img`, with the EvolutionX system still flashed:
**TWRP started.**

This was read as "the LineageOS kernel boots, the EvolutionX kernel does not".
That reading was wrong. The two boot images differ in the kernel **and** in the
command line, and the command line was what mattered (see step 5).

### Hypothesis B: the EvolutionX kernel does not match the installed `dtbo`

Test: `fastboot erase dtbo`, then boot EvolutionX.

**Result: black screen, no fastboot, no recovery.** LK itself needs `dtbo`.
The phone was brought back through BROM with mtkclient by writing `dtbo` and
`boot` again ([brom-recovery.md](brom-recovery.md)).

Later confirmed wrong: LineageOS's `dtbo.img` is byte-identical to stock.
There was never a mismatch to find.

## 4. Two useful discoveries on the way

- `fastboot boot` is a no-op and `fastboot reboot recovery` does not reach
  recovery on this device. Writing a BCB to `para` does.
- mtkclient on Windows needs a patch to work without UsbDk, and installing
  UsbDk was followed by a Windows crash ([windows.md](windows.md)).

## 5. The actual cause

Two facts put together:

1. **Vendor.** The EvolutionX 4.4 zip does not include vendor, so it depends on
   whatever is already installed. The LineageOS 20 zip had replaced the stock
   vendor (`ro.vndk.version=28`) with its own (`ro.vndk.version=33`). An Android
   10 system on that vendor makes init die.
2. **Where a dying init goes.** AOSP `android10-release`
   `system/core/init/reboot_utils.cpp` defaults `init_fatal_reboot_target` to
   `"bootloader"` and overrides it from `androidboot.init_fatal_reboot_target=`
   on the kernel command line. LineageOS 20 sets it to `recovery`; EvolutionX
   4.4 does not set it.

Every result above now fits:

| # | boot image | vendor | `dtbo` | Result | Explanation |
|---|---|---|---|---|---|
| 1 | EvolutionX original | LineageOS (VNDK 33) | stock-equal | FASTBOOT | init dies, default target `bootloader` |
| 2 | variant A (v1, no ramdisk, EvoX cmdline) | LineageOS | stock-equal | FASTBOOT | same |
| 3 | variant C (EvoX kernel + LOS ramdisk, EvoX cmdline) | LineageOS | stock-equal | FASTBOOT | same |
| 4 | LineageOS 20 original | LineageOS | stock-equal | TWRP | init dies, cmdline target `recovery` |
| 5 | EvolutionX original | LineageOS | **erased** | black screen | LK cannot run without `dtbo` |
| 6 | EvolutionX + `init_fatal_reboot_target=recovery` | **stock (VNDK 28)** | stock-equal | **EvolutionX boots** | vendor matches |

The system partition held the EvolutionX system, with the `fuseblk` edit, in
every row.

## 6. Fix

Take `vendor.img` from the stock firmware `UMIDIGI_A5_Pro_V2.0_20210326.rar`,
expand the sparse image, `dd` it to `vendor`, and boot. Full procedure:
[evolutionx-4.4.md](evolutionx-4.4.md).

## Lessons

- **"Drops to fastboot" does not mean the bootloader rejected the image.** On
  Android 10+, check the kernel command line for
  `androidboot.init_fatal_reboot_target` first. Adding `=recovery` gets you
  into TWRP, where logs can be read.
- **Change one variable per experiment.** The control in step 3 changed kernel
  and command line together and pointed at the wrong one.
- **Compare against stock before blaming a component.** Diffing `lk` and `dtbo`
  against the stock firmware would have ruled out both wrong hypotheses without
  touching the phone.
- **Never erase a partition to test a theory** on MediaTek. Overwrite it with a
  known image instead, and keep that image on the PC.

## Not tried

**Newest EvolutionX as a GSI.** `EvoX-11.11-GSI_treble_arm64-ab-VANILLA-20260914.img.xz`
from [Doze-off/EvoX_treble](https://github.com/Doze-off/EvoX_treble/releases)
(Android 16). Research notes put its uncompressed size at 3,142,012,928 bytes,
under the 3,221,225,472-byte `system` partition, with the MicroG and GApps
variants too large. Those figures were not verified here. Doubtful anyway:
vendor VINTF `target-level` is 3 (Android 9), far below what Android 16 expects.
