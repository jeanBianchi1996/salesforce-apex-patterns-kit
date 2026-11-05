---
description: Cria uma integração inbound (@RestResource) ou outbound (callout) completa no padrão do kit
argument-hint: <inbound|outbound> <NomeDoRecurso> <SObject> [detalhes: chave externa, named credential, contrato]
---

Crie a integração: $ARGUMENTS

Use o agente `salesforce-integration-specialist` e a skill `apex-integrations`.

- **outbound**: `python3 <kit>/scripts/scaffold.py outbound <Nome> --sobject <Obj> --named-credential <NC>`; implemente DTOs conforme o contrato, Transformer (um campo por linha), Publisher no TriggerHandler se o disparo vier de alteração de registro.
- **inbound**: `python3 <kit>/scripts/scaffold.py inbound <Nome> --sobject <Obj> --external-id <Campo__c>`; contrato com inner classes, relacionamentos por chave externa, savepoint, log, respostas 201/400.

Depois: testes (CalloutMock / RestContext / mocks), `apex_lint.py`, lista de metadados necessários na org (Named/External Credential, campos de chave externa, objeto de log, Permission Set do usuário de integração) e um exemplo de request/response JSON.
