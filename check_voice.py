"""One direct check for model reuse/download, private settings and real 1.2x audio."""
import importlib.util
from pathlib import Path
import json
import subprocess
import tempfile
from unittest.mock import patch


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


setup = load('setup_voice')
speed = load('speed_voice')
for installed in (True, False):
    state = {'ready': installed}
    calls = []
    def api(path, data=None):
        calls.append((path, data))
        if path.endswith('/health'):
            return {'ok': True}
        if path == '/models':
            return {'models': [{'repo_id': setup.MODEL, 'installed': state['ready']}]}
        if path == '/models/install':
            state['ready'] = True
        return {}
    with patch.object(setup, 'api', side_effect=api):
        setup.install_model()
    assert sum(p == '/models/install' for p, _ in calls) == int(not installed)
    assert calls[-1] == ('/engines/select', {'family': 'tts', 'backend_id': 'voxcpm2', 'model_id': setup.MODEL})
with tempfile.TemporaryDirectory() as scratch:
    root = Path(scratch)
    config = root / 'private/voice.json'
    with patch.object(setup, 'CONFIG', config):
        setup.save_config('user-selected-voice')
    assert json.loads(config.read_text())['speed'] == 1.2
    assert config.stat().st_mode & 0o077 == 0
    original, output = root / 'original.wav', root / 'fast.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=6', str(original)], check=True)
    speed.speed_voice(original, output)
    assert abs(speed.duration(output) - 5) < 0.1
    try:
        speed.speed_voice(output, root / 'double.wav')
    except ValueError:
        pass
    else:
        raise AssertionError('Double speed application was not blocked')
print('PASS: model reuse/download routing, private config, real 1.2x duration and double-application guard.')

transcript = (setup.BUNDLED / 'transcript.txt').read_text().strip()
with patch.object(setup, 'api', return_value=[]), patch.object(setup, 'register_voice', return_value={'id': 'new'}) as register:
    assert setup.bundled_voice() == 'new'
    assert register.call_count == 1
with patch.object(setup, 'api', return_value=[{'id': 'existing', 'name': setup.BUNDLED_NAME, 'ref_text': transcript}]), patch.object(setup, 'register_voice') as register:
    assert setup.bundled_voice() == 'existing'
    register.assert_not_called()
assert 7 < speed.duration(setup.BUNDLED / 'reference.wav') < 9
print('PASS: bundled audio exists; new voice registers and existing matching voice is reused.')
