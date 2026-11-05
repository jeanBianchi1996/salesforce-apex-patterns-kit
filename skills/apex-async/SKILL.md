---
name: apex-async
description: Processamento assíncrono em Apex — Queueable, @future, Schedulable (CRON), Batch (encadeamento, volumetria), Transaction Finalizers e seus testes. Use para jobs, filas, agendamentos, processamento em massa, "too many queueable jobs", "uncommitted work pending" ou quando um callout precisa sair de uma trigger.
---

# Assíncrono em Apex

## Escolha
| Caso | Use | Atenção |
|---|---|---|
| Integração disparada por trigger | `Queueable, Database.AllowsCallouts` | Passe só os Ids filtrados; lotes ≤ 100 callouts; encadeie o resto |
| Tarefa simples com primitivos | `@future` (evite em código novo) | 50 por transação → receba `List<Id>`; não chama outro `@future` |
| Rotina em horário | `Schedulable` fino | Só dispara Batch/Service; nome de job único |
| Milhões de registros | `Database.Batchable<SObject>` | `start` via Repository; `execute` delega; encadeie no `finish` quando houver vários objetos |
| Desacoplar produtor/consumidor | Platform Event | Consumidor em trigger do evento (com handler) |

## Volumetria antes de codar
Calcule o **pior caso** por lote: registros do `execute` × registros relacionados (ex.: 200 contas × 200 oportunidades = 40.000 linhas DML > 10.000) → separe em Batches encadeados ou reduza o `scope` (`Database.executeBatch(job, 50)`).

## Padrões de código
```apex
// Publisher no TriggerHandler
private void publishApprovedOrders() {
    List<Order> approvedOrders = filter.byChangedStatus(newOrders, oldOrders, 'Approved');
    if (approvedOrders.isEmpty()) {
        return;
    }
    System.enqueueJob(new AsyncOrderOutboundService(new Map<Id, Order>(approvedOrders).keySet()));
}
```
- Encadeamento testável: `protected virtual void enqueueNextJob(...)` sobrescrito no teste — **nunca** `Test.isRunningTest()`.
- Schedulable: `System.schedule(nome, '0 0 3 * * ?', new PurgeLogJob())`; acompanhe por `CronTrigger`/`CronJobDetail`; cancele com `System.abortJob`.
- Batch: acompanhe por `AsyncApexJob`; `Database.Stateful` só se precisar acumular entre lotes.

## Testes
- Tudo assíncrono roda no `Test.stopTest()`.
- `Test.setCreatedDate` para simular registros antigos; poucos registros (estrutura, não volume).
- `@TestSetup` só se todos os métodos usam os mesmos dados.
- Queueable/Batch: teste o `execute` diretamente com Repository mock para cenários de borda; 1 teste integrado de ponta a ponta.

## Senior+
`System.attachFinalizer` para log/retry; `AsyncOptions` (`MaximumQueueableStackDepth`, `DuplicateSignature`); limites diários de assíncronos = max(250.000, licenças × 200).

Detalhes: `knowledge/08-processamento-assincrono.md`.
