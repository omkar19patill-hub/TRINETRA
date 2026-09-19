"""Unit tests for MITRE ATT&CK Enrichment Adapter"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from integrations.mitre_attack import MitreAttackEnricher


def test_mitre_attack_enrich_rce():
    """Test ATT&CK mapping for Remote Code Execution vulnerabilities."""
    enricher = MitreAttackEnricher()
    result = enricher.enrich(
        cve_id="CVE-2024-3400",
        description="Command injection allowing unauthenticated remote code execution.",
        is_kev=True,
        known_ransomware=True,
    )

    assert "Initial Access" in result.tactics
    assert "Execution" in result.tactics
    assert "Impact" in result.tactics
    assert any("T1190" in tech for tech in result.techniques)
    assert any("T1486" in tech for tech in result.techniques)
    assert "LockBit" in result.groups or "Lazarus Group" in result.groups


def test_mitre_attack_enrich_privilege_escalation():
    """Test ATT&CK mapping for Privilege Escalation."""
    enricher = MitreAttackEnricher()
    result = enricher.enrich(
        cve_id="CVE-2023-23397",
        description="Microsoft Outlook Elevation of Privilege Vulnerability.",
    )

    assert "Privilege Escalation" in result.tactics
    assert any("T1068" in tech for tech in result.techniques)


def test_mitre_attack_enrich_empty_description():
    """Test non-matching description returns empty list without error."""
    enricher = MitreAttackEnricher()
    result = enricher.enrich(cve_id="CVE-2026-0001", description=None)

    assert isinstance(result.tactics, list)
    assert len(result.tactics) == 0
