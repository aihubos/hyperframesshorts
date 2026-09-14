#!/usr/bin/env python3
"""Install this workflow without deleting an existing skill or changing other projects."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

SOURCE = Path(__file__).resolve().parent
VERSION = '0.8.35'
SKILL_NAME = 'hyperframesshorts'


def install_skill(target):
    target = target.expanduser().absolute()
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f'.{SKILL_NAME}-', dir=target.parent))
    backup = None
    try:
        for name in ('SKILL.md', 'agents', 'references', 'LICENSE'):
            src = SOURCE / name
            if src.is_dir():
                shutil.copytree(src, stage / name)
            else:
                shutil.copy2(src, stage / name)
        if target.exists() or target.is_symlink():
            backup_root = Path.home() / '.local/share' / SKILL_NAME / 'backups'
            backup_root.mkdir(parents=True, exist_ok=True)
            backup = Path(tempfile.mkdtemp(prefix=datetime.now().strftime('%Y%m%d-%H%M%S-'), dir=backup_root))
            (backup / 'restore.json').write_text(json.dumps({'original': str(target), 'symlink': os.readlink(target) if target.is_symlink() else None}, indent=2))
            target.rename(backup / SKILL_NAME)
        try:
            stage.rename(target)
        except OSError:
            if backup:
                (backup / SKILL_NAME).rename(target)
            raise
        print(f'Installed: {target}')
        if backup:
            print(f'Previous skill preserved: {backup}')
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def setup_runtime(runtime):
    for tool in ('node', 'npm', 'ffmpeg', 'ffprobe'):
        if not shutil.which(tool):
            raise RuntimeError(f'{tool} is missing. Install prerequisites using README.md, then rerun.')
    version = subprocess.check_output(['node', '--version'], text=True).strip()
    if int(version.lstrip('v').split('.')[0]) < 22:
        raise RuntimeError('Node.js 22 or newer is required; see README.md.')
    runtime.mkdir(parents=True, exist_ok=True)
    cli = runtime / 'node_modules/.bin/hyperframes'
    if not cli.exists():
        subprocess.run(['npm', 'install', '--prefix', str(runtime), '--save-exact', f'hyperframes@{VERSION}'], check=True)
    else:
        print(f'Reusing existing runtime: {runtime}')
    subprocess.run([str(cli), '--version'], check=True)
    subprocess.run([str(cli), 'browser', 'ensure'], check=True)
    print(f'Engine ready: {cli}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skills-dir', type=Path, help='Install into this skill parent directory (default: Codex only).')
    parser.add_argument('--runtime-dir', type=Path, default=Path.home() / '.local/share/hyperframes/runtime')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--setup-runtime', action='store_true', help='Optionally prepare a separate engine when no existing engine is available.')
    mode.add_argument('--skip-runtime', action='store_true', help='Explicit skill-only installation; this is already the default.')
    args = parser.parse_args()
    if args.setup_runtime:
        setup_runtime(args.runtime_dir.expanduser().absolute())
    roots = [args.skills_dir] if args.skills_dir else [Path(os.environ.get('CODEX_HOME') or str(Path.home() / '.codex')) / 'skills']
    for root in dict.fromkeys(root.expanduser().absolute() for root in roots):
        install_skill(root / SKILL_NAME)
    print('Read the installed SKILL.md to apply it now. Restart your agent app for fresh automatic discovery.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'Installation stopped: {exc}', file=sys.stderr)
        sys.exit(1)
