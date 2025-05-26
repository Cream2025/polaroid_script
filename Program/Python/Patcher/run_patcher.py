#!/usr/bin/env python3

import os
import sys
import hashlib
import tarfile
import shutil
import subprocess
import datetime
import atexit
import requests
from pathlib import Path

# ============ 설정 ============
# APP_DIR = Path("/opt/myapp")
# BACKUP_ROOT = Path("/opt/backups")
# PATCH_FILE = Path("/tmp/update.tar.gz")
# LOG_FILE = Path("/var/log/update.log")

APP_DIR = Path("C://temp/A/opt/myapp")
PATCH_FILE = Path("C://temp/A/update.tar.gz")
LOG_PATH = Path("C://temp/A/log")

SERVICE_NAME = "myapp.service"


# ==============================

def log(message: str):
    # 디렉토리 경로가 없으면 생성
    os.makedirs(LOG_PATH, exist_ok=True)
    # 타임스탬프 추가
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    current_date = datetime.datetime.now().strftime("%Y%m%d")
    file_name = f"{LOG_PATH}/update_{current_date}.log"

    # 파일 열기 (append 모드)
    with open(file_name, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(message)


def download_patch(url: str):
    log(f"Downloading patch from {url}")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(PATCH_FILE, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    log("Download completed.")


def verify_hash(expected_hash: str):
    log("Verifying SHA256 hash...")
    sha256 = hashlib.sha256()
    with open(PATCH_FILE, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    actual_hash = sha256.hexdigest()
    if actual_hash != expected_hash:
        raise ValueError(f"Hash mismatch! Expected: {expected_hash}, Got: {actual_hash}")
    log("Hash verification passed.")


def apply_patch():
    log("Applying patch...")

    # 디렉토리가 존재하면 삭제
    if os.path.exists(APP_DIR):
        shutil.rmtree(APP_DIR)

    # 디렉토리 다시 생성
    os.makedirs(APP_DIR, exist_ok=True)

    # 패치 파일 압축 해제
    with tarfile.open(PATCH_FILE, "r:gz") as tar:
        tar.extractall(path=APP_DIR)

    log("Patch applied.")


def restart_service():
    log(f"Restarting service: {SERVICE_NAME}")
    subprocess.run(["systemctl", "restart", SERVICE_NAME], check=True)
    log("Service restarted.")


def clear_resource():
    if PATCH_FILE.exists():
        PATCH_FILE.unlink()
    log("Temporary files cleaned up.")


def main():
    # if len(sys.argv) < 3:
    #     print("Usage: run_patch.py <PATCH_URL> <VERSION> [<SHA256>]")
    #     sys.exit(1)
    #
    # url = sys.argv[1]
    # version = sys.argv[2]
    # expected_hash = sys.argv[3] if len(sys.argv) > 3 else None

    url = "https://github.com/firebase/firebase-tools/archive/refs/tags/v14.4.0.tar.gz"
    version = "14.4.0"
    expected_hash = "d97a0e85a22bee542f955470e77875875d312a39d008bfae8a938905fe0bbefe"

    try:
        log(f"Starting patch to version {version}")
        download_patch(url)
        if expected_hash:
            verify_hash(expected_hash)
        apply_patch()
        # restart_service()
        log("Patch completed successfully.")
    except Exception as e:
        log(f"Patch failed: {e}")
        sys.exit(1)
    finally:
        clear_resource()


if __name__ == "__main__":
    atexit.register(clear_resource)
    main()
