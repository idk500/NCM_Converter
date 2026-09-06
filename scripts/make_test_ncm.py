#!/usr/bin/env python3
"""Generate a synthetic .ncm test fixture.

Implements the exact inverse of ncmdump/core.py::dump (verified against the
installed ncmdump==0.1.1 source), so the fixture needs no copyrighted music.
The script is self-verifying: after writing the file it decrypts it with the
real ncmdump library and asserts a byte-for-byte round trip plus tags.

Usage: python make_test_ncm.py [--format mp3|flac] [--output PATH]
"""
import argparse
import base64
import binascii
import json
import os
import struct
import sys

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

CORE_KEY = binascii.a2b_hex('687A4852416D736F356B496E62617857')
META_KEY = binascii.a2b_hex('2331346C6A6B5F215C5D2630553C2728')
META_PREFIX = b'163 key(Don\'t modify):'


def make_placeholder_mp3(seconds: float = 1.0, sample_rate: int = 44100) -> bytes:
    """Minimal MPEG-1 Layer III stream (silence): enough structure for mutagen
    to parse headers and write ID3 tags. Not meant to sound like anything."""
    # 128 kbps, 44.1 kHz, mono: frame size = 144*128000/44100 - padding = 417 bytes
    frame_len = 417
    n_frames = max(1, int(sample_rate / 1152 * seconds))
    header = bytes([0xFF, 0xFB, 0x90, 0x00])
    frame = header + bytes(frame_len - len(header))
    return frame * n_frames


def rc4_key_box(key: bytes) -> bytearray:
    S = bytearray(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]
    return S


def encrypt(audio: bytes, image: bytes, meta: dict, identifier: str, rc4_key: bytes) -> bytes:
    out = bytearray()
    out += b'CTENFDAM'
    out += b'\x00\x00'  # gap

    key_payload = pad(b'neteasecloudmusic' + rc4_key, 16)
    key_stored = bytes(b ^ 0x64 for b in AES.new(CORE_KEY, AES.MODE_ECB).encrypt(key_payload))
    out += struct.pack('<I', len(key_stored)) + key_stored

    meta_payload = pad(b'music:' + json.dumps(meta).encode('utf-8'), 16)
    meta_b64 = base64.b64encode(AES.new(META_KEY, AES.MODE_ECB).encrypt(meta_payload))
    meta_stored = bytes(b ^ 0x63 for b in META_PREFIX + meta_b64)
    out += struct.pack('<I', len(meta_stored)) + meta_stored

    # NOTE: ncmdump 0.1.1 (the ground truth) reads only a 5-byte gap here —
    # no crc32 field, unlike some NCM format docs circulating online.
    out += b'\x00' * 5
    out += struct.pack('<I', len(image)) + struct.pack('<I', len(image)) + image

    S = rc4_key_box(rc4_key)
    stream = bytes(S[(S[i] + S[(i + S[i]) & 0xFF]) & 0xFF] for i in range(256))
    stream = bytes(stream * (len(audio) // 256 + 1))[1:1 + len(audio)]
    out += bytes(a ^ b for a, b in zip(audio, stream))
    return bytes(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--format', choices=['mp3', 'flac'], default='mp3')
    parser.add_argument('--output', default=None)
    parser.add_argument('--cover', default=None, help='png/jpeg file to embed as album art')
    args = parser.parse_args()

    if args.format == 'flac':
        print('flac fixture needs a real FLAC stream; use --format mp3 (default)', file=sys.stderr)
        return 1

    rc4_key = binascii.a2b_hex('3D5A61B724EDC6D34A82BF7C6D4B9F10')  # fixed for reproducibility
    meta = {
        'musicName': 'Test Song',
        'album': 'Test Album',
        'artist': [['Test Artist', 0]],
        'format': args.format,
    }
    audio = make_placeholder_mp3()
    image = open(args.cover, 'rb').read() if args.cover else b''
    blob = encrypt(audio, image, meta, META_PREFIX.decode() + 'fixtures', rc4_key)

    out_path = args.output or os.path.join(os.path.dirname(__file__), 'fixture_test.ncm')
    with open(out_path, 'wb') as f:
        f.write(blob)

    # Self-verification: round trip through the real ncmdump library.
    # Run this script with the repo venv: .venv/bin/python scripts/make_test_ncm.py
    import tempfile
    import ncmdump

    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, 'fixture_test.ncm')
        with open(src, 'wb') as f:
            f.write(blob)
        got_path = ncmdump.dump(src, skip=False)
        assert got_path and got_path.endswith('.mp3'), got_path
        got = open(got_path, 'rb').read()
        # dump() writes ID3v2 tags onto the output; strip the tag before
        # comparing the raw audio stream.
        offset = 0
        if got[:3] == b'ID3':
            size = ((got[6] << 21) | (got[7] << 14) | (got[8] << 7) | got[9])
            offset = 10 + size
        assert got[offset:] == audio, \
            f'audio mismatch: {len(got) - offset} vs {len(audio)} bytes'

        from mutagen.mp3 import MP3
        m = MP3(got_path)
        assert m['TIT2'].text[0] == 'Test Song', m['TIT2']
        assert m['TALB'].text[0] == 'Test Album'
        assert m['TPE1'].text[0] == 'Test Artist'
        if image:
            assert m.tags.getall('APIC'), 'cover missing'
    print(f'OK {out_path} ({len(blob)} bytes, round trip verified)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
