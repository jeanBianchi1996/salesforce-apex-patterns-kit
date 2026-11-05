#!/usr/bin/env bash
# Gera código de todos os tipos num diretório temporário e garante que o linter não aponta nada.
set -euo pipefail

KIT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
cd "$WORK"

python3 "$KIT/scripts/scaffold.py" core > /dev/null
python3 "$KIT/scripts/scaffold.py" trigger Account > /dev/null
python3 "$KIT/scripts/scaffold.py" trigger Case > /dev/null
python3 "$KIT/scripts/scaffold.py" trigger Invoice__c > /dev/null
python3 "$KIT/scripts/scaffold.py" outbound ErpOrder --sobject Order --named-credential ERP > /dev/null
python3 "$KIT/scripts/scaffold.py" inbound PurchaseOrder --sobject Order --external-id ErpCode__c > /dev/null
python3 "$KIT/scripts/scaffold.py" job PurgeLogs --sobject Log__c > /dev/null

if grep -rn "{{" force-app; then
  echo "Placeholders não resolvidos" >&2
  exit 1
fi

python3 "$KIT/hooks/scripts/apex_lint.py" force-app --strict
echo "selftest OK"
