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
