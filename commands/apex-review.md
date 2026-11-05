---
description: Code review Apex sênior (checklist bloqueante + linter de arquitetura)
argument-hint: [caminho ou arquivos; padrão = alterações do git]
---

Revise o código Apex em: $ARGUMENTS (se vazio, use `git diff --name-only` contra a branch principal, filtrando `.cls` e `.trigger`).

Use o agente `apex-code-reviewer` com a skill `apex-code-review`. Rode `python3 <kit>/hooks/scripts/apex_lint.py <arquivos>` e combine com a revisão manual. Entregue o parecer no formato: Resumo (aprovado / com ressalvas / reprovado), Bloqueantes (arquivo:linha + correção com código), Melhorias, Pontos positivos.
