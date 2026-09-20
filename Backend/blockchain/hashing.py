"""Deterministic Canonical Hashing Engine for Decision Provenance

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
DEV 2: Blockchain Provenance Layer

Provides:
1. Canonical JSON serialization (deterministic sorting, normalized numeric types).
2. SHA-256 digest computation for data snapshots, calculation results, and composite records.
3. Strict sanitization to guarantee NO sensitive financial CSVs, credentials, or raw DB dumps are stored on-chain.
"""

import hashlib
import json
import re
from typing import Any, Dict, List, Set, Union
from pydantic import BaseModel


# Sensitive key patterns that must NEVER be hashed directly with sensitive values or stored in raw provenance metadata
SENSITIVE_KEY_PATTERNS = [
    r"password",
    r"secret",
    r"token",
    r"api[_-]?key",
    r"credential",
    r"raw[_-]?csv",
    r"company[_-]?csv",
    r"private[_-]?key",
    r"ssn",
    r"pii",
]


def is_sensitive_key(key: str) -> bool:
    """Check if a dictionary key indicates sensitive, non-provenance data."""
    key_lower = key.lower()
    return any(re.search(pat, key_lower) for pat in SENSITIVE_KEY_PATTERNS)


def sanitize_data(data: Any) -> Any:
    """Recursively strip or redact sensitive fields before hashing or metadata serialization.
    
    Guarantees compliance with TRINETRA Security rules:
    - Never store raw company CSVs, personal data, secrets, or full vulnerability databases on-chain.
    """
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if is_sensitive_key(str(k)):
                sanitized[k] = "[REDACTED_SENSITIVE_DATA]"
            else:
                sanitized[k] = sanitize_data(v)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    elif isinstance(data, BaseModel):
        return sanitize_data(data.model_dump())
    return data


def canonical_json(data: Any) -> str:
    """Convert any Python structure or Pydantic model into a deterministic, canonical JSON string.
    
    Guarantees:
    - Alphabetically sorted keys.
    - Compact separators without whitespace (',' and ':').
    - Stable float formatting (rounded to 8 decimal places for consistency).
    """
    if isinstance(data, BaseModel):
        data = data.model_dump()

    def _normalize(item: Any) -> Any:
        if isinstance(item, dict):
            return {str(k): _normalize(v) for k, v in sorted(item.items())}
        elif isinstance(item, (list, tuple)):
            return [_normalize(x) for x in item]
        elif isinstance(item, float):
            # Normalize float representations to prevent cross-platform floating point divergence
            return round(item, 8)
        elif item is None or isinstance(item, (int, str, bool)):
            return item
        else:
            return str(item)

    normalized = _normalize(data)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hash(data: Union[str, bytes, Dict[str, Any], List[Any], BaseModel]) -> str:
    """Calculate the SHA-256 hexadecimal hash digest of raw data or canonicalized JSON."""
    if isinstance(data, (dict, list, BaseModel)):
        raw_str = canonical_json(data)
        encoded = raw_str.encode("utf-8")
    elif isinstance(data, str):
        encoded = data.encode("utf-8")
    elif isinstance(data, bytes):
        encoded = data
    else:
        encoded = str(data).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def compute_data_snapshot_hash(data: Any) -> str:
    """Compute the SHA-256 hash digest of an assessment's input data snapshot."""
    if data is None:
        return hashlib.sha256(b"{}").hexdigest()
    sanitized = sanitize_data(data)
    return sha256_hash(sanitized)


def compute_result_hash(result: Any) -> str:
    """Compute the SHA-256 hash digest of an assessment's quantitative decision result."""
    if result is None:
        return hashlib.sha256(b"{}").hexdigest()
    sanitized = sanitize_data(result)
    return sha256_hash(sanitized)


def compute_composite_hash(
    assessment_id: str,
    decision_id: str,
    model_version: str,
    timestamp: str,
    data_snapshot_hash: str,
    result_hash: str,
) -> str:
    """Compute the master canonical SHA-256 provenance hash covering all core provenance attributes."""
    composite_payload = {
        "assessment_id": assessment_id,
        "decision_id": decision_id,
        "model_version": model_version,
        "timestamp": timestamp,
        "data_snapshot_hash": data_snapshot_hash,
        "result_hash": result_hash,
    }
    return sha256_hash(composite_payload)
