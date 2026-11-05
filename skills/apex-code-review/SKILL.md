---
name: apex-code-review
description: Revisão de código Apex como arquiteto sênior, com checklist bloqueante (papéis, bulkificação, limites, segurança, sharing, Clean Code, testes) e linter de arquitetura apex_lint. Use quando pedirem revisão, code review, auditoria, análise de PR ou "o que está errado neste código Apex".
---

# Code review Apex

## 1. Rode o linter de arquitetura
```bash
python3 <kit>/hooks/scripts/apex_lint.py <caminho> --format text
```
Ele cobre: trigger com lógica (APX001), SOQL/DML fora de Repository (APX002/003), SOQL/DML em loop (APX004/014), notação húngara (APX005), `Test.isRunningTest` (APX006), `SeeAllData` (APX007), teste sem assert (APX008), Id fixo (APX009), endpoint fixo (APX010), sharing ausente/injustificado (APX011/012), indentação > 3 (APX013), `@future` (APX015), `SECURITY_ENFORCED` (APX016), SOQL concatenado (APX017), nome de teste fora do BDD (APX018), callout em loop (APX019). Se o projeto usar PMD/Code Analyzer, rode também.

## 2. Revise o que o linter não vê
- **Papéis**: cada classe tem uma razão para mudar? Validator atribuindo campo? Transformer consultando banco? Service virando god class?
- **Filter presente** no handler? Processa só o que mudou?
- **Limites**: pior caso de volumetria por transação; queries seletivas (campos indexados); heap com coleções grandes.
- **Transação**: callout após DML? savepoint/rollback em inbound? log que se perde no rollback?
- **Segurança**: user mode onde há usuário final; dados sensíveis em log; `without sharing` realmente necessário?
- **Ordem de execução / automação duplicada** com Flows no mesmo objeto.
- **Testes**: asserts significativos (não só cobertura), sucesso + falha, bulk de 200, estratégia mock × integrado correta.
- **Nomes e legibilidade**: intenção clara, um nível de abstração, ordem de leitura.

## 3. Formato do parecer
```
## Resumo
<aprovado | aprovado com ressalvas | reprovado> — 1 frase do porquê

## Bloqueantes
- [arquivo:linha] problema → correção proposta (com trecho de código)

## Melhorias
- ...

## Pontos positivos
- ...
```
Ordene por severidade. Para cada bloqueante, mostre o código corrigido no padrão do kit, não apenas a crítica.

Checklist completo: `knowledge/11-nomenclatura-e-checklist.md`.
