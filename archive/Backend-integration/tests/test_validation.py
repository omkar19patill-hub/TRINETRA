"""Unit tests for Validation Module

Tests strict CVE regex format checks, CVSS [0.0 - 10.0] bounds, EPSS [0.0 - 1.0] bounds,
and rejection of corrupted or out-of-bounds payloads.
"""

import sys
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from validation.vulnerability_validator import (
    InvalidCVEFormatError,
    InvalidMetricBoundsError,
    validate_cve_id,
    validate_cvss_score,
    validate_date_string,
    validate_epss_score,
)


def test_validate_cve_id_valid():
    """Test valid CVE identifiers are normalized to uppercase."""
    assert validate_cve_id("CVE-2024-3400") == "CVE-2024-3400"
    assert validate_cve_id("cve-2021-44228") == "CVE-2021-44228"
    assert validate_cve_id("  cve-2023-1234567  ") == "CVE-2023-1234567"


def test_validate_cve_id_invalid():
    """Test invalid CVE strings raise InvalidCVEFormatError."""
    with pytest.raises(InvalidCVEFormatError):
        validate_cve_id("NOT-A-CVE")

    with pytest.raises(InvalidCVEFormatError):
        validate_cve_id("CVE-24-1234")  # Year must be 4 digits

    with pytest.raises(InvalidCVEFormatError):
        validate_cve_id("")

    with pytest.raises(InvalidCVEFormatError):
        validate_cve_id(None)


def test_validate_cvss_score_bounds():
    """Test CVSS bounds checking [0.0 - 10.0]."""
    assert validate_cvss_score(9.8) == 9.8
    assert validate_cvss_score(0.0) == 0.0
    assert validate_cvss_score(10.0) == 10.0
    assert validate_cvss_score("7.5") == 7.5
    assert validate_cvss_score(None) is None

    with pytest.raises(InvalidMetricBoundsError):
        validate_cvss_score(11.5)

    with pytest.raises(InvalidMetricBoundsError):
        validate_cvss_score(-0.1)

    with pytest.raises(InvalidMetricBoundsError):
        validate_cvss_score("invalid-score")


def test_validate_epss_score_bounds():
    """Test EPSS bounds checking [0.0 - 1.0]."""
    score, pct = validate_epss_score(0.85, 0.99)
    assert score == 0.85
    assert pct == 0.99

    score_str, _ = validate_epss_score("0.12345", None)
    assert score_str == 0.12345

    with pytest.raises(InvalidMetricBoundsError):
        validate_epss_score(1.5, 0.5)

    with pytest.raises(InvalidMetricBoundsError):
        validate_epss_score(-0.01, 0.5)

    with pytest.raises(InvalidMetricBoundsError):
        validate_epss_score(0.5, 1.2)


def test_validate_date_string():
    """Test ISO date parsing and validation."""
    assert validate_date_string("2026-03-01T12:00:00Z") == "2026-03-01T12:00:00Z"
    assert validate_date_string("2026-03-01") == "2026-03-01"
    assert validate_date_string(None) is None
