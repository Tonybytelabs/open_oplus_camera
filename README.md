# open_oplus_camera

OPLUS camera, gallery and Private Safe for AxionOS on the OnePlus 9 / 9 Pro (`lemonade`, `lemonadep`).

This repo holds no blobs. It holds the list of stock files, the patches applied to them and the
build configuration. `extract-files.py` copies the stock files out of firmware dumps, applies the
patches and writes the result to `vendor/oplus/camera-blobs`, the private
`open_oplus_camera_blobs` repo, which the build uses.

| Path | Contents |
|---|---|
| `proprietary-files.txt` | every blob, its source path in the firmware and its destination |
| `patches/` | OplusCamera 7.013.11 (`OplusCamera.apk`) |
| `patches-sdk/` | the camera unit SDK (`com.oplus.camera.unit.sdk.jar`) |
| `patches-gallery/` | com.oneplus.gallery 16.50.8 (`OppoGallery2.apk`) |
| `patches-safe/` | OPLUS Private Safe 17.3.3 (`FileEncryption.apk`) |
| `tools/smali_patch.py` | applies one of the patch directories to an APK or jar |
| `opluscamera.mk`, `configs/`, `init/`, `sepolicy/`, `OplusPermissions/` | build configuration |

## Sources

| Files | Firmware |
|---|---|
| `my_product/...` (camera app, unit jars, JNI libraries) | OPPO Find X10 Pro Max, PMX110_17.0.0.105(CN01) |
| `my_stock/...` (gallery, Private Safe) | OnePlus 15, CPH2747_16.0.10.601(EX01) |
| everything else | OxygenOS 16 port for the OnePlus 9, LE2113_16.0.10.500(EX01) |

## Use

1. Clone this repo to `vendor/oplus/camera` and `open_oplus_camera_blobs` to `vendor/oplus/camera-blobs`.
2. Inherit it from the device tree:

   ```
   $(call inherit-product-if-exists, vendor/oplus/camera/opluscamera.mk)
   ```

3. `PRODUCT_BRAND` has to be oneplus, oppo or realme, and must not be overridden by a SafetyNet hack.

## Regenerating the blobs

Lay out a dump directory that holds the source paths from `proprietary-files.txt` (`my_product/`,
`my_stock/`, `system/`, `system_ext/`, `odm/`), then run from the source tree root:

```
vendor/oplus/camera/extract-files.py --allow-prohibited-files <dump dir>
```

`--allow-prohibited-files` is needed for the SenseTime licence files in `odm/etc/camera/`. The camera's
SenseTime features need them, and LineageOS keeps them out of its own repos. That is one reason the
blob repo is private.

The run needs Java (the tree's `prebuilts/jdk/jdk21`, or `$JAVA`) and git. Commit the output in
`vendor/oplus/camera-blobs`. Blobs over 95 MB are written as 20 MiB `.partNN` files, which
`vendorsetup.sh` joins again.

## How the patches work

Each patch is a git diff over `baksmali --sequential-labels` output, with paths `a/<dex>/...`
(`a/classes7/com/oplus/...` edits `classes7.dex`). `tools/smali_patch.py`:

1. normalizes each dex a patch names (baksmali, smali, then baksmali with sequential labels), so
   labels do not depend on code offsets;
2. applies the patches in file-name order with `git apply`;
3. assembles the trees again and puts the new dex files into a raw copy of the original zip, so
   the manifest, resources and native libraries stay byte-identical.

Helper classes (`mm.DV`, the Dolby Vision muxer; `com.oplus.gallery.aosp.AospIntents`;
`com.oplus.encryption.aosp.AospLock`) are new smali files inside the patch that needs them. Their
Java sources are in `src/`, for reading; the build uses the smali.

To add a patch: decompile the current dex the same way, edit it, and export the change with
`git diff --no-index --no-prefix a/<dex> b/<dex>` into the next numbered file.

smali and baksmali 2.5.2 (`tools/smali/`) are by Ben Gruver, under the BSD 3-clause licence
(https://github.com/JesusFreke/smali).

## Credits

- Hecheng Yu ([dodge-camera-port/vendor_oplus_camera](https://github.com/dodge-camera-port/vendor_oplus_camera)):
  the layout of this repo, and the gallery `ActionReceiver` export-flag patch.
