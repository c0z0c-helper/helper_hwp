"""
pytest conftest

테스트 실행 완료 후:
  - tests/report/YYYYMMDDHHMMSS_report.md  — 테스트 결과 리포트
  - tests/output/                          — 변환 출력 파일 (test_convert_outputs 에서 생성)

output 디렉터리는 test_convert_outputs.py 에서 직접 _save() 로 생성합니다.
conftest 는 output 디렉터리가 존재하는지 보장하고 report 를 생성합니다.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pytest

# ---------------------------------------------------------------------------
# 수집 컨테이너
# ---------------------------------------------------------------------------

_results: List[Dict] = []


# ---------------------------------------------------------------------------
# Hook: 각 테스트 결과 수집
# ---------------------------------------------------------------------------


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """call 단계 결과만 수집 (setup/teardown 제외)"""
    if report.when != "call":
        return

    _results.append(
        {
            "nodeid": report.nodeid,
            "outcome": report.outcome,  # "passed" | "failed" | "skipped"
            "duration": report.duration,
            "longrepr": str(report.longrepr) if report.longrepr else "",
        }
    )


# ---------------------------------------------------------------------------
# Hook: 세션 시작 시 output 디렉터리 보장
# ---------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    """output / report 디렉터리 미리 생성"""
    base = Path(__file__).parent
    (base / "output").mkdir(exist_ok=True)
    (base / "report").mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Hook: 세션 종료 시 report 파일 생성
# ---------------------------------------------------------------------------


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """전체 세션 종료 후 마크다운 리포트 생성"""
    report_dir = Path(__file__).parent / "report"
    report_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    report_path = report_dir / f"{timestamp}_report.md"

    passed = [r for r in _results if r["outcome"] == "passed"]
    failed = [r for r in _results if r["outcome"] == "failed"]
    skipped = [r for r in _results if r["outcome"] == "skipped"]
    total = len(_results)

    lines: List[str] = []

    lines.append("# 테스트 리포트")
    lines.append("")
    lines.append(f"실행일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## 요약")
    lines.append("")
    lines.append("| 항목 | 수 |")
    lines.append("| --- | --- |")
    lines.append(f"| 전체 | {total} |")
    lines.append(f"| PASS | {len(passed)} |")
    lines.append(f"| FAIL | {len(failed)} |")
    lines.append(f"| SKIP | {len(skipped)} |")
    lines.append("")

    lines.append("## 상세 결과")
    lines.append("")
    lines.append("| # | 테스트 | 결과 | 소요시간(s) |")
    lines.append("| --- | --- | --- | --- |")

    for i, r in enumerate(_results, 1):
        icon = {"passed": "PASS", "failed": "FAIL", "skipped": "SKIP"}.get(
            r["outcome"], r["outcome"]
        )
        lines.append(f"| {i} | `{r['nodeid']}` | {icon} | {r['duration']:.3f} |")

    lines.append("")

    # output 디렉터리 내 생성된 파일 목록 추가
    output_dir = Path(__file__).parent / "output"
    output_files = sorted(output_dir.iterdir()) if output_dir.exists() else []
    if output_files:
        lines.append("## 생성된 출력 파일")
        lines.append("")
        lines.append("| 파일명 | 크기(bytes) |")
        lines.append("| --- | --- |")
        for f in output_files:
            if f.is_file():
                lines.append(f"| `{f.name}` | {f.stat().st_size:,} |")
        lines.append("")

    if failed:
        lines.append("## 실패 상세")
        lines.append("")
        for r in failed:
            lines.append(f"### `{r['nodeid']}`")
            lines.append("")
            lines.append("```")
            lines.append(r["longrepr"])
            lines.append("```")
            lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[report] {report_path}")
