"""Optional MITRE ATT&CK Threat Context Enrichment Adapter

TRINETRA - SIH 2026
Theme: Blockchain & Cybersecurity | Problem ID: SIH26105

Provides decoupled threat intelligence enrichment (tactics, techniques, threat groups)
without creating hard dependencies for the core Risk Engine.
"""

import logging
from typing import Dict, List, Optional
from schemas.vulnerability import RawMitreAttackData, SourceStatusEnum

logger = logging.getLogger("trinetra.integrations.mitre_attack")


class MitreAttackEnricher:
    """Decoupled enricher for MITRE ATT&CK techniques, tactics, and adversary profiles."""

    def __init__(self):
        # Heuristic / Knowledge-base mapping for common vulnerability classes
        self._pattern_mapping: Dict[str, Dict[str, List[str]]] = {
            "RCE": {
                "tactics": ["Initial Access", "Execution"],
                "techniques": ["T1190 - Exploit Public-Facing Application", "T1059 - Command and Scripting Interpreter"],
                "groups": ["APT28", "APT29", "Lazarus Group"],
                "software": ["Cobalt Strike", "Mimikatz"],
            },
            "PRIVILEGE_ESCALATION": {
                "tactics": ["Privilege Escalation"],
                "techniques": ["T1068 - Exploitation for Privilege Escalation"],
                "groups": ["FIN7", "Wizard Spider"],
                "software": ["PrintNightmare", "PsExec"],
            },
            "SQLI": {
                "tactics": ["Initial Access", "Credential Access"],
                "techniques": ["T1190 - Exploit Public-Facing Application", "T1552 - Unsecured Credentials"],
                "groups": ["FIN6", "Mantis"],
                "software": ["SQLmap"],
            },
            "RANSOMWARE": {
                "tactics": ["Impact"],
                "techniques": ["T1486 - Data Encrypted for Impact", "T1490 - Inhibit System Recovery"],
                "groups": ["LockBit", "BlackCat", "Cl0p"],
                "software": ["LockBit 3.0", "ALPHV"],
            },
            "AUTHENTICATION_BYPASS": {
                "tactics": ["Defense Evasion", "Initial Access"],
                "techniques": ["T1078 - Valid Accounts", "T1556 - Modify Authentication Process"],
                "groups": ["Volt Typhoon", "Salt Typhoon"],
                "software": [],
            },
        }

    def enrich(
        self,
        cve_id: str,
        description: Optional[str] = None,
        is_kev: bool = False,
        known_ransomware: bool = False,
    ) -> RawMitreAttackData:
        """Enrich a vulnerability with relevant ATT&CK tactics, techniques, and adversary groups.

        This method is purely non-blocking and fail-safe.
        """
        tactics: List[str] = []
        techniques: List[str] = []
        groups: List[str] = []
        software: List[str] = []

        desc_lower = (description or "").lower()

        # Heuristic matching based on description keywords
        if "remote code execution" in desc_lower or " rce" in desc_lower or "arbitrary code" in desc_lower:
            pattern = self._pattern_mapping["RCE"]
            tactics.extend(pattern["tactics"])
            techniques.extend(pattern["techniques"])
            groups.extend(pattern["groups"])
            software.extend(pattern["software"])

        if "privilege escalation" in desc_lower or "elevation of privilege" in desc_lower:
            pattern = self._pattern_mapping["PRIVILEGE_ESCALATION"]
            tactics.extend(pattern["tactics"])
            techniques.extend(pattern["techniques"])
            groups.extend(pattern["groups"])

        if "sql injection" in desc_lower or "sqli" in desc_lower:
            pattern = self._pattern_mapping["SQLI"]
            tactics.extend(pattern["tactics"])
            techniques.extend(pattern["techniques"])
            groups.extend(pattern["groups"])

        if "authentication bypass" in desc_lower or "bypass authorization" in desc_lower:
            pattern = self._pattern_mapping["AUTHENTICATION_BYPASS"]
            tactics.extend(pattern["tactics"])
            techniques.extend(pattern["techniques"])
            groups.extend(pattern["groups"])

        if is_kev or known_ransomware:
            pattern = self._pattern_mapping["RANSOMWARE"]
            tactics.extend(pattern["tactics"])
            techniques.extend(pattern["techniques"])
            groups.extend(pattern["groups"])
            software.extend(pattern["software"])

        # Deduplicate while preserving order
        return RawMitreAttackData(
            tactics=list(dict.fromkeys(tactics)),
            techniques=list(dict.fromkeys(techniques)),
            groups=list(dict.fromkeys(groups)),
            software=list(dict.fromkeys(software)),
            status=SourceStatusEnum.AVAILABLE,
        )
