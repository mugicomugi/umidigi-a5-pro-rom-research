# mtkclient-allow-winusb.patch

Lets [mtkclient](https://github.com/bkerler/mtkclient) talk to the phone through
the in-box Windows WinUSB driver instead of requiring UsbDk.

- Base commit: `cd25cf9c1ff6d36e82697ac2c798e69e9cfb78c3` (mtkclient V2.1.4)
- Touches only `mtkclient/Library/Connection/usblib.py`

## Why

On Windows, mtkclient calls `libusb_set_option(ctx, 1)`. Option 1 is
`LIBUSB_OPTION_USE_USBDK`, so libusb is forced onto the UsbDk backend. With
UsbDk not installed, or installed but not working, every enumeration then fails
with `usb.core.USBError: [Errno None] Other error`, before the phone is even
plugged in.

The patch adds two environment variables:

| Variable | Effect |
|---|---|
| `MTK_NO_USBDK=1` | skip the `libusb_set_option(ctx, 1)` call |
| `MTK_LIBUSB_DLL=<path>` | load this `libusb-1.0.dll` instead of searching for one |

## Use

```bash
git clone https://github.com/bkerler/mtkclient
cd mtkclient
git checkout cd25cf9c1ff6d36e82697ac2c798e69e9cfb78c3
git apply ../patches/mtkclient-allow-winusb.patch

export MTK_NO_USBDK=1
export MTK_LIBUSB_DLL='C:\path\to\libusb-1.0.dll'
python mtk.py printgpt
```

The device also needs WinUSB bound for BROM/preloader mode; see
[`../zadig/`](../zadig/) and [`../docs/windows.md`](../docs/windows.md).

## License

mtkclient is GPL-3.0, so this patch is distributed under GPL-3.0 as well. The
rest of this repository is MIT.
