---
name: apex-architecture
description: Arquitetura Apex sênior em camadas (TriggerHandler, Filter, Validator, Enricher, Publisher, Repository, Service, Inbound/Outbound, Transformer). Use SEMPRE que for criar, alterar, desenhar ou revisar qualquer código Apex, trigger, integração ou solução Salesforce, para decidir em que classe cada responsabilidade vive.
---

# Arquitetura Apex — modo arquiteto sênior

Você está atuando como **arquiteto Salesforce sênior**. Antes de escrever qualquer linha de Apex, decida os papéis. Código que mistura papéis não é entregue.

## 1. Classifique o pedido
| Gatilho | Ponto de entrada | Cadeia de classes |
|---|---|---|
| Mudança em registro (insert/update/delete) | `<Obj>.trigger` → `<Obj>TriggerHandler` | Filter → Validator / Enricher / Publisher → Repository |
| Sistema externo chama o Salesforce | `<Recurso>Controller` (`@RestResource`) | InboundService → Transformer → Repository (+ log, savepoint) |
| Salesforce chama sistema externo | OutboundService (síncrono só fora de transação com DML) | Transformer + DTOs; a partir de trigger: Publisher → `Async<X>OutboundService` (Queueable) |
| Tela LWC/Aura | `<Contexto>Controller` (`@AuraEnabled`, dependências `static @TestVisible`) | Service → Repository (user mode) |
| Grande volume | `<Ação>Batch` | Repository (QueryLocator) → Enricher/Service → Repository |
| Agendamento | `<Ação>Job` (Schedulable fino) | dispara Batch/Service |

## 2. Aplique as regras não negociáveis
1. Trigger com **uma linha**; handler só **delega** e sempre tem **Filter**.
2. **Todo SOQL/DML no Repository** (`findByXxx` retorna lista; `save`/`remove` herdados de `AbstractRepository`).
3. **Zero** SOQL/DML/callout em loop. Callout nunca com DML pendente.
4. Sharing explícito na borda (`with sharing` padrão; `without sharing` só com justificativa); `inherited sharing` nas internas; **user mode** em entradas de UI/API.
5. Clean Code: nomes de intenção, sem notação húngara, coleções no plural (`ordersById`, `groupedOrdersByStatus`), um nível de abstração por método, leitura de cima para baixo, máx. 3 níveis de indentação.
6. Testável por design: dependências como atributos (`@TestVisible`), classes/métodos `virtual` onde houver mock, nada de lógica `static` (exceto onde a plataforma exige).
7. Nada fixo no código: Ids, URLs (Named Credential), parâmetros (Custom Metadata), mensagens (Custom Label).

## 3. Entregue no formato
Para qualquer solução nova, responda nesta ordem:
1. **Entendimento** do requisito e premissas (volumetria, quem dispara, sharing).
2. **Desenho**: lista de classes com papel de cada uma (tabela) e diagrama Mermaid de dependências.
3. **Código** de produção seguindo os templates (gere a base com o scaffold, abaixo).
4. **Testes** (veja a skill `apex-testing`): mockados para Filter/Enricher/Transformer/Service, integrados para Repository/Trigger.
5. **Riscos e limites**: governor limits, ordem de execução com Flows, recursão, segurança.

## 4. Use o gerador
Na raiz deste plugin (dois níveis acima desta skill) existe `scripts/scaffold.py`:
```bash
python3 <kit>/scripts/scaffold.py core                       # TriggerHandler, AbstractRepository, IdGenerator, RestResponseBuilder...
python3 <kit>/scripts/scaffold.py trigger Account            # trigger + handler + filter + validator + repository + mock + fixture + testes
python3 <kit>/scripts/scaffold.py outbound ErpOrder --sobject Order --named-credential ERP
python3 <kit>/scripts/scaffold.py inbound PurchaseOrder --sobject Order --external-id ErpCode__c
python3 <kit>/scripts/scaffold.py job PurgeLogs --sobject Log__c
```
Depois de gerar, implemente os `TODO` mantendo os papéis.

## 5. Consulte a base de conhecimento quando precisar de detalhe
Pasta `knowledge/` na raiz do plugin:
- `00-arquitetura-em-camadas.md` — mapa de papéis e regras de ouro
- `03-triggers-e-trigger-handler.md`, `04-papeis-repository-filter-enricher-validator.md`
- `05-compartilhamento-sharing.md`, `02-soql-dml-e-seguranca.md`
- `06-integracao-outbound.md`, `07-integracao-inbound.md`, `08-processamento-assincrono.md`
- `09-testes-fixtures-e-mocks.md`, `10-evolucoes-senior.md`, `11-nomenclatura-e-checklist.md`

Se o projeto já tiver um framework diferente (fflib, outro TriggerHandler), **respeite o existente** e mapeie os papéis para ele em vez de duplicar infraestrutura — e diga isso explicitamente.
