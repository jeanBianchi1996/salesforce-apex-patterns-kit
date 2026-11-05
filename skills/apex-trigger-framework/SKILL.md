---
name: apex-trigger-framework
description: Cria ou refatora triggers Salesforce no padrão TriggerHandler com Filter, Validator, Enricher e Publisher. Use quando o pedido envolver trigger, regra executada ao salvar registro, validação complexa em Apex, enriquecimento de dados ou refatoração de trigger legada.
---

# Triggers no padrão TriggerHandler

## Passo a passo
1. **Inventário**: o objeto já tem trigger? Se sim, **não crie outra** — evolua a existente para uma linha e mova a lógica para o handler.
2. **Gere a base** (se ainda não existir): `python3 <kit>/scripts/scaffold.py trigger <SObject>` (e `core` se as classes base não existirem).
3. **Mapeie cada regra** para um papel:
   | A regra… | Vai para |
   |---|---|
   | decide *quais* registros processar (mudou status, tem campo X) | `<Obj>Filter.by<Condição>(news, olds)` |
   | bloqueia salvamento | `<Obj>Validator.validate` → método privado `validate<Regra>` com `addError` |
   | preenche campos do próprio registro (before) | `<Intenção>Enricher` sem DML |
   | cria/altera outros registros (after) | `<Intenção>Enricher` → Repository |
   | integra com sistema externo | `<Obj><Evento>Publisher` → `System.enqueueJob(Async…OutboundService)` |
4. **Escreva o handler** só com delegação:
```apex
override protected void afterUpdate() {
    inactivateOriginalContracts();
    publishApprovedOrders();
}

private void inactivateOriginalContracts() {
    List<Contract> signedAmendments = filter.byChangedToSignedStatus(newContracts, oldContracts);
    inactivateOriginalContract.inactivatedBy(signedAmendments);
}
```
5. **Declare todos os eventos** usados pelo handler na trigger.
6. **Testes**: handler/trigger integrados (inclua 200 registros e verifique `Limits.getQueries()`), Filter/Enricher/Validator mockados.

## Refatorando trigger legada (sequência segura)
1. Escreva teste de caracterização (integrado) cobrindo o comportamento atual.
2. Extraia queries/DML → Repository. Rode os testes.
3. Extraia condições → Filter. Rode os testes.
4. Extraia regra com nome de intenção → Enricher/Validator. Rode os testes.
5. Mova tudo para o handler; trigger fica com uma linha. Rode os testes.
6. Adicione testes mockados das novas classes.

## Controles do `TriggerHandler` base
- `TriggerHandler.bypass('AccountTriggerHandler')` / `clearBypass` / `clearAllBypasses` — cargas e testes.
- `handler.setMaxLoopCount(1)` — evita recursão quando o after atualiza o próprio objeto.
- Sobrescreva `isEnabled()` para ligar/desligar via Custom Metadata.

## Erros comuns que você deve recusar
- Lógica, loop ou query na trigger.
- `if (Trigger.isInsert)` espalhado — use os métodos de evento.
- Callout síncrono na trigger.
- Validator que também atribui campos.
- Processar todos os `Trigger.new` sem filtrar o que mudou.

Detalhes: `knowledge/03-triggers-e-trigger-handler.md` e `knowledge/04-papeis-repository-filter-enricher-validator.md`.
