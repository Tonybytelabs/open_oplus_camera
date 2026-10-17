#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2026 The AxionOS Project
# SPDX-License-Identifier: Apache-2.0
#
"""Apply a directory of smali patches to an APK or jar.

usage: smali_patch.py <in.apk|jar> <out.apk|jar> <patch dir>

Every <patch dir>/*.patch is a git diff over baksmali output, paths a/<dex>/... b/<dex>/...
(a/classes7/com/oplus/... edits classes7.dex). Patches apply in file name order.

Each dex a patch names is normalized first (baksmali -> smali -> baksmali --sequential-labels),
the same way the patches were made, so labels do not depend on code offsets and smali round-trip
artefacts cancel out. The patched trees are assembled again and swapped into a raw copy of the
input zip (tools/apkrepack.py); every other entry, the manifest and resources included, is copied
byte for byte. The output is unsigned: the build signs it.

Java: $JAVA, else prebuilts/jdk/jdk21/linux-x86/bin/java of the source tree, else java on PATH.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

TOOLS = os.path.dirname(os.path.realpath(__file__))
SMALI = os.path.join(TOOLS, 'smali', 'smali.jar')
BAKSMALI = os.path.join(TOOLS, 'smali', 'baksmali.jar')
APKREPACK = os.path.join(TOOLS, 'apkrepack.py')
API = '29'


def java():
    if os.environ.get('JAVA'):
        return os.environ['JAVA']
    root = os.path.realpath(os.path.join(TOOLS, '..', '..', '..', '..'))
    jdk = os.path.join(root, 'prebuilts', 'jdk', 'jdk21', 'linux-x86', 'bin', 'java')
    if os.path.exists(jdk):
        return jdk
    return shutil.which('java') or sys.exit('smali_patch: no java found (set $JAVA)')


def run(*cmd, cwd=None):
    subprocess.run(cmd, check=True, cwd=cwd)


def jar(tool, *args):
    run(java(), '-Xmx6g', '-jar', tool, *args)


def patched_dexes(patches):
    dexes = set()
    for p in patches:
        for line in open(p, encoding='utf-8', newline=''):
            m = re.match(r'^(?:---|\+\+\+) [ab]/(classes\d*)/', line)
            if m:
                dexes.add(m.group(1))
    return sorted(dexes)


def apply(src, dst, patch_dir):
    patches = sorted(
        os.path.join(patch_dir, f)
        for f in os.listdir(patch_dir)
        if f.endswith('.patch')
    )
    if not patches:
        sys.exit(f'smali_patch: no patches in {patch_dir}')
    with tempfile.TemporaryDirectory(prefix='smali_patch.') as w:
        names = set(zipfile.ZipFile(src).namelist())
        repl = []
        dexes = patched_dexes(patches)
        for d in dexes:
            entry = d + '.dex'
            if entry not in names:
                sys.exit(f'smali_patch: {src} has no {entry}')
            raw, rt = os.path.join(w, 'raw'), os.path.join(w, 'rt.dex')
            with zipfile.ZipFile(src) as z, open(os.path.join(w, entry), 'wb') as f:
                f.write(z.read(entry))
            jar(BAKSMALI, 'd', os.path.join(w, entry), '-o', raw)
            jar(SMALI, 'a', raw, '-a', API, '-o', rt)
            jar(BAKSMALI, 'd', '-l', rt, '-o', os.path.join(w, 'tree', d))
            shutil.rmtree(raw)
            os.remove(rt)
        for p in patches:
            print(f'smali_patch: {os.path.basename(p)}')
            run('git', 'apply', '-p1', '--whitespace=nowarn', p, cwd=os.path.join(w, 'tree'))
        for d in dexes:
            out = os.path.join(w, d + '.dex')
            jar(SMALI, 'a', os.path.join(w, 'tree', d), '-a', API, '-o', out)
            repl.append(f'{d}.dex={out}')
        tmp = os.path.join(w, 'out.zip')
        run(sys.executable, APKREPACK, src, tmp, *repl)
        shutil.move(tmp, dst)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    apply(*sys.argv[1:])
