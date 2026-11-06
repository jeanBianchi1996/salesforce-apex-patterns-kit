#!/usr/bin/env python3
"""
apex_lint — regras de ARQUITETURA do salesforce-apex-patterns-kit (complementa o PMD).

Modos:
  CLI:   python3 apex_lint.py force-app [--format text|json|github] [--strict]
  Hook:  python3 apex_lint.py --hook   (lê o JSON do Claude Code no stdin; PostToolUse em Write|Edit)

No modo hook:
  - erro  → mensagem no stderr + exit 2 (o Claude recebe o feedback e corrige);
  - aviso → JSON com additionalContext no stdout + exit 0.
  Variáveis: APEX_KIT_STRICT=1 (avisos viram erros), APEX_KIT_DISABLE=1 (desliga),
             APEX_KIT_MODE=warn (nada bloqueia; erros e avisos voltam como contexto — ideal para código legado).

Supressão (use com justificativa):
  // apex-kit:ignore APX002            → na própria linha ou na linha anterior
  // apex-kit:ignore-file APX003,APX002 → no arquivo todo
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# Windows: garante UTF-8 na saída (acentos nas mensagens dos hooks)
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


ERROR, WARNING = "error", "warning"

RULES = {
    "APX001": (ERROR, "Trigger com lógica. A trigger deve ter uma linha: new <Obj>TriggerHandler().run();"),
    "APX002": (ERROR, "SOQL fora de Repository. Mova a consulta para <Obj>Repository.findByXxx()."),
    "APX003": (ERROR, "DML fora de Repository. Use <Obj>Repository.save()/remove()."),
    "APX004": (ERROR, "SOQL/DML dentro de loop. Colete em coleções e faça uma única operação fora do loop."),
    "APX005": (WARNING, "Notação húngara/sufixo de tipo no nome. Use plural com contexto (accounts, ordersById)."),
    "APX006": (ERROR, "Test.isRunningTest() em código de produção. Extraia um método protected virtual e sobrescreva num Mock."),
    "APX007": (ERROR, "SeeAllData=true quebra o princípio Repeatable. Crie os dados com FixtureFactory."),
    "APX008": (ERROR, "Classe de teste sem asserções. Todo teste precisa ser auto-verificável (Assert.*)."),
    "APX009": (ERROR, "Id do Salesforce fixo no código. Em produção use consulta/Custom Metadata; em teste use IdGenerator."),
    "APX010": (ERROR, "Endpoint fixo no código. Use Named Credential: setEndpoint('callout:Nome/...')."),
    "APX011": (WARNING, "Classe de entrada sem sharing explícito. Declare 'with sharing' (ou 'without sharing' justificado)."),
    "APX012": (WARNING, "'without sharing' sem justificativa. Comente o motivo na linha anterior à declaração."),
    "APX013": (WARNING, "Mais de 3 níveis de indentação no método (regra das 3 tabs). Extraia método/classe."),
    "APX014": (WARNING, "Chamada de Repository dentro de loop. Provável SOQL/DML em loop: agrupe antes."),
    "APX015": (WARNING, "@future em código novo. Prefira Queueable (objetos complexos, encadeamento, Finalizer)."),
    "APX016": (WARNING, "WITH SECURITY_ENFORCED está superado. Prefira WITH USER_MODE / AccessLevel.USER_MODE."),
    "APX017": (ERROR, "SOQL dinâmico concatenado. Use Database.queryWithBinds com binds (risco de injeção)."),
    "APX018": (WARNING, "Nome de método de teste fora do padrão BDD (given...When...Then... ou should...)."),
    "APX019": (WARNING, "Callout dentro de loop sem lote. Garanta o limite de 100 callouts por transação."),
    "APX020": (WARNING, "Trigger não declara todos os eventos? Uma trigger por objeto deve listar todos os eventos tratados pelo handler."),
}

DATA_ACCESS_CLASS = re.compile(r"(Repository|Selector|UnitOfWork)$")
ENTRY_CLASS = re.compile(r"(TriggerHandler|Controller|Batch|Job|Schedulable)$")
DML_STATEMENT = re.compile(r"(?<![\w.])(insert|update|upsert|delete|undelete|merge)\s+(as\s+(user|system)\s+)?[\w(\[]", re.I)
DML_DATABASE = re.compile(r"\bDatabase\s*\.\s*(insert|update|upsert|delete|undelete|merge|convertLead)\s*\(", re.I)
SOQL = re.compile(r"\[\s*(SELECT|FIND)\b", re.I)
SOQL_DATABASE = re.compile(r"\bDatabase\s*\.\s*(query|queryWithBinds|getQueryLocator|countQuery|getQueryLocatorWithBinds)\s*\(", re.I)
LOOP_START = re.compile(r"^\s*(for|while)\s*\(|^\s*do\s*\{|\}\s*while\s*\(", re.I)
REPOSITORY_CALL = re.compile(r"\b\w*[Rr]epository\s*\.\s*(find\w*|save|remove)\s*\(")
CALLOUT = re.compile(r"\.\s*send\s*\(\s*\w*[Rr]equest")
SF_ID_LITERAL = re.compile(r"'([a-zA-Z0-9]{3}[0-9][a-zA-Z0-9]{11}(?:[a-zA-Z0-9]{3})?)'")
HARDCODED_ENDPOINT = re.compile(r"setEndpoint\s*\(\s*'https?://", re.I)
HUNGARIAN = [
    re.compile(r"\b(?:List|Set|Map)\s*<[^;=()]*>\s+((?:lst|list|map|set|arr)[A-Z]\w*)\s*[=;,)]"),
    re.compile(r"\b(?:List|Set|Map)\s*<[^;=()]*>\s+(\w+(?:List|Map|Set|Lst))\s*[=;,)]"),
    re.compile(r"\b(?:String|Integer|Decimal|Double|Long|Date|Datetime|Boolean|Id)\s+((?:str|int|dec|dbl|lng|dt|bln|bool|my)[A-Z]\w*)\s*[=;,)]"),
]
CLASS_DECL = re.compile(
    r"\b(public|global|private)?\s*((?:virtual|abstract|with sharing|without sharing|inherited sharing)\s+)*class\s+(\w+)",
    re.I,
)
IGNORE_LINE = re.compile(r"apex-kit:ignore\s+([A-Z0-9, ]+)")
IGNORE_FILE = re.compile(r"apex-kit:ignore-file\s+([A-Z0-9, ]+)")


@dataclass
class Finding:
    file: str
    line: int
    rule: str
    severity: str
    message: str


def strip_comments_and_strings(source: str) -> str:
    """Remove comentários e conteúdo de strings preservando quebras de linha (números de linha)."""
    out, i, n = [], 0, len(source)
    while i < n:
        two = source[i:i + 2]
        if two == "//":
            while i < n and source[i] != "\n":
                i += 1
        elif two == "/*":
            i += 2
            while i < n and source[i:i + 2] != "*/":
                out.append("\n" if source[i] == "\n" else " ")
                i += 1
            i += 2
        elif source[i] == "'":
            out.append("'")
            i += 1
            while i < n and source[i] != "'":
                if source[i] == "\\":
                    i += 1
                elif source[i] == "\n":
                    out.append("\n")
                i += 1
            out.append("'")
            i += 1
        else:
            out.append(source[i])
            i += 1
    return "".join(out)


def strip_comments(source: str) -> str:
    """Remove só comentários (mantém strings) — usado em regras que olham literais."""
    code = strip_comments_and_strings(source)
    result, src_lines, code_lines = [], source.split("\n"), code.split("\n")
    for raw, clean in zip(src_lines, code_lines):
        cut = raw
        if "//" in raw and "//" not in clean:
            idx = raw.find("//")
            # só corta se o // não estiver dentro de string
            if raw[:idx].count("'") % 2 == 0:
                cut = raw[:idx]
        result.append(cut if clean.strip() else "")
    return "\n".join(result)


class FileLinter:
    def __init__(self, path: Path, source: str):
        self.path = path
        self.source = source
        self.raw_lines = source.split("\n")
        self.code = strip_comments_and_strings(source)
        self.lines = self.code.split("\n")
        self.literal_lines = strip_comments(source).split("\n")
        self.findings: list[Finding] = []
        self.is_trigger = path.suffix == ".trigger"
        self.is_test = bool(re.search(r"@\s*isTest\b", self.code, re.I))
        match = CLASS_DECL.search(self.code)
        self.class_name = match.group(3) if match else path.stem
        self.file_ignores = set()
        for found in IGNORE_FILE.findall(source):
            self.file_ignores.update(rule.strip() for rule in found.split(","))

    # -------------------------------------------------------------- utilidades
    def add(self, line_index: int, rule: str, detail: str = "") -> None:
        if rule in self.file_ignores or self.is_ignored(line_index, rule):
            return
        severity, message = RULES[rule]
        if detail:
            message = f"{message} [{detail.strip()[:90]}]"
        if any(f.line == line_index + 1 and f.rule == rule for f in self.findings):
            return
        self.findings.append(Finding(str(self.path), line_index + 1, rule, severity, message))

    def is_ignored(self, line_index: int, rule: str) -> bool:
        for idx in (line_index, line_index - 1):
            if 0 <= idx < len(self.raw_lines):
                match = IGNORE_LINE.search(self.raw_lines[idx])
                if match and rule in [r.strip() for r in match.group(1).split(",")]:
                    return True
        return False

    def is_data_access_class(self) -> bool:
        return bool(DATA_ACCESS_CLASS.search(self.class_name)) or self.class_name == "AbstractRepository"

    # ------------------------------------------------------------------- regras
    def run(self) -> list[Finding]:
        if self.is_trigger:
            self.check_trigger()
            return self.findings
        self.check_data_access_outside_repository()
        self.check_loops_and_nesting()
        self.check_naming()
        self.check_literals()
        self.check_sharing()
        self.check_misc()
        if self.is_test:
            self.check_tests()
        return sorted(self.findings, key=lambda f: (f.line, f.rule))

    def check_trigger(self) -> None:
        body = self.code.split("{", 1)[1].rsplit("}", 1)[0] if "{" in self.code else ""
        statements = [s.strip() for s in body.split(";") if s.strip()]
        handler_call = re.compile(r"^new\s+\w+TriggerHandler\s*\(\s*\)\s*\.\s*run\s*\(\s*\)$")
        if len(statements) != 1 or not handler_call.match(statements[0]):
            first_body_line = next((i for i, l in enumerate(self.lines) if "{" in l), 0)
            self.add(first_body_line, "APX001")

    def check_data_access_outside_repository(self) -> None:
        if self.is_test or self.is_data_access_class():
            return
        for i, line in enumerate(self.lines):
            if SOQL.search(line) or SOQL_DATABASE.search(line):
                self.add(i, "APX002", self.raw_lines[i])
            if DML_DATABASE.search(line) or self.is_dml_statement(line):
                self.add(i, "APX003", self.raw_lines[i])

    @staticmethod
    def is_dml_statement(line: str) -> bool:
        stripped = line.strip()
        if not DML_STATEMENT.match(stripped):
            return False
        # evita falsos positivos: declarações/chamadas como "update(...)" de métodos próprios
        return not re.match(r"^(insert|update|upsert|delete|undelete|merge)\s*\(", stripped, re.I)

    def check_loops_and_nesting(self) -> None:
        depth = 0
        loop_depths: list[int] = []
        pending_loop = False
        method_depth = None
        reported_nesting_for_method = False
        for i, line in enumerate(self.lines):
            stripped = line.strip()
            starts_loop = bool(LOOP_START.search(stripped)) and not stripped.startswith("}")
            if starts_loop:
                pending_loop = True
                # loop de uma linha sem chaves: for (...) x;
                if "{" not in stripped and stripped.endswith(";"):
                    self.check_inside_loop(i, stripped.split(")", 1)[-1])
                    pending_loop = False
            elif loop_depths:
                self.check_inside_loop(i, line)

            for char in line:
                if char == "{":
                    depth += 1
                    if pending_loop:
                        loop_depths.append(depth)
                        pending_loop = False
                    if method_depth is None and depth == 2:
                        method_depth = depth
                        reported_nesting_for_method = False
                    if method_depth is not None and depth - method_depth > 3 and not reported_nesting_for_method:
                        self.add(i, "APX013")
                        reported_nesting_for_method = True
                elif char == "}":
                    if loop_depths and loop_depths[-1] == depth:
                        loop_depths.pop()
                    depth -= 1
                    if method_depth is not None and depth < method_depth:
                        method_depth = None

    def check_inside_loop(self, i: int, line: str) -> None:
        if SOQL.search(line) or SOQL_DATABASE.search(line) or DML_DATABASE.search(line) or self.is_dml_statement(line):
            self.add(i, "APX004", self.raw_lines[i])
        elif REPOSITORY_CALL.search(line):
            self.add(i, "APX014", self.raw_lines[i])
        elif CALLOUT.search(line) and not self.is_test:
            self.add(i, "APX019", self.raw_lines[i])

    def check_naming(self) -> None:
        for i, line in enumerate(self.lines):
            for pattern in HUNGARIAN:
                match = pattern.search(line)
                if match:
                    self.add(i, "APX005", match.group(1))
                    break

    def check_literals(self) -> None:
        for i, line in enumerate(self.literal_lines):
            for match in SF_ID_LITERAL.finditer(line):
                literal = match.group(1)
                if sum(c.isdigit() for c in literal) >= 5 and not self.is_test:
                    self.add(i, "APX009", literal)
            if HARDCODED_ENDPOINT.search(line) and not self.is_test:
                self.add(i, "APX010", line)

    def check_sharing(self) -> None:
        if self.is_test:
            return
        match = CLASS_DECL.search(self.code)
        if not match:
            return
        declaration = self.code[match.start():self.code.find("{", match.start())]
        decl_line = self.code[:match.start()].count("\n")
        is_rest = bool(re.search(r"@\s*RestResource", self.code[:match.start()], re.I))
        has_sharing = re.search(r"\b(with|without|inherited)\s+sharing\b", declaration, re.I)
        is_framework_base = self.class_name in {"TriggerHandler"}
        if (ENTRY_CLASS.search(self.class_name) or is_rest) and not has_sharing and not is_framework_base:
            self.add(decl_line, "APX011", self.class_name)
        for i, line in enumerate(self.lines):
            if re.search(r"\bwithout\s+sharing\b", line, re.I):
                context = "\n".join(self.raw_lines[max(0, i - 3):i + 1])
                if not re.search(r"(//|\*).*\w{4,}", context.replace(self.raw_lines[i], "")):
                    self.add(i, "APX012")

    def check_misc(self) -> None:
        for i, line in enumerate(self.lines):
            if re.search(r"\bTest\s*\.\s*isRunningTest\s*\(", line):
                self.add(i, "APX006")
            if re.search(r"@\s*future\b", line, re.I):
                self.add(i, "APX015")
            if re.search(r"WITH\s+SECURITY_ENFORCED", line, re.I):
                self.add(i, "APX016")
            if re.search(r"Database\s*\.\s*query\s*\([^)]*\+", self.raw_lines[i]) or (
                re.search(r"Database\s*\.\s*query\s*\(", line) and "+" in self.raw_lines[i]
            ):
                self.add(i, "APX017", self.raw_lines[i])

    def check_tests(self) -> None:
        for i, line in enumerate(self.lines):
            if re.search(r"SeeAllData\s*=\s*true", line, re.I):
                self.add(i, "APX007")
        has_test_methods = re.search(r"@\s*isTest\s*(\([^)]*\))?\s*(static|public|private)?\s*static\s+void|\btestMethod\b", self.code, re.I)
        has_asserts = re.search(r"\b(Assert\s*\.\s*\w+|System\s*\.\s*assert\w*)\s*\(|\bmocker\s*\.\s*assert\s*\(", self.code, re.I)
        if has_test_methods and not has_asserts:
            self.add(0, "APX008", self.class_name)
        method_pattern = re.compile(r"@\s*isTest[^\n]*\n\s*(?:public\s+|private\s+)?static\s+void\s+(\w+)\s*\(", re.I)
        for match in method_pattern.finditer(self.code):
            name = match.group(1)
            if not re.match(r"^(given\w*When\w*Then\w*|should\w+)$", name):
                self.add(self.code[:match.start(1)].count("\n"), "APX018", name)


def lint_file(path: Path) -> list[Finding]:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    return FileLinter(path, source).run()


def collect(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(p for p in path.rglob("*") if p.suffix in (".cls", ".trigger")))
        elif path.suffix in (".cls", ".trigger") and path.exists():
            files.append(path)
    return files


def format_text(findings: list[Finding]) -> str:
    return "\n".join(f"{f.file}:{f.line}: [{f.rule}] {f.severity.upper()}: {f.message}" for f in findings)


def run_hook() -> int:
    if os.environ.get("APEX_KIT_DISABLE") == "1":
        return 0
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not file_path.endswith((".cls", ".trigger")):
        return 0
    findings = lint_file(Path(file_path))
    strict = os.environ.get("APEX_KIT_STRICT") == "1"
    warn_only = os.environ.get("APEX_KIT_MODE", "").lower() == "warn"
    errors = [f for f in findings if f.severity == ERROR or strict]
    warnings = [f for f in findings if f not in errors]
    if errors and warn_only:
        warnings, errors = errors + warnings, []
    if errors:
        print(
            "salesforce-apex-patterns-kit: o arquivo viola regras de arquitetura. Corrija antes de seguir:\n"
            + format_text(errors)
            + ("\nAvisos:\n" + format_text(warnings) if warnings else "")
            + "\nReferência: knowledge/ do kit (skill apex-architecture). Supressão justificada: // apex-kit:ignore <REGRA>",
            file=sys.stderr,
        )
        return 2
    if warnings:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    "Achados de arquitetura Apex (modo aviso). Corrija o que você introduziu nesta edição; "
                    "não refatore código legado não relacionado sem o usuário pedir:\n" if warn_only else
                    "Avisos de arquitetura Apex (avalie e corrija se fizer sentido):\n"
                ) + format_text(warnings),
            }
        }))
    return 0


def main(argv: list[str]) -> int:
    if "--hook" in argv:
        return run_hook()
    fmt = "text"
    if "--format" in argv:
        fmt = argv[argv.index("--format") + 1]
    strict = "--strict" in argv
    targets = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--format")]
    findings = [f for path in collect(targets or ["."]) for f in lint_file(path)]
    if fmt == "json":
        print(json.dumps([asdict(f) for f in findings], indent=2, ensure_ascii=False))
    elif fmt == "github":
        for f in findings:
            level = "error" if f.severity == ERROR or strict else "warning"
            print(f"::{level} file={f.file},line={f.line},title={f.rule}::{f.message}")
    elif findings:
        print(format_text(findings))
    errors = [f for f in findings if f.severity == ERROR or strict]
    if fmt == "text":
        print(f"\n{len(findings)} achado(s): {len(errors)} erro(s), {len(findings) - len(errors)} aviso(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
