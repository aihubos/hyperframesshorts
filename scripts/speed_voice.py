#!/usr/bin/env python3
"""Apply 1.2x once to original narration; do not pass the music mix or a sped-up file."""
import argparse
import json
from pathlib import Path
import subprocess


def duration(path):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
        'format=duration', '-of', 'default=nw=1:nk=1', str(path)], text=True))


def speed_voice(source, output):
    source, output = source.resolve(), output.resolve()
    record = output.with_suffix(output.suffix + '.json')
    if source == output or output.exists() or record.exists():
        raise ValueError('Use a new output path; the original and existing output must remain intact.')
    if source.with_suffix(source.suffix + '.json').exists():
        metadata = json.loads(source.with_suffix(source.suffix + '.json').read_text())
        if metadata.get('speed_applied'):
            raise ValueError('Input is already speed-adjusted. Select the original narration.')
    before = duration(source)
    subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', str(source), '-vn',
                    '-af', 'atempo=1.2', '-c:a', 'pcm_s16le', str(output)], check=True)
    after = duration(output)
    if abs(after - before / 1.2) > max(0.1, before * 0.01):
        raise RuntimeError('Unexpected duration; inspect output before using it.')
    record.write_text(json.dumps({'source': str(source), 'speed_applied': 1.2,
        'source_seconds': before, 'output_seconds': after}, ensure_ascii=False, indent=2))
    print(f'{output}: {before:.3f}s -> {after:.3f}s (1.2x)')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path, help='New .wav path')
    a = p.parse_args()
    if a.output.suffix.lower() != '.wav':
        p.error('Output must use .wav')
    speed_voice(a.source, a.output)
