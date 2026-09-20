"""One direct check for model reuse/download, private settings and real 1.2x audio."""
import importlib.util
from pathlib import Path
import json
import os
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
    if os.name != 'nt':
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

transcript = (setup.BUNDLED / 'transcript.txt').read_text(encoding='utf-8').strip()
with patch.object(setup, 'api', return_value=[]), patch.object(setup, 'register_voice', return_value={'id': 'new'}) as register:
    assert setup.bundled_voice() == 'new'
    assert register.call_count == 1
with patch.object(setup, 'api', return_value=[{'id': 'existing', 'name': setup.BUNDLED_NAME, 'ref_text': transcript}]), patch.object(setup, 'register_voice') as register:
    assert setup.bundled_voice() == 'existing'
    register.assert_not_called()
assert 7 < speed.duration(setup.BUNDLED / 'reference.wav') < 9
print('PASS: bundled audio exists; new voice registers and existing matching voice is reused.')

# Cloud setup never starts/downloads the local engine, and failed connections preserve settings.
with tempfile.TemporaryDirectory() as scratch:
    config = Path(scratch) / 'voice.json'
    for provider, tier in [('elevenlabs-free', 'free'), ('elevenlabs-paid', 'creator')]:
        with patch.object(setup, 'CONFIG', config), patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test-only-key'}, clear=True), patch.object(setup.sys, 'argv', ['setup_voice.py', '--provider', provider, '--elevenlabs-voice-id', 'chosen']), patch.object(setup, 'eleven_api', side_effect=[{'tier': tier}, {'voice_id': 'chosen'}]) as cloud, patch.object(setup, 'ensure_app') as app, patch.object(setup, 'install_model') as model:
            setup.main()
            app.assert_not_called()
            model.assert_not_called()
            settings = json.loads(config.read_text())
            assert settings['engine'] == 'elevenlabs' and settings['provider'] == provider
            assert settings['voice_id'] == 'chosen' and 'test-only-key' not in config.read_text()
            assert [c.args[0] for c in cloud.call_args_list] == ['/v1/user/subscription', '/v1/voices/chosen']
    before = config.read_bytes()
    for env, response in [({}, {}), ({'ELEVENLABS_API_KEY': 'test-only-key'}, {'tier': 'free'})]:
        with patch.object(setup, 'CONFIG', config), patch.dict(os.environ, env, clear=True), patch.object(setup, 'eleven_api', return_value=response):
            try:
                setup.setup_elevenlabs('elevenlabs-paid', 'chosen')
            except RuntimeError:
                pass
            else:
                raise AssertionError('Missing key or plan mismatch must fail')
            assert config.read_bytes() == before
    with patch.object(setup, 'CONFIG', config), patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test-only-key'}, clear=True), patch.object(setup, 'eleven_api', side_effect=RuntimeError('connection failed')):
        try:
            setup.setup_elevenlabs('elevenlabs-paid', 'chosen')
        except RuntimeError:
            pass
        else:
            raise AssertionError('Connection failure must stop setup')
        assert config.read_bytes() == before
for number, provider in enumerate(setup.PROVIDERS, 1):
    with patch.object(setup.sys.stdin, 'isatty', return_value=True), patch('builtins.input', return_value=str(number)):
        assert setup.select_provider() == provider
with patch.object(setup.sys.stdin, 'isatty', return_value=False):
    try:
        setup.select_provider()
    except RuntimeError:
        pass
    else:
        raise AssertionError('Unattended setup requires a user choice')
print('PASS: all provider choices, cloud skips local setup, connection failure preserves settings, no API key saved.')
