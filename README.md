# UMIDIGI A5 Pro custom ROM research

[日本語](README.ja.md)

Notes, measurements and small tools from getting **LineageOS 20** and
**EvolutionX 4.4** running on a UMIDIGI A5 Pro (MediaTek Helio P23 / MT6763,
codename `breeze` / `A5_Pro`). Everything was tested on a single unit in
September 2026.

> **Warning.** Flashing wipes your data and can brick the phone. All of this was
> done on a disposable device. Read [Safety](#safety) before trying anything.

## Main finding

The only EvolutionX build for this phone (4.4, Android 10, 2020) will not boot
after LineageOS 20 has been installed. It lands in **FASTBOOT mode**, which
looks like the bootloader rejecting it. It is not:

- The EvolutionX zip ships **no vendor partition**. It expects the stock
  Android 9 vendor (`ro.vndk.version=28`); LineageOS 20 replaces vendor with its
  own (`ro.vndk.version=33`), and Android 10's init dies on it.
- A dying init reboots to `androidboot.init_fatal_reboot_target`, which in AOSP
  defaults to `bootloader`. LineageOS sets it to `recovery` and EvolutionX
  does not, so the same crash shows up as fastboot in one ROM and TWRP in the
  other.

Writing the stock vendor from `UMIDIGI_A5_Pro_V2.0_20210326` makes EvolutionX
4.4 boot. Procedure: [docs/evolutionx-4.4.md](docs/evolutionx-4.4.md). Every
wrong turn taken to get there, including a soft brick:
[docs/investigation-log.md](docs/investigation-log.md).

## Status

| | Result |
|---|---|
| LineageOS 20 unofficial (20231119) + MindTheGapps 13 | boots, Google apps present |
| EvolutionX 4.4 (Android 10) with stock vendor | boots to setup and home screen; Wi-Fi, calls, camera, fingerprint not tested yet |
| EvolutionX 11.11 GSI (Android 16) | not tried |
| Status bar clock clipped on LineageOS 20 | unresolved |

## Findings

1. **EvolutionX 4.4 needs the stock vendor.** LineageOS 20 overwrites it.
   [evolutionx-4.4](docs/evolutionx-4.4.md)
2. **"Drops to fastboot" can simply be init crashing.** Check
   `androidboot.init_fatal_reboot_target` before blaming the bootloader.
   [evolutionx-4.4](docs/evolutionx-4.4.md#why-it-drops-to-fastboot)
3. **LineageOS 20 does not change the bootloader in any meaningful way.** Its
   `dtbo.img` is byte-identical to stock and its `lk.img` differs by 100 bytes.
   The stock `boot.img` is ramdisk-less too. [device-facts](docs/device-facts.md)
4. **Never erase `dtbo`.** LK needs it; the phone goes fully dark. Recovery
   through BROM with mtkclient works. [brom-recovery](docs/brom-recovery.md)
5. **TWRP 3.7.0 (Hadenix) cannot receive files over about 1-2 MB via adb.**
   Push while Android is booted instead (3 GB in 90 s).
   [pitfalls](docs/pitfalls.md#twrp-370-cannot-receive-large-files-over-adb)
6. **MindTheGapps 13 fails with `Could not mount /mnt/system`** because this
   device has no `/dev/block/bootdevice`. One symlink fixes it.
   [pitfalls](docs/pitfalls.md#mindthegapps-could-not-mount-mntsystem-aborting)
7. **`fastboot boot` is a no-op and `fastboot reboot recovery` does not reach
   recovery.** Write a BCB to the `para` partition.
   [pitfalls](docs/pitfalls.md#fastboot-cannot-boot-recovery)
8. **Windows:** fastboot needs WinUSB with Google's interface GUID; Zadig
   silently adds trusted root certificates; mtkclient can run without UsbDk, and
   installing UsbDk was followed by a Windows crash. [windows](docs/windows.md)

## Device at a glance

| | |
|---|---|
| SoC | MediaTek Helio P23 (MT6763), arm64 |
| Codename | `breeze` (LineageOS 20, TWRP 3.7.0), `A5_Pro` (EvolutionX 4.4) |
| Partitions | legacy; no `super`, no A/B |
| Block devices | `/dev/block/platform/bootdevice/by-name/` |
| `system` / `vendor` / `boot` | 3 GiB / 656 MiB / 32 MiB |
| misc partition | `para` |
| BROM USB ID | `0e8d:0003` (visible about 3.7 s) |

Full GPT, boot image headers and vendor comparison: [docs/device-facts.md](docs/device-facts.md)

## Repository layout

```text
docs/
  evolutionx-4.4.md       working procedure and root cause
  lineageos-20.md         LineageOS 20 + MindTheGapps install sequence
  pitfalls.md             TWRP adb limits, MindTheGapps fix, fastboot quirks, ...
  windows.md              fastboot driver GUID, Zadig side effects, mtkclient, UsbDk
  brom-recovery.md        recovering from a dead bootloader with mtkclient
  device-facts.md         partition table, boot headers, firmware comparison
  investigation-log.md    every hypothesis tested, including the wrong ones
tools/
  bootimg.py              unpack/repack Android boot images (v0/v1/v2)
  dat2img.py              rebuild system.img from system.new.dat + transfer list
  simg2img.py             expand an Android sparse image
  make_bcb.py             BCB image that boots recovery (flash to `para`)
  mtkwatch.py             log when BROM/preloader appears on USB
  push_chunks.ps1         chunked adb push with timeout, retry and resume
zadig/                    Zadig presets: fastboot (with GUID), BROM, preloader
patches/                  mtkclient patch to run without UsbDk
```

The Python tools need Python 3 (tested with 3.13). `mtkwatch.py` also needs
`pyusb` and a `libusb-1.0.dll`. Run any script without arguments for usage.

## Safety

- **Back up anything you care about.** Unlocking and flashing erase data.
- **Do not erase partitions to test ideas.** `fastboot erase dtbo` killed the
  bootloader. Overwrite with a known image and keep a copy on the PC.
- **Keep a rollback on the phone.** Leave a working ROM zip on `/sdcard` and
  use `twrp wipe data`, which keeps internal storage.
- **Prefer not to install UsbDk** on Windows. See [windows.md](docs/windows.md#usbdk-crashed-windows).
- **Zadig adds certificates** to `LocalMachine\Root` and `TrustedPublisher`.
  Remove them when you are done ([windows.md](docs/windows.md#zadig-side-effect-trusted-root-certificates)).
- ROM zips, firmware and GApps are **not included** in this repository. Get them
  from the linked sources and verify the checksums given in the docs.

## Credits

- EvolutionX: Team Evolution X. The A5_Pro 4.4 build was posted on
  [XDA](https://xdaforums.com/t/rom-evolution-x-4-4-for-the-umidigi-a5-pro-a5_pro-unnofficial.4121941/) by jmpf_bmx.
- LineageOS 20 unofficial and TWRP 3.7.0 for `breeze`: hadenix and
  [umidigi-mt6763-dev](https://github.com/umidigi-mt6763-dev).
- [MindTheGapps](https://github.com/MindTheGapps)
- [mtkclient](https://github.com/bkerler/mtkclient) by B. Kerler
- [Zadig / libwdi](https://github.com/pbatard/libwdi) by Pete Batard
- Stock firmware: UMIDIGI

## License

MIT for the documentation and tools, see [LICENSE](LICENSE).
[`patches/`](patches/) is GPL-3.0 because it modifies mtkclient.
