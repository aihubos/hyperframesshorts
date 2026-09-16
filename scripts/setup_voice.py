#!/usr/bin/env python3
"""Prepare VoiceStudio + VoxCPM2; keep voice selection private to this machine."""
import argparse
import json
import os
import uuid
import platform
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import urllib.error

API = 'http://127.0.0.1:3900'
MODEL = 'openbmb/VoxCPM2'
BUNDLED = Path(__file__).resolve().parent.parent / 'assets/voice'
BUNDLED_NAME = 'Hyperframes Shorts Shared Voice'
CONFIG = Path.home() / '.config/hyperframesshorts/voice.json'


def api(path, data=None):
    req = urllib.request.Request(API + path, data=None if data is None else json.dumps(data).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=3600 if path == '/models/install' else 15) as response:
        return json.load(response)


def ensure_app():
    try:
        api('/engines/tts')
        return
    except urllib.error.URLError:
        pass
    if platform.system() == 'Windows':
        if platform.machine().lower() not in ('amd64', 'x86_64'):
            raise RuntimeError('Automatic Windows installation requires Windows 10/11 x64.')
        local = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local'))
        apps = [folder / exe for folder in (local / 'VoiceStudio (Current User)',
                Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'VoiceStudio')
                for exe in ('omnivoice-studio.exe', 'VoiceStudio.exe')]
        if os.environ.get('HYPERFRAMES_VOICESTUDIO_APP'):
            apps.insert(0, Path(os.environ['HYPERFRAMES_VOICESTUDIO_APP']))
        app = next((p for p in apps if p.is_file()), None)
        if app is None:
            # Official per-user MSI: no execution-policy or machine-wide settings changes.
            with tempfile.TemporaryDirectory() as temp:
                installer = Path(temp) / 'VoiceStudio.msi'
                url = 'https://github.com/debpalash/VoiceStudio/releases/download/v0.5.2/VoiceStudio_Current_User_0.5.2_x64_en-US.msi'
                print('Downloading official VoiceStudio 0.5.2 Windows installer...', flush=True)
                urllib.request.urlretrieve(url, installer)
                result = subprocess.run(['msiexec.exe', '/i', str(installer), '/passive', '/norestart'])
                if result.returncode not in (0, 3010):
                    raise RuntimeError(f'VoiceStudio MSI failed (code {result.returncode}); complete the official installer and rerun.')
                if result.returncode == 3010:
                    raise RuntimeError('Windows requests a restart. Restart when convenient, then rerun.')
            app = next((p for p in apps if p.is_file()), None)
        if app is None:
            raise RuntimeError('Set HYPERFRAMES_VOICESTUDIO_APP to your installed VoiceStudio.exe path, then rerun.')
        subprocess.Popen([str(app)])
    elif platform.system() == 'Darwin' and platform.machine() == 'arm64':
        apps = [Path('/Applications/VoiceStudio.app'), Path.home() / 'Applications/VoiceStudio.app']
        app = next((p for p in apps if p.exists()), None)
        if app is None:
            with tempfile.TemporaryDirectory() as temp:
                installer = Path(temp) / 'install.sh'
                subprocess.run(['curl', '-fL', 'https://raw.githubusercontent.com/debpalash/VoiceStudio/v0.5.2/scripts/install.sh', '-o', str(installer)], check=True)
                subprocess.run(['sh', str(installer), '--binary', '--version', '0.5.2'], check=True)
            app = next((p for p in apps if p.exists()), None)
            if app is None:
                raise RuntimeError('VoiceStudio app was not found after installation.')
        subprocess.run(['open', '-g', str(app)], check=True)
    else:
        raise RuntimeError('Install/start VoiceStudio using https://voicestudio.sh/download, then rerun. Automatic app installation supports Apple Silicon macOS and Windows x64.')
    for _ in range(30):
        try:
            api('/engines/tts')
            return
        except urllib.error.URLError:
            time.sleep(2)
    raise RuntimeError('Complete the first-launch OS approval and VoiceStudio setup, then rerun this command. No security settings were changed.')


def backend_tools():
    windows = platform.system() == 'Windows'
    if windows:
        root = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local')) / 'com.debpalash.omnivoice-studio'
    else:
        root = Path.home() / 'Library/Application Support/com.debpalash.omnivoice-studio'
    config = root / 'config.json'
    env_root = root
    if config.is_file():
        env_root = Path(json.loads(config.read_text(encoding='utf-8')).get('env_dir') or root)
    python = Path(os.environ.get('HYPERFRAMES_VOICESTUDIO_PYTHON') or
                  env_root / ('project/.venv/Scripts/python.exe' if windows else 'project/.venv/bin/python'))
    executable = 'uv.exe' if windows else 'uv'
    candidates = [shutil.which(executable), str(env_root / 'tools' / executable),
                  str(root / 'tools' / executable), str(Path.home() / '.local/bin' / executable)]
    uv = next((p for p in candidates if p and Path(p).is_file()), None)
    if not python.is_file() or uv is None:
        raise RuntimeError('Complete VoiceStudio first-run setup. For a custom/portable environment set HYPERFRAMES_VOICESTUDIO_PYTHON and put uv on PATH; see references/voice.md.')
    return python, uv


def install_model():
    health = api('/engines/voxcpm2/health')
    if not health.get('ok'):
        python, uv = backend_tools()
        subprocess.run([uv, 'pip', 'install', '--python', str(python), 'voxcpm>=2.0.3'], check=True)
        if not api('/engines/voxcpm2/health').get('ok'):
            raise RuntimeError('VoxCPM installed. Restart VoiceStudio and rerun to refresh engine availability.')
    models = api('/models')['models']
    model = next((m for m in models if m['repo_id'] == MODEL), None)
    if model is None or not model.get('supported', True):
        raise RuntimeError('VoxCPM2 is not available on this VoiceStudio installation/hardware.')
    if not model.get('installed') or model.get('incomplete'):
        print('Downloading VoxCPM2 (~5 GB); this can take several minutes.', flush=True)
        api('/models/install', {'repo_id': MODEL, 'target': 'local'})
        # The catalogue can cache on-disk state for ten seconds.
        for _ in range(7):
            models = api('/models')['models']
            model = next(m for m in models if m['repo_id'] == MODEL)
            if model.get('installed') and not model.get('incomplete'):
                break
            time.sleep(2)
        else:
            raise RuntimeError('Model download is not complete; check VoiceStudio download status and rerun.')
    api('/engines/select', {'family': 'tts', 'backend_id': 'voxcpm2', 'model_id': MODEL})


def register_voice(audio, transcript, name):
    # UTF-8 multipart avoids Windows console encoding and curl version differences.
    boundary = 'shorts-' + uuid.uuid4().hex
    parts = []
    for key, value in {'name': name, 'kind': 'clone', 'language': 'Korean',
                       'ref_text': transcript.read_text(encoding='utf-8-sig')}.items():
        parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n').encode('utf-8'))
    parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="ref_audio"; filename="reference{audio.suffix}"\r\nContent-Type: application/octet-stream\r\n\r\n').encode('utf-8'))
    parts.extend([audio.read_bytes(), f'\r\n--{boundary}--\r\n'.encode()])
    req = urllib.request.Request(API + '/profiles', data=b''.join(parts),
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response)


def bundled_voice():
    transcript = (BUNDLED / 'transcript.txt').read_text(encoding='utf-8').strip()
    profiles = api('/profiles')
    for profile in profiles if isinstance(profiles, list) else profiles.get('profiles', []):
        if profile['name'] == BUNDLED_NAME and profile.get('ref_text', '').strip() == transcript:
            return profile['id']
    return register_voice(BUNDLED / 'reference.wav', BUNDLED / 'transcript.txt', BUNDLED_NAME)['id']


def save_config(profile_id):
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=CONFIG.parent, delete=False, encoding='utf-8') as out:
        json.dump({'engine': 'voxcpm2', 'model': MODEL, 'profile_id': profile_id,
                   'speed': 1.2, 'language': 'Korean'}, out, indent=2)
        name = out.name
    Path(name).replace(CONFIG)
    print(f'Voice selection saved locally: {CONFIG}; narration speed=1.2')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group()
    group.add_argument('--bundled-voice', action='store_true', help='Select the creator-shared voice bundled with this skill.')
    group.add_argument('--profile-id', help='Use only the voice explicitly selected by the user.')
    group.add_argument('--voice-audio', type=Path, help='Locally supplied voice reference, ideally 5–15 seconds.')
    p.add_argument('--voice-text', type=Path, help='UTF-8 exact transcript matching the entire reference.')
    p.add_argument('--voice-name', default='My Shorts Voice')
    args = p.parse_args()
    if args.voice_audio and (not args.voice_audio.is_file() or not args.voice_text or not args.voice_text.is_file()):
        p.error('--voice-audio requires an existing audio file and --voice-text transcript file.')
    if args.voice_audio and not args.voice_text.read_text(encoding='utf-8-sig').strip():
        p.error('The matching voice transcript must not be empty.')
    ensure_app()
    install_model()
    profile_id = args.profile_id
    if not profile_id and not args.voice_audio and not args.bundled_voice and CONFIG.exists():
        profile_id = json.loads(CONFIG.read_text(encoding='utf-8')).get('profile_id')
    if args.voice_audio:
        profile = register_voice(args.voice_audio, args.voice_text, args.voice_name)
        profile_id = profile['id']
    if not profile_id and not args.voice_audio:
        profile_id = bundled_voice()
    if profile_id:
        api('/profiles/' + urllib.parse.quote(profile_id, safe=''))
        save_config(profile_id)
        print('VoiceStudio + VoxCPM2 + selected voice configured. Verify a short spoken sample before production.')
    else:
        print('VoiceStudio + VoxCPM2 ready. Ask the user to select a voice; rerun with --profile-id or --voice-audio/--voice-text.')
        profiles = api('/profiles')
        for profile in profiles if isinstance(profiles, list) else profiles.get('profiles', []):
            print(profile['id'], profile['name'])


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f'Voice setup incomplete: {exc}')
