#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"src"
forbidden_imports=("neo4j", "boto3", "kubernetes", "requests", "httpx", "openai")
secret_patterns={
    "private_key":re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "github_token":re.compile(r"gh[pousr]_[A-Za-z0-9_]{30,}"),
    "aws_access_key":re.compile(r"AKIA[0-9A-Z]{16}"),
}
bad=[]
for p in ROOT.rglob("*"):
    if not p.is_file() or any(x in p.parts for x in ("__pycache__", ".git")): continue
    try: text=p.read_text(encoding="utf-8")
    except UnicodeDecodeError: continue
    if p.is_relative_to(SRC):
        for name in forbidden_imports:
            if re.search(rf"^\s*(?:from|import)\s+{re.escape(name)}\b",text,re.M): bad.append(f"forbidden import {name}: {p.relative_to(ROOT)}")
        if "ALLOW" in text or "DENY" in text: bad.append(f"authority verb in reference source: {p.relative_to(ROOT)}")
    for label,pat in secret_patterns.items():
        if pat.search(text): bad.append(f"possible {label}: {p.relative_to(ROOT)}")
if bad: raise SystemExit("\n".join(bad))
print("security boundary scan: pass")

