/**
 * Corpo padrão de erro das APIs expostas. Nunca devolva stack trace ao cliente.
 */
public inherited sharing class RestResponseError {

    public String error;
    public String errorType;
    public String correlationId;

    public RestResponseError(DmlException dmlException) {
        this(dmlException.getDmlMessage(0), dmlException.getTypeName());
    }

    public RestResponseError(Exception error) {
        this(error.getMessage(), error.getTypeName());
    }

    public RestResponseError(String error, String errorType) {
        this.error = error;
        this.errorType = errorType;
        this.correlationId = Request.getCurrent().getRequestId();
    }

    public static RestResponseError fromJson(String payload) {
        return (RestResponseError) JSON.deserialize(payload, RestResponseError.class);
    }
}
