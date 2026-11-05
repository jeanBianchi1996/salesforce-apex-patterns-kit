#!/usr/bin/env python3
"""
Pluga o salesforce-apex-patterns-kit em um projeto Salesforce (SFDX) existente.

  python3 scripts/install_into_project.py /caminho/do/projeto [opções]

Sempre faz:
  - copia ferramentas e conhecimento para <projeto>/.apex-kit/ (scaffold, linter, templates, knowledge)
  - mescla as regras em AGENTS.md (bloco entre marcadores, idempotente)
  - garante que CLAUDE.md importe o AGENTS.md (@AGENTS.md)
  - escreve .github/copilot-instructions.md (bloco) e .cursor/rules/salesforce-apex-patterns.mdc

Opções:
  --with-core      gera as classes base (TriggerHandler, AbstractRepository, IdGenerator...) em force-app
  --claude-hooks   registra os hooks em <projeto>/.claude/settings.json (para quem NÃO instalou o plugin)
  --ci             adiciona o workflow GitHub Actions de lint de arquitetura
  --api-version    versão de API para --with-core (padrão 62.0)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
START, END = "<!-- salesforce-apex-patterns-kit:start -->", "<!-- salesforce-apex-patterns-kit:end -->"
VENDOR_DIR = ".apex-kit"
VENDORED = ["scripts/scaffold.py", "hooks/scripts", "templates", "knowledge", "llm"]


def merge_block(path: Path, block: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if pattern.search(current):
        updated = pattern.sub(lambda _: block.strip(), current)
    else:
        updated = (current.rstrip() + "\n\n" if current.strip() else "") + block.strip() + "\n"
    path.write_text(updated, encoding="utf-8")
    print(f"  regras mescladas: {path}")


def vendor(project: Path) -> None:
    target = project / VENDOR_DIR
    for item in VENDORED:
        source = KIT / item
        destination = target / item
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    (target / "VERSION").write_text(json.loads((KIT / ".claude-plugin/plugin.json").read_text())["version"] + "\n")
    print(f"  ferramentas copiadas: {target}")


def ensure_claude_import(project: Path) -> None:
    claude_md = project / "CLAUDE.md"
    content = claude_md.read_text(encoding="utf-8") if claude_md.exists() else "# CLAUDE.md\n"
    if "@AGENTS.md" not in content:
        content = content.rstrip() + "\n\n## Padrões Apex\n@AGENTS.md\n"
        claude_md.write_text(content, encoding="utf-8")
    print(f"  CLAUDE.md importa AGENTS.md: {claude_md}")


def write_cursor_rule(project: Path, rules: str) -> None:
    path = project / ".cursor" / "rules" / "salesforce-apex-patterns.mdc"
    path.parent.mkdir(parents=True, exist_ok=True)
    header = "---\ndescription: Padrões Apex do projeto (salesforce-apex-patterns-kit)\nglobs: \"**/*.cls,**/*.trigger\"\nalwaysApply: false\n---\n"
    path.write_text(header + rules, encoding="utf-8")
    print(f"  regra do Cursor: {path}")


def register_claude_hooks(project: Path) -> None:
    settings_path = project / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    hooks = settings.setdefault("hooks", {})
    lint = f'python3 "$CLAUDE_PROJECT_DIR/{VENDOR_DIR}/hooks/scripts/apex_lint.py" --hook'
    guard = f'python3 "$CLAUDE_PROJECT_DIR/{VENDOR_DIR}/hooks/scripts/deploy_guard.py"'
    context = f'python3 "$CLAUDE_PROJECT_DIR/{VENDOR_DIR}/hooks/scripts/session_context.py"'
    wanted = {
        "PostToolUse": {"matcher": "Write|Edit|MultiEdit", "hooks": [{"type": "command", "command": lint}]},
        "PreToolUse": {"matcher": "Bash", "hooks": [{"type": "command", "command": guard}]},
        "SessionStart": {"hooks": [{"type": "command", "command": context}]},
    }
    for event, entry in wanted.items():
        entries = hooks.setdefault(event, [])
        command = entry["hooks"][0]["command"]
        if not any(h.get("command") == command for e in entries for h in e.get("hooks", [])):
            entries.append(entry)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  hooks registrados: {settings_path}")


def add_ci(project: Path) -> None:
    destination = project / ".github" / "workflows" / "apex-architecture-lint.yml"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(KIT / "templates" / "ci" / "apex-architecture-lint.yml", destination)
    print(f"  workflow de CI: {destination}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project")
    parser.add_argument("--with-core", action="store_true")
    parser.add_argument("--claude-hooks", action="store_true")
    parser.add_argument("--ci", action="store_true")
    parser.add_argument("--api-version", default="62.0")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    if not project.is_dir():
        parser.error(f"projeto não encontrado: {project}")
    if not (project / "sfdx-project.json").exists():
        print("  Aviso: sfdx-project.json não encontrado — confirme que é um projeto Salesforce.")

    print(f"Instalando salesforce-apex-patterns-kit em {project}")
    vendor(project)
    rules = (KIT / "llm" / "AGENTS.md").read_text(encoding="utf-8").replace("<kit>", VENDOR_DIR)
    merge_block(project / "AGENTS.md", rules)
    ensure_claude_import(project)
    merge_block(project / ".github" / "copilot-instructions.md", rules)
    write_cursor_rule(project, rules)
    if args.claude_hooks:
        register_claude_hooks(project)
    if args.ci:
        add_ci(project)
    if args.with_core:
        subprocess.run(
            [sys.executable, str(KIT / "scripts" / "scaffold.py"), "core", "--api-version", args.api_version,
             "--target", str(project / "force-app" / "main" / "default")],
            check=True,
        )
    print("Pronto. Gere código com: python3 .apex-kit/scripts/scaffold.py trigger <SObject>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
