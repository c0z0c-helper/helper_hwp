"""
pytest conftest

테스트 실행 완료 후 tests/report/YYYYMMDDHHMMSS_report.md 파일을 생성합니다.
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

    lines.append(f"# 테스트 리포트")
    lines.append(f"")
    lines.append(f"실행일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"")
    lines.append(f"## 요약")
    lines.append(f"")
    lines.append(f"| 항목 | 수 |")
    lines.append(f"| --- | --- |")
    lines.append(f"| 전체 | {total} |")
    lines.append(f"| PASS | {len(passed)} |")
    lines.append(f"| FAIL | {len(failed)} |")
    lines.append(f"| SKIP | {len(skipped)} |")
    lines.append(f"")

    lines.append(f"## 상세 결과")
    lines.append(f"")
    lines.append(f"| # | 테스트 | 결과 | 소요시간(s) |")
    lines.append(f"| --- | --- | --- | --- |")

    for i, r in enumerate(_results, 1):
        icon = {"passed": "PASS", "failed": "FAIL", "skipped": "SKIP"}.get(
            r["outcome"], r["outcome"]
        )
        lines.append(f"| {i} | `{r['nodeid']}` | {icon} | {r['duration']:.3f} |")

    lines.append(f"")

    if failed:
        lines.append(f"## 실패 상세")
        lines.append(f"")
        for r in failed:
            lines.append(f"### `{r['nodeid']}`")
            lines.append(f"")
            lines.append(f"```")
            lines.append(r["longrepr"])
            lines.append(f"```")
            lines.append(f"")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    # 터미널에 경로 출력 (pytest 캡처 밖)
    print(f"\n[report] {report_path}")
