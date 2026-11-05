---
name: apex-data-layer
description: Camada de dados Apex com Repository (AbstractRepository), consultas SOQL seguras, DML bulk, upsert por chave externa, agregações e modos de acesso (user/system mode). Use ao escrever qualquer SOQL, DML, consulta, persistência ou ao corrigir "SOQL em loop", "Too many SOQL queries" e problemas de segurança/FLS.
---

# Repository e acesso a dados

## Regras
- Uma classe por SObject: `public inherited sharing virtual class <Obj>Repository extends AbstractRepository`.
- Somente aqui existem `[SELECT ...]`, `Database.query*`, `insert/update/upsert/delete`.
- Métodos `public virtual`, nomeados `findBy<Critério>`, retornando **lista** (vazia quando não houver resultado — nunca `null`).
- Sem regra de negócio, sem transformação. Recebe critério → devolve dados; recebe registros → persiste → devolve.
- Agregações moram aqui (`findTotalOfPendingContracts` → `List<AggregateResult>`).
- Bind variables sempre. SOQL dinâmico só com `query(soql, binds)` do `AbstractRepository` (usa `Database.queryWithBinds`).

## API herdada do `AbstractRepository`
| Método | Comportamento |
|---|---|
| `save(SObject)` / `save(List<SObject>)` | insere quem não tem Id e atualiza quem tem (seguro para listas genéricas) |
| `save(List<SObject>, Schema.SObjectField)` | upsert por chave externa (converte para lista tipada) |
| `remove(SObject)` / `remove(List<SObject>)` | delete |
| `withUserMode()` / `withSystemMode()` | CRUD/FLS/sharing do usuário vs modo sistema |
| `query(soql, binds)` (protected) | SOQL dinâmico com binds e o modo de acesso escolhido |

## Exemplo
```apex
public inherited sharing virtual class OpportunityRepository extends AbstractRepository {

    public virtual List<Opportunity> findOpenByAccountIds(Set<Id> accountIds) {
        return [
            SELECT Id, AccountId, OwnerId, StageName
            FROM Opportunity
            WHERE AccountId IN :accountIds AND IsClosed = false
        ];
    }

    public virtual List<AggregateResult> findAmountByAccountIds(Set<Id> accountIds) {
        return [
            SELECT AccountId, SUM(Amount) total
            FROM Opportunity
            WHERE AccountId IN :accountIds
            GROUP BY AccountId
        ];
    }
}
```

## Integrações por chave externa
```apex
order.Account = new Account(ErpCode__c = request.accountCode);           // standard: Id → relacionamento
order.PaymentTerm__r = new PaymentTerm__c(ExternalId__c = request.term); // custom: __c → __r
orderRepository.save(new List<Order>{ order }, Order.ErpCode__c);
```

## Quando escolher user mode
- `@AuraEnabled`, `@RestResource`, Visualforce, `@InvocableMethod` acionados pelo usuário → `new XRepository().withUserMode()`.
- Triggers, batches de manutenção, integrações com usuário técnico → system mode (padrão), sharing decidido pela classe de entrada.

## Testes
Repository é a única camada testada **sempre integrada** (pega validation rules, flows, campos obrigatórios). Use FixtureFactory e crie um `<Obj>RepositoryMock` reutilizável para os demais testes (`scaffold.py data <Obj>`).

Detalhes: `knowledge/02-soql-dml-e-seguranca.md`, `knowledge/04-...`, `knowledge/05-compartilhamento-sharing.md`.
