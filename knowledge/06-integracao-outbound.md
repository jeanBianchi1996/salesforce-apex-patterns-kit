# 06 — Integração Outbound (Salesforce consome API externa)

## Peças
| Classe | Papel |
|---|---|
| `<Ação><Recurso>OutboundService` | Monta `HttpRequest` (`buildRequest`), envia, converte `HttpResponse` em DTO (`build<X>Response`). Só isso. |
| `<Recurso>OutboundResponse` / `<Fornecedor><Recurso>Response` | DTO com atributos idênticos ao JSON (desserialização direta com `JSON.deserialize(body, Tipo.class)`). |
| `<Recurso>OutboundRequest` | DTO do corpo enviado. |
| `<Destino><Recurso>OutboundTransformer` | Mapeia DTO ⇄ SObject (`toLead(response, lead)`, `toOrderOutboundRequest(order)`). Sem dependências de Repository/Service. |
| `Get<Destino><Recurso>OutboundService` | Orquestra quando o callout é reutilizável em vários contextos (ex.: busca de CEP genérica + "endereço do Lead"). |
| `<Classe>CalloutMock implements HttpCalloutMock` (`@IsTest`) | Stub HTTP com construtor `(payload)` → 200 e `(payload, statusCode)`. |
| `<Recurso>OutboundFixtureFactory` (`@IsTest`) | `defaultSuccessPayload()`, `fromJson(payload)`. |

```apex
public inherited sharing virtual class GetAddressOutboundService {
    static final String NAMED_CREDENTIAL = 'callout:ViaCep'; // [Sênior+] nunca URL fixa

    public virtual AddressOutboundResponse findAddressByZipCode(String zipCode) {
        HttpResponse response = new Http().send(buildRequest(zipCode));
        return buildAddressResponse(response);
    }

    private HttpRequest buildRequest(String zipCode) {
        HttpRequest request = new HttpRequest();
        request.setEndpoint(NAMED_CREDENTIAL + '/ws/' + EncodingUtil.urlEncode(zipCode, 'UTF-8') + '/json/');
        request.setMethod('GET');
        request.setHeader('Content-Type', 'application/json; charset=utf-8');
        request.setTimeout(20000);
        return request;
    }

    private AddressOutboundResponse buildAddressResponse(HttpResponse response) {
        if (response.getStatusCode() != 200) {
            return null; // ou lance uma exceção de domínio — decida e documente
        }
        return (AddressOutboundResponse) JSON.deserialize(response.getBody(), AddressOutboundResponse.class);
    }
}
```

## Regras
- **Nunca** faça callout com DML pendente na mesma transação ("uncommitted work pending"). A partir de trigger, use Queueable + `Database.AllowsCallouts` (ou `@future(callout=true)`).
- Testes **não** fazem callout real: `Test.setMock(HttpCalloutMock.class, new XCalloutMock(payload, status))`. Cubra sucesso **e** falha (4xx/5xx/timeout).
- Testes de Transformer: **uma asserção por linha de mapeamento** — é onde a maioria dos bugs de integração aparece. Use instâncias em memória (`LeadFixtureFactory.newLead`), sem DML.
- Nome de teste no formato BDD: `given<Contexto>When<Ação>Then<Resultado>`.
- O serviço que orquestra **não** mapeia campos (isso é do Transformer) — mantenha o nível de abstração.

## [Sênior+] Produção
- **Named Credential + External Credential** para endpoint e autenticação (sem Remote Site Setting + segredo em código).
- Parâmetros (timeout, paths, flags) em **Custom Metadata Type** (o livro já aponta essa evolução).
- Um `RequestBuilder` configurável quando houver muitos endpoints do mesmo fornecedor.
- Log de integração (request/response/status/duração) em objeto próprio — ver arquivo 07.
- Idempotência e retry com backoff via Queueable encadeado + Transaction Finalizer.
