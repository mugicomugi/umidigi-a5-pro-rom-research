# EvolutionX 4.4 (Android 10) on a UMIDIGI A5 Pro that ran LineageOS 20

## Result

EvolutionX 4.4 booted to its setup wizard and home screen on a unit that had
previously been flashed with the unofficial LineageOS 20 build.

The partitions at the moment it booted:

| Partition | Contents |
|---|---|
| `recovery` | TWRP 3.7.0 Hadenix (`breeze`) |
| `boot` | EvolutionX 4.4 `boot.img` with one cmdline parameter added ([below](#3-diagnostic-boot-image)) |
| `system` | EvolutionX 4.4 system, rebuilt from the zip payload, with the installer's SELinux edit applied |
| `vendor` | **stock V2.0_20210326 vendor (VNDK 28)** |
| `lk`, `dtbo`, `tee`, modem, `logo` | as written by the LineageOS 20 zip (its `dtbo` equals stock; its `lk` is stock plus a 100-byte patch) |
| `userdata` | wiped with `twrp wipe data` |

**Not tested yet:** Wi-Fi, mobile data, calls/VoLTE, camera, fingerprint, and
Google sign-in. Also not tested: the original, unmodified EvolutionX
`boot.img` on the stock vendor. It should behave the same, since the only
difference is the fatal-reboot target, which matters only when init crashes.

## Files

| File | Size (bytes) | Checksum | Source |
|---|---:|---|---|
| `EvolutionX_4.4_A5_Pro-10.0-20200622-2341-UNOFFICIAL.zip` | 1,111,914,018 | md5 `1122cd8f52f18a56476d8c4f8899fb77` | [XDA thread](https://xdaforums.com/t/rom-evolution-x-4-4-for-the-umidigi-a5-pro-a5_pro-unnofficial.4121941/), [AndroidFileHost](https://androidfilehost.com/?fid=8889791610682876786) |
| `UMIDIGI_A5_Pro_V2.0_20210326.rar` | 1,205,371,696 | sha256 `8d4f44974f16ef60e78bc7a0a7cf9212c877b6ed3b0200c251e20043c57d89c2` | [UMIDIGI file service](https://projects.umidigi.com/fileservice/android/download/95fec272557a4fb58ff9131f8f753763/26040068888075430/UMIDIGI_A5_Pro_V2.0_20210326.rar) |
| `TWRP_3.7.0_9_20231020_Hadenix-breeze.img` | 24,725,504 | md5 `b3b48b824cbb61648e5c9b5bb6b7372c` | [SourceForge umidigi-mt6763-dev](https://sourceforge.net/projects/umidigi-mt6763-dev/files/TWRP/) |
| `lineage-20.0-20231119-UNOFFICIAL-breeze.zip` (rollback) | 812,517,867 | md5 `33f94a3b00e1b00299c1871931ccc9a4` | [SourceForge umidigi-mt6763-dev](https://sourceforge.net/projects/umidigi-mt6763-dev/files/ROM/OSS/LineageOS/) |

None of these are redistributed here. Check the hashes after downloading.

Intermediate files you will build, for comparison:

| File | Size (bytes) | Checksum |
|---|---:|---|
| `system.new.dat` (after brotli) | 2,487,201,792 | |
| `system.img` (before the SELinux edit) | 3,221,225,472 | md5 `2af5f86024101e538b738057503c175b` |
| stock `vendor.img` (sparse, from the rar) | 344,150,248 | sha256 `f3291b24bc269085519808288722bc10a3b432f24bd7d7ecc200af704f6aec0f` |
| `vendor_raw.img` | 687,865,856 | md5 `cadbb2e4921a127bcec68a1b6ceda051` |
| EvolutionX `boot.img` (original) | 9,082,880 | md5 `e0cc7917628e9c59a921da2d0c99f814` |
| `boot_diag.img` | 9,082,880 | md5 `448beedc72c458efb6ca4e4efb8e4462` |

## Why the zip does not just work

### 1. The codename assert

The zip's `updater-script` starts with:

```
assert(getprop("ro.product.device") == "A5_Pro" || getprop("ro.build.product") == "A5_Pro" || abort("E3004: ..."));
```

TWRP 3.7.0 reports `breeze`, so the install aborts with `E3004: This package is
for device: A5_Pro; this device is breeze.` Setting the property in TWRP fails
(`setprop` on `ro.*` returns error `0xb`). Same hardware, different codename.

The rest of the script does four things:

```
block_image_update("/dev/block/platform/bootdevice/by-name/system", "system.transfer.list", "system.new.dat.br", "system.patch.dat");
delete_recursive("/data/system/package_cache");
package_extract_file("boot.img", "/dev/block/platform/bootdevice/by-name/boot");
run_program("/sbin/sed", "-i", "/fuseblk/d", "/system_root/system/etc/selinux/plat_sepolicy.cil");
```

So the procedure below does the same by hand: rebuild the system image, write
system and boot, delete the one `fuseblk` line. The XDA post also asks for a
"SeLinux Fix AB" zip, and no working link to it could be found. EvolutionX
booted without it. Its kernel cmdline already contains
`androidboot.selinux=permissive`.

### 2. The zip ships no vendor

The zip contains only `system.*`, `boot.img` and the installer. It was built
to run on the stock Android 9 vendor (`ro.vndk.version=28`). The LineageOS 20
zip rewrites vendor to its own VNDK 33 build. On that vendor, EvolutionX 4.4's
init dies during boot.

**Coming from LineageOS 20 (or anything else that replaced vendor), you must
restore the stock vendor.** That was the one missing piece.

## Why it drops to fastboot

With the LineageOS vendor in place, EvolutionX 4.4 landed in **FASTBOOT mode**
on every boot. That looks like the bootloader rejecting `boot.img`, but it is
not. The kernel starts fine and init is the thing crashing.

In AOSP `android10-release`, `system/core/init/reboot_utils.cpp`:

```cpp
static std::string init_fatal_reboot_target = "bootloader";
...
const char kRebootTargetString[] = "androidboot.init_fatal_reboot_target=";
```

When init hits a fatal error it reboots to `init_fatal_reboot_target`, which
defaults to `bootloader`, i.e. fastboot mode. LineageOS 20's cmdline sets
`androidboot.init_fatal_reboot_target=recovery`. EvolutionX 4.4's does not.
The same crash therefore shows up in two different places:

| Boot image cmdline | Vendor | What you see |
|---|---|---|
| EvolutionX 4.4 (no target) | LineageOS VNDK 33 | FASTBOOT mode |
| LineageOS 20 (`=recovery`) | LineageOS VNDK 33, EvolutionX system | TWRP |
| EvolutionX 4.4 + `=recovery` | **stock VNDK 28** | **EvolutionX boots** |

## Procedure

### Requirements

- Unlocked bootloader and TWRP 3.7.0 in `recovery`.
- A PC with Python 3, `brotli`, `unzip` and 7-Zip (Git for Windows ships `brotli` and `unzip`).
- The files and scripts from this repository.
- **A booted Android system on the phone** (e.g. LineageOS 20) to push the images
  with. This TWRP build cannot receive files larger than about 1-2 MB over adb
  ([pitfalls](pitfalls.md#twrp-370-cannot-receive-large-files-over-adb)).

On Windows, run `adb` from PowerShell or cmd. Git Bash rewrites `/sdcard/...`
arguments into Windows paths.

### 1. Rebuild the system image

```bash
unzip EvolutionX_4.4_A5_Pro-10.0-20200622-2341-UNOFFICIAL.zip system.new.dat.br system.transfer.list boot.img
brotli -d -o system.new.dat system.new.dat.br
python tools/dat2img.py system.transfer.list system.new.dat system.img
# -> transfer list v4, 619174 blocks declared, highest block 786432
# -> output size: 3221225472 bytes (3.000 GiB)
```

The image is exactly the size of the `system` partition.

### 2. Expand the stock vendor

```powershell
7z e UMIDIGI_A5_Pro_V2.0_20210326.rar "UMIDIGI_A5_Pro_V2.0_20210326\vendor.img"
```

```bash
python tools/simg2img.py vendor.img vendor_raw.img
# -> sparse v1.0  block size 4096  blocks 167936  chunks 17
# -> expected raw size: 687865856 bytes
```

`vendor.img` in the rar is an Android sparse image (magic `0xed26ff3a`). It has
to be expanded before it can be written with `dd`.

### 3. Diagnostic boot image

Optional but recommended: add `androidboot.init_fatal_reboot_target=recovery`
so a crashing init drops you into TWRP, where you can read logs, instead of a
silent fastboot screen.

```bash
python tools/bootimg.py unpack boot.img evox_boot
python tools/bootimg.py repack evox_boot boot_diag.img --cmdline "bootopt=64S3,32N2,64N2 androidboot.selinux=permissive androidboot.init_fatal_reboot_target=recovery buildvariant=userdebug"
```

Only 68 bytes differ from the original, all inside the 512-byte cmdline field.

### 4. Push while Android is booted

With USB debugging enabled on the running system:

```powershell
adb push system.img     /sdcard/evox_system.img
adb push vendor_raw.img /sdcard/stock_vendor.img
adb push boot_diag.img  /sdcard/evox_boot.img
adb shell md5sum /sdcard/stock_vendor.img /sdcard/evox_boot.img
adb reboot recovery
```

Compare the md5 values with your PC copies. On the test unit, booted-system adb
moved the 3 GB system image in about 90 s.

### 5. Write the partitions from TWRP

TWRP's adb handles these short shell commands fine; only large pushes fail.
This TWRP's busybox `dd` rejects `bs=4M`, so give the block size in bytes.

```powershell
adb shell "dd if=/sdcard/stock_vendor.img of=/dev/block/platform/bootdevice/by-name/vendor bs=1048576"
adb shell "dd if=/sdcard/evox_system.img  of=/dev/block/platform/bootdevice/by-name/system bs=1048576"
adb shell "mkdir -p /mnt/ss && mount -o rw /dev/block/platform/bootdevice/by-name/system /mnt/ss"
adb shell "sed -i /fuseblk/d /mnt/ss/system/etc/selinux/plat_sepolicy.cil"
adb shell "sync; umount /mnt/ss"
adb shell "dd if=/sdcard/evox_boot.img    of=/dev/block/platform/bootdevice/by-name/boot bs=1048576"
adb shell "twrp wipe data"
adb shell "twrp wipe cache"
adb shell "twrp wipe dalvik"
adb shell "twrp reboot system"
```

Expected `dd` output: `656+0 records` for vendor (about 11 s) and
`3072+0 records` for system (about 75 s). The line `sed` removes is
`(genfscon fuseblk / (u object_r vfat ((s0) (s0))))`.

`twrp wipe data` keeps `/data/media`, so the images on `/sdcard` survive.
Going from Android 13 to Android 10 needs the data wipe.

### 6. First boot

Give it a few minutes. According to the XDA post, this build includes GApps and
should not have another GApps package flashed on top.

## Verify before rebooting

```powershell
adb shell "mkdir -p /mnt/vv && mount -o ro /dev/block/platform/bootdevice/by-name/vendor /mnt/vv"
adb shell "grep ro.vendor.build.date= /mnt/vv/build.prop"
# -> ro.vendor.build.date=Fri Mar 26 10:31:15 CST 2021
adb shell "grep -rh ro.vndk.version /mnt/vv/build.prop /mnt/vv/default.prop /mnt/vv/etc/*.prop"
# -> ro.vndk.version=28
adb shell "umount /mnt/vv"

adb shell "mount -o ro /dev/block/platform/bootdevice/by-name/system /mnt/ss"
adb shell "grep ro.build.version.release= /mnt/ss/system/build.prop"
# -> ro.build.version.release=10
adb shell "grep -c fuseblk /mnt/ss/system/etc/selinux/plat_sepolicy.cil"
# -> 0
adb shell "umount /mnt/ss"
```

Do not rely on `ro.vendor.build.fingerprint`: the stock vendor and the
LineageOS vendor report the same value.

## Roll back to LineageOS 20

Keep the LineageOS zip on `/sdcard` before you start. From TWRP:

```powershell
adb shell "twrp install /sdcard/Download/lineage-20.0-20231119-UNOFFICIAL-breeze.zip"
adb shell "twrp wipe data"
adb shell "twrp wipe cache"
adb shell "twrp wipe dalvik"
adb shell "twrp reboot system"
```

The LineageOS zip rewrites system, vendor, boot and its firmware images, so this
fully undoes the steps above. It was used several times during testing.

## Untested ideas

- **Coming from stock firmware.** The stock vendor is already present, so only
  system, boot and the SELinux edit should be needed.
- **An older TWRP that reports `A5_Pro`.** The same SourceForge folder has
  `TWRP_3.5.1_9_20210401_Hadenix-A5_Pro.img`. If it reports `A5_Pro`, the zip's
  assert should pass and the zip could be flashed normally, together with a
  stock vendor.
