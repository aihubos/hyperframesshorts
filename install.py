#!/usr/bin/env python3
"""Install this workflow without deleting an existing skill or changing other projects."""
import argparse
import json
import os
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from scripts.setup_voice import PROVIDERS, select_provider

SOURCE = Path(__file__).resolve().parent
VERSION = '0.8.35'
SKILL_NAME = 'hyperframesshorts'


def install_skill(target):
    target = target.expanduser().absolute()
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f'.{SKILL_NAME}-', dir=target.parent))
    backup = None
    try:
        for name in ('SKILL.md', 'agents', 'references', 'scripts', 'assets', 'LICENSE'):
            src = SOURCE / name
            if src.is_dir():
                shutil.copytree(src, stage / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
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


def existing_engine(runtime):
    # Search only the selected runtime and current/source ancestors, not the whole disk.
    roots = [runtime, Path.cwd(), *Path.cwd().parents, SOURCE, *SOURCE.parents]
    for root in dict.fromkeys(roots):
        cli = root / 'node_modules/hyperframes/bin/hyperframes.mjs'
        if cli.is_file():
            return cli
    installed = shutil.which('hyperframes')
    if installed:
        path = Path(installed)
        if path.suffix.lower() == '.cmd':
            path = path.parent / 'node_modules/hyperframes/bin/hyperframes.mjs'
        else:
            path = path.resolve()
        if path.is_file() and path.suffix == '.mjs':
            return path
    return None


def require_linux_cloud():
    if platform.system() != 'Linux':
        raise RuntimeError('이 설치는 원격 Linux 클라우드 컴퓨터에서 실행합니다. 학생의 Mac/Windows PC에서는 실행하지 마세요.')


def setup_runtime(runtime, reuse_existing=False):
    for tool in ('node', 'ffmpeg', 'ffprobe'):
        if not shutil.which(tool):
            raise RuntimeError(f'{tool} is missing. On this Linux cloud computer install Git, Python 3, Node.js 22+, FFmpeg and ffprobe as described in README.md, then rerun.')
    version = subprocess.check_output(['node', '--version'], text=True).strip()
    if int(version.lstrip('v').split('.')[0]) < 22:
        raise RuntimeError('Node.js 22 or newer is required on this Linux cloud computer; see README.md.')
    cli = existing_engine(runtime) if reuse_existing else None
    cli = cli or runtime / 'node_modules/hyperframes/bin/hyperframes.mjs'
    if not cli.exists():
        runtime.mkdir(parents=True, exist_ok=True)
        npm = shutil.which('npm')
        if not npm:
            raise RuntimeError('npm is missing. Install Node.js 22 or newer with npm on this Linux cloud computer, then rerun.')
        subprocess.run([npm, 'install', '--prefix', str(runtime), '--save-exact', f'hyperframes@{VERSION}'], check=True)
    else:
        print(f'Reusing existing engine: {cli}')
    subprocess.run(['node', str(cli), '--version'], check=True)
    subprocess.run(['node', str(cli), 'browser', 'ensure'], check=True)
    print(f'Engine ready: {cli}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skills-dir', type=Path, help='Install into this skill parent directory (default: Codex only).')
    parser.add_argument('--runtime-dir', type=Path, default=Path.home() / '.local/share/hyperframes/runtime')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--setup', action='store_true', help='Linux cloud setup: engine, skill, and the selected ElevenLabs plan.')
    mode.add_argument('--setup-runtime', action='store_true', help='Optionally prepare a separate engine when no existing engine is available.')
    mode.add_argument('--skip-runtime', action='store_true', help='Explicit skill-only installation; this is already the default.')
    parser.add_argument('--setup-voice', action='store_true', help='Prepare the selected ElevenLabs plan after installing the skill.')
    parser.add_argument('--voice-provider', choices=PROVIDERS, help='User-selected narration: elevenlabs-free or elevenlabs-paid.')
    parser.add_argument('--elevenlabs-voice-id', help='Voice ID chosen by the user for ElevenLabs.')
    args = parser.parse_args()
    if (args.voice_provider or args.elevenlabs_voice_id) and not (args.setup or args.setup_voice):
        parser.error('음성 옵션은 --setup 또는 --setup-voice와 함께 사용하세요.')
    if args.setup or args.setup_runtime or args.setup_voice:
        require_linux_cloud()
    provider = select_provider(args.voice_provider) if args.setup or args.setup_voice else None
    if args.setup or args.setup_runtime:
        print('[1/3] Prepare Hyperframes (reuse existing engine when --setup is selected).', flush=True)
        setup_runtime(args.runtime_dir.expanduser().absolute(), reuse_existing=args.setup)
    if args.setup:
        print('[2/3] Install skill; preserve previous files.', flush=True)
    roots = [args.skills_dir] if args.skills_dir else [Path(os.environ.get('CODEX_HOME') or str(Path.home() / '.codex')) / 'skills']
    for root in dict.fromkeys(root.expanduser().absolute() for root in roots):
        install_skill(root / SKILL_NAME)
    if args.setup or args.setup_voice:
        print('[3/3] Prepare selected voice provider: ' + provider, flush=True)
        command = [sys.executable, str(SOURCE / 'scripts/setup_voice.py'), '--provider', provider]
        if args.elevenlabs_voice_id:
            command += ['--elevenlabs-voice-id', args.elevenlabs_voice_id]
        subprocess.run(command, check=True)
    print('Read the installed SKILL.md to apply it now. Restart your agent app for fresh automatic discovery.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, EOFError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'Installation stopped: {exc}', file=sys.stderr)
        sys.exit(1)
