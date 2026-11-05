#!/usr/bin/env python3
"""
Gerador de código Apex no padrão do salesforce-apex-patterns-kit.

Uso:
  python3 scripts/scaffold.py core                       # classes base (TriggerHandler, AbstractRepository...)
  python3 scripts/scaffold.py trigger Account            # trigger + handler + filter + validator + repository + fixtures + testes
  python3 scripts/scaffold.py data Invoice__c            # só camada de dados: repository + mock + fixture
  python3 scripts/scaffold.py outbound ErpOrder --sobject Order --named-credential ERP
  python3 scripts/scaffold.py inbound PurchaseOrder --sobject Order --external-id ErpCode__c
  python3 scripts/scaffold.py batch PurgeLogs --sobject Log__c
  python3 scripts/scaffold.py job PurgeLogs --sobject Log__c   # schedulable + batch

Opções comuns:
  --target DIR        pasta de saída (padrão: force-app/main/default)
  --api-version X.Y   versão de API dos -meta.xml (padrão: 62.0)
  --force             sobrescreve arquivos existentes
  --dry-run           só lista o que seria criado
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = KIT_ROOT / "templates"

RESERVED_VARIABLES = {"case": "caze", "group": "groupRecord", "order": "order", "select": "selectRecord"}

REQUIRED_FIELDS = {
    "Account": "Name = 'Test Account'",
    "Contact": "LastName = 'Test Contact'",
    "Lead": "LastName = 'Test Lead', Company = 'Test Company'",
    "Opportunity": "Name = 'Test Opportunity', StageName = 'Prospecting', CloseDate = Date.today().addDays(30)",
    "Case": "Subject = 'Test Case'",
    "Product2": "Name = 'Test Product', IsActive = true",
    "Campaign": "Name = 'Test Campaign'",
    "Task": "Subject = 'Test Task'",
}

CLASS_META = """<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>{api}</apiVersion>
    <status>Active</status>
</ApexClass>
"""

TRIGGER_META = """<?xml version="1.0" encoding="UTF-8"?>
<ApexTrigger xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>{api}</apiVersion>
    <status>Active</status>
</ApexTrigger>
"""

DATA_LAYER = ("{{SObjectName}}Repository.cls.tmpl", "{{SObjectName}}RepositoryMock.cls.tmpl",
              "{{SObjectName}}FixtureFactory.cls.tmpl")


def lower_first(value: str) -> str:
    return value[:1].lower() + value[1:]


def pluralize(word: str) -> str:
    if re.search(r"[^aeiou]y$", word):
        return word[:-1] + "ies"
    if re.search(r"(s|x|z|ch|sh)$", word):
        return word + "es"
    return word + "s"


def class_name_of(sobject: str) -> str:
    name = re.sub(r"__(c|mdt|e|b|x)$", "", sobject)
    name = name.split("__")[-1]
    return "".join(part[:1].upper() + part[1:] for part in name.split("_") if part)


def build_context(args: argparse.Namespace) -> dict[str, str]:
    sobject = getattr(args, "sobject", None) or getattr(args, "name", None) or "Account"
    sobject_name = class_name_of(sobject)
    plural = pluralize(sobject_name)
    var = lower_first(sobject_name)
    var = RESERVED_VARIABLES.get(var, var)
    name = getattr(args, "name", None) or sobject_name
    return {
        "SObject": sobject,
        "SObjectName": sobject_name,
        "Plural": plural,
        "plural": lower_first(plural),
        "var": var,
        "Name": name,
        "route": re.sub(r"(?<!^)(?=[A-Z])", "-", pluralize(name)).lower(),
        "NamedCredential": getattr(args, "named_credential", None) or name,
        "ExternalIdField": getattr(args, "external_id", None) or "ExternalId__c",
        "RequiredFields": REQUIRED_FIELDS.get(sobject, "/* TODO: campos obrigatórios */"),
    }


def render(text: str, context: dict[str, str]) -> str:
    for key, value in context.items():
        text = text.replace("{{" + key + "}}", value)
    leftover = re.findall(r"\{\{\w+\}\}", text)
    if leftover:
        raise SystemExit(f"Placeholders sem valor: {sorted(set(leftover))}")
    return text


class Writer:
    def __init__(self, target: Path, api_version: str, force: bool, dry_run: bool):
        self.target = target
        self.api_version = api_version
        self.force = force
        self.dry_run = dry_run
        self.created: list[Path] = []
        self.skipped: list[Path] = []

    def write(self, file_name: str, content: str) -> None:
        is_trigger = file_name.endswith(".trigger")
        folder = self.target / ("triggers" if is_trigger else "classes")
        path = folder / file_name
        if path.exists() and not self.force:
            self.skipped.append(path)
            return
        self.created.append(path)
        if self.dry_run:
            return
        folder.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        meta = TRIGGER_META if is_trigger else CLASS_META
        Path(str(path) + "-meta.xml").write_text(meta.format(api=self.api_version), encoding="utf-8")

    def report(self) -> None:
        action = "Seria criado" if self.dry_run else "Criado"
        for path in self.created:
            print(f"  {action}: {path}")
        for path in self.skipped:
            print(f"  Ignorado (já existe, use --force): {path}")


def generate(kind: str, context: dict[str, str], writer: Writer, only: tuple[str, ...] | None = None) -> None:
    for template in sorted((TEMPLATES / "scaffold" / kind).glob("*.tmpl")):
        if only and template.name not in only:
            continue
        file_name = render(template.name[: -len(".tmpl")], context)
        writer.write(file_name, render(template.read_text(encoding="utf-8"), context))


def ensure_data_layer(context: dict[str, str], writer: Writer) -> None:
    repository = writer.target / "classes" / f"{context['SObjectName']}Repository.cls"
    if not repository.exists():
        print(f"  {context['SObjectName']}Repository não encontrado: gerando camada de dados.")
        generate("trigger", context, writer, only=DATA_LAYER)


def copy_core(writer: Writer) -> None:
    for source in sorted((TEMPLATES / "core" / "classes").glob("*.cls")):
        writer.write(source.name, source.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("kind", choices=["core", "trigger", "data", "outbound", "inbound", "batch", "job"])
    parser.add_argument("name", nargs="?", help="SObject (trigger/data) ou nome do recurso (demais)")
    parser.add_argument("--sobject", help="SObject alvo (outbound/inbound/batch/job)")
    parser.add_argument("--named-credential")
    parser.add_argument("--external-id")
    parser.add_argument("--target", default="force-app/main/default")
    parser.add_argument("--api-version", default="62.0")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.kind != "core" and not args.name:
        parser.error("informe o nome (SObject ou recurso)")
    if args.kind in {"trigger", "data"}:
        args.sobject = args.name
    elif args.kind != "core" and not args.sobject:
        parser.error(f"'{args.kind}' exige --sobject")

    writer = Writer(Path(args.target), args.api_version, args.force, args.dry_run)
    context = build_context(args)

    if args.kind == "core":
        copy_core(writer)
    elif args.kind == "trigger":
        generate("trigger", context, writer)
    elif args.kind == "data":
        generate("trigger", context, writer, only=DATA_LAYER)
    elif args.kind == "job":
        ensure_data_layer(context, writer)
        generate("batch", context, writer)
        generate("job", context, writer)
    else:
        ensure_data_layer(context, writer)
        generate(args.kind, context, writer)

    core_marker = writer.target / "classes" / "TriggerHandler.cls"
    if args.kind != "core" and not core_marker.exists():
        print("  Aviso: classes base ausentes. Rode antes: python3 scripts/scaffold.py core")
    if args.kind == "inbound" and not args.external_id:
        print("  Aviso: usando ExternalId__c como chave externa. Ajuste com --external-id.")
    writer.report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
