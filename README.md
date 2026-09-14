# hyperframesshorts

**Hyperframes가 설치된 환경에서 한국어 쇼츠와 썸네일을 만드는 에이전트 스킬**입니다. 주제·후킹·장면 구성 → 동영상/이미지 생성 → 내레이션·자막 → 설명 도식 → 최종 MP4·썸네일·유튜브 제목/설명을 연결합니다.

사용자 제작 워크플로이며 [HeyGen Hyperframes](https://github.com/heygen-com/hyperframes) 공식 엔진과 별개입니다. 스킬 이름은 `hyperframesshorts`이므로 기존 `hyperframes` 스킬을 덮어쓰지 않습니다.

## AI에게 설치 요청하기

Codex 또는 Claude Code에 아래 문장을 전달하세요.

```text
https://github.com/aihubos/hyperframesshorts 저장소를 확인하고 README.md대로 내 에이전트에 설치해줘.
Hyperframes는 이미 설치되어 있으니 기존 엔진을 재사용하고 엔진을 재설치하거나 업데이트하지 마.
기존 hyperframes 스킬은 보존하고 hyperframesshorts만 추가해줘.
설치된 SKILL.md를 직접 읽어 현재 요청부터 적용해줘.
영상 생성·이미지 생성·ElevenLabs에 필요한 도구와 내 계정 연결 상태도 확인해줘.
```

## 직접 설치 — Hyperframes가 이미 있는 경우

Git과 Python 3가 필요합니다. 공개 저장소를 받는 데 GitHub 계정이나 `gh` 설치는 필요하지 않습니다.

```bash
git clone https://github.com/aihubos/hyperframesshorts.git
cd hyperframesshorts
python3 install.py
```

기본 설치는 **Codex 스킬만** `$CODEX_HOME/skills/hyperframesshorts` 또는 `~/.codex/skills/hyperframesshorts`에 복사합니다. 엔진 설치·업데이트, 로그인, 다른 스킬 설치를 수행하지 않습니다.

Claude Code 또는 공유 스킬 폴더를 사용한다면 필요한 대상 하나를 지정하세요.

```bash
# Claude Code
python3 install.py --skills-dir "$HOME/.claude/skills"

# 공유 에이전트 스킬 폴더를 사용하는 환경
python3 install.py --skills-dir "$HOME/.agents/skills"
```

앱마다 검색 경로가 다릅니다. 같은 스킬을 여러 검색 경로에 중복 설치할 필요는 없습니다. 자동 목록 반영은 앱 재시작 후 확인하세요. 즉시 적용하려면 AI에게 설치된 `SKILL.md`를 읽도록 요청하세요.

Git이 없는 경우 GitHub의 **Code → Download ZIP**으로 받아 압축을 풀고 그 폴더에서 `python3 install.py`를 실행해도 됩니다. Windows에서 Python 명령이 `py`라면 `py install.py`를 사용하세요. 설치 프로그램의 실제 실행 검증 환경은 macOS이며 다른 OS에서의 렌더링까지 검증한 것은 아닙니다.

## 다른 스킬도 필요한가요?

**별도 사용자 제작 스킬은 필수가 아닙니다.** 편집 규칙과 원리 설명 방식은 이 패키지에 포함되어 있습니다. `imagegen`, `ponytail`, `skill-creator` 등 보조 스킬을 함께 설치할 필요는 없습니다. 이미지 생성 **도구**와 스킬은 별개입니다.

| 필요한 환경 | 역할 |
| --- | --- |
| Codex/Claude Code 등 파일·명령 실행이 가능한 에이전트 | 스킬을 읽고 제작 실행 |
| 기존 Hyperframes + 해당 엔진의 Node.js·브라우저 | HTML 타임라인을 MP4로 출력 |
| FFmpeg 및 ffprobe | 음성 믹싱·길이 확인·영상 검증 |
| Omni Flash 360p 제공 서비스와 사용자 계정 | 실제 동영상 생성 |
| 이미지 생성 도구 또는 서비스 | 이미지·썸네일 생성, GPT 이미지 생성 우선 |
| ElevenLabs 계정 또는 사용자가 제공한 음성 파일 | Viraj 또는 지정 목소리 |
| 필요 시 브라우저/컴퓨터 사용 도구 | 로그인된 생성 서비스 조작·다운로드 |
| 사용자 음악 파일·사용 가능한 한국어 폰트 | 배경음악과 자막 |

스킬 설치만으로 서비스 로그인·유료 구독·생성 도구가 생기지는 않습니다. 수신자는 자신의 계정으로 로그인하고 음악과 사용할 목소리를 지정해야 합니다. 기본 음악 파일은 저장소에 없으므로 원래 제작자와 똑같은 음악을 원하면 별도로 제공받아야 합니다.

자막은 실제 발화 시점에 맞춥니다. 정렬에는 환경에 이미 있는 Whisper 계열/강제 정렬 도구를 활용할 수 있으며, 특정 정렬 패키지를 필수 설치하지는 않습니다. 사용할 수 없는 경우 직접 확인·조정한 범위를 기록합니다.

## 사용 예시

```text
$hyperframesshorts로 잠자리의 후진 비행을 주제로 45초 쇼츠를 만들어줘.
초반 후킹을 강하게 하고 다양한 거리와 각도로 구성해줘.
동작은 Omni Flash 360p 영상, 원리는 움직이는 2D 설명 도식으로 보여줘.
내 ElevenLabs 목소리와 첨부한 배경음악을 사용해줘.
최종 MP4·썸네일과 유튜브 제목·설명을 함께 전달해줘.
```

기본값은 45초 세로 쇼츠, Omni Flash 360p 생성 원본, 최종 1080×1920/30fps, Viraj 음성, Wanted Sans 굵은 자막입니다. 사용자의 지정값이 우선합니다. 서비스에서 실제 모델/해상도를 확인하며 다른 모델로 임의 대체하지 않습니다.

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

MIT 라이선스로 배포하는 워크플로 문서와 설치 프로그램만 포함합니다. 공식 엔진·생성 모델·이미지·영상·음성·음악·폰트는 포함하지 않으며 해당 서비스와 자산의 조건을 따릅니다. API 키·쿠키·개인 파일도 포함하지 않습니다.

`python3 check_installer.py`로 임시 폴더에서 설치와 기존 폴더/심볼릭 링크 보존을 확인할 수 있습니다. 패키지와 설치 확인은 수신자 계정에서 실제 영상 생성·렌더링까지 성공했다는 의미는 아닙니다.
