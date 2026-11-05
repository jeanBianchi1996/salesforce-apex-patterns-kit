# 11 — Nomenclatura (cola rápida) e checklist de PR

## Nomes de classes
| Contexto | Padrão | Exemplo |
|---|---|---|
| Trigger | `<SObject>` | `Account.trigger` |
| Handler | `<SObject>TriggerHandler` | `OrderTriggerHandler` |
| Filtro | `<SObject>Filter` | `OrderFilter` |
| Validação | `<SObject>Validator` / `<Domínio>Validator` | `AccountValidator`, `BrazilianDocumentValidator` |
| Enriquecimento | `<Intenção>Enricher` | `OrderApprovalEnricher` |
| Disparo de integração | `<SObject><Evento>Publisher` | `OrderApprovedPublisher` |
| Dados | `<SObject>Repository` | `ContractRepository` |
| Caso de uso | `<Contexto>Service` | `OrderApprovalService` |
| Callout | `<Ação><Recurso>OutboundService` | `GetAddressOutboundService` |
| Callout assíncrono | `Async<Recurso>OutboundService` | `AsyncOrderOutboundService` |
| API exposta | `<Recurso>Controller` + `<Recurso>InboundService` | `OrderController`, `OrderInboundService` |
| Mapeamento de integração | `<Recurso><Inbound/Outbound>Transformer` | `PurchaseOrderInboundTransformer` |
| DTOs | `<Recurso>InboundRequest/Response`, `<Recurso>OutboundRequest/Response` | `PurchaseOrderInboundRequest` |
| Agendado | `<Ação>Job` | `PurgeLogJob` |
| Lote | `<Ação>Batch` | `ChangeCaseOwnerBatch` |
| Teste | `<Classe>Test` | `OrderFilterTest` |
| Dados de teste | `<SObject>FixtureFactory` / `<Recurso>FixtureFactory` | `AccountFixtureFactory` |
| Dublê | `<Classe>Mock`, `<Classe><Cenário>Mock` | `OrderRepositoryDmlExceptionMock` |

## Nomes de métodos
- Repository: `findBy<Critério>`, `save`, `remove`.
- Filter: `by<Condição>`, `extract<X>Ids`/`pull<X>Ids`, `indexBy<Campo>`, `groupBy<Campo>`.
- Validator: `validate` (público) + `validate<Regra>` (privados).
- Enricher: verbo de intenção (`inactivatedBy`, `enrichWithApprovers`).
- Transformer: `to<Destino>` (`toLead`, `toOrderItems`, `toLog`).
- Fixture: `new<Obj>`, `create`, `fromJson`, `fromJsonArray`, `createIntegratedScenario`.
- Teste: `given...When...Then...`.

## Nomes de variáveis
- Sem notação húngara: ❌ `lstAccounts`, `strName`, `mapOrders`, `dtToday`, `myDate`, `accountList` → ✅ `accounts`, `name`, `ordersById`, `today`, `createdDate`.
- Coleção = plural com contexto (`approvedOrders`). Map indexado = `<plural>By<Chave>`; agrupado = `grouped<Plural>By<Chave>`.
- `case` é reservado: use `caze` ou `supportCase`, nunca `cs`/`c`.

## Checklist de Pull Request (bloqueante)
- [ ] Trigger com uma linha; handler delega; Filter presente.
- [ ] Nenhum SOQL/DML fora de `*Repository` (exceto testes).
- [ ] Nenhum SOQL/DML/callout dentro de loop.
- [ ] Callout nunca na mesma transação de DML pendente (assíncrono a partir de trigger).
- [ ] Sharing explícito nas classes de entrada; `without sharing` justificado.
- [ ] Segurança: user mode em entradas de UI/API; nada de SOQL dinâmico concatenado sem escape/bind.
- [ ] Sem Ids, URLs, credenciais ou strings mágicas hard-coded.
- [ ] Métodos com um nível de abstração; ≤ 3 níveis de indentação; nomes significativos.
- [ ] Classes de produção testáveis (dependências injetáveis, `virtual` onde for mockado).
- [ ] Testes F.I.R.S.T., BDD, com asserts; Fixtures reutilizadas; sem `SeeAllData`, sem `Test.isRunningTest()` em produção.
- [ ] Cenários de sucesso **e** falha cobertos; Transformers com assert por linha.
- [ ] Bulk testado (200 registros) no teste integrado do handler.
