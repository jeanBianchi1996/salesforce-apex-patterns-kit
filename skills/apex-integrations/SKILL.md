---
name: apex-integrations
description: Integrações Salesforce em Apex — consumir APIs REST (OutboundService, Transformer, DTOs, HttpCalloutMock, Named Credential) e expor APIs (@RestResource Controller fino, InboundService, chaves externas, savepoint, log, respostas HTTP padronizadas). Use para qualquer callout, webservice, API REST, integração com ERP/sistemas externos ou JSON.
---

# Integrações Apex

## Outbound (Salesforce → externo)
1. `scaffold.py outbound <Nome> --sobject <Obj> --named-credential <NC>` gera: `<Nome>OutboundService`, `<Nome>OutboundRequest/Response`, `<Nome>OutboundTransformer`, `Async<Nome>OutboundService` (Queueable + `Database.AllowsCallouts`, em lotes e encadeado), `<Nome>CalloutMock`, fixture e testes.
2. **OutboundService**: `buildRequest` → `send` → `buildResponse`. Endpoint `callout:<NamedCredential>`, timeout explícito, erro HTTP vira exceção de domínio (ou `null` documentado).
3. **Transformer**: um campo por linha, sem dependências de Repository/Service.
4. **DTOs** com atributos idênticos ao JSON → `JSON.deserialize(body, Tipo.class)`; nada de manipular `String`.
5. Disparo a partir de trigger: Publisher filtra e enfileira o Queueable (callout com DML pendente é proibido).
6. Se o callout é genérico (ex.: CEP) e serve vários objetos, separe o serviço genérico do serviço de contexto (`GetLeadAddressOutboundService` usa `GetAddressOutboundService` + Transformer).

## Inbound (externo → Salesforce)
1. `scaffold.py inbound <Nome> --sobject <Obj> --external-id <Campo__c>` gera Controller, InboundService, Request/Response, Transformer e teste.
2. **Controller** `@RestResource(urlMapping='/api/v1/<recurso>/*')`, `global with sharing`, método `void`, delega e responde com `RestResponseBuilder` (200/201 ou 400 com `RestResponseError`). **Nunca propaga exceção** (seria rollback do log).
3. **InboundService**: `Savepoint` → transformar → upsert por chave externa → log → resposta; no `catch`: `Database.rollback(sp)`, log de falha, relança.
4. **Contrato próprio** (`<Nome>InboundRequest` com inner classes) — nunca exponha SObject.
5. Relacionamentos por chave externa no Transformer; dados mestre ausentes geram `DmlException` que deve ir para o log com o payload.
6. Dependências do Controller como `static @TestVisible` para mock.

## Testes obrigatórios
| Classe | Cenários |
|---|---|
| OutboundService | sucesso (200) e falha (4xx/5xx) com `Test.setMock(HttpCalloutMock.class, ...)`; verifique método/endpoint da request |
| Transformer | um `Assert` por campo mapeado, sem DML |
| Async…OutboundService | Repository mock + CalloutMock + encadeamento sobrescrito |
| Controller | `RestContext.request/response` novos; sucesso (status + corpo) e erro (400 + mensagem) com service mockado |
| InboundService | Repositories mockados (IdGenerator) + 1 cenário integrado se houver flows/validation rules |

## Senior+
Named/External Credentials; Custom Metadata para parâmetros; versionamento de URL; OAuth Client Credentials/JWT (nunca *password* em produção); log por Platform Event *Publish Immediately*; idempotência por chave externa; retry com Transaction Finalizer.

Detalhes: `knowledge/06-integracao-outbound.md`, `knowledge/07-integracao-inbound.md`.
