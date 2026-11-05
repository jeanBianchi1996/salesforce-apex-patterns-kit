---
description: Cria (ou adequa) a trigger de um SObject no padrão TriggerHandler + Filter + Validator + Repository + testes
argument-hint: <SObject> [descrição das regras]
---

Objetivo: trigger no padrão do kit para: $ARGUMENTS

1. Verifique se já existe trigger/handler para o objeto (`Grep`). Se existir, adeque-a ao padrão em vez de criar outra.
2. Garanta as classes base: se `TriggerHandler.cls` não existir em `force-app`, rode `python3 <kit>/scripts/scaffold.py core`.
3. Rode `python3 <kit>/scripts/scaffold.py trigger <SObject>` (sem `--force` se já houver arquivos).
4. Mapeie cada regra descrita para Filter / Validator / Enricher / Publisher (skill `apex-trigger-framework`) e implemente com TDD (skill `apex-testing`).
5. Ajuste os eventos da trigger aos que o handler realmente usa.
6. Rode `python3 <kit>/hooks/scripts/apex_lint.py force-app` e corrija tudo.
7. Resuma: arquivos, regras → classes, como testar.
