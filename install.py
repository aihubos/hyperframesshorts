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


def setup_runtime(runtime, reuse_existing=False):
    for tool in ('node', 'ffmpeg', 'ffprobe'):
        if not shutil.which(tool):
            raise RuntimeError(f'{tool} is missing. Install prerequisites using README.md, then rerun.')
    version = subprocess.check_output(['node', '--version'], text=True).strip()
    if int(version.lstrip('v').split('.')[0]) < 22:
        raise RuntimeError('Node.js 22 or newer is required; see README.md.')
    cli = existing_engine(runtime) if reuse_existing else None
    cli = cli or runtime / 'node_modules/hyperframes/bin/hyperframes.mjs'
    if not cli.exists():
        runtime.mkdir(parents=True, exist_ok=True)
        npm = [shutil.which('npm')]
        if not npm[0]:
            raise RuntimeError('npm is missing. Install Node.js with npm, then rerun.')
        if os.name == 'nt':
            npm_cli = Path(npm[0]).parent / 'node_modules/npm/bin/npm-cli.js'
            if not npm_cli.is_file():
                raise RuntimeError('Cannot find npm-cli.js. Install the official Node.js distribution, then rerun.')
            npm = ['node', str(npm_cli)]
        subprocess.run(npm + ['install', '--prefix', str(runtime), '--save-exact', f'hyperframes@{VERSION}'], check=True)
    else:
        print(f'Reusing existing engine: {cli}')
    subprocess.run(['node', str(cli), '--version'], check=True)
    subprocess.run(['node', str(cli), 'browser', 'ensure'], check=True)
    print(f'Engine ready: {cli}')


def select_skills_dir(selected):
    if selected is None:
        default = Path(os.environ.get('CODEX_HOME') or str(Path.home() / '.codex')) / 'skills'
        if not sys.stdin.isatty():
            raise RuntimeError('먼저 사용자에게 스킬 설치 폴더를 확인한 뒤 --skills-dir "폴더 경로"로 실행하세요.')
        print('스킬을 설치할 상위 폴더를 지정하세요. 그 안에 hyperframesshorts 폴더를 만듭니다.')
        print('사용자 지정 폴더는 에이전트의 스킬 검색 경로에 등록되어 있어야 합니다.')
        selected = Path(input(f'설치 폴더 [Enter: {default}]: ').strip() or default)
    selected = selected.expanduser().absolute()
    target = selected / SKILL_NAME
    if selected.exists() and not selected.is_dir():
        raise RuntimeError(f'폴더가 아닌 경로입니다: {selected}')
    source = SOURCE.resolve()
    destination = target.resolve()
    if destination == source or source in destination.parents or destination in source.parents:
        raise RuntimeError('원본 저장소와 겹치지 않는 설치 폴더를 선택하세요.')
    print(f'스킬 설치 위치: {target}', flush=True)
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skills-dir', type=Path, help='Install into this skill parent directory (default: Codex only).')
    parser.add_argument('--runtime-dir', type=Path, default=Path.home() / '.local/share/hyperframes/runtime')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--setup', action='store_true', help='Unified macOS/Windows setup: engine, skill, VoiceStudio, VoxCPM2 and shared voice.')
    mode.add_argument('--setup-runtime', action='store_true', help='Optionally prepare a separate engine when no existing engine is available.')
    mode.add_argument('--skip-runtime', action='store_true', help='Explicit skill-only installation; this is already the default.')
    parser.add_argument('--setup-voice', action='store_true', help='Prepare VoiceStudio and VoxCPM2 after installing the skill.')
    args = parser.parse_args()
    skills_dir = select_skills_dir(args.skills_dir)
    if args.setup or args.setup_runtime:
        print('[1/3] Prepare Hyperframes (reuse existing engine when --setup is selected).', flush=True)
        setup_runtime(args.runtime_dir.expanduser().absolute(), reuse_existing=args.setup)
    if args.setup:
        print('[2/3] Install skill; preserve previous files.', flush=True)
    roots = [skills_dir]
    for root in dict.fromkeys(root.expanduser().absolute() for root in roots):
        install_skill(root / SKILL_NAME)
    if args.setup or args.setup_voice:
        print('[3/3] Prepare VoiceStudio, VoxCPM2 and voice; narration speed 1.2x.', flush=True)
        subprocess.run([sys.executable, str(SOURCE / 'scripts/setup_voice.py')], check=True)
    print('Read the installed SKILL.md to apply it now. Restart your agent app for fresh automatic discovery.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, EOFError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'Installation stopped: {exc}', file=sys.stderr)
        sys.exit(1)
