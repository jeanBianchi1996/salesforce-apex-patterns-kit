# 01 — Orientação a Objetos em Apex (base para todos os padrões)

Apex é ~95% Java em sintaxe e convenções. Use as convenções de Java: `PascalCase` para classes, `camelCase` para métodos/variáveis, `UPPER_SNAKE_CASE` para constantes `static final`.

## Classe, estado e comportamento
- **Atributos** = estado; **métodos** = comportamento. Um objeto é uma instância com valores próprios.
- `this` referencia a instância atual; use-o para desambiguar atributos e parâmetros e para encadear construtores (`this(...)`).
- Construtores sobrecarregados: o "completo" recebe tudo; os demais delegam com `this(...)`. Isso é o que viabiliza injeção de dependência nos testes:

```apex
public with sharing class AccountTriggerHandler extends TriggerHandler {
    List<Account> newAccounts;
    Map<Id, Account> oldAccounts;

    public AccountTriggerHandler() {
        this((List<Account>) Trigger.new, (Map<Id, Account>) Trigger.oldMap);
    }

    public AccountTriggerHandler(List<Account> newAccounts, Map<Id, Account> oldAccounts) {
        this.newAccounts = newAccounts;
        this.oldAccounts = oldAccounts;
    }
}
```

## Visibilidade
| Modificador | Uso recomendado |
|---|---|
| `private` (padrão) | Detalhes de implementação. **Default para tudo que não é contrato.** |
| `protected` | Ganchos para subclasses (`virtual protected void enqueueNextJob(...)`). |
| `public` | Contrato da classe — o mínimo possível (ex.: Validator expõe só `validate`). |
| `global` | Apenas quando a plataforma exige (`@RestResource`, pacotes gerenciados). |
| `@TestVisible` | Expor atributo privado para injeção em teste sem abrir o contrato. |

## Coleções — escolha certa
- `List<T>`: ordem, duplicados, entrada/saída de triggers e repositórios.
- `Set<T>`: unicidade, filtros `IN :ids`, checagem `contains` O(1).
- `Map<K,V>`: **indexação** (`Map<Id, Account>` via `new Map<Id, Account>(lista)`) e **agrupamento** (`Map<Id, List<Contact>>`).
- Nomes de coleção sempre no **plural** e com contexto: `approvedOrders`, `ordersByStatus` (indexado), `groupedOrdersByStatus` (agrupado). Nunca `lstOrder`, `orderList`, `mapOrder`.

## Sobrecarga (overload)
Mesmo nome, assinaturas diferentes — oferece conveniência sem duplicar lógica. A versão simples delega para a completa:

```apex
public virtual SObject save(SObject record) {
    save(new List<SObject>{ record });
    return record;
}
```

## Herança — a pergunta "é um?"
Use herança somente quando a subclasse **é um** tipo da superclasse (ex.: `OrderRepository` **é um** `AbstractRepository`). Para "tem um"/"usa um", use composição.
- `virtual` = pode ser estendida/sobrescrita; `abstract` = obriga implementação; `override` = sobrescreve; `super` = acessa a mãe.
- Em Apex, **classes e métodos são finais por padrão**. Para mockar por herança, a classe e o método precisam ser `virtual`.

## Polimorfismo
Código cliente depende do tipo-base; o comportamento concreto é decidido em tempo de execução. É o que permite:
- `AbstractRepository` genérico para qualquer `SObject`;
- trocar `OrderRepository` por `OrderRepositoryMock` sem tocar no serviço;
- substituir cadeias de `if/else` por tipo por classes especializadas (ex.: cálculo de bônus por cargo: `Analyst`, `Manager`, `Director` estendendo `Employee` e sobrescrevendo `calculateBonus()`).

## Interfaces
Contratos sem implementação. Use para: pontos de extensão (`Queueable`, `Schedulable`, `Database.Batchable<SObject>`, `HttpCalloutMock`, `System.StubProvider`) e para estratégias plugáveis (ex.: `Type.forName(nomeVindoDeCustomMetadata).newInstance()`).

## Ciclo de vida
Objetos vivem dentro da **transação**. Atributos `static` também duram só a transação (não há sessão entre requisições) — por isso `static` serve como cache por transação e controle de recursão, nunca como estado persistente.
