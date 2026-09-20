# 음성 방식 선택과 연결 + 1.2배속

## 먼저 음성 방식을 선택

`install.py --setup` 또는 `--setup-voice`는 1. 로컬 무료(목소리 권리 준수 시 수익화 가능, 컴퓨터 자원 소모), 2. ElevenLabs 무료 API(무료 한도, 수익화 불가, 출처 표시), 3. ElevenLabs 구독(유료, 구독 중 생성물 상업 이용 가능)을 묻는다. 비대화형 에이전트는 사용자 답변을 먼저 받고 `--voice-provider local|elevenlabs-free|elevenlabs-paid`로 전달한다. 설치 폴더는 묻지 않는다.

## ElevenLabs 선택 시 — VoiceStudio 설치 없음

1. 사용자가 ElevenLabs 계정에서 API 키를 만들고 로컬 환경변수 `ELEVENLABS_API_KEY`로 설정한다. [공식 API 키 안내](https://elevenlabs.io/docs/overview/administration/workspaces/api-keys)를 제공한다. API 키를 채팅이나 명령 인수로 받지 않는다. OS 환경변수 설정 후 에이전트/터미널을 다시 열어야 할 수 있다.
2. User와 Voices 읽기 권한으로 연결을 확인하고, 음성 제작에는 Text to Speech 권한도 부여한다. 무료/구독 선택과 실제 `/v1/user/subscription` 요금제가 다르면 기존 설정을 유지하고 중단한다.
3. 사용자가 Voices 화면에서 고른 목소리 ID를 `--elevenlabs-voice-id` 또는 `ELEVENLABS_VOICE_ID`로 전달한다. 이전 ElevenLabs 목소리 선택은 재사용할 수 있다. 무료 계정은 API로 사용할 수 있는 목소리를 선택해야 한다.
4. `/v1/voices/{voice_id}` 확인 후 `voice.json`에 엔진·요금제·목소리·모델·속도만 저장한다. API 키는 저장하지 않으며 실제 생성 시에도 환경변수가 필요하다. 읽기 연결 성공은 TTS 권한·잔여 한도·실제 음성 생성 성공을 보장하지 않는다.

```bash
python3 scripts/setup_voice.py --provider elevenlabs-free --elevenlabs-voice-id 선택한_ID
python3 scripts/setup_voice.py --provider elevenlabs-paid --elevenlabs-voice-id 선택한_ID
```

생성 시 `voice.json`의 `engine`이 `elevenlabs`이면 ElevenLabs 공식 TTS API를 사용한다. `ELEVENLABS_API_KEY`를 `xi-api-key` 헤더에 넣고, 선택한 `voice_id` 및 `model`(`eleven_multilingual_v2`)로 원본을 생성한다. 생성 직전에 요금제를 다시 확인한다. 무료 선택에서 유료 과금으로 또는 유료 선택에서 무료로 바뀌면 사용자에게 알리고 선택을 갱신한다. 실패 시 로컬 음성으로 임의 전환하지 않는다. 원본 생성 후 아래 `speed_voice.py`로 1.2배속을 한 번만 적용하고 자막을 맞춘다.

무료는 상업 이용 불가이며 공개 제목에 `elevenlabs.io` 또는 `11.ai`를 표시한다. 구독 중 생성한 음성은 약관상 상업 이용이 가능하며, 무료 생성물에 유료 권한이 소급되지 않는다. Beta 서비스 등 예외는 [공식 이용 안내](https://help.elevenlabs.io/hc/en-us/articles/13313564601361-Can-I-publish-the-content-I-generate-on-the-platform)를 확인한다. 어떤 방식도 YouTube 수익화 승인을 보장하지 않는다.

아래 VoiceStudio 설치·등록·생성 절차는 **1번 로컬 선택에만** 적용한다.

## 설치 및 재개

저장소에서 `python3 install.py --setup`를 실행한다. 1번 로컬 선택 시 기존 Hyperframes를 재사용하고, 스킬, VoiceStudio, VoxCPM2 순서로 준비한다. 두 OS 모두 Docker 없이 직접 설치한다. 이미 설치되어 실행 중인 VoiceStudio와 다운로드된 모델은 재사용한다.

- Apple Silicon macOS: 앱이 없으면 VoiceStudio 공식 v0.5.2 설치 프로그램으로 설치하고 실행한다. macOS의 최초 앱 실행 승인과 앱 초기 설정은 사용자가 완료해야 할 수 있다. 보안 설정을 해제하지 않는다. 초기 설정 후 같은 명령으로 재개한다.
- Windows 10/11 x64: `py -3 install.py --setup`로 공식 Current User MSI 설치·실행 후 같은 모델과 공유 목소리를 설정한다. 기존 설치를 재사용하며 최초 앱 설정 후 재실행이 필요할 수 있다.
- Linux/Intel Mac: 앱 설치는 [공식 다운로드](https://voicestudio.sh/download)의 지원 범위를 따른다. 이 패키지의 데스크톱 자동 설치는 Apple Silicon macOS와 Windows x64를 지원한다. 로컬 API가 실행되면 모델/목소리 설정 코드는 재사용할 수 있지만 Windows 실기 설치·생성은 아직 검증하지 않았다.
- API 기준: `http://127.0.0.1:3900`. 포트가 다르거나 인증을 요구하는 설치는 실제 설정을 먼저 확인한다. 원격 서버로 개인 음성을 임의 전송하지 않는다.
- VoxCPM2 패키지가 없으면 각 OS의 기존 VoiceStudio 관리 환경에서 `uv pip install --python <VoiceStudio Python 경로> 'voxcpm>=2.0.3'`를 실행한다. 탐지하지 못한 환경에서는 에이전트가 실제 Python 환경을 찾아 공식 [엔진 안내](https://github.com/debpalash/VoiceStudio/blob/main/docs/engines/voxcpm2.md)를 따른다. 시스템 Python에 무작정 설치하지 않는다.
- 모델은 `openbmb/VoxCPM2` 약 5GB를 공식 모델 API로 다운로드하고 TTS 엔진을 `voxcpm2`로 선택한다. 실패 시 다른 모델로 대체하지 않는다.

VoiceStudio 앱은 AGPL-3.0, [VoxCPM2 모델](https://huggingface.co/openbmb/VoxCPM2)은 Apache-2.0이다. 서로 다른 라이선스이며 이 저장소에 앱이나 모델 가중치를 재배포하지 않는다.

## 목소리 선택과 자동 등록

첫 설치에서는 공개 승인된 `assets/voice/` 목소리를 자동 등록한다. 기존에 선택한 목소리는 유지하며, 다른 목소리를 원하면 사용자에게 물어 선택한다. 이미 명시적으로 승인한 목소리는 다시 묻지 않고 재사용한다. 첫 설치에서 가장 최근 목소리나 첫 번째 항목을 임의 선택하지 않는다.

```bash
# 목록을 표시한 후 사용자가 선택한 ID를 지정
python3 scripts/setup_voice.py --provider local
python3 scripts/setup_voice.py --provider local --profile-id 선택한_ID

# 별도로 전달받은, 사용 권한이 있는 음성을 자동 등록
python3 scripts/setup_voice.py --provider local --voice-audio /절대경로/목소리.wav --voice-text /절대경로/정확한_녹취.txt --voice-name '내 쇼츠 목소리'
```

설치된 스킬에서는 해당 스킬 폴더의 `scripts/`를 사용한다. ID·모델·속도는 `~/.config/hyperframesshorts/voice.json`에 로컬 저장한다. 제작자가 공개를 요청한 7.8초 참조 음성과 정확한 녹취는 `assets/voice/`에 포함한다. 계정 정보나 로컬 프로필 ID는 공유하지 않는다. 공유 음성은 이름·녹취가 같은 기존 프로필이 있으면 재사용한다. 기존 선택 대신 공유 목소리를 쓰려면 `python3 scripts/setup_voice.py --provider local --bundled-voice`를 실행한다. 사용자가 별도 음성을 반복 등록하면 새 프로필이 생기므로 이후에는 ID로 재사용한다.

참조 음성은 잡음 없는 5–15초를 권장한다. 긴 녹음에 일부 녹취만 넣으면 생성 음성이 짧게 끊길 수 있다. 참조를 자르면 녹취도 같은 구간으로 맞춘다. 기존 사용자 프로필을 임의 수정하지 말고 프로젝트용 짧은 참조를 별도로 만든다.

## 생성과 속도 적용

VoiceStudio `/openapi.json`에서 현재 API 형식을 먼저 확인한다. `/generate`는 multipart 요청이며 응답은 JSON이 아닌 WAV 바이너리다. 기본은 `engine=voxcpm2`, `language=Korean`, `speed=1.0`으로 원본을 생성한다. 선택한 `profile_id`를 사용하거나 같은 목소리의 정확한 짧은 `ref_audio`/`ref_text`를 사용한다. 두 방식을 동시에 전달하면 프로필이 참조를 덮어쓸 수 있으므로 함께 보내지 않는다. 짧은 샘플의 발음과 목소리를 확인한 뒤 전체 대본을 생성한다.

```bash
python3 scripts/speed_voice.py /절대경로/나레이션_원본.wav /절대경로/나레이션_1.2x.wav
```

- **생성 원본 대비 1.2배속을 정확히 한 번** 적용한다. 원본을 먼저 0.75배로 늦추거나 이전 1.2배 파일에 다시 적용하지 않는다.
- 보조 프로그램은 원본과 기존 출력물을 덮어쓰지 않고 길이·배속 기록을 출력 옆 JSON에 저장한다. 별도 도구로 이미 가속한 파일은 기록이 없을 수 있으므로 원본 출처도 확인한다.
- 최종 가속 음성으로 발화 정렬을 수행한 뒤 자막과 장면 길이를 결정한다. 배경음악은 정상 속도로 반복하고 따로 믹싱한다.
- 제작정보에 엔진/모델, 선택 목소리 이름, 원본 길이, 실제 1.2배 적용과 결과 길이를 기록한다. 생성 성공·목소리 선택·재생 확인을 구분한다.

Windows에서 Python 명령은 `py -3`, 경로는 `%USERPROFILE%` 기준이다. 앱 또는 Python 환경이 사용자 지정 경로에 있으면 `HYPERFRAMES_VOICESTUDIO_APP` / `HYPERFRAMES_VOICESTUDIO_PYTHON`을 사용한다. Python 탐지는 앱 config.json의 env_dir도 반영한다. portable 또는 앱의 비ASCII 경로 우회 환경은 실제 Python 경로를 지정한다. 이 설치 명령에는 Whisper 추가 설치가 포함되지 않는다.
