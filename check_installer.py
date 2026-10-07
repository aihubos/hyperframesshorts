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
    with patch.object(sys, 'argv', ['install.py', '--setup', '--voice-provider', 'local', '--skills-dir', str(root/'skills')]), patch.object(installer, 'setup_runtime') as engine, patch.object(installer, 'install_skill') as skill, patch.object(installer.subprocess, 'run') as voice:
        installer.main()
        assert engine.call_args.kwargs['reuse_existing'] is True
        skill.assert_called_once()
        assert voice.call_args.args[0][-3].endswith('scripts/setup_voice.py')
        assert voice.call_args.args[0][-2:] == ['--provider', 'local']
print('PASS: unified setup reuses the engine and invokes the shared skill/voice pipeline.')

# Optional audio must never download on skip, insufficient resources, or a later resource drop.
audio = installer.select_audio.__module__
import importlib
sound = importlib.import_module(audio)
ready = {'supported': True, 'ram': 32, 'ram_required': 24, 'disk': 30, 'disk_required': 25}
with patch.object(sound.sys.stdin, 'isatty', return_value=False), patch.object(sound, 'resources') as scan:
    assert sound.select_audio() == 'none'
    assert sound.select_audio('none') == 'none'
    scan.assert_not_called()
with patch.object(sound, 'resources', return_value=ready), patch.object(sound.sys.stdin, 'isatty', return_value=True), patch('builtins.input', return_value='2'):
    assert sound.select_audio() == 'agent-audio'
for low in ({**ready, 'disk': 24}, {**ready, 'ram': 16}, {**ready, 'ram': None}, {**ready, 'supported': False}):
    with patch.object(sound, 'resources', return_value=low), patch.object(sound.subprocess, 'run') as run:
        try:
            sound.select_audio('agent-audio')
            raise AssertionError('resource gate was bypassed')
        except RuntimeError:
            pass
        try:
            sound.setup_audio()
            raise AssertionError('resource recheck was bypassed')
        except RuntimeError:
            pass
        run.assert_not_called()
with patch.object(sys, 'argv', ['install.py', '--setup-audio', '--audio-provider', 'agent-audio']), patch.object(installer, 'select_audio', return_value='agent-audio'), patch.object(installer, 'setup_audio') as setup, patch.object(installer, 'install_skill') as skill, patch.object(installer, 'setup_runtime') as engine:
    installer.main()
    setup.assert_called_once()
    skill.assert_not_called()
    engine.assert_not_called()
with tempfile.TemporaryDirectory() as scratch:
    source = Path(scratch) / 'source'
    with patch.object(sound, 'resources', return_value=ready), patch.object(sound.shutil, 'which', return_value='/tool'), patch.object(sound.subprocess, 'run') as run:
        sound.setup_audio(source)
        commands = [call.args[0] for call in run.call_args_list]
        assert commands[:3] == [['git', 'clone', sound.REPOSITORY, str(source)], ['git', '-C', str(source), 'checkout', '--detach', sound.REVISION], ['uv', 'sync', '--frozen']]
        assert [cmd[-1] for cmd in commands[3:]] == ['--doctor', '--runtime-only', '--register-only']
print('PASS: optional audio skips by default, gates resources before downloads, and delegates to the official installer.')
