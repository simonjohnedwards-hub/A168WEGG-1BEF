#!/usr/bin/env python3
"""Generate a tiny 5x7 bitmap font for Garmin watch face. No dependencies required."""
import struct, zlib, os

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "fonts")
PNG_PATH = os.path.join(FONT_DIR, "TinyFont_0.png")
FNT_PATH = os.path.join(FONT_DIR, "TinyFont.fnt")

CHAR_HEIGHT = 7
LINE_HEIGHT = 7
BASE = 7
SCALE = 2  # Each pixel becomes a 2x2 block

# 5x7 pixel font glyphs (standard LED/LCD style)
# Key = Unicode code point, Value = list of 7 binary strings ('1'=pixel on)
GLYPHS = {
    32: ['000', '000', '000', '000', '000', '000', '000'],  # space
    37: ['11001', '11010', '00100', '01000', '10100', '01011', '00011'],  # %
    45: ['00000', '00000', '00000', '11111', '00000', '00000', '00000'],  # -
    46: ['00', '00', '00', '00', '00', '00', '01'],  # .
    48: ['01110', '10001', '10011', '10101', '11001', '10001', '01110'],  # 0
    49: ['00100', '01100', '00100', '00100', '00100', '00100', '01110'],  # 1
    50: ['01110', '10001', '00001', '00110', '01000', '10000', '11111'],  # 2
    51: ['01110', '10001', '00001', '00110', '00001', '10001', '01110'],  # 3
    52: ['00010', '00110', '01010', '10010', '11111', '00010', '00010'],  # 4
    53: ['11111', '10000', '11110', '00001', '00001', '10001', '01110'],  # 5
    54: ['00110', '01000', '10000', '11110', '10001', '10001', '01110'],  # 6
    55: ['11111', '00001', '00010', '00100', '01000', '01000', '01000'],  # 7
    56: ['01110', '10001', '10001', '01110', '10001', '10001', '01110'],  # 8
    57: ['01110', '10001', '10001', '01111', '00001', '00010', '01100'],  # 9
    58: ['0', '1', '0', '0', '0', '1', '0'],  # :
    65: ['01110', '10001', '10001', '11111', '10001', '10001', '10001'],  # A
    66: ['11110', '10001', '10001', '11110', '10001', '10001', '11110'],  # B
    67: ['01110', '10001', '10000', '10000', '10000', '10001', '01110'],  # C
    68: ['11100', '10010', '10001', '10001', '10001', '10010', '11100'],  # D
    69: ['11111', '10000', '10000', '11110', '10000', '10000', '11111'],  # E
    70: ['11111', '10000', '10000', '11110', '10000', '10000', '10000'],  # F
    71: ['01110', '10001', '10000', '10111', '10001', '10001', '01110'],  # G
    72: ['10001', '10001', '10001', '11111', '10001', '10001', '10001'],  # H
    73: ['111', '010', '010', '010', '010', '010', '111'],  # I
    74: ['00111', '00010', '00010', '00010', '00010', '10010', '01100'],  # J
    75: ['10001', '10010', '10100', '11000', '10100', '10010', '10001'],  # K
    76: ['10000', '10000', '10000', '10000', '10000', '10000', '11111'],  # L
    77: ['10001', '11011', '10101', '10001', '10001', '10001', '10001'],  # M
    78: ['10001', '11001', '10101', '10011', '10001', '10001', '10001'],  # N
    79: ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],  # O
    80: ['11110', '10001', '10001', '11110', '10000', '10000', '10000'],  # P
    81: ['01110', '10001', '10001', '10001', '10101', '10010', '01101'],  # Q
    82: ['11110', '10001', '10001', '11110', '10100', '10010', '10001'],  # R
    83: ['01110', '10001', '10000', '01110', '00001', '10001', '01110'],  # S
    84: ['11111', '00100', '00100', '00100', '00100', '00100', '00100'],  # T
    85: ['10001', '10001', '10001', '10001', '10001', '10001', '01110'],  # U
    86: ['10001', '10001', '10001', '10001', '01010', '01010', '00100'],  # V
    87: ['10001', '10001', '10001', '10101', '10101', '01010', '01010'],  # W
    88: ['10001', '10001', '01010', '00100', '01010', '10001', '10001'],  # X
    89: ['10001', '10001', '01010', '00100', '00100', '00100', '00100'],  # Y
    90: ['11111', '00001', '00010', '00100', '01000', '10000', '11111'],  # Z
}

# Compute positions (scaled)
chars = sorted(GLYPHS.keys())
x_cursor = 0
char_data = []
for cid in chars:
    rows = GLYPHS[cid]
    w = len(rows[0]) * SCALE
    xadv = w + SCALE
    char_data.append((cid, x_cursor, 0, w, CHAR_HEIGHT * SCALE, 0, 0, xadv))
    x_cursor += w + SCALE

SHEET_W = x_cursor
SHEET_H = CHAR_HEIGHT * SCALE

# Build RGBA pixel buffer (all zeros = transparent black)
buf = bytearray(SHEET_W * SHEET_H * 4)
for cid, cx, cy, w, h, xoff, yoff, xadv in char_data:
    rows = GLYPHS[cid]
    for ri, row in enumerate(rows):
        for ci, bit in enumerate(row):
            if bit == '1':
                for sy in range(SCALE):
                    for sx in range(SCALE):
                        px = cx + ci * SCALE + sx
                        py = cy + ri * SCALE + sy
                        idx = (py * SHEET_W + px) * 4
                        buf[idx] = 255      # R
                        buf[idx+1] = 255    # G
                        buf[idx+2] = 255    # B
                        buf[idx+3] = 255    # A

# Write PNG (no external deps)
def png_chunk(ctype, data):
    c = ctype + data
    crc = struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
    return struct.pack('>I', len(data)) + c + crc

raw = b''
for y in range(SHEET_H):
    raw += b'\x00'  # filter byte = None
    off = y * SHEET_W * 4
    raw += bytes(buf[off:off + SHEET_W * 4])

png = b'\x89PNG\r\n\x1a\n'
png += png_chunk(b'IHDR', struct.pack('>IIBBBBB', SHEET_W, SHEET_H, 8, 6, 0, 0, 0))
png += png_chunk(b'IDAT', zlib.compress(raw))
png += png_chunk(b'IEND', b'')

with open(PNG_PATH, 'wb') as f:
    f.write(png)

# Write .fnt (BMFont text format)
with open(FNT_PATH, 'w') as f:
    f.write('info face="TinyFont" size=%d bold=0 italic=0 charset="" unicode=1 stretchH=100 smooth=0 aa=0 padding=0,0,0,0 spacing=1,1 outline=0\n' % (CHAR_HEIGHT * SCALE))
    f.write('common lineHeight=%d base=%d scaleW=%d scaleH=%d pages=1 packed=0 alphaChnl=0 redChnl=4 greenChnl=4 blueChnl=4\n' % (LINE_HEIGHT * SCALE, BASE * SCALE, SHEET_W, SHEET_H))
    f.write('page id=0 file="TinyFont_0.png"\n')
    f.write('chars count=%d\n' % len(char_data))
    for cid, x, y, w, h, xoff, yoff, xadv in char_data:
        f.write('char id=%-6d x=%-8d y=%-8d width=%-8d height=%-8d xoffset=%-8d yoffset=%-8d xadvance=%-8d page=0  chnl=15\n' % (cid, x, y, w, h, xoff, yoff, xadv))

print("Generated: %s (%dx%d)" % (PNG_PATH, SHEET_W, SHEET_H))
print("Generated: %s (%d chars)" % (FNT_PATH, len(char_data)))

# ===== Generate larger variant (30% bigger = 3x scale) =====
SCALE_LG = 3
PNG_PATH_LG = os.path.join(FONT_DIR, "TinyFontLg_0.png")
FNT_PATH_LG = os.path.join(FONT_DIR, "TinyFontLg.fnt")

x_cursor_lg = 0
char_data_lg = []
for cid in chars:
    rows = GLYPHS[cid]
    w = len(rows[0]) * SCALE_LG
    xadv = w + SCALE_LG
    char_data_lg.append((cid, x_cursor_lg, 0, w, CHAR_HEIGHT * SCALE_LG, 0, 0, xadv))
    x_cursor_lg += w + SCALE_LG

SHEET_W_LG = x_cursor_lg
SHEET_H_LG = CHAR_HEIGHT * SCALE_LG

buf_lg = bytearray(SHEET_W_LG * SHEET_H_LG * 4)
for cid, cx, cy, w, h, xoff, yoff, xadv in char_data_lg:
    rows = GLYPHS[cid]
    for ri, row in enumerate(rows):
        for ci, bit in enumerate(row):
            if bit == '1':
                for sy in range(SCALE_LG):
                    for sx in range(SCALE_LG):
                        px = cx + ci * SCALE_LG + sx
                        py = cy + ri * SCALE_LG + sy
                        idx = (py * SHEET_W_LG + px) * 4
                        buf_lg[idx] = 255
                        buf_lg[idx+1] = 255
                        buf_lg[idx+2] = 255
                        buf_lg[idx+3] = 255

raw_lg = b''
for y in range(SHEET_H_LG):
    raw_lg += b'\x00'
    off = y * SHEET_W_LG * 4
    raw_lg += bytes(buf_lg[off:off + SHEET_W_LG * 4])

png_lg = b'\x89PNG\r\n\x1a\n'
png_lg += png_chunk(b'IHDR', struct.pack('>IIBBBBB', SHEET_W_LG, SHEET_H_LG, 8, 6, 0, 0, 0))
png_lg += png_chunk(b'IDAT', zlib.compress(raw_lg))
png_lg += png_chunk(b'IEND', b'')

with open(PNG_PATH_LG, 'wb') as f:
    f.write(png_lg)

with open(FNT_PATH_LG, 'w') as f:
    f.write('info face="TinyFontLg" size=%d bold=0 italic=0 charset="" unicode=1 stretchH=100 smooth=0 aa=0 padding=0,0,0,0 spacing=1,1 outline=0\n' % (CHAR_HEIGHT * SCALE_LG))
    f.write('common lineHeight=%d base=%d scaleW=%d scaleH=%d pages=1 packed=0 alphaChnl=0 redChnl=4 greenChnl=4 blueChnl=4\n' % (LINE_HEIGHT * SCALE_LG, BASE * SCALE_LG, SHEET_W_LG, SHEET_H_LG))
    f.write('page id=0 file="TinyFontLg_0.png"\n')
    f.write('chars count=%d\n' % len(char_data_lg))
    for cid, x, y, w, h, xoff, yoff, xadv in char_data_lg:
        f.write('char id=%-6d x=%-8d y=%-8d width=%-8d height=%-8d xoffset=%-8d yoffset=%-8d xadvance=%-8d page=0  chnl=15\n' % (cid, x, y, w, h, xoff, yoff, xadv))

print("Generated: %s (%dx%d)" % (PNG_PATH_LG, SHEET_W_LG, SHEET_H_LG))
print("Generated: %s (%d chars)" % (FNT_PATH_LG, len(char_data_lg)))
