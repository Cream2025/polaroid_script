# PolaroidUpdater

이 프로젝트는 폴라로이드 키오스크 시스템의 라즈베리파이 장비를 원격으로 패치하기 위한 **업데이트 전용 클라이언트**입니다.

## 특징

- 관리자 페이지 또는 키오스크 서버의 WebSocket 메시지를 통해 업데이트 트리거를 수신합니다.
- 지정된 URL로부터 `.tar.gz` 패치 파일을 다운로드하고, 무결성 검증 후 설치합니다.
- 설치 완료 후 대상 서비스를 재시작하거나 시스템을 재부팅합니다.
- 독립 실행 구조로 설계되어 있어, `printer_daemon` 등 기존 서비스와 충돌하지 않습니다.

## 시작하기

- Python 3.11 이상 버전으로 인터프리터를 설정합니다. (venv 사용 권장)
- 프로젝트 루트 디렉토리에서 venv를 설정하고 활성화합니다:

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows는 .venv\Scripts\activate
```
아래 명령어로 필요한 패키지를 설치합니다:

```bash
pip install -r requirements.txt
```
settings.py 파일에서 필요한 환경변수를 수정합니다.

또는 IDE의 Run/Debug Configuration에서 직접 환경변수를 설정할 수 있습니다.

## 실행하기
WebSocket 수신기 실행
WebSocket을 통해 서버의 패치 명령을 수신하려면 다음 명령을 실행합니다:

```bash
python update_receiver.py
````
이 스크립트는 백그라운드에서 항상 대기하며, 메시지 수신 시 자동으로 run_patch.py를 실행합니다.

### 수동 패치 실행
테스트 또는 직접 명령어로 패치를 적용하려면 다음처럼 실행합니다:

```bash
python run_patch.py "https://your-server.com/patches/update_v1.2.3.tar.gz" "v1.2.3"
```

## 패치 처리 순서
run_patch.py는 아래와 같은 순서로 업데이트를 진행합니다:

1. 서버에서 지정된 .tar.gz 파일 다운로드
2. SHA256 해시 무결성 검증
3. 현재 실행 중인 앱 백업
4. 압축 해제 및 파일 덮어쓰기
5. 서비스 재시작 또는 시스템 재부팅
6. 업데이트 결과를 로그로 기록


## 로그
/var/log/update.log 에 업데이트 로그가 저장됩니다.
에러가 발생한 경우 update_receiver.py 또는 run_patch.py 로그를 확인해주세요.