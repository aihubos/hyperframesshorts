"""Optional Agent Audio setup using its upstream installer and a conservative resource gate."""
import ctypes
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

REPOSITORY = 'https://github.com/AIEGOBOT/agent-audio.git'
REVISION = '975d804594f515e81cdb8858587af5469cf78ebf'
DEFAULT_SOURCE = Path.home() / '.local/share/agent-audio/source'
GIB = 1024 ** 3


def total_memory():
    try:
        if platform.system() == 'Darwin':
            return int(subprocess.check_output(['sysctl', '-n', 'hw.memsize'], text=True)) / GIB
        if platform.system() == 'Windows':
            class MemoryStatus(ctypes.Structure):
                _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
                    (name, ctypes.c_ulonglong) for name in
                    ('total', 'available', 'page_total', 'page_available', 'virtual_total', 'virtual_available', 'extended')]
            status = MemoryStatus()
            status.length = ctypes.sizeof(status)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return None
            return status.total / GIB
        return os.sysconf('SC_PHYS_PAGES') * os.sysconf('SC_PAGE_SIZE') / GIB
    except (OSError, ValueError, AttributeError, subprocess.CalledProcessError):
        return None


def free_disk(path):
    path = path.expanduser().absolute()
    while not path.exists():
        path = path.parent
    return shutil.disk_usage(path).free / GIB


def resources(source):
    apple = platform.system() == 'Darwin' and platform.machine().lower() in ('arm64', 'aarch64')
    supported = apple or (platform.system() == 'Windows' and platform.machine().lower() in ('amd64', 'x86_64'))
    data = Path(os.environ.get('AGENT_AUDIO_HOME', str(Path.home() / '.agent-audio')))
    return {'supported': supported, 'ram': total_memory(), 'ram_required': 24 if apple else 32,
            'disk': min(free_disk(source), free_disk(data)), 'disk_required': 25}


def eligible(info):
    return (info['supported'] and info['ram'] is not None
            and info['ram'] >= info['ram_required'] and info['disk'] >= info['disk_required'])


def select_audio(selected=None, source=DEFAULT_SOURCE):
    if selected == 'none' or (selected is None and not sys.stdin.isatty()):
        print('Agent Audio: 설치 안 함 (기본값).')
        return 'none'
    info = resources(source)
    ram = '확인 불가' if info['ram'] is None else f"{info['ram']:.1f} GiB"
    print(f"Agent Audio 효과음: RAM {ram}, 설치 경로 여유 {info['disk']:.1f} GiB")
    print(f"이 설치기의 보수적 기준: RAM {info['ram_required']} GiB, 디스크 여유 25 GiB 이상.")
    print('검증된 최소 사양이나 생성 속도 보장이 아닙니다. 실행 전 가용 메모리도 확인하세요.')
    print('모델 약 6.9–7.4 GB + 실행 환경·캐시 다운로드. 로컬 연산·전력 사용, 별도 API 생성료 없음.')
    print('모델 이용 약관·필요한 인증은 사용자가 직접 진행합니다. 자동 동의하지 않습니다.')
    if not info['supported']:
        print('자동 설치 대상: Apple Silicon macOS 또는 Windows x64. 다른 환경은 공식 안내로 별도 확인하세요.')
    if selected is None:
        print('1. 설치 안 함 (기본값)\n2. Agent Audio 로컬 효과음 설치')
        choice = input('선택 [1/2, 기본 1]: ').strip() or '1'
        if choice not in ('1', '2'):
            raise ValueError('1 또는 2를 선택하세요.')
        selected = 'none' if choice == '1' else 'agent-audio'
    if selected not in ('none', 'agent-audio'):
        raise ValueError('Unknown audio provider.')
    if selected == 'agent-audio' and not eligible(info):
        raise RuntimeError('Agent Audio 설치 기준 미달 또는 자원 확인 불가. 다운로드하지 않습니다. --audio-provider none으로 계속하거나 자원 확보 후 재실행하세요.')
    return selected


def setup_audio(source=DEFAULT_SOURCE):
    source = source.expanduser().absolute()
    # Voice/model setup may have consumed disk space since the initial choice.
    if not eligible(resources(source)):
        raise RuntimeError('현재 Agent Audio 설치 자원이 부족합니다. 기존 파일을 유지하고 효과음 설치를 중단합니다.')
    for tool in ('git', 'uv'):
        if not shutil.which(tool):
            raise RuntimeError(f'{tool}이 필요합니다. 설치 후 --setup-audio --audio-provider agent-audio로 재개하세요.')
    if source.exists():
        origin = subprocess.check_output(['git', '-C', str(source), 'remote', 'get-url', 'origin'], text=True).strip()
        revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        changed = subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True).strip()
        if origin != REPOSITORY or revision != REVISION or changed:
            raise RuntimeError('기존 Agent Audio 소스가 이 설치기의 기준 버전과 다르거나 수정되어 있습니다. 보존했으므로 공식 업데이트 안내를 확인하세요.')
    else:
        source.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'clone', REPOSITORY, str(source)], check=True)
        subprocess.run(['git', '-C', str(source), 'checkout', '--detach', REVISION], check=True)
    subprocess.run(['uv', 'sync', '--frozen'], cwd=source, check=True)
    for mode in ('--doctor', '--runtime-only', '--register-only'):
        subprocess.run(['uv', 'run', '--frozen', 'python', 'install/bootstrap.py', mode], cwd=source, check=True)
    print('Agent Audio 설치·등록 완료. 실제 WAV 생성과 새 대화의 도구 인식은 별도로 확인하세요.')
