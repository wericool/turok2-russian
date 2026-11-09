# -*- coding: utf-8 -*-
"""Переназначение cmap TrueType-шрифта под «кодировку Siberian».

Движок Turok 2 (KEX 3.0) переводит строки в CP-1252 перед отрисовкой. Русификатор
хранит кириллицу как байты cp1251, которые движок читает как CP-1252
(0xC0 -> 'À' и т.д.). Чтобы TTF-шрифт рисовал русские буквы, символы CP-1252
U+00C0..U+00FF (и прочие из диапазона 0x80..0xFF) должны указывать на глифы
соответствующей кириллицы, которые в шрифте уже есть.

Поддерживается шрифт, у которого все подтаблицы cmap ссылаются на одну таблицу формата 4.
"""
import struct


def _tables(d):
    n = struct.unpack('>H', d[4:6])[0]
    t = {}
    for i in range(n):
        tag, cs, off, ln = struct.unpack('>4sIII', d[12 + 16 * i:28 + 16 * i])
        t[tag] = (i, off, ln)
    return t


def _read_fmt4(d, s):
    seg = struct.unpack('>H', d[s + 6:s + 8])[0] // 2
    p = s + 14
    ends = struct.unpack(f'>{seg}H', d[p:p + 2 * seg]); p += 2 * seg + 2
    starts = struct.unpack(f'>{seg}H', d[p:p + 2 * seg]); p += 2 * seg
    deltas = struct.unpack(f'>{seg}h', d[p:p + 2 * seg]); p += 2 * seg
    ro_pos = p
    roffs = struct.unpack(f'>{seg}H', d[p:p + 2 * seg])
    m = {}
    for i in range(seg):
        for c in range(starts[i], ends[i] + 1):
            if c == 0xFFFF:
                continue
            if roffs[i] == 0:
                g = (c + deltas[i]) & 0xFFFF
            else:
                a = ro_pos + 2 * i + roffs[i] + 2 * (c - starts[i])
                g = struct.unpack('>H', d[a:a + 2])[0]
                if g:
                    g = (g + deltas[i]) & 0xFFFF
            if g:
                m[c] = g
    return m


def _build_fmt4(m):
    cps = sorted(c for c in m if c < 0xFFFF)
    segs = []  # (start, end, delta)
    for c in cps:
        dl = (m[c] - c) & 0xFFFF
        if segs and segs[-1][1] == c - 1 and segs[-1][2] == dl:
            segs[-1][1] = c
        else:
            segs.append([c, c, dl])
    segs.append([0xFFFF, 0xFFFF, 1])
    n = len(segs)
    sr = 2 * (1 << (n.bit_length() - 1)); es = (n.bit_length() - 1); rs = 2 * n - sr
    body = struct.pack('>HHHH', 2 * n, sr, es, rs)
    body += struct.pack(f'>{n}H', *[s[1] for s in segs]) + b'\0\0'
    body += struct.pack(f'>{n}H', *[s[0] for s in segs])
    body += struct.pack(f'>{n}H', *[s[2] for s in segs])
    body += struct.pack(f'>{n}H', *([0] * n))
    length = 6 + len(body)
    assert length < 65536, 'cmap format 4 too big'
    return struct.pack('>HHH', 4, length, 0) + body


def _checksum(b):
    b = b + b'\0' * (-len(b) % 4)
    return sum(struct.unpack(f'>{len(b) // 4}I', b)) & 0xFFFFFFFF


def remap(d):
    t = _tables(d)
    idx, o, ln = t[b'cmap']
    nt = struct.unpack('>H', d[o + 2:o + 4])[0]
    subs = [struct.unpack('>HHI', d[o + 4 + 8 * i:o + 12 + 8 * i]) for i in range(nt)]
    fmt4 = [x for x in subs if struct.unpack('>H', d[o + x[2]:o + x[2] + 2])[0] == 4]
    assert fmt4, 'no format 4 cmap subtable'
    m = _read_fmt4(d, o + fmt4[0][2])
    # новая cmap: только Unicode-подтаблицы (0,3) и (3,1), обе на один формат 4
    subs = [(0, 3, 0), (3, 1, 0)]
    nt = len(subs)
    changed = 0
    for b in range(0x80, 0x100):
        try:
            u1 = bytes([b]).decode('cp1252')
        except UnicodeDecodeError:
            u1 = chr(b)
        u2 = bytes([b]).decode('cp1251', errors='ignore')
        if not u2 or u1 == u2 or ord(u2) not in m:
            continue
        m[ord(u1)] = m[ord(u2)]
        changed += 1
    sub = _build_fmt4(m)
    hdr = struct.pack('>HH', 0, nt)
    off0 = 4 + 8 * nt
    for pid, eid, _ in subs:
        hdr += struct.pack('>HHI', pid, eid, off0)
    cmap = hdr + sub
    out = bytearray(d) + b'\0' * (-len(d) % 4)
    new_off = len(out)
    out += cmap + b'\0' * (-len(cmap) % 4)
    struct.pack_into('>4sIII', out, 12 + 16 * idx, b'cmap', _checksum(cmap), new_off, len(cmap))
    return bytes(out), changed


if __name__ == '__main__':
    import sys
    src, dst = sys.argv[1], sys.argv[2]
    data, n = remap(open(src, 'rb').read())
    open(dst, 'wb').write(data)
    print('remapped', n, 'codes ->', dst)
