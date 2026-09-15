# Recovering from a dead bootloader through BROM

## Do not erase `dtbo`

```bash
fastboot erase dtbo    # do not do this
```

On the UMIDIGI A5 Pro this took the phone from "drops to fastboot" to a black
screen with no fastboot, no recovery and no reaction to any button
combination. **The bootloader (LK) itself needs `dtbo`.** Without it LK never
gets far enough to offer fastboot.

The erase was an attempt to test the theory that a mismatched `dtbo` was
stopping EvolutionX 4.4 from booting. The theory was wrong: the `dtbo` in place
was byte-identical to stock ([device-facts](device-facts.md#firmware-the-lineageos-20-zip-writes)).

## Symptoms

- Black screen. Holding power, and Volume Up/Down + Power, do nothing visible.
- `adb devices` and `fastboot devices` are empty.
- Windows Device Manager briefly shows `MT65xx Preloader` (`0e8d:2000`) with an error.

## What still works

The SoC's boot ROM (BROM) sits below LK and cannot be erased. It enumerates as
`0e8d:0003` for a few seconds per power cycle; on the test unit
[`tools/mtkwatch.py`](../tools/mtkwatch.py) measured about 3.7 s:

```text
[   2.86s] appeared 0e8d:0003  BROM (boot ROM)
[   6.62s] gone     0e8d:0003
```

[mtkclient](https://github.com/bkerler/mtkclient) talks to BROM, loads a
download agent and can then read and write partitions by name. It reads the GPT
from the phone, so no scatter file is needed.

## Steps that worked

Set up mtkclient on Windows first, including the WinUSB presets for
`0e8d:0003` and `0e8d:2000` and the no-UsbDk patch: [windows.md](windows.md#mtkclient-without-usbdk).

1. Get a matching `dtbo.img` and a bootable `boot.img`. The ones inside
   `lineage-20.0-20231119-UNOFFICIAL-breeze.zip` were used. That `dtbo.img` is
   identical to stock V2.0 (md5 `f3c77ac432c50726c546b7c306007bcd`).

2. Check the connection. Unplug the phone, then:

   ```powershell
   $env:MTK_NO_USBDK = "1"
   $env:MTK_LIBUSB_DLL = "C:\path\to\libusb-1.0.dll"
   python mtk.py printgpt
   ```

   It waits with `Waiting for PreLoader VCOM`. Hold **Volume Up + Volume Down**,
   plug the cable in and keep holding for about 10 s. On success it prints
   `DA Extensions successfully added` and the partition table.

3. Write `dtbo`, reconnecting the same way when it waits:

   ```powershell
   python mtk.py w dtbo dtbo.img
   ```

   ```text
   Wrote dtbo.img to sector 888832 with sector count 16384.
   ```

4. Write `boot` the same way. Several `Handshake failed, retrying...` lines
   showed up before it connected and completed:

   ```powershell
   python mtk.py w boot boot.img
   ```

   ```text
   Wrote boot.img to sector 806912 with sector count 65536.
   ```

   The sector numbers are the GPT offsets divided by 512 (`dtbo` at
   `0x1b200000`, `boot` at `0x18a00000`).

5. Hold power for 15 s to switch off, then power on. The test unit went to TWRP:
   LineageOS's `boot.img` carries `androidboot.init_fatal_reboot_target=recovery`,
   and init could not run the EvolutionX system still on `system`.

6. Reinstall a ROM from TWRP.

The preloader, `lk` and `seccfg` were never written during recovery. Only
`dtbo` and `boot` were.
