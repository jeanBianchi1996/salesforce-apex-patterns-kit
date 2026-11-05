# 04 — Papéis: Repository, Filter, Enricher, Validator, Publisher

## Repository (Evans/Fowler — DDD / PoEAA)
Abstração de acesso a dados que se comporta como uma **coleção** de objetos. Concentra **todo** SOQL e DML.

Regras:
- Um Repository por SObject (`AccountRepository`, `ContractRepository`...), estendendo `AbstractRepository` (que já tem `save`/`remove` genéricos — DRY).
- Pesquisas sempre `findByXxx(...)`: `findByIds`, `findByAccountAndStatus`, `findOpenOpportunities`, `findTotalOfPendingContracts` (agregações também moram aqui).
- Retorna **sempre** `List<...>` (ou instância). Nunca retorna `null` para "não achou" — retorna lista vazia.
- Não transforma nem decide nada: recebe → persiste → devolve; ou recebe critério → pesquisa → devolve.
- Classe e métodos `virtual` para permitir mocks.
- Upsert por chave externa via `save(registros, Schema.SObjectField)`; não sobrescreva `save` para "sempre usar a chave X" (quebra o reuso).

```apex
public inherited sharing virtual class ContractRepository extends AbstractRepository {
    public virtual List<Contract> findByIds(List<String> ids) {
        return [SELECT Id, Status, OriginalContract__c FROM Contract WHERE Id IN :ids];
    }

    public virtual List<AggregateResult> findTotalOfPendingContracts(List<String> accountIds) {
        return [
            SELECT COUNT(Id) total, AccountId
            FROM Contract
            WHERE AccountId IN :accountIds AND Status NOT IN ('Assinado', 'Inativado')
            GROUP BY AccountId
        ];
    }
}
```

## Filter
Encapsula **filtro, extração, indexação e agrupamento** de SObjects em memória. Sem SOQL, sem DML, sem alterar campos. 100% testável sem banco.

Nomes: `byChangedToSignedStatus(news, olds)`, `byChangedStatus(news, olds, 'Approved')`, `byNotCreditCardAndBoleto(orders)`, `extractOriginalContractIds(contracts)`, `pullAccountIds(...)`, `indexById(...)`, `indexByAccount(...)`, `groupByStatus(...)`.

```apex
public inherited sharing class ContractFilter {
    public List<Contract> byChangedToSignedStatus(List<Contract> newContracts, Map<Id, Contract> oldContracts) {
        List<Contract> signedAmendments = new List<Contract>();
        for (Contract contract : newContracts) {
            if (isChangedToSigned(contract, oldContracts.get(contract.Id))) {
                signedAmendments.add(contract);
            }
        }
        return signedAmendments;
    }

    private Boolean isChangedToSigned(Contract contract, Contract oldContract) {
        return contract.Status == 'Assinado'
            && oldContract?.Status != 'Assinado'
            && contract.OriginalContract__c != null;
    }

    public List<String> extractOriginalContractIds(List<Contract> contracts) {
        List<String> ids = new List<String>();
        for (Contract contract : contracts) {
            ids.add(contract.OriginalContract__c);
        }
        return ids;
    }

    public Map<Id, Contract> indexById(List<Contract> contracts) {
        return new Map<Id, Contract>(contracts);
    }
}
```

## Enricher (variação do Builder — GoF)
Encapsula o **enriquecimento** (construir/modificar) de registros. O nome expressa a intenção (`InactivateOriginalContractEnricher`, `AccountContractEnricher.enrichWithTotalPendingContracts`, `OrderApprovalEnricher.enrichWithApprovers`). Use o sufixo *Enricher* em contexto de trigger; fora dele, *Builder* ou *Service*.

Estrutura típica: método público que conta a história (encontrar → transformar → salvar), com privados logo abaixo, cada um em um só nível de abstração. Pode compor um Builder para montar estruturas complexas.

## Validator
- **Um** método público `validate(List<SObject>)`; cada regra num método privado (`validateDocumentNumber(account)`), com *early return* quando válido.
- Usa `addError`. **Nunca** atribui valores (isso quebraria SRP — é papel do Enricher).
- Validadores de domínio reutilizáveis (ex.: `BrazilianDocumentValidator` para CPF/CNPJ) são compostos pelo `<Obj>Validator`.

## Publisher
Disparo de integração/evento a partir da trigger. Sempre **assíncrono**: `System.enqueueJob(new Async<Obj>OutboundService(registros))` ou `EventBus.publish(eventos)`. Filtra antes (ex.: só pedidos que mudaram para "Approved").

## Clean Code aplicado (vale para todos os papéis)
- **Nomes significativos**: sem prefixo/sufixo de tipo (`strName`, `lstOrders`, `dtToday`, `myDate`); coleções no plural; Maps dizem se são *indexados* (`ordersById`) ou *agrupados* (`groupedOrdersByStatus`); booleanos como adjetivo (`active`, `closed`); substantivos para variáveis, verbos para métodos.
- **Ordem de declaração**: leitura linear de cima para baixo.
- **Mesmo nível de abstração por método**.
- **Regra das 3 tabs**.
- Validar SRP perguntando: "se a regra X mudar, quantos métodos/classes eu altero?" A resposta deve ser **um**.
