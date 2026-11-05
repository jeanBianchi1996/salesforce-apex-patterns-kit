# 08 — Processamento assíncrono: Future, Queueable, Schedulable, Batch

## Quando usar cada um
| Necessidade | Ferramenta | Observações |
|---|---|---|
| Disparo simples, parâmetros primitivos, "fire and forget" | `@future` (`callout=true` se houver callout) | `public static void`; só tipos primitivos/coleções deles; não pode chamar outro `@future`; máx. 50 por transação → **agrupe** (receba `List<Id>`, não 1 Id por chamada). |
| Objetos complexos, encadeamento, Job Id para rastrear | `Queueable` (+ `Database.AllowsCallouts`) | `System.enqueueJob(new Job(lista))`. Preferido para integrações vindas de trigger. |
| Execução em horário | `Schedulable` | Fino: só dispara Batch/Service. Cron de 7 campos (seg min hora dia-mês mês dia-semana [ano]). |
| Volume alto (até 50 milhões via QueryLocator) | `Database.Batchable<SObject>` | `start` → `execute` (lotes, padrão 200) → `finish`. Vários objetos? **Encadeie** no `finish`. |

## Padrões do kit
- `Async<Obj>OutboundService implements Queueable, Database.AllowsCallouts` chamado pelo Publisher do TriggerHandler, **apenas** com registros filtrados.
- O Queueable delega para o OutboundService (não faz o callout "na mão").
- Schedulable de manutenção (ex.: `PurgeLogJob`) usa Repository (`findByCreatedLessThanDays(n)` com `LAST_N_DAYS:n`).
- Batch: `start` usa o Repository para obter o `QueryLocator`; `execute` constrói/atualiza e salva via Repository; algoritmos complexos vão para classes próprias (Enricher/Service).
- Planeje volumetria pelo **pior caso** (ex.: 200 contas × 200 oportunidades = 40.000 linhas > limite de 10.000 DML rows → separe em batches encadeados).

## Rastreamento
- `CronTrigger` / `CronJobDetail` para agendamentos (cancelar com `System.abortJob(id)`).
- `AsyncApexJob` para Batch/Queueable (`Status`, `TotalJobItems`, `JobItemsProcessed`, `NumberOfErrors`).
- Limites: 100 jobs agendados; execuções assíncronas/dia = max(250.000, licenças × 200).

## Testes
- Todo assíncrono executa no `Test.stopTest()`; envolva a chamada com `Test.startTest()`/`stopTest()`.
- Schedulable: nomes de job únicos por teste (CronTrigger persiste nomes da org).
- `Test.setCreatedDate(id, data)` para simular registros antigos.
- Batch: teste **estrutura**, não volume — poucos registros bastam.
- `@TestSetup` só quando **todos** os métodos usam os mesmos dados (senão deixa a suíte lenta).
- Encadeamento de Queueable não roda em teste (profundidade máxima): **não** use `Test.isRunningTest()`; extraia `protected virtual void enqueueNextJob(...)` e sobrescreva num Mock.

## [Sênior+]
- **Transaction Finalizer** (`System.attachFinalizer(new MeuFinalizer())`) em Queueables para logar falhas e reenfileirar com retry.
- `AsyncOptions` (`MaximumQueueableStackDepth`, `DuplicateSignature`) para controlar profundidade de cadeia e evitar jobs duplicados.
- `Database.Stateful` só quando precisar acumular estado entre lotes (custa serialização).
- Prefira **Platform Events** para desacoplar produtores/consumidores e para cargas com picos.
- Evite `@future` em código novo; Queueable cobre os mesmos casos com mais controle.
