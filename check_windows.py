"""Host-independent checks of Windows branches; not a Windows end-to-end run."""
import importlib.util
import io
import json
import tempfile
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('voice', Path(__file__).parent / 'scripts/setup_voice.py')
voice = importlib.util.module_from_spec(spec)
spec.loader.exec_module(voice)
with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    exe = root / 'VoiceStudio (Current User)/omnivoice-studio.exe'
    managed = root / 'com.debpalash.omnivoice-studio'
    python = managed / 'project/.venv/Scripts/python.exe'
    uv = managed / 'tools/uv.exe'
    for file in (python, uv):
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch()
    def install(args):
        assert args[0] == 'msiexec.exe' and '/norestart' in args
        exe.parent.mkdir(parents=True)
        exe.touch()
        return SimpleNamespace(returncode=0)
    with patch.object(voice.platform, 'system', return_value='Windows'), patch.object(voice.platform, 'machine', return_value='AMD64'), patch.dict(voice.os.environ, {'LOCALAPPDATA': str(root)}, clear=True), patch.object(voice.shutil, 'which', return_value=None):
        assert voice.backend_tools() == (python, str(uv))
        with patch.object(voice, 'api', side_effect=[urllib.error.URLError('not started'), {}]), patch.object(voice.urllib.request, 'urlretrieve') as download, patch.object(voice.subprocess, 'run', side_effect=install), patch.object(voice.subprocess, 'Popen') as launch:
            voice.ensure_app()
            assert 'Current_User_0.5.2' in download.call_args.args[0]
            launch.assert_called_once_with([str(exe)])
        with patch.object(voice, 'api', side_effect=[urllib.error.URLError('not started'), {}]), patch.object(voice.urllib.request, 'urlretrieve') as download, patch.object(voice.subprocess, 'Popen'):
            voice.ensure_app()
            download.assert_not_called()
    captured = []
    def receive(request, timeout):
        captured.append(request.data)
        return io.BytesIO(json.dumps({'id':'registered'}).encode())
    with patch.object(voice.urllib.request, 'urlopen', side_effect=receive):
        assert voice.register_voice(voice.BUNDLED/'reference.wav', voice.BUNDLED/'transcript.txt', '공유 목소리')['id']=='registered'
    assert '공유 목소리'.encode() in captured[0] and b'RIFF' in captured[0]
print('PASS: Windows per-user install, existing-app reuse, managed Python/uv paths, Korean multipart audio registration.')
