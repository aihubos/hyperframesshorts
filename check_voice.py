"""Check ElevenLabs plan matching, private settings, and real 1.2x audio."""
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
assert setup.PROVIDERS == ('elevenlabs-free', 'elevenlabs-paid')
try:
    setup.select_provider('local')
except ValueError:
    pass
else:
    raise AssertionError('local provider must be rejected')
with patch.object(setup.sys, 'argv', ['setup_voice.py', '--provider', 'local']):
    try:
        setup.main()
    except SystemExit as exc:
        assert exc.code != 0
    else:
        raise AssertionError('local provider must be rejected')

with tempfile.TemporaryDirectory() as scratch:
    root = Path(scratch)
    config = root / 'private/voice.json'
    with patch.object(setup, 'CONFIG', config):
        setup.write_config({'engine': 'elevenlabs', 'provider': 'elevenlabs-free', 'speed': 1.2})
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
print('PASS: ElevenLabs-only providers, private config, real 1.2x duration and double-application guard.')

with tempfile.TemporaryDirectory() as scratch:
    config = Path(scratch) / 'voice.json'
    for provider, tier in [('elevenlabs-free', 'free'), ('elevenlabs-paid', 'creator')]:
        with patch.object(setup, 'CONFIG', config), patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test-only-key'}, clear=True), patch.object(setup.sys, 'argv', ['setup_voice.py', '--provider', provider, '--elevenlabs-voice-id', 'chosen']), patch.object(setup, 'eleven_api', side_effect=[{'tier': tier}, {'voice_id': 'chosen'}]) as cloud:
            setup.main()
            settings = json.loads(config.read_text())
            assert settings['engine'] == 'elevenlabs' and settings['provider'] == provider
            assert settings['voice_id'] == 'chosen' and 'test-only-key' not in config.read_text()
            assert [c.args[0] for c in cloud.call_args_list] == ['/v1/user/subscription', '/v1/voices/chosen']
    before = config.read_bytes()
    mismatches = [
        ({}, {}, 'elevenlabs-paid'),
        ({'ELEVENLABS_API_KEY': 'test-only-key'}, {'tier': 'free'}, 'elevenlabs-paid'),
        ({'ELEVENLABS_API_KEY': 'test-only-key'}, {'tier': 'creator'}, 'elevenlabs-free'),
    ]
    for env, response, provider in mismatches:
        with patch.object(setup, 'CONFIG', config), patch.dict(os.environ, env, clear=True), patch.object(setup, 'eleven_api', return_value=response):
            try:
                setup.setup_elevenlabs(provider, 'chosen')
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
with tempfile.TemporaryDirectory() as scratch:
    config = Path(scratch) / 'voice.json'
    config.write_text(json.dumps({'engine': 'voxcpm2', 'provider': 'local', 'voice_id': 'should-not-reuse'}), encoding='utf-8')
    before = config.read_bytes()
    with patch.object(setup, 'CONFIG', config), patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test-only-key'}, clear=True), patch.object(setup.sys.stdin, 'isatty', return_value=False), patch.object(setup, 'eleven_api', return_value={'tier': 'free'}):
        try:
            setup.setup_elevenlabs('elevenlabs-free')
        except RuntimeError as exc:
            assert '목소리 ID' in str(exc)
        else:
            raise AssertionError('an old local voice config must not be reused')
        assert config.read_bytes() == before
    config.write_text(json.dumps({'engine': 'elevenlabs', 'provider': 'elevenlabs-free', 'voice_id': 'kept'}), encoding='utf-8')
    with patch.object(setup, 'CONFIG', config), patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test-only-key'}, clear=True), patch.object(setup, 'eleven_api', side_effect=[{'tier': 'free'}, {'voice_id': 'kept'}]):
        setup.setup_elevenlabs('elevenlabs-free')
        assert json.loads(config.read_text())['voice_id'] == 'kept'
        assert 'test-only-key' not in config.read_text()
for number, provider in enumerate(setup.PROVIDERS, 1):
    with patch.object(setup.sys.stdin, 'isatty', return_value=True), patch('builtins.input', return_value=str(number)):
        assert setup.select_provider() == provider
with patch.object(setup.sys.stdin, 'isatty', return_value=True), patch('builtins.input', return_value='3'):
    try:
        setup.select_provider()
    except ValueError:
        pass
    else:
        raise AssertionError('only choices 1 and 2 are valid')
with patch.object(setup.sys.stdin, 'isatty', return_value=False):
    try:
        setup.select_provider()
    except RuntimeError:
        pass
    else:
        raise AssertionError('Unattended setup requires a user choice')
print('PASS: both ElevenLabs plans, plan mismatch stops, connection failure preserves settings, no API key saved.')
