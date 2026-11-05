# 00 — Arquitetura em camadas (visão geral)

> Fonte conceitual: livro *Salesforce APEX: Implemente soluções com padrões e técnicas de Orientação a Objetos* (Eduardo R. de Carvalho "Bisso", Casa do Código, 2024). Texto escrito com palavras próprias; nada aqui é cópia do livro. Itens marcados **[Sênior+]** são evoluções que não estão no livro.

## A ideia central

Toda classe tem **um papel** e **uma razão para mudar** (SRP). Uma regra de negócio em Apex nunca vive "solta" dentro de uma trigger, de um controller ou de um método estático gigante. Ela é decomposta em papéis com nomes fixos, para que qualquer dev (ou LLM) saiba onde está cada coisa só pelo nome da classe.

```
               ┌───────────── Pontos de entrada (definem o sharing) ─────────────┐
               │ Trigger → <Obj>TriggerHandler   @RestResource <Ctx>Controller   │
               │ @AuraEnabled/<Ctx>Controller    Batch / Queueable / Schedulable │
               └───────────────┬─────────────────────────────────────────────────┘
                               │ delega (composição)
   ┌──────────┬────────────┬───┴───────┬──────────────┬───────────────┬─────────────┐
   │ Filter   │ Validator  │ Enricher  │ Publisher    │ InboundService│ OutboundSvc │
   │ separa,  │ valida e   │ enriquece │ dispara      │ orquestra API │ faz callout │
   │ indexa,  │ addError() │ / constrói│ integração   │ exposta       │             │
   │ agrupa   │            │ registros │ (async)      │               │             │
   └──────────┴────────────┴─────┬─────┴──────────────┴───────┬───────┴──────┬──────┘
                                 │                            │              │
                         ┌───────┴────────┐            ┌──────┴──────┐ ┌─────┴───────┐
                         │ <Obj>Repository│            │ Transformer │ │ Request/    │
                         │ SOQL + DML     │            │ mapeia dados│ │ Response    │
                         │ (único lugar)  │            │ de integração│ │ (DTOs)      │
                         └────────────────┘            └─────────────┘ └─────────────┘
```

## Catálogo de papéis (nomenclatura obrigatória)

| Papel | Nome da classe | Responsabilidade única | NÃO pode |
|---|---|---|---|
| Trigger | `<SObject>.trigger` (uma por objeto) | Uma linha: `new <SObject>TriggerHandler().run();` | Ter qualquer lógica, SOQL, DML, loop |
| TriggerHandler | `<SObject>TriggerHandler extends TriggerHandler` | Roteia eventos e **delega**; métodos de evento só chamam métodos privados | Fazer SOQL/DML/loop de regra diretamente |
| Filter | `<SObject>Filter` | Selecionar registros que mudaram, extrair Ids, indexar (`Map<Id,..>`), agrupar (`Map<K,List<..>>`) | Consultar banco, alterar campos |
| Validator | `<SObject>Validator` | Um único método público `validate(List<..>)`; cada regra em um método privado; usa `addError` | Atribuir valores (misturar validação com enriquecimento) |
| Enricher | `<Intenção>Enricher` (ex.: `InactivateOriginalContractEnricher`) | Enriquecer/montar registros (variação do Builder) no contexto de trigger | Conter SOQL/DML direto (usa Repository) |
| Publisher | `<SObject><Evento>Publisher` | Disparar integrações/eventos a partir da trigger (sempre assíncrono) | Fazer callout síncrono em trigger |
| Repository | `<SObject>Repository extends AbstractRepository` | **Todo** SOQL e DML. Métodos `findByXxx` retornam lista ou instância; `save`/`remove` | Transformar dados, ter regra de negócio |
| Service | `<Contexto>Service` | Orquestrar um caso de uso (fora do escopo de trigger) | Ser "god class" |
| OutboundService | `<Ação><Recurso>OutboundService` (ex.: `GetAddressOutboundService`) | Fazer o callout e devolver a resposta tipada | Mapear para SObject (isso é do Transformer) |
| InboundService | `<Recurso>InboundService` | Orquestrar a API exposta: transformar → persistir → logar → responder | Conhecer `RestContext` |
| Controller (REST) | `<Recurso>Controller` com `@RestResource` | Receber HTTP, delegar ao InboundService, montar resposta via `RestResponseBuilder` | Ter regra de negócio |
| Transformer | `<Recurso><Inbound/Outbound>Transformer` | Mapear DTO ⇄ SObject em integrações (variação do Adapter) | Depender de Repository/Service |
| DTO | `<Recurso>InboundRequest/InboundResponse`, `<Recurso>OutboundRequest/Response` | Contrato de integração desacoplado dos SObjects | Expor SObject diretamente para o cliente externo |
| FixtureFactory | `<SObject>FixtureFactory` (`@IsTest`) | Dados de teste: `new<Obj>()` (memória) e `create(...)` (persiste), `fromJson`, `createIntegratedScenario()` | Ser uma classe única para todos os objetos |
| Mock | `<Classe>Mock` (`@IsTest`) | Dublê que sobrescreve métodos `virtual` | Fazer DML real |

## Regras de ouro

1. **Uma trigger por objeto**, com uma linha só.
2. **Todo acesso a dados passa pelo Repository.** Se você vê `[SELECT` ou `insert/update/delete/upsert` fora de um `*Repository` (ou de teste), está errado.
3. **Sempre há um Filter no TriggerHandler**: a trigger recebe tudo; você processa apenas o que mudou de verdade.
4. **Um nível de abstração por método.** O método público conta a história; os privados fazem os detalhes. Ordem de declaração: quem chama fica em cima, quem é chamado logo abaixo (leitura de cima para baixo).
5. **Regra das três tabulações**: passou do 3º nível de indentação, extraia método/classe.
6. **Sem `if` de tipo/status espalhado**: prefira polimorfismo, Filter e composição.
7. **Testável por design**: dependências como atributos de instância, classes/métodos `virtual`, *setters* (ou `@TestVisible`) para injeção, nada de lógica em métodos `static` (exceto onde a plataforma exige — e aí as dependências ficam em atributos `static` inicializados em bloco `static`).
8. **Bulkificação sempre**: nunca SOQL/DML dentro de loop; trabalhe com `List`, `Set`, `Map`.
9. **Sharing definido na borda**: classes de entrada (TriggerHandler, Controller, RestResource, Batch) declaram `with sharing`/`without sharing`; as de baixo usam `inherited sharing` (ou omitem) e herdam.
10. **Teste antes (Test First)** e siga F.I.R.S.T.; mocke tudo que não é Repository/Trigger.

## Fluxo de decisão rápido

- Mudança em registro dispara regra? → Trigger → Handler → **Filter** → Validator/Enricher/Publisher → Repository.
- Sistema externo chama o Salesforce? → `@RestResource` Controller → InboundService → Transformer → Repository (+ log + savepoint).
- Salesforce chama sistema externo? → OutboundService (+ Transformer + DTOs). Se vier de trigger/DML → **assíncrono** (Queueable com `Database.AllowsCallouts`).
- Volume alto? → Batch (encadeado no `finish` se envolver vários objetos).
- Agendado? → Schedulable fino que só dispara o Batch/Service.

Veja os detalhes em cada arquivo desta pasta.
