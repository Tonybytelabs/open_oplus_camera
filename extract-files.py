#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

import os
import re
import sys
from pathlib import Path

from extract_utils.fixups_blob import (
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.fixups_lib import (
    lib_fixups,
    lib_fixups_user_type,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tools'))
import manifest_add_permission  # noqa: E402
import smali_patch  # noqa: E402


def lib_fixup_system_ext_suffix(lib: str, partition: str, *args, **kwargs):
    return f'{lib}_{partition}' if partition == 'system_ext' else None


lib_fixups: lib_fixups_user_type = {
    **lib_fixups,
    (
        'libSuperTextWrapper',
        'libXDocProcessSDK',
        'libYTCommon',
        'libextendfile',
        'libmpbase',
    ): lib_fixup_system_ext_suffix,
}


def smali_patches(patch_dir: str) -> blob_fixup:
    # The patch sets are git diffs over baksmali output, see tools/smali_patch.py.
    def impl(ctx, file, file_path, *args, **kwargs):
        smali_patch.apply(file_path, file_path, os.path.join(ctx.module_dir, patch_dir))

    return blob_fixup().call(impl, need_tmp_dir=False)


def add_permissions(*permissions: str) -> blob_fixup:
    def impl(ctx, file, file_path, *args, **kwargs):
        manifest_add_permission.apply(file_path, file_path, list(permissions))

    return blob_fixup().call(impl, need_tmp_dir=False)


blob_fixups: blob_fixups_user_type = {
    'system_ext/priv-app/OplusCamera/OplusCamera.apk': smali_patches('patches'),
    'system_ext/framework/com.oplus.camera.unit.sdk.jar': smali_patches('patches-sdk'),
    'system_ext/priv-app/OppoGallery2/OppoGallery2.apk': smali_patches('patches-gallery'),
    'system_ext/app/FileEncryption/FileEncryption.apk': smali_patches('patches-safe'),
    # The scanner opens the system-only logical camera; CameraService wants SYSTEM_CAMERA for it.
    'system_ext/priv-app/OcrScanner/OcrScanner.apk': add_permissions('android.permission.SYSTEM_CAMERA'),
}  # fmt: skip

# The blobs go to vendor/oplus/camera-blobs (the open_oplus_camera_blobs repo); this repo only
# carries the list, the patches and the configuration.
module = ExtractUtilsModule(
    'camera-blobs',
    'oplus',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    device_rel_path='vendor/oplus/camera',
)

# GitHub refuses files over 100 MB; such blobs are kept as 20 MiB .partNN files that
# vendorsetup.sh joins again in the source tree.
SPLIT_OVER = 95 * 1024 * 1024
PART_SIZE = 20 * 1024 * 1024


def split_large_blobs(root: Path):
    for f in sorted((root / 'proprietary').rglob('*')):
        if not f.is_file() or '.part' in f.name or f.stat().st_size <= SPLIT_OVER:
            continue
        with open(f, 'rb') as src:
            n = 0
            while chunk := src.read(PART_SIZE):
                f.with_name(f'{f.name}.part{n:02d}').write_bytes(chunk)
                n += 1
        f.unlink()
        print(f'split {f.relative_to(root)} into {n} parts')


if __name__ == '__main__':
    utils = ExtractUtils.device(module)
    utils.run()

    blobs = Path(module.vendor_path)

    # extract-utils turns dexpreopt off for every APK and knows nothing about
    # uses-libs. OplusCamera is compiled at build time
    # (PRODUCT_DEXPREOPT_SPEED_APPS in opluscamera.mk), which puts it through
    # Soong's manifest_check against its <uses-library> tags; the manifest
    # declares org.apache.http.legacy, com.oplus.camera.unit.sdk,
    # androidx.window.extensions and androidx.window.sidecar as optional, and
    # the SDK one is provided by a dex_import, which Soong refuses to accept in
    # optional_uses_libs, so the check is switched off for this module instead.
    bp = blobs / 'Android.bp'
    bp.write_text(
        re.sub(
            r'(name: "OplusCamera",[^}]*?)    dex_preopt: \{\n        enabled: false,\n    \},\n',
            r'\1    enforce_uses_libs: false,\n',
            bp.read_text(),
            count=1,
            flags=re.S,
        )
    )

    split_large_blobs(blobs)
