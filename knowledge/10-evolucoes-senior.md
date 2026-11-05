# 10 — [Sênior+] Evoluções e correções sobre o livro

O livro é a fundação. Este arquivo registra o que um arquiteto sênior acrescenta em 2026, e pontos onde o código de exemplo precisa de ajuste para produção.

## Correções técnicas
1. **`upsert` em `List<SObject>` genérica falha em tempo de execução** ("DML on generic List<SObject> only allowed for insert, update or delete"). O `save(SObject record)` que embrulha em `new List<SObject>{ record }` cai nesse erro. O `AbstractRepository` deste kit separa inserções (Id nulo) de atualizações e, para upsert por chave externa, converte para lista tipada (`List<Order>`) antes de chamar `Database.upsert`.
2. **`WITH SECURITY_ENFORCED` está superado por `WITH USER_MODE`** (mais completo, inclui sharing e não falha só pelo primeiro campo). Use user mode em entradas de UI/API.
3. **Endpoints fixos em código** → Named Credentials (`callout:Nome`).
4. **Fluxo OAuth *password*** só para testes manuais; integrações de produção usam Client Credentials ou JWT Bearer.
5. **Log gravado no `catch` e exceção relançada** é perdido no rollback, a menos que a borda devolva 400 (solução do livro) ou o log vá por Platform Event *Publish Immediately*.

## Acréscimos de arquitetura
- **Custom Metadata** para parametrizar integrações, bypass de triggers e estratégias plugáveis (`Type.forName(config.Handler__c)`).
- **Unit of Work** (inspirado em fflib) quando um caso de uso grava vários objetos relacionados: registra novos/alterados e faz um commit ordenado com savepoint. Útil como evolução do "objeto agregador" sugerido no livro.
- **Selector vs Repository**: este kit mantém o Repository do livro (consulta + DML). Se o time adotar fflib (Enterprise Patterns), mapeie: Repository ≈ Selector + UnitOfWork; Enricher/Validator ≈ Domain; Service ≈ Service.
- **Logger estruturado** (ex.: Nebula Logger) em vez de `System.debug`.
- **Platform Events / Change Data Capture** para integrações orientadas a evento.
- **Transaction Finalizers** e `AsyncOptions` em Queueables.
- **Feature flags** com Custom Permission (`FeatureManagement.checkPermission`).

## Qualidade e pipeline
- Análise estática: **PMD/Salesforce Code Analyzer** + o `apex-lint.py` deste kit (regras de arquitetura do livro).
- Cobertura mínima 75% é exigência da plataforma; meta do time: **≥ 90%** com asserts significativos.
- Rode testes locais rápidos (mockados) em todo PR; suíte integrada completa antes do deploy.
- Versão de API única no projeto (`sfdx-project.json` → `sourceApiVersion`), atualizada a cada release.
- Revisão de código guiada pelo checklist em `skills/apex-code-review/SKILL.md`.

## Decisões padrão (quando ninguém disse o contrário)
| Tema | Padrão |
|---|---|
| Sharing do TriggerHandler | `with sharing` |
| Sharing de camadas internas | `inherited sharing` |
| Modo de acesso de Repository em trigger/batch | system mode |
| Modo de acesso em controllers LWC/Aura/REST | user mode |
| Assíncrono a partir de trigger | Queueable |
| Mensagens de erro ao usuário | Custom Label |
| Constantes de picklist | classe de constantes ou `enum` mapeado — nunca string mágica repetida |
