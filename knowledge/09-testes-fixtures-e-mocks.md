# 09 — Testes: F.I.R.S.T., FixtureFactory, dublês e o framework Mocker

## Princípios F.I.R.S.T. (Clean Code, R. C. Martin)
- **Fast** — feedback rápido; DML em massa nos testes multiplica o tempo de deploy.
- **Independent** — qualquer ordem, nenhum teste depende de outro.
- **Repeatable** — determinístico em qualquer org. **Proibido `@IsTest(SeeAllData=true)`**.
- **Self-validating** — sempre com asserções (`Assert.areEqual`, `Assert.isTrue`, `Assert.fail`...). Teste sem assert é só cobertura.
- **Timely** — teste escrito antes (Test First / TDD). Classe difícil de testar = problema de design.

## Nomenclatura
- BDD: `given<Contexto>When<Ação>Then<Resultado>` (ex.: `givenInvalidZipCodeWhenFindAddressThenReturnNull`), ou `should<Resultado>When<Contexto>`.
- Corpo organizado em *given / when / then* (ou *arrange / act / assert*). `Test.startTest()`/`stopTest()` envolvem só o *when*.

## FixtureFactory (dados de teste)
- `@IsTest public class <Obj>FixtureFactory` — uma por objeto, **nunca** uma fábrica única.
- `new<Obj>(...)` → instância em memória (sem DML). `create(...)` → persiste (sobrecarregado: `create(campos...)` e `create(<Obj> registro)`).
- `fromJson(payload)` / `fromJsonArray(payload)` → ótimo para mocks (inclusive campos somente leitura e relacionamentos).
- Métodos `static`, respeitando campos obrigatórios e regras de validação.
- Hierarquias (Account → Product2 → PricebookEntry → Opportunity → OpportunityLineItem → Contract): `createIntegratedScenario()` retorna `Map<String, SObject>` com chaves (`'account'`, `'product'`, `'priceBook'`...), cada fábrica reaproveita o cenário da anterior. Pricebook padrão via `Test.getStandardPricebookId()`.

## Dublês de teste (Meszaros — xUnit Test Patterns)
| Tipo | O que é | No kit |
|---|---|---|
| **Fake** | Implementação alternativa com a mesma assinatura | `OrderRepositoryMock extends OrderRepository` sobrescrevendo `save` |
| **Stub** | Devolve respostas pré-definidas | `HttpCalloutMock`, Mock que desserializa um JSON passado no construtor |
| **Spy** | Stub que registra chamadas (quantas vezes) | `shouldBeCalledOnce()` no Mocker; contador em Fake |
| **Mock** | Tudo acima + verificação de expectativas | Mocker (`mocker.assert()`) |

### Fake/Stub por herança (sem framework)
Pré-requisitos na classe de produção:
- classe e métodos **`virtual`**;
- dependências como **atributos de instância**, com *setter* ou `@TestVisible` para injeção;
- **nada de `static`** na lógica (não há sobrescrita).

```apex
@IsTest
public class OrderRepositoryMock extends OrderRepository {
    override public List<SObject> save(List<SObject> records, Schema.SObjectField field) {
        return IdGenerator.generate(records); // Id falso válido, sem DML
    }
}

@IsTest
public class OrderRepositoryDmlExceptionMock extends OrderRepository {
    override public List<SObject> save(List<SObject> records, Schema.SObjectField field) {
        throw new DmlException('Invalid Account');
    }
}
```

- **`IdGenerator`** (`@IsTest`) gera Ids falsos válidos a partir do prefixo do SObject — elimina o truque de copiar Ids reais da org. Implementação própria em `templates/core/classes/IdGenerator.cls`.
- Mantenha um Mock "padrão" por Repository junto aos testes do Repository; todos os consumidores reutilizam.
- **Nunca** deixe um teste mockado fazer DML real (dados falsos + DML = `INVALID_CROSS_REFERENCE_KEY` em outra org).

### Framework Mocker (Stub API: `System.StubProvider` + `Test.createStub`)
O livro usa o **GS Apex Mocking Framework** (https://github.com/gscloudsolutions/GS-Apex-Mocking-Framework). Instale-o no projeto (não está incluído neste kit). Fluxo AAA:

```apex
// Arrange
Mocker mocker = Mocker.startStubbing();
ContractRepository repository = (ContractRepository) mocker.mock(ContractRepository.class);
mocker.when(repository.findByIds(new List<String>{ '' }))
      .withAnyValues()
      .thenReturn(originalContracts)
      .shouldBeCalledOnce();
mocker.when(repository.save(new List<Contract>()))
      .withAnyValues()
      .thenReturn(expectedContracts)
      .shouldBeCalledOnce();
mocker.stopStubbing();

InactivateOriginalContractEnricher enricher = new InactivateOriginalContractEnricher();
enricher.setRepository(repository);

// Act
List<Contract> inactivated = enricher.inactivatedBy(signedContracts);

// Assert
mocker.assert();                       // verifica as expectativas (Spy)
Assert.areEqual('Inativado', inactivated[0].Status);
```

Recursos: `when(...).thenReturn(...)`, `withAnyValues()` (ignora argumentos; combinável com configurações específicas), `thenThrow(new DmlException(...))`, `shouldBeCalledOnce()`, `shouldBeCalled(n)`, `shouldNeverBeCalled()`, `shouldBeCalledBetween(min, max)`. Use `shouldBeCalledOnce()` em métodos de Repository para **provar que não há SOQL/DML em loop**.
Limitação: não faz mock parcial (substituir só um método da própria classe testada) → use Fake por herança.

### Classes com escopo estático (`@RestResource`, `@AuraEnabled`, `@InvocableMethod`)
Declare as dependências como atributos **`static`** inicializados em bloco `static` (ou na declaração) e `@TestVisible`; o teste substitui pelo mock.

## Matriz: mockado × integrado
| Tipo de classe | Estratégia |
|---|---|
| Repository | **Integrado** (o propósito é falar com o banco; pega validation rules/flows) |
| Trigger / TriggerHandler | **Integrado** (inclua um cenário com 200 registros) |
| Filter | 100% mockado (listas em memória) |
| Validator | Mockado: instâncias em memória; `addError` fora de trigger não lança exceção, então verifique com `registro.hasErrors()` / `registro.getErrors()`. O caminho com DML fica no teste integrado do handler |
| Enricher | 100% mockado |
| Transformer | 100% mockado, **um assert por linha mapeada** |
| OutboundService | Mockado (`Test.setMock`); ≥1 integrado se houver DML com flows |
| InboundService / Controller | Mockado; ≥1 integrado cobrindo o caminho parametrizado |
| Future / Queueable / Schedulable | Mockado |
| Batch | Mockado no `execute`; ≥1 integrado se o contexto pedir |

## Anti-padrões proibidos
- `Test.isRunningTest()` em código de produção → substitua por gancho `protected virtual` + Mock.
- `SeeAllData=true`.
- Teste sem assert; `System.assert(true)` como "verificação".
- Ids reais hard-coded.
- Fixture duplicada em cada classe de teste.
