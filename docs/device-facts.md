# Device facts (measured)

Everything here was read off one physical UMIDIGI A5 Pro unless marked
otherwise. If a guide elsewhere contradicts these numbers, trust these for this
hardware.

## Identity

| Item | Value |
|---|---|
| SoC | MediaTek Helio P23 (MT6763), arm64 |
| Codename on modern trees (LineageOS 20, TWRP 3.7.0) | `breeze` |
| Codename on 2020-era trees (EvolutionX 4.4) | `A5_Pro` |
| `fastboot getvar product` | `a5_pro_bsp` |
| Stock OS | Android 9, `UMIDIGI/A5_Pro/A5_Pro:9/PPR1.180610.011/1616484719:user/release-keys` |
| Display | 1080 x 2280, physical density 420 |
| Partition scheme | legacy: no `super`, no dynamic partitions, no A/B slots |

`breeze` and `A5_Pro` are the same hardware. The difference only matters because
installer scripts assert on the codename (see [pitfalls](pitfalls.md#evolutionx-44-zip-refuses-to-install-e3004)).

## Bootloader state

The test unit was already unlocked when it arrived: `fastboot getvar unlocked`
returned `yes`, `fastboot getvar secure` returned `no`, and
`ro.boot.flash.locked` was `0`. Unlocking a locked unit was not tested.

## fastboot behaviour

| Command | Result on this device |
|---|---|
| `fastboot flash recovery <24 MB img>` | works, about 1.5 s |
| `fastboot flash boot <9-10 MB img>` | works |
| `fastboot erase dtbo` | works, and **soft-bricks the phone** (see [brom-recovery](brom-recovery.md)) |
| `fastboot boot <img>` | prints `OKAY` and does nothing; stays in fastboot |
| `fastboot reboot recovery` | does not reach recovery |
| `fastboot flash para <BCB image>` then `fastboot reboot` | boots recovery (use [`tools/make_bcb.py`](../tools/make_bcb.py)) |

The multi-GB system image was never flashed through fastboot; it was written
with `dd` from TWRP instead.

## USB IDs (VID 0e8d)

| PID | Mode | Windows driver that worked |
|---|---|---|
| `0003` | BROM (boot ROM) | WinUSB, pre-installed via [`zadig/brom_0e8d_0003.cfg`](../zadig/brom_0e8d_0003.cfg) |
| `2000` | preloader | WinUSB, pre-installed via [`zadig/preloader_0e8d_2000.cfg`](../zadig/preloader_0e8d_2000.cfg) |
| `201c` | fastboot | WinUSB with Google's interface GUID, [`zadig/fastboot_0e8d_201c.cfg`](../zadig/fastboot_0e8d_201c.cfg) |
| `201d` | Android with USB debugging (composite MTP + ADB) | Windows default |
| `2008` | Android, MTP only | Windows default (WPD) |
| `4ee7` | TWRP 3.7.0 adb | bound automatically |

BROM mode was visible for about 3.7 s per attempt. mtkclient connected when
Volume Up + Volume Down were held while plugging the cable in.

## Partition table

Read from the GPT with mtkclient `printgpt` over BROM. All partitions are type
`EFI_BASIC_DATA`. Block devices appear under
`/dev/block/platform/bootdevice/by-name/` - note the extra `/platform/`;
`/dev/block/bootdevice/by-name/` does **not** exist on this device.

| Partition | Offset | Length | Bytes | Size |
|---|---|---|---:|---:|
| `boot_para` | `0x0000000000008000` | `0x0000000000100000` | 1,048,576 | 1 MiB |
| `recovery` | `0x0000000000108000` | `0x0000000002000000` | 33,554,432 | 32 MiB |
| `para` | `0x0000000002108000` | `0x0000000000080000` | 524,288 | 512 KiB |
| `expdb` | `0x0000000002188000` | `0x0000000001400000` | 20,971,520 | 20 MiB |
| `frp` | `0x0000000003588000` | `0x0000000000100000` | 1,048,576 | 1 MiB |
| `nvcfg` | `0x0000000003688000` | `0x0000000002000000` | 33,554,432 | 32 MiB |
| `nvdata` | `0x0000000005688000` | `0x0000000004000000` | 67,108,864 | 64 MiB |
| `metadata` | `0x0000000009688000` | `0x0000000002000000` | 33,554,432 | 32 MiB |
| `protect1` | `0x000000000b688000` | `0x0000000000800000` | 8,388,608 | 8 MiB |
| `protect2` | `0x000000000be88000` | `0x0000000000978000` | 9,928,704 | 9.47 MiB |
| `seccfg` | `0x000000000c800000` | `0x0000000000800000` | 8,388,608 | 8 MiB |
| `sec1` | `0x000000000d000000` | `0x0000000000200000` | 2,097,152 | 2 MiB |
| `proinfo` | `0x000000000d200000` | `0x0000000000300000` | 3,145,728 | 3 MiB |
| `md1img` | `0x000000000d500000` | `0x0000000004000000` | 67,108,864 | 64 MiB |
| `md1dsp` | `0x0000000011500000` | `0x0000000001000000` | 16,777,216 | 16 MiB |
| `spmfw` | `0x0000000012500000` | `0x0000000000100000` | 1,048,576 | 1 MiB |
| `sspm_1` | `0x0000000012600000` | `0x0000000000100000` | 1,048,576 | 1 MiB |
| `sspm_2` | `0x0000000012700000` | `0x0000000000100000` | 1,048,576 | 1 MiB |
| `gz1` | `0x0000000012800000` | `0x0000000001000000` | 16,777,216 | 16 MiB |
| `gz2` | `0x0000000013800000` | `0x0000000001000000` | 16,777,216 | 16 MiB |
| `nvram` | `0x0000000014800000` | `0x0000000004000000` | 67,108,864 | 64 MiB |
| `lk` | `0x0000000018800000` | `0x0000000000100000` | 1,048,576 | 1 MiB |
| `lk2` | `0x0000000018900000` | `0x0000000000100000` | 1,048,576 | 1 MiB |
| `boot` | `0x0000000018a00000` | `0x0000000002000000` | 33,554,432 | 32 MiB |
| `logo` | `0x000000001aa00000` | `0x0000000000800000` | 8,388,608 | 8 MiB |
| `dtbo` | `0x000000001b200000` | `0x0000000000800000` | 8,388,608 | 8 MiB |
| `tee1` | `0x000000001ba00000` | `0x0000000000500000` | 5,242,880 | 5 MiB |
| `tee2` | `0x000000001bf00000` | `0x0000000000900000` | 9,437,184 | 9 MiB |
| `vendor` | `0x000000001c800000` | `0x0000000029000000` | 687,865,856 | 656 MiB |
| `system` | `0x0000000045800000` | `0x00000000c0000000` | 3,221,225,472 | 3 GiB |
| `cache` | `0x0000000105800000` | `0x000000001b000000` | 452,984,832 | 432 MiB |
| `userdata` | `0x0000000120800000` | `0x00000006263fbe00` | 26,411,515,392 | 24.60 GiB |
| `flashinfo` | `0x0000000746bfbe00` | `0x0000000001000000` | 16,777,216 | 16 MiB |

Total disk size: `0x0000000747c00000` = 31,268,536,320 bytes (29.12 GiB).

The misc partition is `para`. `system` is exactly 3 GiB and cannot grow, so any
system image or GSI has to fit in 3,221,225,472 bytes.

## Boot images compared

All four share page size 2048, kernel address `0x40080000`, ramdisk address
`0x55000000` and tags address `0x54000000`.

| | header | kernel bytes | ramdisk bytes | kernel md5 |
|---|---:|---:|---:|---|
| Stock V2.0_20210326 | v1 | 9,079,780 | **0** | `70b06a3dc32149930132e6685054824f` |
| LineageOS 20 (20231119) | v1 | 9,079,780 | 1,430,670 | `70b06a3dc32149930132e6685054824f` |
| TWRP 3.7.0 Hadenix | v1 | 9,079,780 | 15,598,001 | `70b06a3dc32149930132e6685054824f` |
| EvolutionX 4.4 (20200622) | v0 | 9,080,469 | **0** | `717ecca4fae23920290860cd25dc4d8b` |

- Stock, LineageOS 20 and TWRP use the byte-identical stock kernel. EvolutionX
  4.4 ships its own kernel build.
- Stock boots with **no ramdisk** (system-as-root), exactly like EvolutionX 4.4,
  so "the bootloader rejects ramdisk-less images" is not a real failure mode here.

Kernel command lines:

| Image | cmdline |
|---|---|
| Stock | `bootopt=64S3,32N2,64N2 buildvariant=user veritykeyid=id:7e4333f9bba00adfe0ede979e28ed1920492b40f` |
| LineageOS 20 | `bootopt=64S3,32N2,64N2 androidboot.selinux=permissive androidboot.init_fatal_reboot_target=recovery buildvariant=userdebug` |
| EvolutionX 4.4 | `bootopt=64S3,32N2,64N2 androidboot.selinux=permissive buildvariant=userdebug` |

The missing `androidboot.init_fatal_reboot_target` on EvolutionX 4.4 is what
turns a dying init into a silent drop to fastboot; see
[evolutionx-4.4](evolutionx-4.4.md#why-it-drops-to-fastboot).

## Vendor images compared

| | Stock V2.0_20210326 | After LineageOS 20 zip |
|---|---|---|
| `ro.vndk.version` | **28** | **33** |
| `ro.vendor.build.version.release` | (not set) | 13 |
| `ro.vendor.build.date` | Fri Mar 26 10:31:15 CST 2021 | Sun Nov 19 17:17:27 +03 2023 |
| `ro.vendor.build.fingerprint` | `UMIDIGI/A5_Pro/A5_Pro:9/PPR1.180610.011/...` | same |
| VINTF `target-level` | 3 | 3 |

The fingerprint is identical, so it cannot tell the two apart; check
`ro.vndk.version` or the build date.

## Firmware the LineageOS 20 zip writes

`lineage-20.0-20231119-UNOFFICIAL-breeze.zip` contains `boot.img`, `dtbo.img`,
`lk.img`, `logo.bin`, `md1dsp.img`, `md1img.img`, `recovery.img`, `spmfw.img`,
`sspm.img`, `tee.img`, and system and vendor payloads. Compared with stock V2.0:

| Image | Result |
|---|---|
| `dtbo.img` | **byte-identical** to stock, md5 `f3c77ac432c50726c546b7c306007bcd`, 45,872 B |
| `lk.img` | stock is 667,616 B (md5 `ab796091d1b930ac4221bf9012f8cab6`); LineageOS is 1,048,576 B (md5 `14ef7e5c0a40a480a2770497c984a956`). Within the first 667,616 bytes exactly 100 bytes differ (offsets `0x3f1b2`-`0x796f9`); everything after is zero padding |
| vendor | replaced: VNDK 28 becomes VNDK 33 |

Installing LineageOS 20 does **not** swap the bootloader for a different one.
The part that matters when going back to an Android 10 ROM is vendor.
