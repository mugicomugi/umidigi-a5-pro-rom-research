# LineageOS 20 + MindTheGapps on the UMIDIGI A5 Pro

The sequence that got the unofficial LineageOS 20 build and MindTheGapps 13
running on a unit that started on stock Android 9. Each step links to the
pitfall it works around.

## Files

| File | Size (bytes) | md5 | Source |
|---|---:|---|---|
| `TWRP_3.7.0_9_20231020_Hadenix-breeze.img` | 24,725,504 | `b3b48b824cbb61648e5c9b5bb6b7372c` | [SourceForge umidigi-mt6763-dev / TWRP](https://sourceforge.net/projects/umidigi-mt6763-dev/files/TWRP/) |
| `lineage-20.0-20231119-UNOFFICIAL-breeze.zip` | 812,517,867 | `33f94a3b00e1b00299c1871931ccc9a4` | [SourceForge umidigi-mt6763-dev / ROM/OSS/LineageOS](https://sourceforge.net/projects/umidigi-mt6763-dev/files/ROM/OSS/LineageOS/) |
| `MindTheGapps-13.0.0-arm64-20231028.zip` | 385,741,639 | `11180da0a5d9f2ed2863882c30a8d556` | [SourceForge wsa-mtg / arm64/20231028](https://sourceforge.net/projects/wsa-mtg/files/arm64/20231028/) |

SourceForge mirrors can cut large downloads short (`curl: (18) end of response
with ... bytes missing`). Resume with `curl -C -` and check the md5.

## Steps

1. Enable developer options and USB debugging, then `adb reboot bootloader`.
2. Make `fastboot devices` see the phone: [windows.md](windows.md#fastboot-device-works-in-device-manager-but-fastboot-devices-is-empty).
3. Check `fastboot getvar unlocked`. The test unit already reported `yes`.
4. Flash TWRP:

   ```bash
   fastboot flash recovery TWRP_3.7.0_9_20231020_Hadenix-breeze.img
   ```

5. Boot straight into TWRP **without** letting stock Android boot first, or it
   may put its own recovery back: [pitfalls](pitfalls.md#the-stock-rom-puts-back-its-own-recovery).
6. In TWRP, starting from stock's encrypted data:

   ```powershell
   adb shell "twrp format data"
   adb shell "twrp reboot recovery"
   ```

7. Get the ROM zip onto `/sdcard`. With no bootable Android at this point, TWRP
   adb is the only route, and it cannot take files above about 1-2 MB. The
   800 KB chunk method worked here: [pitfalls](pitfalls.md#twrp-370-cannot-receive-large-files-over-adb).
   Check the md5 after reassembling.
8. Install:

   ```powershell
   adb shell "twrp install /sdcard/lineage-20.0-breeze.zip"
   adb shell "twrp wipe cache"
   adb shell "twrp wipe dalvik"
   ```

   Expected output ends with `script succeeded: result was [1.000000]`. The
   installer writes system, vendor, and its firmware images; see
   [device-facts](device-facts.md#firmware-the-lineageos-20-zip-writes).
9. Boot LineageOS once.
10. GApps: download MindTheGapps **on the phone** over Wi-Fi, or `adb push` it
    while Android is booted. Then `adb reboot recovery` and:

    ```powershell
    adb shell "ln -s /dev/block/platform/bootdevice /dev/block/bootdevice"
    adb shell "twrp install /sdcard/Download/MindTheGapps-13.0.0-arm64-20231028.zip"
    adb shell "twrp wipe cache"
    adb shell "twrp wipe dalvik"
    adb shell "twrp reboot system"
    ```

    Without the symlink the install fails with `Could not mount /mnt/system`:
    [pitfalls](pitfalls.md#mindthegapps-could-not-mount-mntsystem-aborting).

Result: LineageOS 20 boots and the Google apps are present.

## Known issues seen

- Status bar clock clipped at the screen edge, unresolved:
  [pitfalls](pitfalls.md#status-bar-clock-clipped-on-lineageos-20-unresolved).
- Calls, camera, fingerprint and Bluetooth were not tested.
