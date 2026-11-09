#!/usr/bin/env python3
"""Connect ElevenLabs narration on this Linux cloud computer. Never store the API key."""
import argparse
import json
import os
import sys
import tempfile
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

CONFIG = Path.home() / '.config/hyperframesshorts/voice.json'
PROVIDERS = ('elevenlabs-free', 'elevenlabs-paid')


def select_provider(selected=None):
    if selected:
        if selected not in PROVIDERS:
            raise ValueError('Unknown voice provider. Use elevenlabs-free or elevenlabs-paid.')
        return selected
    if not sys.stdin.isatty():
        raise RuntimeError('사용자에게 음성 방식 1. ElevenLabs 무료 API 또는 2. ElevenLabs 구독을 물어본 후 --voice-provider elevenlabs-free|elevenlabs-paid로 실행하세요.')
    print('음성 생성 방식을 선택하세요. 클라우드 컴퓨터에서 ElevenLabs API로 생성합니다.')
    print('1. ElevenLabs 무료 API: 무료 한도 내 · 수익화 불가 · 공개 시 출처 표시')
    print('2. ElevenLabs 구독: 유료 · 구독 중 생성한 음성의 상업 이용 가능(약관 적용)')
    choice = input('선택 [1/2]: ').strip()
    if choice not in ('1', '2'):
        raise ValueError('1 또는 2를 선택하고 다시 실행하세요.')
    return PROVIDERS[int(choice) - 1]


def eleven_api(path, key):
    req = urllib.request.Request('https://api.elevenlabs.io' + path, headers={'xi-api-key': key})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'ElevenLabs 연결 실패 (HTTP {exc.code}). API 키, User/Voices 읽기 권한과 계정 상태를 확인하세요.') from None
    except urllib.error.URLError:
        raise RuntimeError('ElevenLabs에 연결할 수 없습니다. 클라우드 컴퓨터의 네트워크를 확인하고 다시 실행하세요.') from None


def write_config(settings):
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=CONFIG.parent, delete=False, encoding='utf-8') as out:
        json.dump(settings, out, indent=2)
        name = out.name
    os.chmod(name, 0o600)
    Path(name).replace(CONFIG)
    print(f'음성 선택을 이 클라우드 컴퓨터에 저장했습니다: {CONFIG}; narration speed=1.2')


def setup_elevenlabs(provider, voice_id=None):
    key = os.environ.get('ELEVENLABS_API_KEY', '').strip()
    if not key:
        raise RuntimeError('ElevenLabs 계정에서 API 키를 만든 뒤 이 클라우드 컴퓨터의 환경변수 ELEVENLABS_API_KEY에 설정하고 재실행하세요. 키를 채팅, 명령 인수, 저장소에 넣지 마세요. 안내: https://elevenlabs.io/docs/overview/administration/workspaces/api-keys')
    subscription = eleven_api('/v1/user/subscription', key)
    tier = subscription.get('tier')
    if not isinstance(tier, str) or not tier:
        raise RuntimeError('계정 요금제를 확인하지 못했습니다. 기존 음성 설정을 유지하고 중단합니다.')
    if (tier == 'free') != (provider == 'elevenlabs-free'):
        raise RuntimeError('선택한 무료/구독 방식과 실제 계정 요금제가 다릅니다. 다른 방식으로 바꾸지 않고 중단합니다. 계정을 확인한 뒤 알맞은 --voice-provider로 다시 실행하세요.')
    previous = json.loads(CONFIG.read_text(encoding='utf-8')) if CONFIG.exists() else {}
    voice_id = voice_id or os.environ.get('ELEVENLABS_VOICE_ID')
    if not voice_id and previous.get('engine') == 'elevenlabs' and previous.get('provider') in PROVIDERS:
        voice_id = previous.get('voice_id')
    if not voice_id:
        if not sys.stdin.isatty():
            raise RuntimeError('사용자가 고른 목소리 ID를 --elevenlabs-voice-id 또는 ELEVENLABS_VOICE_ID로 지정하세요.')
        print('ElevenLabs의 Voices에서 사용할 목소리의 ID를 복사하세요.')
        voice_id = input('목소리 ID: ').strip()
    if not voice_id or not voice_id.strip():
        raise ValueError('목소리 ID가 필요합니다.')
    voice_id = voice_id.strip()
    voice = eleven_api('/v1/voices/' + urllib.parse.quote(voice_id, safe=''), key)
    if voice.get('voice_id') != voice_id:
        raise RuntimeError('선택한 목소리를 확인하지 못했습니다. 기존 음성 설정을 유지하고 중단합니다.')
    write_config({'engine': 'elevenlabs', 'provider': provider, 'tier': tier,
                  'voice_id': voice_id, 'model': 'eleven_multilingual_v2',
                  'api_key_env': 'ELEVENLABS_API_KEY', 'speed': 1.2, 'language': 'Korean'})
    print('ElevenLabs 계정·목소리 연결 확인 완료. API 키는 파일에 저장하지 않습니다.')
    print('음성 생성 시에도 이 클라우드 컴퓨터의 ELEVENLABS_API_KEY가 필요합니다. 실제 생성 가능 여부는 짧은 샘플로 별도 확인하세요.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--provider', choices=PROVIDERS)
    p.add_argument('--elevenlabs-voice-id')
    args = p.parse_args()
    setup_elevenlabs(select_provider(args.provider), args.elevenlabs_voice_id)


if __name__ == '__main__':
    try:
        main()
    except (OSError, EOFError, RuntimeError, ValueError, KeyError) as exc:
        raise SystemExit(f'Voice setup incomplete: {exc}')
