# hyperframesshorts

**Hyperframes가 설치된 환경에서 한국어 쇼츠와 썸네일을 만드는 에이전트 스킬**입니다. 주제·후킹·장면 구성 → 동영상/이미지 생성 → 내레이션·자막 → 설명 도식 → 최종 MP4·썸네일·유튜브 제목/설명을 연결합니다.

사용자 제작 워크플로이며 [HeyGen Hyperframes](https://github.com/heygen-com/hyperframes) 공식 엔진과 별개입니다. 스킬 이름은 `hyperframesshorts`이므로 기존 `hyperframes` 스킬을 덮어쓰지 않습니다.

## AI에게 설치 요청하기

Codex 또는 Claude Code에 아래 문장을 전달하세요.

```text
https://github.com/aihubos/hyperframesshorts 저장소를 확인하고 README.md대로 내 에이전트에 설치해줘.
Hyperframes가 이미 있으면 재사용하고, 없을 때만 설치해줘. 기존 엔진을 업데이트하지 마.
기존 hyperframes 스킬은 보존하고 hyperframesshorts만 추가해줘.
설치된 SKILL.md를 직접 읽어 현재 요청부터 적용해줘.
macOS는 python3 install.py --setup, Windows는 py -3 install.py --setup으로 동일한 설치 흐름을 실행해줘.
처음에는 포함된 제작자 공유 목소리를 자동 등록해줘. 기존에 내가 선택한 목소리가 있으면 유지해줘.
나레이션은 생성 원본 대비 1.2배속을 한 번 적용하고 그 음성에 자막을 맞춰줘.
Flow는 Aside 브라우저와 컴퓨터 유즈를 우선 사용하고 화면을 점유하지 않는 백그라운드 방식으로 작업해줘.
Aside의 백그라운드 제어가 지원되지 않으면 그 제약을 알리고 다른 브라우저로 임의 전환하지 마.
영상·이미지 생성 도구와 내 계정 연결 상태도 확인해줘.
```

## 공통 설치 — macOS와 Windows

Git, Python 3, Node.js 22 이상, FFmpeg/ffprobe가 필요합니다. 없으면 아래 OS별 준비 명령으로 설치한 후 진행합니다. 공개 저장소를 받는 데 GitHub 계정이나 `gh` 설치는 필요하지 않습니다.

```bash
git clone https://github.com/aihubos/hyperframesshorts.git
cd hyperframesshorts
python3 install.py --setup
```

`--setup`은 기존 Hyperframes 탐색·재사용(없으면 설치) → 스킬 설치 → VoiceStudio 앱(Apple Silicon macOS / Windows x64)과 VoxCPM2 다운로드·선택까지 진행합니다. 최초 OS 실행 승인/앱 초기 설정 후 재실행이 필요할 수 있습니다. 첫 설치에서는 포함된 제작자 공유 목소리를 자동 등록하며 기존 선택은 유지합니다. [전체 음성 설정 안내](references/voice.md)를 확인하세요.

옵션 없는 `python3 install.py`는 **Codex 스킬만** `$CODEX_HOME/skills/hyperframesshorts` 또는 `~/.codex/skills/hyperframesshorts`에 복사합니다. 엔진 설치·업데이트, 로그인, 다른 스킬 설치를 수행하지 않습니다.

Claude Code 또는 공유 스킬 폴더를 사용한다면 필요한 대상 하나를 지정하세요.

```bash
# Claude Code
python3 install.py --skills-dir "$HOME/.claude/skills"

# 공유 에이전트 스킬 폴더를 사용하는 환경
python3 install.py --skills-dir "$HOME/.agents/skills"
```

앱마다 검색 경로가 다릅니다. 같은 스킬을 여러 검색 경로에 중복 설치할 필요는 없습니다. 자동 목록 반영은 앱 재시작 후 확인하세요. 즉시 적용하려면 AI에게 설치된 `SKILL.md`를 읽도록 요청하세요.

Git이 없는 경우 GitHub의 **Code → Download ZIP**으로 받아 압축을 풀고 그 폴더에서 `python3 install.py`를 실행해도 됩니다. Windows에서 Python 명령이 `py`라면 `py install.py`를 사용하세요. 실제 앱 연동 검증은 macOS에서 수행했습니다. Windows 경로·설치 분기는 모의 확인했으며 Windows PC의 첫 설치·음성 생성·렌더링은 아직 실기 검증하지 않았습니다.

## 다른 스킬도 필요한가요?

**별도 사용자 제작 스킬은 필수가 아닙니다.** 편집 규칙과 원리 설명 방식은 이 패키지에 포함되어 있습니다. `imagegen`, `ponytail`, `skill-creator` 등 보조 스킬을 함께 설치할 필요는 없습니다. 이미지 생성 **도구**와 스킬은 별개입니다.

| 필요한 환경 | 역할 |
| --- | --- |
| Codex/Claude Code 등 파일·명령 실행이 가능한 에이전트 | 스킬을 읽고 제작 실행 |
| 기존 Hyperframes + 해당 엔진의 Node.js·브라우저 | HTML 타임라인을 MP4로 출력 |
| FFmpeg 및 ffprobe | 음성 믹싱·길이 확인·영상 검증 |
| Omni Flash 360p 제공 서비스와 사용자 계정 | 실제 동영상 생성 |
| 이미지 생성 도구 또는 서비스 | 이미지·썸네일 생성, GPT 이미지 생성 우선 |
| VoiceStudio + VoxCPM2 및 선택한 목소리 | 로컬 한국어 내레이션, 원본 대비 1.2배속 |
| 필요 시 브라우저/컴퓨터 사용 도구 | 로그인된 생성 서비스 조작·다운로드 |
| 사용자 음악 파일·사용 가능한 한국어 폰트 | 배경음악과 자막 |

스킬 설치만으로 서비스 로그인·유료 구독·생성 도구가 생기지는 않습니다. 수신자는 자신의 계정으로 로그인하고 음악과 사용할 목소리를 지정해야 합니다. 기본 음악 파일은 저장소에 없으므로 원래 제작자와 똑같은 음악을 원하면 별도로 제공받아야 합니다.

자막은 실제 발화 시점에 맞춥니다. 정렬에는 환경에 이미 있는 Whisper 계열/강제 정렬 도구를 활용할 수 있으며, 특정 정렬 패키지를 필수 설치하지는 않습니다. 사용할 수 없는 경우 직접 확인·조정한 범위를 기록합니다.

## 사용 예시

```text
$hyperframesshorts로 잠자리의 후진 비행을 주제로 45초 쇼츠를 만들어줘.
초반 후킹을 강하게 하고 다양한 거리와 각도로 구성해줘.
동작은 Omni Flash 360p 영상, 원리는 움직이는 2D 설명 도식으로 보여줘.
내가 선택한 VoiceStudio 목소리와 첨부한 배경음악을 사용해줘.
최종 MP4·썸네일과 유튜브 제목·설명을 함께 전달해줘.
```

기본값은 45초 세로 쇼츠, Omni Flash 360p 생성 원본, 최종 1080×1920/30fps, VoiceStudio/VoxCPM2의 사용자 선택 음성 1.2배속, Wanted Sans 굵은 자막입니다. 사용자의 지정값이 우선합니다. 서비스에서 실제 모델/해상도를 확인하며 다른 모델로 임의 대체하지 않습니다.

- 비슷한 구도의 반복을 피하고 넓은 장면·근접·정면·사선·위/아래 각도를 섞습니다.
- 원리 구간에는 2D/3D 도해·표·그래프·설명 애니메이션 중 적합한 자료를 실제로 넣습니다.
- 자막은 글자 수 비율이 아닌 실제 발화에 맞춥니다. 불필요한 제작·검토 문구는 영상에 넣지 않습니다.
- 결과는 `~/Projects/Youtube/영상 제목/`에 저장합니다.
- 최종 채팅에는 영상·썸네일 링크와 **제목·설명 각각의 코드 블록**을 제공합니다.
- YouTube 업로드는 별도 요청 때만 수행합니다.

## 업데이트·백업

수정한 로컬 파일이 없다면 복제한 저장소에서 실행하세요. 로컬 수정이 있다면 먼저 보존하세요.

```bash
git pull --ff-only
python3 install.py
```

다른 설치 경로를 사용했다면 같은 `--skills-dir`를 다시 지정하세요. 이전 동명 스킬은 `~/.local/share/hyperframesshorts/backups/`에 보존하며 `restore.json`에 원래 경로가 기록됩니다. 기존 `hyperframes` 폴더와 프로젝트 엔진은 수정하지 않습니다.

## 엔진이 없는 사용자만 선택

먼저 Git, Python 3, Node.js 22 이상, FFmpeg/ffprobe를 준비하세요. macOS에서 Homebrew가 이미 있다면 `brew install git python node ffmpeg`를 사용할 수 있습니다. 다른 환경은 각 도구의 공식 OS별 설치 안내를 따르세요.

```bash
python3 install.py --setup-runtime
```

별도 경로 `~/.local/share/hyperframes/runtime`에 제작 호환 기준인 Hyperframes **0.8.35**를 설치하고 렌더링 브라우저를 준비합니다. 이미 이 경로에 엔진이 있으면 재사용합니다. 최신 버전임을 뜻하지 않으며 기존 프로젝트를 업데이트하지 않습니다.

## 포함 범위와 확인

MIT 라이선스로 배포하는 워크플로 문서와 설치 프로그램만 포함합니다. 공식 엔진·생성 모델·이미지·영상·음악·폰트는 포함하지 않으며 해당 서비스와 자산의 조건을 따릅니다. 공개 승인된 목소리 참조와 녹취는 `assets/voice/`에 포함합니다. API 키·쿠키·그 밖의 개인 파일은 포함하지 않습니다.

`python3 check_installer.py`로 임시 폴더에서 설치와 기존 폴더/심볼릭 링크 보존을 확인할 수 있습니다. 패키지와 설치 확인은 수신자 계정에서 실제 영상 생성·렌더링까지 성공했다는 의미는 아닙니다.

음성 자동 설정 확인: `python3 check_voice.py`. 앱 최초 설치와 다른 OS는 별도 환경에서 검증이 필요합니다. 제작자 공유 목소리는 [assets/voice](assets/voice/)에 포함되어 자동 등록됩니다. `python3 scripts/setup_voice.py --bundled-voice`로 명시적으로 선택할 수도 있습니다.

## Flow 브라우저 기본값

**Aside 우선·백그라운드 작업**입니다. 스킬이 브라우저 연결 기능을 설치하는 것은 아닙니다. 현재 Aside 앱 화면 읽기는 확인했지만 완전한 백그라운드 입력·생성·다운로드는 미검증입니다. 지원되지 않으면 화면을 임의로 점유하거나 다른 브라우저로 전환하지 않고 필요한 선택만 안내합니다. [동작 기준](references/production.md#aside와-백그라운드-작업)을 참고하세요.

## Windows 10/11 x64 설치

macOS와 동일한 흐름입니다: **기본 도구 확인 → Hyperframes 재사용/설치 → 스킬 → VoiceStudio → VoxCPM2 → 공유 목소리 → 나레이션 1.2배속**. Whisper는 이 설치 명령에서 별도 설치하지 않습니다.

Git, Python 3, FFmpeg/ffprobe가 없다면 PowerShell에서 필요한 항목만 설치하세요. 엔진도 준비할 경우 Node.js 22 이상이 필요합니다.

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.11 -e
winget install --id Gyan.FFmpeg -e
winget install --id OpenJS.NodeJS.LTS -e
```

설치 후 PowerShell을 새로 열고 실행합니다. 이미 받은 저장소는 다시 복제하지 않고 `git pull --ff-only`로 업데이트합니다.

```powershell
git clone https://github.com/aihubos/hyperframesshorts.git
cd hyperframesshorts
py -3 install.py --setup
```

VoiceStudio가 없으면 공식 **0.5.2 Current User MSI**를 받아 사용자별로 설치하고 실행합니다. 기존 설치는 재사용합니다. 초기 앱 설정·OS 승인·네트워크 다운로드가 끝나지 않으면 안내에 따라 같은 명령을 다시 실행하세요. 자동 재부팅이나 보안 설정 변경은 하지 않습니다. Windows ARM/32비트는 자동 설치 대상이 아닙니다.

- 스킬: `%USERPROFILE%\.codex\skills\hyperframesshorts` (`CODEX_HOME` 지정 시 해당 경로 사용)
- 설정: `%USERPROFILE%\.config\hyperframesshorts\voice.json`
- 영상 저장: `%USERPROFILE%\Projects\Youtube\영상 제목`
- VoiceStudio Python: `%LOCALAPPDATA%\com.debpalash.omnivoice-studio\project\.venv\Scripts\python.exe`
- 사용자 지정 환경: `HYPERFRAMES_VOICESTUDIO_APP`에 앱 EXE, `HYPERFRAMES_VOICESTUDIO_PYTHON`에 실제 Python 경로를 지정할 수 있습니다. 관리 환경의 `uv`를 재사용합니다.

Flow 로그인, Aside 설치·제어 연결, 음악·폰트는 별도 준비합니다. Windows에서도 Aside 우선 규칙은 같지만 Aside의 해당 OS 지원 및 도구 연결을 확인해야 합니다. 앱 설치만으로 백그라운드 브라우저 제어가 가능해지지는 않습니다.

## 두 OS의 동일한 setup 순서

Docker 없이 각 OS에 직접 설치합니다. 차이는 Python 실행 명령과 앱 설치 파일(.app / MSI)뿐입니다.

| 단계 | macOS Apple Silicon / Windows x64 공통 동작 |
| --- | --- |
| 1 | Node.js 22+, FFmpeg, ffprobe 확인. 없으면 준비 방법을 알리고 중단 |
| 2 | 지정 runtime 경로·현재 폴더의 상위 프로젝트·PATH에서 Hyperframes 탐색, 기존 엔진 재사용 또는 없을 때 0.8.35 설치 |
| 3 | 렌더링 브라우저 준비, 기존 스킬 백업 후 설치 |
| 4 | 기존 VoiceStudio 재사용 또는 공식 앱 설치·실행 |
| 5 | VoxCPM2 준비, 기존 목소리 유지 또는 포함된 공유 목소리 등록 |
| 6 | 내레이션 원본 대비 1.2배속 설정 저장 |

```bash
# macOS (Homebrew가 있는 경우, 없는 기본 도구만 준비)
brew install git python node ffmpeg
python3 install.py --setup
```

```powershell
# Windows (위 winget 준비 후 새 PowerShell에서)
py -3 install.py --setup
```

기존 엔진이 자동 탐색 범위 밖에 있으면 `--runtime-dir "기존 프로젝트 경로"`를 함께 지정하세요. 최초 VoiceStudio 설정이 끝나지 않았다면 화면에서 완료하고 같은 setup 명령으로 재개합니다. 서비스 로그인·음악·폰트 준비는 두 OS 모두 별도입니다. Whisper와 Docker는 설치하지 않습니다.

기존 세부 옵션도 유지합니다: 옵션 없음은 스킬만 설치, `--setup-voice`는 스킬+음성 환경만, `--setup-runtime`은 지정된 별도 엔진 환경을 준비합니다.
