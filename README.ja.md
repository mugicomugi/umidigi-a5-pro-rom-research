# UMIDIGI A5 Pro カスタムROM検証

[English](README.md)

UMIDIGI A5 Pro(MediaTek Helio P23 / MT6763、コードネーム `breeze` / `A5_Pro`)で
**LineageOS 20** と **EvolutionX 4.4** を動かすまでの記録、実測値、自作ツールです。
すべて2026年9月に実機1台で検証しました。

> **警告**: 書き込みを行うとデータは消え、端末が起動しなくなる可能性があります。
> ここに書いた作業はすべて使い捨ての端末で行ったものです。試す前に[安全上の注意](#安全上の注意)を読んでください。

## 主な発見

この端末向けに存在する唯一のEvolutionX(4.4、Android 10、2020年)は、LineageOS 20を
入れた後だと起動せず、**FASTBOOTモード**に落ちます。ブートローダーに拒否されたように
見えますが、そうではありません。

- EvolutionXのzipには**vendorパーティションが含まれていません**。純正Android 9の
  vendor(`ro.vndk.version=28`)を前提としていますが、LineageOS 20はvendorを自前のもの
  (`ro.vndk.version=33`)に置き換えるため、Android 10のinitが起動途中で死にます。
- 死んだinitは `androidboot.init_fatal_reboot_target` の指定先へ再起動し、AOSPでの既定値は
  `bootloader` です。LineageOSは `recovery` を指定していますがEvolutionXは指定していないので、
  同じクラッシュが一方ではfastboot、もう一方ではTWRPとして現れます。

`UMIDIGI_A5_Pro_V2.0_20210326` の純正vendorを書き戻すと、EvolutionX 4.4は起動します。
手順は [docs/evolutionx-4.4.md](docs/evolutionx-4.4.md)、文鎮化を含むここに至るまでの
試行錯誤は [docs/investigation-log.md](docs/investigation-log.md) にあります(英語)。

## 状況

| | 結果 |
|---|---|
| LineageOS 20 非公式版(20231119)+ MindTheGapps 13 | 起動、Googleアプリあり |
| EvolutionX 4.4(Android 10)+ 純正vendor | セットアップ画面とホーム画面まで起動。Wi-Fi・通話・カメラ・指紋は未検証 |
| EvolutionX 11.11 GSI(Android 16) | 未試行 |
| LineageOS 20でステータスバーの時計が見切れる問題 | 未解決 |

## 発見の一覧

1. **EvolutionX 4.4には純正vendorが必要。** LineageOS 20はこれを上書きする。
   [evolutionx-4.4](docs/evolutionx-4.4.md)
2. **「fastbootに落ちる」はinitのクラッシュである場合がある。** ブートローダーを疑う前に
   `androidboot.init_fatal_reboot_target` を確認する。
   [evolutionx-4.4](docs/evolutionx-4.4.md#why-it-drops-to-fastboot)
3. **LineageOS 20はブートローダーを実質的に変えていない。** `dtbo.img` は純正とバイト単位で
   同一、`lk.img` の差は100バイトのみ。純正の `boot.img` もramdiskを持たない。
   [device-facts](docs/device-facts.md)
4. **`dtbo` は絶対に消さない。** LKが必要とするため、画面が完全に真っ暗になる。
   mtkclientを使ったBROM経由の復旧は可能。[brom-recovery](docs/brom-recovery.md)
5. **TWRP 3.7.0(Hadenix版)はadbで約1〜2MBを超えるファイルを受け取れない。** Android起動中に
   転送すればよい(3GBが90秒)。
   [pitfalls](docs/pitfalls.md#twrp-370-cannot-receive-large-files-over-adb)
6. **MindTheGapps 13は `Could not mount /mnt/system` で失敗する。** この端末に
   `/dev/block/bootdevice` が無いためで、シンボリックリンク1つで直る。
   [pitfalls](docs/pitfalls.md#mindthegapps-could-not-mount-mntsystem-aborting)
7. **`fastboot boot` は何もせず、`fastboot reboot recovery` ではリカバリーに入れない。**
   `para` パーティションにBCBを書き込む。
   [pitfalls](docs/pitfalls.md#fastboot-cannot-boot-recovery)
8. **Windows:** fastbootにはGoogleのインターフェースGUID付きWinUSBが必要。Zadigは
   信頼されたルート証明書を黙って追加する。mtkclientはUsbDkなしで動き、UsbDkを入れた後に
   Windowsがクラッシュした。[windows](docs/windows.md)

## 端末の概要

| | |
|---|---|
| SoC | MediaTek Helio P23(MT6763)、arm64 |
| コードネーム | `breeze`(LineageOS 20、TWRP 3.7.0)、`A5_Pro`(EvolutionX 4.4) |
| パーティション | 従来型。`super` なし、A/Bなし |
| ブロックデバイス | `/dev/block/platform/bootdevice/by-name/` |
| `system` / `vendor` / `boot` | 3 GiB / 656 MiB / 32 MiB |
| miscパーティション | `para` |
| BROMのUSB ID | `0e8d:0003`(見えるのは約3.7秒) |

GPT全体、boot.imgヘッダ、vendorの比較: [docs/device-facts.md](docs/device-facts.md)

## リポジトリ構成

```text
docs/
  evolutionx-4.4.md       動作した手順と根本原因
  lineageos-20.md         LineageOS 20 + MindTheGapps の導入手順
  pitfalls.md             TWRPのadb制限、MindTheGapps修正、fastbootの癖など
  windows.md              fastbootドライバのGUID、Zadigの副作用、mtkclient、UsbDk
  brom-recovery.md        mtkclientで死んだブートローダーから復旧する
  device-facts.md         パーティション表、bootヘッダ、ファームウェア比較
  investigation-log.md    検証した仮説すべて(間違っていたものも含む)
tools/
  bootimg.py              Android boot.imgの分解・再構築(v0/v1/v2)
  dat2img.py              system.new.dat + transfer listからsystem.imgを復元
  simg2img.py             Android sparseイメージを展開
  make_bcb.py             リカバリー起動用BCBイメージを生成(`para` に書く)
  mtkwatch.py             BROM/preloaderがUSBに現れた瞬間を記録
  push_chunks.ps1         タイムアウト・再試行・再開付きの分割adb push
zadig/                    Zadigプリセット: fastboot(GUID付き)、BROM、preloader
patches/                  mtkclientをUsbDkなしで動かすパッチ
```

PythonツールはPython 3が必要です(3.13で確認)。`mtkwatch.py` は `pyusb` と
`libusb-1.0.dll` も必要です。各スクリプトは引数なしで実行すると使い方を表示します。
ドキュメント本文は英語です。

## 安全上の注意

- **大事なデータはバックアップする。** アンロックや書き込みでデータは消えます。
- **仮説を試すためにパーティションを消去しない。** `fastboot erase dtbo` でブートローダーが
  動かなくなりました。既知のイメージで上書きし、そのコピーをPCに残してください。
- **端末内にロールバック手段を置いておく。** 動作するROMのzipを `/sdcard` に置き、内部ストレージを
  残す `twrp wipe data` を使います。
- **WindowsにはできればUsbDkを入れない。** [windows.md](docs/windows.md#usbdk-crashed-windows) を参照。
- **Zadigは証明書を追加する。** `LocalMachine\Root` と `TrustedPublisher` に入るので、
  作業が終わったら削除してください([windows.md](docs/windows.md#zadig-side-effect-trusted-root-certificates))。
- ROMのzip、ファームウェア、GAppsはこのリポジトリに**含めていません。** リンク先から入手し、
  ドキュメントに記載したチェックサムで確認してください。

## クレジット

- EvolutionX: Team Evolution X。A5_Pro向け4.4ビルドは jmpf_bmx 氏が
  [XDA](https://xdaforums.com/t/rom-evolution-x-4-4-for-the-umidigi-a5-pro-a5_pro-unnofficial.4121941/)で公開。
- `breeze` 向け LineageOS 20 非公式版と TWRP 3.7.0: hadenix 氏と
  [umidigi-mt6763-dev](https://github.com/umidigi-mt6763-dev)
- [MindTheGapps](https://github.com/MindTheGapps)
- [mtkclient](https://github.com/bkerler/mtkclient)(B. Kerler 氏)
- [Zadig / libwdi](https://github.com/pbatard/libwdi)(Pete Batard 氏)
- 純正ファームウェア: UMIDIGI

## ライセンス

ドキュメントとツールはMIT([LICENSE](LICENSE))。[`patches/`](patches/) はmtkclientを
改変するものなのでGPL-3.0です。
