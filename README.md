# hyperframesshorts

**원격 Linux 클라우드 컴퓨터에 설치해 한국어 쇼츠와 썸네일을 만드는 에이전트 스킬**입니다. 학생의 Mac/Windows PC가 아니라, 학생이 사용하는 클라우드 머신에서 주제·후킹·장면 구성 → 동영상/이미지 생성 → 내레이션·자막 → 설명 도식 → 최종 MP4·썸네일·유튜브 제목/설명을 연결합니다.

사용자 제작 워크플로이며 [HeyGen Hyperframes](https://github.com/heygen-com/hyperframes) 공식 엔진과 별개입니다. 스킬 이름은 `hyperframesshorts`이므로 기존 `hyperframes` 스킬을 덮어쓰지 않습니다.

## AI에게 설치 요청하기

Codex 또는 Claude Code에 아래 문장을 전달하세요. 에이전트는 클라우드 컴퓨터의 터미널에서 실행합니다.

```text
https://github.com/aihubos/hyperframesshorts 저장소를 확인하고 README.md대로 클라우드 컴퓨터(원격 Linux 머신)에 설치해줘.
학생의 Mac/Windows PC에는 설치하지 마.
Hyperframes가 이미 클라우드 컴퓨터에 있으면 재사용하고, 없을 때만 설치해줘. 기존 엔진을 업데이트하지 마.
기존 hyperframes 스킬은 보존하고 hyperframesshorts만 추가해줘.
설치된 SKILL.md를 직접 읽어 현재 요청부터 적용해줘.
클라우드 컴퓨터에서 python3 install.py --setup 을 실행해줘.
먼저 음성 방식 1. ElevenLabs 무료 API 2. ElevenLabs 구독 중 하나를 나에게 물어봐줘.
효과음은 별도 요청이 없으면 추가하지 마.
선택한 값을 --voice-provider elevenlabs-free 또는 elevenlabs-paid로 전달해줘.
ELEVENLABS_API_KEY는 클라우드 컴퓨터의 환경변수로만 사용해. API 키를 채팅으로 요청하거나 명령 인수·저장소에 넣지 마.
선택한 요금제와 API 계정의 요금제가 다르면 중단하고, 다른 방식으로 바꾸지 마.
나레이션은 생성 원본 대비 1.2배속을 한 번 적용하고 그 음성에 자막을 맞춰줘.
Flow는 Aside 브라우저와 컴퓨터 유즈를 우선 사용하고 화면을 점유하지 않는 백그라운드 방식으로 작업해줘.
Aside의 백그라운드 제어가 지원되지 않으면 그 제약을 알리고 다른 브라우저로 임의 전환하지 마.
영상·이미지 생성 도구와 내 계정 연결 상태도 확인해줘.
```

## 클라우드 컴퓨터 준비 — Linux

필요한 도구는 Git, Python 3, Node.js 22 이상(`npm` 포함), FFmpeg, ffprobe입니다. 공개 저장소를 받는 데 GitHub 계정이나 `gh` 설치는 필요하지 않습니다. 아래 확인은 클라우드 컴퓨터의 터미널에서 합니다.

```bash
git --version
python3 --version
node --version
npm --version
ffmpeg -version
ffprobe -version
```

`node --version`이 v22 미만이거나 명령이 없으면 [Node.js 배포 페이지](https://nodejs.org/en/download)에서 22 이상을 설치합니다. `npm`은 그 Node.js 설치에 포함되어야 합니다. 배포판 저장소의 `nodejs` 패키지는 22보다 낮을 수 있으므로 설치 후 버전을 다시 확인합니다.

Debian/Ubuntu 계열 클라우드 이미지에서 Git, Python 3, FFmpeg를 받는 예시입니다. `ffmpeg` 패키지에 ffprobe가 함께 들어 있습니다. 다른 배포판은 그 배포판의 패키지 관리자를 사용합니다.

```bash
sudo apt-get update
sudo apt-get install -y git python3 ffmpeg
```

이 문서의 apt 예시는 새 클라우드 이미지에서 처음부터 실행해 확인하지 않았습니다. 이 변경을 작성한 환경에 이미 있던 도구는 아래 [확인한 범위](#확인한-범위)에 적습니다.

## 설치

저장소를 클라우드 컴퓨터에 받은 뒤 설치합니다. 경로는 그 컴퓨터의 홈 디렉터리 기준입니다.

```bash
git clone https://github.com/aihubos/hyperframesshorts.git
cd hyperframesshorts
python3 install.py --setup
```

`--setup`은 음성 방식을 묻고, 기존 Hyperframes 재사용(없으면 설치) → 스킬 설치 → ElevenLabs 연결 순서로 진행합니다. Linux가 아닌 환경에서 `--setup`을 실행하면 설치 전에 중단합니다. 설치 폴더는 자동 지정합니다.

| 선택 | 비용·이용 범위 | 연결 |
| --- | --- | --- |
| 1. ElevenLabs 무료 API (`elevenlabs-free`) | 무료 한도 내, 수익화 불가, 공개 시 출처 표시 | API 키 → 무료 요금제 확인 → 목소리 연결 |
| 2. ElevenLabs 구독 (`elevenlabs-paid`) | 유료, 구독 중 생성한 음성의 상업 이용 가능(약관 적용) | API 키 → 구독 요금제 확인 → 목소리 연결 |

API 연결 실패나 요금제 불일치 시 다른 방식으로 바꾸지 않고 중단합니다. 무료로 만든 음성은 나중에 구독해도 상업 이용 권한이 소급되지 않습니다.

AI가 대신 설치할 때는 먼저 위 두 가지를 사용자에게 물어본 뒤 실행하세요. 비대화형 실행에 선택값이 없으면 설치 전에 중단합니다.

```bash
python3 install.py --setup --voice-provider elevenlabs-free --elevenlabs-voice-id 선택한_ID
python3 install.py --setup --voice-provider elevenlabs-paid --elevenlabs-voice-id 선택한_ID
```

ElevenLabs는 클라우드 컴퓨터의 환경변수 `ELEVENLABS_API_KEY`를 먼저 설정합니다. 키를 채팅·명령 인수·저장소에 넣지 않습니다. 연결 시 계정/목소리 읽기 권한, 제작 시 Text to Speech 권한이 필요합니다. 설치에서는 과금되는 음성을 생성하지 않으므로 실제 생성 가능 여부는 별도 샘플로 확인합니다. [API 연결 및 음성 설정 안내](references/voice.md)를 따르세요.

무료 공개물에는 제목에 `elevenlabs.io` 또는 `11.ai`를 표시합니다. 유료의 Beta 서비스 등 예외는 [ElevenLabs 공식 이용 안내](https://help.elevenlabs.io/hc/en-us/articles/13313564601361-Can-I-publish-the-content-I-generate-on-the-platform)를 따릅니다.

옵션 없는 `python3 install.py`는 **Codex 스킬만** `$CODEX_HOME/skills/hyperframesshorts` 또는 `~/.codex/skills/hyperframesshorts`에 복사합니다. 엔진 설치·업데이트, 로그인, 다른 스킬 설치를 수행하지 않습니다.

Claude Code 또는 공유 스킬 폴더를 사용한다면 필요한 대상 하나를 지정하세요.

```bash
# Claude Code
python3 install.py --skills-dir "$HOME/.claude/skills"

# 공유 에이전트 스킬 폴더를 사용하는 환경
python3 install.py --skills-dir "$HOME/.agents/skills"
```

앱마다 검색 경로가 다릅니다. 같은 스킬을 여러 검색 경로에 중복 설치할 필요는 없습니다. 자동 목록 반영은 앱 재시작 후 확인하세요. 즉시 적용하려면 AI에게 설치된 `SKILL.md`를 읽도록 요청하세요.

Git이 없는 경우 GitHub의 **Code → Download ZIP**으로 클라우드 컴퓨터에 받아 압축을 풀고, 그 폴더에서 `python3 install.py`를 실행해도 됩니다.

## 다른 스킬도 필요한가요?

**별도 사용자 제작 스킬은 필수가 아닙니다.** 편집 규칙과 원리 설명 방식은 이 패키지에 포함되어 있습니다. `imagegen`, `ponytail`, `skill-creator` 등 보조 스킬을 함께 설치할 필요는 없습니다. 이미지 생성 **도구**와 스킬은 별개입니다.

| 필요한 환경 | 역할 |
| --- | --- |
| 클라우드 컴퓨터의 Codex/Claude Code 등 파일·명령 실행이 가능한 에이전트 | 스킬을 읽고 제작 실행 |
| 그 컴퓨터의 Hyperframes + 해당 엔진의 Node.js·브라우저 | HTML 타임라인을 MP4로 출력 |
| FFmpeg 및 ffprobe | 음성 믹싱·길이 확인·영상 검증 |
| Flow Omni 1.1 Flash 360p 제공 서비스와 사용자 계정 | 실제 동영상 생성 |
| 이미지 생성 도구 또는 서비스 | 이미지·썸네일 생성, GPT 이미지 생성 우선 |
| ElevenLabs 무료 API 또는 구독 API | 한국어 내레이션, 원본 대비 1.2배속 |
| 필요 시 브라우저/컴퓨터 사용 도구 | 로그인된 생성 서비스 조작·다운로드 |
| 포함된 기본 음악·사용 가능한 한국어 폰트 | 배경음악과 자막 |

스킬 설치만으로 서비스 로그인·유료 구독·생성 도구가 생기지는 않습니다. 수신자는 자신의 서비스 계정으로 로그인합니다. 기본 배경음악이 포함되어 있으며, 별도 지정이 없으면 같은 음악을 사용합니다. 목소리는 사용자의 ElevenLabs Voices에서 고릅니다.

### 오디오 기본 구성

쇼츠는 내레이션과 배경음악을 기본으로 사용합니다. 사용자가 별도로 요청한 경우에만 효과음을 추가하며, 장면 전환이나 강조만으로 넣지 않습니다.

선택한 ElevenLabs 목소리와 승인된 BGM을 유지합니다. 새 음악을 요청하면 사용자가 지정한 서비스를 우선 사용하고, 유료 생성은 모델·개수·규격·예상 비용·현재 잔액을 제시한 뒤 승인받습니다. 음악 요청이 없으면 포함된 기본 BGM을 유지합니다.

자막은 실제 발화 시점에 맞춥니다. 정렬에는 클라우드 컴퓨터에 이미 있는 Whisper 계열/강제 정렬 도구를 활용할 수 있으며, 특정 정렬 패키지를 필수 설치하지는 않습니다. 사용할 수 없는 경우 직접 확인·조정한 범위를 기록합니다.

## 최근 제작 방식

- 주제 10개 제안 → 사용자 선택 → 첫 3초 훅·기승전결·영상 개수·비용 브리핑
- 기본 8초 클립 5개, 기준 이미지 실제 첨부, Flow 360p → 실제 720p 업스케일 각각 저장
- 기존 Hypit/Hyperframes 편집 프로젝트 재사용, 45초 세로 영상
- 선택한 ElevenLabs 음성과 BGM 유지, 발화에 맞춘 배경 없는 자막, 불필요한 AI 고지 화면 자막 제외
- 상단 파란 큰 제목 제외, 하단 자막 문장 마침표 제거, 자막은 조금 아래로 배치하되 하단 여백 유지
- 영상·생성 썸네일·제목·설명 전달, 제목에 관련 해시태그 1~2개와 #Shorts
- 예약 자동화는 별도 연결·승인 후 사용. [주제 제안·제작·예약 운영](references/shorts-workflow.md)

## 사용 예시

```text
$hyperframesshorts로 잠자리의 후진 비행을 주제로 45초 쇼츠를 만들어줘.
초반 후킹을 강하게 하고 다양한 거리와 각도로 구성해줘.
동작은 Flow Omni 1.1 Flash 360p 영상, 원리는 움직이는 2D 설명 도식으로 보여줘.
내가 선택한 ElevenLabs 목소리와 포함된 기본 배경음악을 사용해줘.
최종 MP4·썸네일과 유튜브 제목·설명을 함께 전달해줘.
```

기본값은 45초 세로 쇼츠, Flow Omni 1.1 Flash 360p 생성 → 실제 720p 업스케일 저장, 최종 1080×1920/30fps, 선택한 ElevenLabs 음성의 1.2배속, 배경 상자 없는 Pretendard Bold 자막입니다. 사용자의 지정값이 우선합니다. 서비스에서 실제 모델/해상도를 확인하며 다른 모델로 임의 대체하지 않습니다.

- 비슷한 구도의 반복을 피하고 넓은 장면·근접·정면·사선·위/아래 각도를 섞습니다.
- 원리 구간에는 2D/3D 도해·표·그래프·설명 애니메이션 중 적합한 자료를 실제로 넣습니다.
- 자막은 글자 수 비율이 아닌 실제 발화에 맞춥니다. 불필요한 제작·검토 문구는 영상에 넣지 않습니다.
- 결과는 클라우드 컴퓨터의 `~/Projects/Youtube/영상 제목/`에 저장합니다.
- 최종 채팅에는 영상·썸네일 링크와 **제목·설명 각각의 코드 블록**을 제공합니다.
- YouTube 업로드는 별도 요청 때만 수행합니다.

## 업데이트·백업

클라우드 컴퓨터에서 저장소 파일을 직접 수정하지 않았다면 복제한 저장소에서 실행하세요. 직접 수정했다면 먼저 보존하세요.

```bash
git pull --ff-only
python3 install.py
```

다른 설치 경로를 사용했다면 같은 `--skills-dir`를 다시 지정하세요. 이전 동명 스킬은 `~/.local/share/hyperframesshorts/backups/`에 보존하며 `restore.json`에 원래 경로가 기록됩니다. 기존 `hyperframes` 폴더와 프로젝트 엔진은 수정하지 않습니다.

## 엔진이 없는 경우

먼저 위의 Git, Python 3, Node.js 22 이상, FFmpeg/ffprobe를 클라우드 컴퓨터에 준비하세요.

```bash
python3 install.py --setup-runtime
```

별도 경로 `~/.local/share/hyperframes/runtime`에 제작 호환 기준인 Hyperframes **0.8.35**를 설치하고 렌더링 브라우저를 준비합니다. 이미 이 경로에 엔진이 있으면 재사용합니다. 최신 버전임을 뜻하지 않으며 기존 프로젝트를 업데이트하지 않습니다. 이 명령의 실제 npm 설치와 브라우저 준비는 [확인한 범위](#확인한-범위)를 보세요.

## 포함 범위와 확인한 범위

워크플로 문서와 설치 프로그램은 MIT 라이선스입니다. 공식 엔진·생성 모델·폰트는 별도이며, 포함된 음악·제작 예시 미디어는 각 자산의 이용 조건을 따릅니다. 기본 음악 원본은 `assets/music/`에 포함합니다. API 키·쿠키·그 밖의 개인 파일은 포함하지 않습니다.

`python3 check_installer.py`로 임시 폴더에서 설치와 기존 폴더/심볼릭 링크 보존을 확인할 수 있습니다. `python3 check_voice.py`는 ElevenLabs 요금제 일치, 설정 파일에 API 키를 남기지 않는 것, 나레이션 1.2배속을 확인합니다. 패키지와 이 확인이 수신자 계정에서 실제 영상 생성·렌더링·음성 생성까지 성공했다는 의미는 아닙니다.

### 확인한 범위

이 변경을 작성한 환경은 Ubuntu 24.04.5 LTS, Linux x86_64입니다. 그 환경에 이미 있던 도구는 Git 2.43.0, Python 3.12.3, Node.js 22.23.4, npm, FFmpeg/ffprobe 6.1.1입니다. 같은 환경에서 아래를 실행했습니다.

- `python3 check_installer.py` 통과: 기존 스킬 보존, 엔진을 설치하지 않는 스킬 전용 설치, `--setup`이 기존 엔진을 재사용하고 `elevenlabs-free`로 이어지는 것, Linux가 아닌 환경과 `local` 음성 선택이 중단되는 것
- `python3 check_voice.py` 통과: 두 ElevenLabs 요금제, 요금제 불일치와 연결 실패 시 기존 설정 유지, API 키를 파일에 남기지 않는 것, 예전 로컬 음성 설정을 재사용하지 않는 것, FFmpeg로 6초 원본이 1.2배속 후 약 5초가 되는 것
- 표준 입력이 없는 `python3 install.py --setup`은 음성 방식을 확인하지 못하면 설치 전에 종료합니다. 확인한 종료 코드는 1입니다
- 임시 경로에서 `python3 install.py --setup-runtime --runtime-dir <임시 경로>`를 실행했습니다. npm이 Hyperframes 0.8.35를 설치했고, `hyperframes --version`이 `0.8.35`를 출력했습니다. `browser ensure`는 Chrome Headless Shell을 받은 뒤 `Ready to render`를 출력했습니다

확인하지 않은 것:

- 비어 있는 클라우드 이미지에서 `apt-get`과 Node.js 22를 처음부터 설치하는 과정
- Hyperframes로 실제 MP4를 렌더하는 과정
- ElevenLabs 실제 계정 연결, 음성 생성, 요금제 응답. 키를 사용하지 않았습니다
- 이 Linux 환경에서 Aside 연결
- 학생의 Mac/Windows PC 설치. 그 경로는 이 저장소의 설치 대상이 아닙니다

## Flow 브라우저 기본값

**Aside 우선·백그라운드 작업**입니다. 스킬이 브라우저 연결 기능을 설치하는 것은 아닙니다. 최근 제작에서는 Aside CLI를 사용하는 Flow 제작 흐름과 720p·1080p 파일 저장 기록을 확인했습니다. 그 기록을 이 Linux 클라우드 컴퓨터의 Aside 연결 성공으로 보지 않습니다. 매 실행에서 이 컴퓨터의 CLI와 연결 상태를 확인합니다. 지원되지 않으면 화면을 임의로 점유하거나 다른 브라우저로 전환하지 않고 필요한 선택만 안내합니다. [동작 기준](references/production.md#aside와-백그라운드-작업)을 참고하세요.

## setup 순서

음성 방식을 선택한 뒤 클라우드 컴퓨터에서 진행합니다.

| 단계 | 동작 |
| --- | --- |
| 1 | Linux 확인. Git, Python 3, Node.js 22+, npm, FFmpeg, ffprobe 확인. 없으면 README대로 준비하고 중단 |
| 2 | 지정 runtime 경로·현재 폴더의 상위 프로젝트·PATH에서 Hyperframes 탐색, 기존 엔진 재사용 또는 없을 때 0.8.35 설치 |
| 3 | 렌더링 브라우저 준비, 기존 스킬 백업 후 설치 |
| 4 | `ELEVENLABS_API_KEY`와 선택한 무료/구독 요금제 확인. 불일치나 연결 실패 시 중단 |
| 5 | 사용자가 고른 목소리 ID 연결. API 키는 `voice.json`에 저장하지 않음 |
| 6 | 내레이션 원본 대비 1.2배속 설정 저장 |

```bash
python3 install.py --setup
```

기존 엔진이 자동 탐색 범위 밖에 있으면 `--runtime-dir "기존 프로젝트 경로"`를 함께 지정하세요. Flow 로그인·폰트 준비는 별도이며 기본 음악은 함께 설치됩니다. Whisper와 Docker는 설치하지 않습니다.

클라우드 컴퓨터의 주요 경로:

- 스킬: `$CODEX_HOME/skills/hyperframesshorts` 또는 `~/.codex/skills/hyperframesshorts`
- 음성 설정: `~/.config/hyperframesshorts/voice.json`
- 영상 저장: `~/Projects/Youtube/영상 제목`
- 엔진이 없을 때의 설치 위치: `~/.local/share/hyperframes/runtime`

기존 세부 옵션도 유지합니다. 옵션 없음은 스킬만 설치하고, `--setup-voice`는 스킬과 ElevenLabs 연결만, `--setup-runtime`은 지정된 별도 엔진 환경을 준비합니다.

## 기본 배경음악

별도 지정이 없는 쇼츠는 [기본 음악 WAV](assets/music/2026-09-01_12-02-40_create-a-bright-warm-playful-background-.wav)를 사용합니다. 설치된 스킬의 `assets/music/`에 포함됩니다. 정상 속도로 반복하고 내레이션보다 낮게 믹싱합니다. 다른 음악 또는 무음악 지시가 우선합니다.
