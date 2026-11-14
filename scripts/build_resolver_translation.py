"""Translate the four literal labels in the verified Play 6 chooser layout."""

import argparse
import hashlib
import struct
import zipfile
from pathlib import Path


ORIGINAL_SHA256 = '9869ccf062ded8c37e399618ad909f48317a2df079dfa88daab25ec9bbaa978a'
LAYOUT = 'res/iA.xml'
LABELS = {
    '打开方式': 'Открыть с помощью',
    '仅此一次': 'Только один раз',
    '始终': 'Всегда',
    '取消': 'Отмена',
}


def translate_layout(layout):
    xml_type, xml_header, xml_size = struct.unpack_from('<HHI', layout)
    pool_type, pool_header, pool_size, count, styles, flags, start, style_start = (
        struct.unpack_from('<HH6I', layout, xml_header)
    )
    if (xml_type, xml_header, xml_size) != (3, 8, len(layout)):
        raise ValueError('Unexpected binary XML header')
    if (pool_type, pool_header, styles, flags, start, style_start) != (
        1, 28, 0, 0x100, 28 + 4 * count, 0,
    ):
        raise ValueError('Unexpected binary XML string pool')

    offsets = struct.unpack_from(f'<{count}I', layout, xml_header + pool_header)
    strings = bytearray()
    translated_offsets = []
    remaining = set(LABELS)
    for offset in offsets:
        position = xml_header + start + offset
        utf16_length, byte_length = struct.unpack_from('BB', layout, position)
        if max(utf16_length, byte_length) >= 128 or layout[position + 2 + byte_length] != 0:
            raise ValueError('Unexpected string encoding')
        encoded = layout[position + 2:position + 2 + byte_length]
        original = encoded.decode('utf-8')
        if original in LABELS:
            remaining.remove(original)
            translated = LABELS[original]
            encoded = translated.encode('utf-8')
            utf16_length = len(translated.encode('utf-16le')) // 2
        translated_offsets.append(len(strings))
        strings.extend(bytes((utf16_length, len(encoded))) + encoded + b'\0')
    if remaining:
        raise ValueError(f'Missing labels: {remaining}')

    strings.extend(b'\0' * (-len(strings) % 4))
    new_pool_size = start + len(strings)
    return (
        struct.pack('<HHI', xml_type, xml_header, xml_size - pool_size + new_pool_size)
        + struct.pack('<HH6I', pool_type, pool_header, new_pool_size, count, styles, flags, start, 0)
        + struct.pack(f'<{count}I', *translated_offsets)
        + strings
        + layout[xml_header + pool_size:]
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if hashlib.sha256(args.original.read_bytes()).hexdigest() != ORIGINAL_SHA256:
        parser.error('Source APK differs from verified Play 6 v1.7.116')
    with zipfile.ZipFile(args.original) as source:
        translated = translate_layout(source.read(LAYOUT))
        with zipfile.ZipFile(args.output, 'x') as output:
            for entry in source.infolist():
                output.writestr(entry, translated if entry.filename == LAYOUT else source.read(entry.filename))
    with zipfile.ZipFile(args.original) as source, zipfile.ZipFile(args.output) as output:
        changed = [name for name in source.namelist() if source.read(name) != output.read(name)]
        if source.namelist() != output.namelist() or changed != [LAYOUT]:
            raise ValueError(f'Unexpected APK changes: {changed}')
    print(hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
