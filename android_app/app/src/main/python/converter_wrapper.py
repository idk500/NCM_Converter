"""Bridge between the Kotlin app and the proven ncmdump core.

The desktop exe and this Android app run the very same library code
(ncmdump 0.1.1 + pycryptodome + mutagen), so there is exactly one crypto
implementation in the whole project.
"""
import json
import os

import ncmdump


def convert(ncm_path: str, output_dir: str, base_name: str = '') -> str:
    """Convert one .ncm file into output_dir. Returns a JSON string so the
    result crosses the Kotlin boundary without dict-protocol dependencies:

        {"path": "...", "format": "mp3", "title": "...", "name": "..."}

    base_name overrides the output file stem: on Android the input arrives
    under a cache temp name, so Kotlin passes the original display name.
    """
    picked = {}

    def output_path_generator(path, meta):
        stem = base_name or os.path.splitext(os.path.basename(path))[0]
        name = stem + '.' + meta['format']
        picked.update({
            'path': os.path.join(output_dir, name),
            'format': meta.get('format', ''),
            'title': meta.get('musicName', ''),
            'name': name,
        })
        return picked['path']

    out = ncmdump.dump(ncm_path, output_path_generator, skip=False)
    if out is None:
        picked['error'] = 'no output produced'
    return json.dumps(picked, ensure_ascii=False)
