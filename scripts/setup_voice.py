#!/usr/bin/env python3
"""Prepare VoiceStudio + VoxCPM2; keep voice selection private to this machine."""
import argparse
import json
import os
import sys
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


PROVIDERS = ('local', 'elevenlabs-free', 'elevenlabs-paid')


def select_provider(selected=None):
    if selected:
        if selected not in PROVIDERS:
            raise ValueError('Unknown voice provider.')
        return selected
    if not sys.stdin.isatty():
        raise RuntimeError('사용자에게 음성 방식 1/2/3을 물어본 후 --voice-provider local|elevenlabs-free|elevenlabs-paid로 실행하세요.')
    print('음성 생성 방식을 선택하세요. 설치 폴더는 자동 지정됩니다.')
    print('1. 로컬 생성: 무료 · 수익화 가능(모델·목소리 권리 준수) · 컴퓨터 자원 소모')
    print('2. ElevenLabs 무료 API: 무료 한도 내 · 수익화 불가 · 공개 시 출처 표시')
    print('3. ElevenLabs 구독: 유료 · 구독 중 생성한 음성의 상업 이용 가능(약관 적용)')
    choice = input('선택 [1/2/3]: ').strip()
    if choice not in ('1', '2', '3'):
        raise ValueError('1, 2, 3 중 하나를 선택하고 다시 실행하세요.')
    return PROVIDERS[int(choice) - 1]


def eleven_api(path, key):
    req = urllib.request.Request('https://api.elevenlabs.io' + path, headers={'xi-api-key': key})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'ElevenLabs 연결 실패 (HTTP {exc.code}). API 키, User/Voices 읽기 권한과 계정 상태를 확인하세요.') from None
    except urllib.error.URLError:
        raise RuntimeError('ElevenLabs에 연결할 수 없습니다. 네트워크를 확인하고 다시 실행하세요.') from None


def setup_elevenlabs(provider, voice_id=None):
    key = os.environ.get('ELEVENLABS_API_KEY', '').strip()
    if not key:
        raise RuntimeError('ElevenLabs 계정에서 API 키를 만든 뒤 로컬 환경변수 ELEVENLABS_API_KEY에 설정하고 재실행하세요. 키를 채팅에 보내지 마세요. 안내: https://elevenlabs.io/docs/overview/administration/workspaces/api-keys')
    subscription = eleven_api('/v1/user/subscription', key)
    tier = subscription.get('tier')
    if not isinstance(tier, str) or not tier:
        raise RuntimeError('계정 요금제를 확인하지 못했습니다. 기존 음성 설정을 유지합니다.')
    if (tier == 'free') != (provider == 'elevenlabs-free'):
        raise RuntimeError('선택한 무료/구독 방식과 실제 계정 요금제가 다릅니다. 계정을 확인하고 알맞은 방식으로 다시 실행하세요.')
    previous = json.loads(CONFIG.read_text(encoding='utf-8')) if CONFIG.exists() else {}
    voice_id = voice_id or os.environ.get('ELEVENLABS_VOICE_ID')
    if not voice_id and previous.get('engine') == 'elevenlabs':
        voice_id = previous.get('voice_id')
    if not voice_id:
        if not sys.stdin.isatty():
            raise RuntimeError('사용자가 고른 목소리 ID를 --elevenlabs-voice-id 또는 ELEVENLABS_VOICE_ID로 지정하세요. VoiceStudio는 설치하지 않습니다.')
        print('ElevenLabs의 Voices에서 사용할 목소리의 ID를 복사하세요.')
        voice_id = input('목소리 ID: ').strip()
    if not voice_id or not voice_id.strip():
        raise ValueError('목소리 ID가 필요합니다.')
    voice_id = voice_id.strip()
    voice = eleven_api('/v1/voices/' + urllib.parse.quote(voice_id, safe=''), key)
    if voice.get('voice_id') != voice_id:
        raise RuntimeError('선택한 목소리를 확인하지 못했습니다. 기존 음성 설정을 유지합니다.')
    write_config({'engine': 'elevenlabs', 'provider': provider, 'tier': tier,
                  'voice_id': voice_id, 'model': 'eleven_multilingual_v2',
                  'api_key_env': 'ELEVENLABS_API_KEY', 'speed': 1.2, 'language': 'Korean'})
    print('ElevenLabs 계정·목소리 연결 확인 완료. API 키는 파일에 저장하지 않습니다.')
    print('음성 생성 시에도 ELEVENLABS_API_KEY가 필요합니다. 실제 생성 가능 여부는 짧은 샘플로 별도 확인하세요.')


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


def write_config(settings):
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=CONFIG.parent, delete=False, encoding='utf-8') as out:
        json.dump(settings, out, indent=2)
        name = out.name
    Path(name).replace(CONFIG)
    print(f'Voice selection saved locally: {CONFIG}; narration speed=1.2')


def save_config(profile_id):
    write_config({'engine': 'voxcpm2', 'provider': 'local', 'model': MODEL,
                  'profile_id': profile_id, 'speed': 1.2, 'language': 'Korean'})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--provider', choices=PROVIDERS)
    p.add_argument('--elevenlabs-voice-id')
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
    provider = select_provider(args.provider)
    if provider != 'local':
        if args.profile_id or args.bundled_voice or args.voice_audio or args.voice_text:
            p.error('로컬 목소리 옵션은 --provider local에서만 사용할 수 있습니다.')
        setup_elevenlabs(provider, args.elevenlabs_voice_id)
        return
    if args.elevenlabs_voice_id:
        p.error('--elevenlabs-voice-id는 ElevenLabs 선택 시에만 사용할 수 있습니다.')
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
    except (OSError, EOFError, RuntimeError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f'Voice setup incomplete: {exc}')
