#!/usr/bin/env python3
"""
PreToolUse (Bash): impede deploy em org de produção sem nível de teste explícito.
Bloqueia (exit 2) quando:
  - o comando é um deploy (sf project deploy start / sfdx force:source:deploy / force:mdapi:deploy);
  - a org alvo parece produção (alias/username contém prod, production ou prd);
  - não há --test-level (ou -l) nem --dry-run.
Desligue com APEX_KIT_DISABLE=1.
"""
import json
import os
import re
import sys

DEPLOY = re.compile(r"\b(sf\s+project\s+deploy\s+(start|validate)|sfdx\s+force:(source|mdapi):deploy)\b")
TARGET = re.compile(r"(?:--target-org|-o|--targetusername|-u)\s+([^\s]+)")
PROD = re.compile(r"(prod|production|prd)", re.I)
TEST_LEVEL = re.compile(r"(--test-level|\s-l\s|--testlevel)")


def main() -> int:
    if os.environ.get("APEX_KIT_DISABLE") == "1":
        return 0
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    command = (payload.get("tool_input") or {}).get("command", "")
    if not DEPLOY.search(command):
        return 0
    target = TARGET.search(command)
    if not target or not PROD.search(target.group(1)):
        return 0
    if TEST_LEVEL.search(command) or "--dry-run" in command or "validate" in command:
        return 0
    print(
        "salesforce-apex-patterns-kit: deploy em produção sem nível de teste explícito foi bloqueado.\n"
        "Use, por exemplo: --test-level RunLocalTests (ou RunSpecifiedTests --tests ...). "
        "Prefira validar antes: sf project deploy validate ... e depois quick deploy.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
