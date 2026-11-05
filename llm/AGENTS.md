<!-- salesforce-apex-patterns-kit:start -->
# Padrões Apex do projeto (salesforce-apex-patterns-kit)

Atue como **arquiteto Salesforce sênior**. Todo código Apex deste repositório segue as regras abaixo. Código que as viola não deve ser proposto nem aceito.

## Arquitetura em camadas (papéis com nomes fixos)
| Papel | Classe | Responsabilidade | Proibido |
|---|---|---|---|
| Trigger | `<Obj>.trigger` (uma por objeto) | `new <Obj>TriggerHandler().run();` — uma linha | qualquer lógica |
| Handler | `<Obj>TriggerHandler extends TriggerHandler` | delegar; métodos de evento só chamam privados | SOQL/DML/loop de regra |
| Filter | `<Obj>Filter` | selecionar o que mudou, extrair Ids, indexar, agrupar | SOQL, DML, alterar campos |
| Validator | `<Obj>Validator` | `validate(List)` + privados com `addError` | atribuir valores |
| Enricher | `<Intenção>Enricher` | enriquecer/montar registros | SOQL/DML direto |
| Publisher | `<Obj><Evento>Publisher` | disparar integração assíncrona | callout síncrono |
| Repository | `<Obj>Repository extends AbstractRepository` | TODO SOQL/DML; `findByXxx` retorna lista | regra de negócio |
| Service | `<Contexto>Service` | orquestrar caso de uso | virar god class |
| OutboundService | `<Ação><Recurso>OutboundService` | callout + DTO | mapear SObject |
| Controller REST | `<Recurso>Controller` (`@RestResource`) | delegar e responder via `RestResponseBuilder` (400 sem propagar exceção) | regra de negócio |
| InboundService | `<Recurso>InboundService` | transformar → upsert por chave externa → log; savepoint/rollback | conhecer `RestContext` |
| Transformer | `<Recurso><Inbound/Outbound>Transformer` | DTO ⇄ SObject, um campo por linha | depender de Repository/Service |
| DTO | `<Recurso>InboundRequest/Response`, `...OutboundRequest/Response` | contrato de integração | expor SObject |

## Regras obrigatórias
1. Nenhum SOQL/DML/callout dentro de loop. Bulkificação sempre (List/Set/Map).
2. Nenhum SOQL/DML fora de `*Repository` (exceto testes).
3. Callout nunca com DML pendente: a partir de trigger use `Queueable` + `Database.AllowsCallouts`.
4. Sharing explícito em classes de entrada (`with sharing` padrão; `without sharing` só com comentário justificando); `inherited sharing` nas internas; `WITH USER_MODE`/`AccessLevel.USER_MODE` em entradas de UI/API.
5. Nada fixo: Ids, URLs (use Named Credential `callout:`), segredos, parâmetros (Custom Metadata), mensagens (Custom Label).
6. Clean Code: nomes de intenção; sem notação húngara (`lstX`, `strX`, `xMap`); coleções no plural; Map indexado `xByY`, agrupado `groupedXByY`; um nível de abstração por método; métodos chamados logo abaixo de quem chama; no máximo 3 níveis de indentação.
7. Testabilidade: dependências como atributos `@TestVisible`; classes/métodos `virtual` quando mockados; sem lógica em `static` (onde a plataforma exige static, dependências em atributos `static @TestVisible`).
8. Assíncrono: Queueable > `@future`; Batch para volume (encadeado no `finish`); Schedulable fino.

## Testes
- F.I.R.S.T.; TDD; nomes `given<Contexto>When<Ação>Then<Resultado>`; *given/when/then*; asserts com mensagem.
- `<Obj>FixtureFactory` por objeto (`new<Obj>`, `create`, `fromJson`, `createIntegratedScenario`).
- Integrado: Repository e Trigger/Handler (com cenário de 200 registros). Mockado: Filter, Validator, Enricher, Transformer, Services, Controllers, assíncronos.
- Mocks por herança (`<Classe>Mock extends <Classe>`) ou framework Mocker (Stub API); `IdGenerator` para Ids falsos; `HttpCalloutMock` para callouts.
- Proibido: `SeeAllData=true`, `Test.isRunningTest()` em produção, teste sem assert, Ids reais fixos.

## Ferramentas do kit
- Gerador: `python3 <kit>/scripts/scaffold.py <core|trigger|data|outbound|inbound|batch|job> ...`
- Linter de arquitetura: `python3 <kit>/hooks/scripts/apex_lint.py force-app`
- Base de conhecimento: `<kit>/knowledge/`

Se o projeto já usa outro framework (ex.: fflib), mantenha-o e mapeie estes papéis para ele.
<!-- salesforce-apex-patterns-kit:end -->
