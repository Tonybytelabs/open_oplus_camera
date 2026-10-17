# Raw-copy an APK, replacing named entries; stored entries keep 4-byte data alignment (4096 for .so).
import sys, zipfile, struct, zlib
src, dst = sys.argv[1], sys.argv[2]
repl = dict(a.split('=', 1) for a in sys.argv[3:])
zin = zipfile.ZipFile(src); raw = open(src, 'rb'); out = open(dst, 'wb'); cd = []
for zi in zin.infolist():
    raw.seek(zi.header_offset); h = raw.read(30)
    nlen, xlen = struct.unpack('<HH', h[26:30]); name = raw.read(nlen)
    raw.seek(zi.header_offset + 30 + nlen + xlen)
    crc, csize, usize, method = zi.CRC, zi.compress_size, zi.file_size, zi.compress_type
    if zi.filename in repl:
        data = open(repl[zi.filename], 'rb').read(); crc = zlib.crc32(data); usize = len(data)
        if method == zipfile.ZIP_DEFLATED:
            c = zlib.compressobj(9, zlib.DEFLATED, -15); data = c.compress(data) + c.flush()
        csize = len(data)
    else:
        data = raw.read(csize)
    flags = zi.flag_bits & ~0x8
    off = out.tell(); pad = b''
    if method == zipfile.ZIP_STORED:
        al = 4096 if zi.filename.endswith('.so') else 4   # stored libs are mapped straight from the APK
        pad = b'\0' * ((-(off + 30 + nlen)) % al)
    out.write(struct.pack('<4sHHHHHIIIHH', b'PK\3\4', zi.extract_version, flags, method, *struct.unpack('<HH', h[10:14]),
                          crc, csize, usize, nlen, len(pad)) + name + pad + data)
    cd.append(struct.pack('<4sHHHHHHIIIHHHHHII', b'PK\1\2', zi.create_version | (zi.create_system << 8), zi.extract_version,
                          flags, method, *struct.unpack('<HH', h[10:14]), crc, csize, usize, nlen, 0, 0, 0,
                          zi.internal_attr, zi.external_attr, off) + name)
start = out.tell(); out.write(b''.join(cd))
out.write(struct.pack('<4sHHHHIIH', b'PK\5\6', 0, 0, len(cd), len(cd), out.tell() - start, start, 0))
