#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2026 The AxionOS Project
# SPDX-License-Identifier: Apache-2.0
#
"""Add <uses-permission> entries to an APK's binary AndroidManifest.xml.

usage: manifest_add_permission.py <in.apk> <out.apk> <permission> [permission...]

Each new element is a copy of the manifest's first single-attribute <uses-permission>, with its
android:name pointing at the permission name appended to the string pool. The copies go right after
that element. Every other zip entry is copied byte for byte (tools/apkrepack.py). The output is
unsigned: the build signs it.
"""
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile

STRING_POOL, START_EL, END_EL = 0x0001, 0x0102, 0x0103
UTF8 = 0x100
APKREPACK = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'apkrepack.py')


def read_string(d, base, off, utf8):
    p = base + off
    if utf8:
        n = d[p]; p += 1
        if n & 0x80:
            p += 1
        m = d[p]; p += 1
        if m & 0x80:
            m = ((m & 0x7f) << 8) | d[p]; p += 1
        return d[p:p + m].decode('utf-8')
    n = struct.unpack_from('<H', d, p)[0]; p += 2
    if n & 0x8000:
        n = ((n & 0x7fff) << 16) | struct.unpack_from('<H', d, p)[0]; p += 2
    return d[p:p + 2 * n].decode('utf-16-le')


def encode_string(s, utf8):
    if utf8:
        b = s.encode('utf-8')
        assert len(s) < 0x80 and len(b) < 0x80
        return bytes([len(s), len(b)]) + b + b'\0'
    assert len(s) < 0x8000
    return struct.pack('<H', len(s)) + s.encode('utf-16-le') + b'\0\0'


def add_permissions(d, perms):
    assert struct.unpack_from('<H', d, 0)[0] == 0x0003
    pool = 8
    typ, hsz, size, count, styles, flags, start, _ = struct.unpack_from('<HHIIIIII', d, pool)
    assert typ == STRING_POOL and styles == 0, 'string pool with styles is not supported'
    utf8 = bool(flags & UTF8)
    offsets = list(struct.unpack_from(f'<{count}I', d, pool + hsz))
    strings = [read_string(d, pool + start, o, utf8) for o in offsets]
    data = d[pool + start:pool + size]

    perms = [p for p in perms if p not in strings or not uses_permission(d, pool + size, strings, p)]
    if not perms:
        return d

    new_idx = []
    for p in perms:
        if p in strings:
            new_idx.append(strings.index(p))
            continue
        offsets.append(len(data))
        data += encode_string(p, utf8)
        new_idx.append(len(strings))
        strings.append(p)
    data += b'\0' * (-len(data) % 4)
    hdr = struct.pack('<HHIIIIII', STRING_POOL, hsz, hsz + 4 * len(offsets) + len(data),
                      len(offsets), 0, flags, hsz + 4 * len(offsets), 0)
    new_pool = hdr + d[pool + 28:pool + hsz] + struct.pack(f'<{len(offsets)}I', *offsets) + data

    body = bytearray(d[pool + size:])
    pos, template = 0, None
    while pos < len(body):
        ctype, _, csize = struct.unpack_from('<HHI', body, pos)
        if ctype == START_EL:
            name = struct.unpack_from('<I', body, pos + 20)[0]
            attrs = struct.unpack_from('<H', body, pos + 28)[0]
            end = pos + csize
            if strings[name] == 'uses-permission' and attrs == 1 \
                    and struct.unpack_from('<H', body, end)[0] == END_EL:
                template = (pos, end + struct.unpack_from('<I', body, end + 4)[0])
                break
        pos += csize
    if template is None:
        sys.exit('manifest_add_permission: no single-attribute <uses-permission> to copy')

    start_el, end_el = template
    insert = b''
    for i in new_idx:
        el = bytearray(body[start_el:end_el])
        attr = 36  # 16-byte chunk header + 20-byte element header
        struct.pack_into('<I', el, attr + 8, i)    # raw value
        struct.pack_into('<I', el, attr + 16, i)   # typed value (TYPE_STRING)
        assert el[attr + 15] == 0x03
        insert += el
    body[end_el:end_el] = insert

    out = bytearray(struct.pack('<HHI', 0x0003, 8, 8 + len(new_pool) + len(body)))
    return bytes(out + new_pool + body)


def uses_permission(d, body_start, strings, perm):
    pos = body_start
    while pos < len(d):
        ctype, _, csize = struct.unpack_from('<HHI', d, pos)
        if ctype == START_EL and struct.unpack_from('<H', d, pos + 28)[0] >= 1 \
                and strings[struct.unpack_from('<I', d, pos + 20)[0]] == 'uses-permission':
            value = struct.unpack_from('<I', d, pos + 36 + 8)[0]
            if value < len(strings) and strings[value] == perm:
                return True
        pos += csize
    return False


def apply(src, dst, perms):
    manifest = zipfile.ZipFile(src).read('AndroidManifest.xml')
    new = add_permissions(manifest, perms)
    with tempfile.TemporaryDirectory(prefix='manifest_add_permission.') as w:
        m = os.path.join(w, 'AndroidManifest.xml')
        open(m, 'wb').write(new)
        tmp = os.path.join(w, 'out.zip')
        subprocess.run([sys.executable, APKREPACK, src, tmp, f'AndroidManifest.xml={m}'], check=True)
        shutil.move(tmp, dst)


if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    apply(sys.argv[1], sys.argv[2], sys.argv[3:])
