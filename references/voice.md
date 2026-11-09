# 음성 방식 선택과 연결 + 1.2배속

이 스킬의 음성은 원격 Linux 클라우드 컴퓨터에서 ElevenLabs API로만 생성한다. 학생의 Mac/Windows PC에 음성 프로그램을 설치하지 않는다.

## 먼저 음성 방식을 선택

`install.py --setup` 또는 `--setup-voice`는 다음 둘 중 하나를 묻는다.

1. ElevenLabs 무료 API (`elevenlabs-free`): 무료 한도, 수익화 불가, 공개 시 출처 표시
2. ElevenLabs 구독 (`elevenlabs-paid`): 유료, 구독 중 생성한 음성의 상업 이용 가능(약관 적용)

비대화형 에이전트는 사용자 답변을 먼저 받고 `--voice-provider elevenlabs-free` 또는 `--voice-provider elevenlabs-paid`로 전달한다. 선택값이 없으면 설치 전에 중단한다. 설치 폴더는 묻지 않는다. 선택한 방식과 계정이 다르거나 연결에 실패하면 다른 방식으로 바꾸지 않고 중단한다.

## API 키와 요금제

1. 사용자가 ElevenLabs 계정에서 API 키를 만들고, 클라우드 컴퓨터의 환경변수 `ELEVENLABS_API_KEY`로 설정한다. [공식 API 키 안내](https://elevenlabs.io/docs/overview/administration/workspaces/api-keys)를 제공한다. API 키를 채팅, 명령 인수, 저장소에 넣지 않는다. 환경변수를 넣은 뒤 에이전트와 터미널을 다시 열어야 할 수 있다.
2. User와 Voices 읽기 권한으로 연결을 확인하고, 음성 제작에는 Text to Speech 권한도 부여한다. 무료/구독 선택과 실제 `/v1/user/subscription` 요금제가 다르면 기존 설정을 유지하고 중단한다.
3. 사용자가 Voices 화면에서 고른 목소리 ID를 `--elevenlabs-voice-id` 또는 `ELEVENLABS_VOICE_ID`로 전달한다. 이전에 이 클라우드 컴퓨터에 저장한 ElevenLabs 목소리(`engine`이 `elevenlabs`이고 `provider`가 위 둘 중 하나)는 재사용할 수 있다. 그 외의 예전 설정은 사용하지 않는다. 무료 계정은 API로 사용할 수 있는 목소리를 선택해야 한다.
4. `/v1/voices/{voice_id}` 확인 후 `voice.json`에 엔진·요금제·목소리·모델·속도만 저장한다. API 키는 저장하지 않으며 실제 생성 시에도 환경변수가 필요하다. 읽기 연결 성공은 TTS 권한·잔여 한도·실제 음성 생성 성공을 보장하지 않는다.

```bash
python3 scripts/setup_voice.py --provider elevenlabs-free --elevenlabs-voice-id 선택한_ID
python3 scripts/setup_voice.py --provider elevenlabs-paid --elevenlabs-voice-id 선택한_ID
```

설정 파일은 클라우드 컴퓨터의 `~/.config/hyperframesshorts/voice.json`이다. 설치된 스킬에서는 해당 스킬 폴더의 `scripts/`를 사용한다.

## 생성

`voice.json`의 `engine`이 `elevenlabs`이고 `provider`가 `elevenlabs-free` 또는 `elevenlabs-paid`일 때만 ElevenLabs 공식 TTS API로 생성한다. 그 외이면 사용자에게 두 방식 중 하나를 다시 묻고 설정을 갱신한 뒤 생성한다.

`ELEVENLABS_API_KEY`를 `xi-api-key` 헤더에 넣고, 선택한 `voice_id` 및 `model`(`eleven_multilingual_v2`)로 원본을 생성한다. 생성 직전에 `/v1/user/subscription`으로 요금제를 다시 확인한다. 무료 선택에서 유료 요금제로, 또는 유료 선택에서 무료 요금제로 바뀌면 사용자에게 알리고 중단한다. 선택을 갱신하기 전에는 생성하지 않는다. 실패한 연결을 다른 요금제나 다른 음성 방식으로 넘기지 않는다.

원본 생성 후 `speed_voice.py`로 1.2배속을 한 번만 적용하고, 그 음성에 자막을 맞춘다.

```bash
python3 scripts/speed_voice.py /절대경로/나레이션_원본.wav /절대경로/나레이션_1.2x.wav
```

- **생성 원본 대비 1.2배속을 정확히 한 번** 적용한다. 원본을 먼저 0.75배로 늦추거나 이전 1.2배 파일에 다시 적용하지 않는다.
- 보조 프로그램은 원본과 기존 출력물을 덮어쓰지 않고 길이·배속 기록을 출력 옆 JSON에 저장한다. 별도 도구로 이미 가속한 파일은 기록이 없을 수 있으므로 원본 출처도 확인한다.
- 최종 가속 음성으로 발화 정렬을 수행한 뒤 자막과 장면 길이를 결정한다. 배경음악은 정상 속도로 반복하고 따로 믹싱한다.
- 제작정보에 엔진/모델, 선택 목소리, 요금제 구분, 원본 길이, 실제 1.2배 적용과 결과 길이를 기록한다. 생성 성공·목소리 선택·재생 확인을 구분한다. API 키는 기록하지 않는다.

## 이용 범위

무료 생성물은 상업 이용이 불가하며, 공개 제목에 `elevenlabs.io` 또는 `11.ai`를 표시한다. 구독 중 생성한 음성은 약관상 상업 이용이 가능하며, 무료 생성물에 유료 권한이 소급되지 않는다. Beta 서비스 등 예외는 [공식 이용 안내](https://help.elevenlabs.io/hc/en-us/articles/13313564601361-Can-I-publish-the-content-I-generate-on-the-platform)를 확인한다. 어떤 방식도 YouTube 수익화 승인을 보장하지 않는다.

이 설치 명령에는 Whisper 추가 설치가 포함되지 않는다. 자막 정렬은 클라우드 컴퓨터에 이미 있는 도구를 쓸 수 있고, 없으면 직접 확인·조정한 범위를 기록한다.
