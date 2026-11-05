---
name: apex-testing
description: Testes Apex de nível sênior — F.I.R.S.T., TDD, nomes BDD, FixtureFactory por objeto, createIntegratedScenario, dublês (Fake, Stub, Spy, Mock) por herança, framework Mocker (Stub API), IdGenerator, HttpCalloutMock e a matriz mockado × integrado. Use ao escrever, corrigir ou acelerar testes Apex, aumentar cobertura ou quando uma classe estiver difícil de testar.
---

# Testes Apex

## Fluxo TDD
1. Escreva o teste com nome `given<Contexto>When<Ação>Then<Resultado>`.
2. Estruture em *given / when / then*; `Test.startTest()/stopTest()` só no *when*.
3. Faça passar com o mínimo de código; refatore mantendo verde.
4. Cubra **sucesso e falha** (exceções, limites, dados inválidos).

## Escolha a estratégia (matriz do kit)
| Classe | Estratégia |
|---|---|
| Repository, Trigger/TriggerHandler | **Integrado** (FixtureFactory; handler com 200 registros) |
| Filter, Enricher, Transformer, Validator, Service | **Mockado** (instâncias em memória, Repository mock, IdGenerator) |
| OutboundService | `HttpCalloutMock` (sucesso + falha) |
| Controller REST/LWC | Mockado via dependência `static @TestVisible` |
| Queueable/Batch/Schedulable | Mockado no `execute`; 1 integrado de ponta a ponta |

## FixtureFactory
- Uma por objeto (`@IsTest public class <Obj>FixtureFactory`), métodos `static`.
- `new<Obj>()` (memória), `new<Plural>(n)`, `new<Plural>WithFakeId(n)`, `create(...)` (persiste), `fromJson`, `fromJsonArray`.
- Hierarquias: `createIntegratedScenario()` → `Map<String, SObject>` reaproveitado entre fábricas; pricebook padrão via `Test.getStandardPricebookId()`.

## Mock por herança (sem framework)
Pré-requisitos na produção: classe/método `virtual`, dependência como atributo `@TestVisible` (ou setter), sem `static`.
```apex
@IsTest
public class ContractRepositoryMock extends ContractRepository {
    List<Contract> storedContracts;
    public ContractRepositoryMock(List<Contract> storedContracts) { this.storedContracts = storedContracts; }
    override public List<Contract> findByIds(List<String> ids) { return storedContracts; }
    override public List<SObject> save(List<SObject> records) { return IdGenerator.generate(records); }
}
```
Cenário de erro: Mock que lança `DmlException` no `save`.

## Framework Mocker (GS Apex Mocking Framework — instalar no projeto)
```apex
Mocker mocker = Mocker.startStubbing();
ContractRepository repository = (ContractRepository) mocker.mock(ContractRepository.class);
mocker.when(repository.save(new List<Contract>()))
      .withAnyValues()
      .thenReturn(expectedContracts)
      .shouldBeCalledOnce();               // prova que não há DML em loop
mocker.when(repository.findByIds(new List<String>{ '' }))
      .withAnyValues()
      .thenThrow(new DmlException('UNABLE_TO_LOCK_ROW'));
mocker.stopStubbing();
// act ...
mocker.assert();
```
Não faz mock parcial da própria classe sob teste → use Fake por herança nesses casos.

## Proibido
`SeeAllData=true`; `Test.isRunningTest()` em produção; teste sem assert; Ids reais fixos; fixture duplicada; DML real em teste "mockado"; `@TestSetup` usado por conveniência quando nem todos os métodos precisam dos dados.

## Classe difícil de testar?
É problema de design. Aplique: extrair dependência para atributo injetável → tornar `virtual` → separar papéis (Filter/Enricher/Transformer) → só então testar.

Detalhes: `knowledge/09-testes-fixtures-e-mocks.md`.
