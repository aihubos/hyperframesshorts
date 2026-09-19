"""Check that replacing a skill preserves both directories and linked source files."""
import importlib.util
from pathlib import Path
import tempfile
import subprocess
import sys
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('installer', Path(__file__).with_name('install.py'))
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)
with tempfile.TemporaryDirectory() as scratch:
    root = Path(scratch)
    target = root / 'skills/hyperframesshorts'
    target.mkdir(parents=True)
    (target / 'existing.txt').write_text('keep this work')
    with patch.object(Path, 'home', return_value=root):
        installer.install_skill(target)
        assert (target / 'SKILL.md').is_file()
        backups = root / '.local/share/hyperframesshorts/backups'
        assert any(p.read_text() == 'keep this work' for p in backups.glob('*/hyperframesshorts/existing.txt'))
        linked_source = root / 'linked-source'
        linked_source.mkdir()
        (linked_source / 'existing.txt').write_text('linked work')
        link = root / 'linked-skills/hyperframesshorts'
        link.parent.mkdir()
        link.symlink_to(linked_source, target_is_directory=True)
        installer.install_skill(link)
        assert not link.is_symlink() and (link / 'SKILL.md').is_file()
        assert (linked_source / 'existing.txt').read_text() == 'linked work'
        assert any(p.is_symlink() for p in backups.glob('*/hyperframesshorts'))
print('PASS: existing directories and symlink sources remain recoverable.')

with tempfile.TemporaryDirectory() as scratch:
    root = Path(scratch)
    parent = root / 'skills'
    existing = parent / 'hyperframes'
    existing.mkdir(parents=True)
    (existing / 'keep.txt').write_text('existing engine skill')
    subprocess.run([sys.executable, str(Path(__file__).with_name('install.py')), '--skills-dir', str(parent), '--runtime-dir', str(root / 'runtime')], check=True)
    assert (parent / 'hyperframesshorts/SKILL.md').is_file()
    assert (existing / 'keep.txt').read_text() == 'existing engine skill'
    assert not (root / 'runtime').exists()
print('PASS: CLI installs shorts skill without changing existing hyperframes or installing an engine.')

# A unified setup must reuse a working project engine without invoking npm.
with tempfile.TemporaryDirectory() as scratch:
    root = Path(scratch)
    cli = root / 'existing/node_modules/hyperframes/bin/hyperframes.mjs'
    cli.parent.mkdir(parents=True)
    cli.write_text('// existing engine')
    with patch.object(installer, 'existing_engine', return_value=cli), patch.object(installer.shutil, 'which', side_effect=lambda name: '/tools/' + name), patch.object(installer.subprocess, 'check_output', return_value='v22.0.0'), patch.object(installer.subprocess, 'run') as run:
        installer.setup_runtime(root / 'unused', reuse_existing=True)
        assert not (root / 'unused').exists()
        assert [call.args[0] for call in run.call_args_list] == [['node', str(cli), '--version'], ['node', str(cli), 'browser', 'ensure']]
    with patch.object(sys, 'argv', ['install.py', '--setup', '--skills-dir', str(root/'skills')]), patch.object(installer, 'setup_runtime') as engine, patch.object(installer, 'install_skill') as skill, patch.object(installer.subprocess, 'run') as voice:
        installer.main()
        assert engine.call_args.kwargs['reuse_existing'] is True
        skill.assert_called_once()
        assert voice.call_args.args[0][-1].endswith('scripts/setup_voice.py')
print('PASS: unified setup reuses the engine and invokes the shared skill/voice pipeline.')

# Folder selection happens before installation, including unattended runs.
with tempfile.TemporaryDirectory() as scratch:
    root = Path(scratch)
    with patch.object(installer.sys.stdin, 'isatty', return_value=True), patch('builtins.input', return_value=str(root / 'chosen')):
        assert installer.select_skills_dir(None) == root / 'chosen'
    with patch.object(installer.sys.stdin, 'isatty', return_value=True), patch('builtins.input', return_value=''), patch.dict(installer.os.environ, {'CODEX_HOME': str(root)}):
        assert installer.select_skills_dir(None) == root / 'skills'
    with patch.object(installer.sys.stdin, 'isatty', return_value=False):
        try:
            installer.select_skills_dir(None)
        except RuntimeError:
            pass
        else:
            raise AssertionError('Unattended installation must require a selected folder')
    try:
        installer.select_skills_dir(installer.SOURCE.parent)
    except RuntimeError:
        pass
    else:
        raise AssertionError('Source folder must not be replaced')
print('PASS: folder selection, default, unattended requirement and source preservation.')
