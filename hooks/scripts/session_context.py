#!/usr/bin/env python3
"""
SessionStart: em projetos Salesforce, injeta no contexto do Claude o resumo das regras do kit.
Silencioso fora de projetos Salesforce (sem sfdx-project.json / force-app).
"""
import os
import sys
from pathlib import Path

CONTEXT = """\
[salesforce-apex-patterns-kit ativo] Atue como ARQUITETO SALESFORCE SÊNIOR e aplique SEMPRE estes padrões em Apex:
- 1 trigger por objeto, 1 linha: new <Obj>TriggerHandler().run(); handler extends TriggerHandler e só DELEGA.
- Papéis fixos: Filter (selecionar/indexar/agrupar), Validator (validate + addError, nunca atribui), Enricher (enriquecer),
  Publisher (integração assíncrona), <Obj>Repository extends AbstractRepository (TODO SOQL/DML, findByXxx retorna lista),
  OutboundService + Transformer + DTOs (callouts), Controller @RestResource fino + InboundService (savepoint, 400 sem propagar exceção).
- Nada de SOQL/DML/callout em loop; callout nunca com DML pendente (Queueable + Database.AllowsCallouts).
- Sharing explícito nas classes de entrada; inherited sharing nas internas; user mode em entradas de UI/API.
- Clean Code: nomes sem notação húngara, coleções no plural, 1 nível de abstração por método, máx. 3 níveis de indentação.
- Testes F.I.R.S.T., BDD (given...When...Then...), FixtureFactory por objeto, Mocks por herança (classes virtual,
  dependências injetáveis) ou framework Mocker; IdGenerator para Ids falsos; nunca SeeAllData nem Test.isRunningTest().
- Gere código novo com: python3 "$KIT/scripts/scaffold.py" <core|trigger|data|outbound|inbound|batch|job> ...
Detalhes: skills apex-* e pasta knowledge/ do kit. O hook apex_lint valida cada .cls/.trigger salvo.
"""


def is_salesforce_project(root: Path) -> bool:
    return (root / "sfdx-project.json").exists() or (root / "force-app").is_dir()


def main() -> int:
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    if os.environ.get("APEX_KIT_DISABLE") == "1" or not is_salesforce_project(root):
        return 0
    kit = os.environ.get("CLAUDE_PLUGIN_ROOT", str(Path(__file__).resolve().parents[2]))
    print(CONTEXT.replace("$KIT", kit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
