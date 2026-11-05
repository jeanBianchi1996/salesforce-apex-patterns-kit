# 07 — Integração Inbound (Salesforce expõe API REST)

## Regras da plataforma para `@RestResource`
- Classe `global` com `@RestResource(urlMapping='/api/<recurso>/*')`; métodos `global static`.
- Um método por verbo (`@HttpGet`, `@HttpPost`, `@HttpPut`, `@HttpPatch`, `@HttpDelete`) por classe.
- Só POST/PUT/PATCH aceitam parâmetros; **o nome do parâmetro vira a chave do JSON** (`create(Lead lead)` espera `{"lead": {...}}`). Alternativa: sem parâmetro, ler `RestContext.request.requestBody`. Não misture as duas (declarar parâmetro remove o `requestBody`).
- GET/DELETE leem `RestContext.request.params` (sempre `String`).
- URL base: `https://<instancia>.my.salesforce.com/services/apexrest/<urlMapping>`.

## Arquitetura do kit
```
Cliente → <Recurso>Controller (@RestResource, fino)
            └─ <Recurso>InboundService (orquestra; testável; injeção por atributo static)
                 ├─ <Recurso>InboundTransformer (DTO → SObjects, chaves externas)
                 ├─ <Obj>Repository(s) (upsert por chave externa)
                 └─ IntegrationLogRepository (sucesso e falha)
          ← RestResponseBuilder (status + JSON) / RestResponseError
```

- **Não exponha SObjects** no contrato: use `<Recurso>InboundRequest` / `<Recurso>InboundResponse` (DTOs `global` com *inner classes*: `PurchaseItem`, `Address`...). Assim o modelo interno evolui sem quebrar consumidores.
- Sistemas externos não conhecem Ids do Salesforce → **chaves externas** (`ErpCode__c`, `ExternalId__c`) + relacionamento por referência no Transformer + `Database.upsert(registros, campo)`.

## Transação, rollback e log (o ponto mais sutil do capítulo)
- A transação nasce no request e termina no response. **Exceção propagada ao cliente = rollback de tudo, inclusive do log gravado no `catch`.**
- Solução do livro, em duas partes:
  1. **Controller** não propaga exceção: captura e responde **HTTP 400** com corpo JSON (`RestResponseBuilder.withError(e)`), método `void`.
  2. Como o rollback automático deixou de acontecer, o **InboundService** usa `Savepoint sp = Database.setSavepoint();` e, no `catch`, `Database.rollback(sp)` **antes** de gravar o log e relançar — preservando a atomicidade (pedido + itens + subitens) e mantendo o log.

```apex
public inherited sharing virtual class OrderInboundService {
    @TestVisible OrderRepository orderRepository = new OrderRepository();
    @TestVisible OrderItemRepository orderItemRepository = new OrderItemRepository();
    @TestVisible IntegrationLogRepository logRepository = new IntegrationLogRepository();
    @TestVisible PurchaseOrderInboundTransformer transformer = new PurchaseOrderInboundTransformer();

    public virtual PurchaseOrderInboundResponse save(PurchaseOrderInboundRequest purchaseOrder) {
        Savepoint savepoint = Database.setSavepoint();
        try {
            Order order = transformer.toOrder(purchaseOrder);
            orderRepository.save(new List<Order>{ order }, Order.ErpCode__c);
            orderItemRepository.save(transformer.toOrderItems(purchaseOrder), OrderItem.ErpCode__c);
            log(purchaseOrder, null);
            return new PurchaseOrderInboundResponse(order.Id);
        } catch (Exception e) {
            Database.rollback(savepoint);
            log(purchaseOrder, e);
            throw e;
        }
    }

    private void log(PurchaseOrderInboundRequest purchaseOrder, Exception error) {
        logRepository.save(transformer.toLog(purchaseOrder, error));
    }
}
```

```apex
@RestResource(urlMapping='/api/orders/*')
global with sharing class OrderController {
    @TestVisible static OrderInboundService orderInboundService = new OrderInboundService();

    @HttpPost
    global static void create(PurchaseOrderInboundRequest purchaseOrder) {
        RestResponseBuilder response = new RestResponseBuilder(RestContext.response);
        try {
            response.withBody(orderInboundService.save(purchaseOrder));
        } catch (DmlException e) {
            response.withError(e);
        } catch (Exception e) {
            response.withError(e);
        }
    }
}
```

Evolução sugerida pelo livro: um objeto agregador (Pedido + Itens + Subitens) para o Transformer devolver um só objeto e o Service ter um único `save`.

## Testes
- Controller: crie `RestContext.request = new RestRequest(); RestContext.response = new RestResponse();`, injete o service mockado (atributo `static`), assegure `statusCode` e corpo.
- InboundService: 100% mockado (Repositories mock + IdGenerator).
- Teste externo: Workbench (REST Explorer) ou Postman com OAuth2 via Connected App/External Client App.

## [Sênior+]
- **Log que sobrevive a rollback sem depender do 400**: publique um Platform Event com *Publish Immediately* e grave o log em um subscriber.
- **Versione a URL** (`/api/v1/orders/*`).
- Autenticação de servidor para servidor: OAuth 2.0 **Client Credentials** ou **JWT Bearer** (o fluxo *password* é só para teste; está desencorajado).
- Respostas de erro padronizadas (código, mensagem, `correlationId`), nunca stack trace.
- Valide o payload na borda (campos obrigatórios) antes de abrir transação.
