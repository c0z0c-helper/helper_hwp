#!/usr/bin/env python3
"""
PyPI 업로드 스크립트

이 스크립트는 helper_hwp 라이브러리를 PyPI에 업로드합니다.
Test PyPI와 Production PyPI 모두 지원합니다.

사용법:
    python upload_to_pypi.py --test    # Test PyPI에 업로드
    python upload_to_pypi.py           # Production PyPI에 업로드
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """명령어 실행 헬퍼 함수"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"실행: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print(f"\n오류: {description} 실패!")
        sys.exit(1)

    return result


def clean_build_artifacts():
    """빌드 아티팩트 정리"""
    print("\n이전 빌드 아티팩트 정리 중...")

    dirs_to_remove = ['dist', 'build', '*.egg-info']
    for pattern in dirs_to_remove:
        for path in Path('.').glob(pattern):
            if path.is_dir():
                print(f"삭제: {path}")
                shutil.rmtree(path)
            elif path.is_file():
                print(f"삭제: {path}")
                path.unlink()


def build_package():
    """패키지 빌드"""
    run_command(
        [sys.executable, "-m", "build"],
        "패키지 빌드 중"
    )

    # 빌드된 파일 확인
    dist_path = Path('dist')
    if dist_path.exists():
        print("\n빌드된 파일:")
        for file in dist_path.iterdir():
            print(f"  - {file.name}")


def check_package():
    """패키지 검증"""
    run_command(
        [sys.executable, "-m", "twine", "check", "dist/*"],
        "패키지 검증 중"
    )


def upload_package(test_pypi=False):
    """패키지 업로드"""
    if test_pypi:
        repository_url = "https://test.pypi.org/legacy/"
        repository_name = "testpypi"
        print("\n Test PyPI에 업로드합니다.")
    else:
        repository_url = "https://upload.pypi.org/legacy/"
        repository_name = "pypi"
        print("\nProduction PyPI에 업로드합니다.")

    # 업로드 확인
    response = input(f"\n{repository_name}에 업로드하시겠습니까? (y/N): ")
    if response.lower() != 'y':
        print("업로드를 취소했습니다.")
        sys.exit(0)

    cmd = [
        sys.executable, "-m", "twine", "upload",
        "--repository-url", repository_url,
        "dist/*"
    ]

    run_command(cmd, f"{repository_name}에 업로드 중")


def main():
    parser = argparse.ArgumentParser(description='PyPI 업로드 스크립트')
    parser.add_argument('--test', action='store_true',
                       help='Test PyPI에 업로드 (기본값: Production PyPI)')
    parser.add_argument('--skip-clean', action='store_true',
                       help='빌드 아티팩트 정리 건너뛰기')

    args = parser.parse_args()

    print("="*60)
    print("PyPI 업로드 프로세스 시작")
    print("="*60)

    # 1. 이전 빌드 정리
    if not args.skip_clean:
        clean_build_artifacts()

    # 2. 패키지 빌드
    build_package()

    # 3. 패키지 검증
    check_package()

    # 4. 업로드
    upload_package(test_pypi=args.test)

    print("\n" + "="*60)
    print("업로드 완료!")
    print("="*60)

    if args.test:
        print("\nTest PyPI에서 설치 테스트:")
        print("pip install --index-url https://test.pypi.org/simple/ helper-hwp")
    else:
        print("\nProduction PyPI에서 설치:")
        print("pip install helper-hwp")


if __name__ == "__main__":
    main()
