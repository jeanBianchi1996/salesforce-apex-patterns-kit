/**
 * Monta respostas de @RestResource sem propagar exceção (exceção propagada = rollback
 * de toda a transação, inclusive do log de integração).
 *
 *   RestResponseBuilder response = new RestResponseBuilder(RestContext.response);
 *   try {
 *       response.withBody(service.save(request));
 *   } catch (Exception e) {
 *       response.withError(e);
 *   }
 */
public inherited sharing class RestResponseBuilder {

    private final RestResponse response;

    public RestResponseBuilder(RestResponse response) {
        this.response = response;
        this.response.statusCode = 200;
        this.response.addHeader('Content-Type', 'application/json');
    }

    public RestResponseBuilder withStatus(Integer statusCode) {
        response.statusCode = statusCode;
        return this;
    }

    public RestResponseBuilder withBody(Object body) {
        response.responseBody = Blob.valueOf(JSON.serialize(body, true));
        return this;
    }

    public RestResponseBuilder withError(DmlException dmlException) {
        return withStatus(400).withBody(new RestResponseError(dmlException));
    }

    public RestResponseBuilder withError(Exception error) {
        return withStatus(400).withBody(new RestResponseError(error));
    }

    public RestResponseBuilder withError(Integer statusCode, Exception error) {
        return withStatus(statusCode).withBody(new RestResponseError(error));
    }
}
