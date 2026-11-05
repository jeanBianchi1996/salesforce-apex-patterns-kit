# 03 — Triggers e o padrão TriggerHandler

## Variáveis de contexto
`Trigger.new`, `Trigger.old`, `Trigger.newMap`, `Trigger.oldMap`, `Trigger.operationType` (enum `System.TriggerOperation`: `BEFORE_INSERT`, `BEFORE_UPDATE`, `BEFORE_DELETE`, `AFTER_INSERT`, `AFTER_UPDATE`, `AFTER_DELETE`, `AFTER_UNDELETE`), `Trigger.isExecuting`.

- **Before**: validar (`addError`) e alterar campos do próprio registro **sem DML**.
- **After**: registros já têm Id; criar/alterar **outros** registros, publicar eventos, enfileirar integração.

## Evolução do código (o raciocínio que o livro constrói)
1. Tudo dentro da trigger (filtro + query + loop + DML) → ilegível, sem teste unitário possível.
2. Extrair **Repository** (query/DML) → ainda poluído.
3. Extrair **Filter** (quem mudou para "Assinado", extrair Ids, indexar por Id) → ~66% menos linhas.
4. Extrair **Enricher** com nome de intenção (`InactivateOriginalContractEnricher.inactivatedBy(...)`) → o código conta a história.
5. Mover tudo para `<Obj>TriggerHandler` → trigger com **uma linha**.

## Estrutura padrão

```apex
trigger Contract on Contract (before insert, before update, after insert, after update) {
    new ContractTriggerHandler().run();
}
```

```apex
public with sharing class ContractTriggerHandler extends TriggerHandler {
    List<Contract> newContracts;
    Map<Id, Contract> oldContracts;

    @TestVisible ContractFilter filter;
    @TestVisible ContractValidator validator;
    @TestVisible InactivateOriginalContractEnricher inactivateOriginalContract;

    public ContractTriggerHandler() {
        this((List<Contract>) Trigger.new, (Map<Id, Contract>) Trigger.oldMap);
    }

    public ContractTriggerHandler(List<Contract> newContracts, Map<Id, Contract> oldContracts) {
        this.newContracts = newContracts;
        this.oldContracts = oldContracts;
        this.filter = new ContractFilter();
        this.validator = new ContractValidator();
        this.inactivateOriginalContract = new InactivateOriginalContractEnricher();
    }

    override protected void beforeInsert() { validate(); }
    override protected void beforeUpdate() { validate(); }
    override protected void afterUpdate()  { inactivateOriginalContracts(); }

    private void validate() {
        validator.validate(newContracts);
    }

    private void inactivateOriginalContracts() {
        List<Contract> signedAmendments = filter.byChangedToSignedStatus(newContracts, oldContracts);
        inactivateOriginalContract.inactivatedBy(signedAmendments);
    }
}
```

## Checklist de um TriggerHandler
- [ ] Um handler por SObject; a trigger declara **todos** os eventos que o handler trata.
- [ ] Delegador puro: usa composição (Filter, Validator, Enricher, Publisher).
- [ ] Sempre existe um **Filter**; nada é processado sem filtrar o que mudou (`new.Campo != old.Campo`).
- [ ] Métodos sobrescritos (`afterInsert()` etc.) **só chamam** métodos privados — um nível de abstração.
- [ ] Construtor vazio lê `Trigger.*`; construtor completo recebe listas (testável sem DML).
- [ ] Declara `with sharing` ou `without sharing` explicitamente (justifique `without sharing` em comentário).
- [ ] Integrações são disparadas via Publisher **assíncrono** (callout com DML pendente é proibido).

## Base `TriggerHandler` deste kit
Implementação própria em `templates/core/classes/TriggerHandler.cls` (API de eventos compatível com o framework de Kevin O'Hara, recomendado pelo livro), com:
- roteamento por `Trigger.operationType`;
- **bypass** por nome (`TriggerHandler.bypass('AccountTriggerHandler')`) para cargas e testes;
- **controle de recursão** (`setMaxLoopCount(n)`);
- gancho `isEnabled()` sobrescrevível para ligar/desligar via Custom Metadata ou Custom Permission **[Sênior+]**.

## [Sênior+] Pontos que o livro não detalha
- **Ordem de execução**: flows *before-save* rodam antes das triggers *before*; flows *after-save* depois das triggers *after*. Evite regras duplicadas entre Flow e Apex no mesmo objeto.
- **Recursão**: um `update` no próprio objeto dentro do after dispara a trigger de novo. Use o controle de loop ou um `Set<Id>` estático de processados.
- **Bulk de 200**: triggers recebem lotes de até 200 registros; teste com 200+ registros pelo menos uma vez (teste integrado do handler).
- **Erros amigáveis**: `addError` no campo (`registro.Campo__c.addError(msg)`) para UX melhor; mensagens em Custom Label.
