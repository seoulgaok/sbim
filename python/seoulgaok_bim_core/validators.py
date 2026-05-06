"""건축법 + scheme 일관성 검증."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .types import Scheme


@dataclass
class ValidationIssue:
    severity: Literal["error", "warning", "info"]
    code: str
    message: str
    floor_id: int | None = None


def check_far(scheme: Scheme, max_far: float | None = None) -> list[ValidationIssue]:
    """용적률 한도 체크."""
    if max_far is None:
        max_far = scheme.data.far  # scheme 자체에 들어있는 한도값
    total_floor_area = sum(fp.data.floor_area for fp in scheme.floor_plans if fp.data.floor_id > 0)
    actual_far = total_floor_area / scheme.data.lot_area if scheme.data.lot_area > 0 else 0
    issues: list[ValidationIssue] = []
    if actual_far > max_far:
        issues.append(
            ValidationIssue(
                severity="error",
                code="FAR_EXCEEDED",
                message=f"용적률 {actual_far:.2f} > 한도 {max_far:.2f}",
            )
        )
    return issues


def check_bcr(scheme: Scheme, max_bcr: float | None = None) -> list[ValidationIssue]:
    """건폐율 한도 체크. 1층(또는 가장 큰 층) 면적 기준."""
    if max_bcr is None:
        max_bcr = scheme.data.bcr
    issues: list[ValidationIssue] = []
    upper_floors = [fp for fp in scheme.floor_plans if fp.data.floor_id > 0]
    if not upper_floors:
        return issues
    max_floor_area = max(fp.data.floor_area for fp in upper_floors)
    actual_bcr = max_floor_area / scheme.data.lot_area if scheme.data.lot_area > 0 else 0
    if actual_bcr > max_bcr:
        issues.append(
            ValidationIssue(
                severity="error",
                code="BCR_EXCEEDED",
                message=f"건폐율 {actual_bcr:.2f} > 한도 {max_bcr:.2f}",
            )
        )
    return issues


def check_all(scheme: Scheme) -> list[ValidationIssue]:
    """모든 룰 종합 검증."""
    issues: list[ValidationIssue] = []
    issues.extend(check_far(scheme))
    issues.extend(check_bcr(scheme))
    # TODO: 사선제한, 일조권, 주차대수, 채광, 환기 등 (LoD 200에서 추가)
    return issues
