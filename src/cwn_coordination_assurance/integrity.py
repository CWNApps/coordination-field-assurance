from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sign_record(record: dict[str, Any], key: bytes) -> str:
    return hmac.new(key, canonical_bytes(record), hashlib.sha256).hexdigest()


def verify_record(record: dict[str, Any], signature: str, key: bytes) -> bool:
    return hmac.compare_digest(sign_record(record, key), signature)

