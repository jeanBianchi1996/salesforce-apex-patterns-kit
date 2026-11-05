/**
 * Base de todos os TriggerHandlers (uma trigger por SObject, uma linha por trigger).
 *
 * Uso:
 *   trigger Account on Account (before insert, before update, after insert) {
 *       new AccountTriggerHandler().run();
 *   }
 *
 * Recursos:
 *  - roteamento por Trigger.operationType para métodos sobrescrevíveis;
 *  - bypass por nome de handler (cargas de dados, testes, automações conflitantes);
 *  - controle de recursão (máximo de execuções por handler na transação);
 *  - gancho isEnabled() para ligar/desligar via Custom Metadata / Custom Permission.
 *
 * API de eventos compatível com o framework de Kevin O'Hara (sfdc-trigger-framework).
 * Implementação própria do salesforce-apex-patterns-kit.
 */
public virtual class TriggerHandler {

    private static final Set<String> BYPASSED_HANDLERS = new Set<String>();
    private static final Map<String, Integer> EXECUTIONS_BY_HANDLER = new Map<String, Integer>();

    @TestVisible
    private System.TriggerOperation operation;

    private final String handlerName;
    private Integer maxExecutions;

    public TriggerHandler() {
        // Executa antes da inicialização dos atributos da subclasse:
        // String.valueOf(this) ainda é barato aqui.
        this.handlerName = String.valueOf(this).substringBefore(':');
        this.operation = Trigger.operationType;
    }

    public void run() {
        if (!shouldRun()) {
            return;
        }
        registerExecution();
        dispatch();
    }

    // ---------------------------------------------------------------- eventos

    protected virtual void beforeInsert() {}
    protected virtual void beforeUpdate() {}
    protected virtual void beforeDelete() {}
    protected virtual void afterInsert() {}
    protected virtual void afterUpdate() {}
    protected virtual void afterDelete() {}
    protected virtual void afterUndelete() {}

    /**
     * Sobrescreva para ligar/desligar o handler por configuração, por exemplo:
     *   return !TriggerSetting__mdt.getInstance(getHandlerName())?.Disabled__c;
     */
    protected virtual Boolean isEnabled() {
        return true;
    }

    // ------------------------------------------------------- controle de loop

    public void setMaxLoopCount(Integer maxExecutions) {
        this.maxExecutions = maxExecutions;
    }

    public void clearMaxLoopCount() {
        this.maxExecutions = null;
    }

    // ----------------------------------------------------------------- bypass

    public static void bypass(String handlerName) {
        BYPASSED_HANDLERS.add(handlerName);
    }

    public static void clearBypass(String handlerName) {
        BYPASSED_HANDLERS.remove(handlerName);
    }

    public static Boolean isBypassed(String handlerName) {
        return BYPASSED_HANDLERS.contains(handlerName);
    }

    public static void clearAllBypasses() {
        BYPASSED_HANDLERS.clear();
    }

    public String getHandlerName() {
        return handlerName;
    }

    // ---------------------------------------------------------------- interno

    private Boolean shouldRun() {
        if (operation == null) {
            throw new TriggerHandlerException(
                'TriggerHandler executado fora do contexto de trigger. Em testes, defina a operação via @TestVisible "operation".'
            );
        }
        return !isBypassed(handlerName) && isEnabled() && !hasExceededMaxExecutions();
    }

    private Boolean hasExceededMaxExecutions() {
        if (maxExecutions == null) {
            return false;
        }
        Integer executions = EXECUTIONS_BY_HANDLER.get(handlerName);
        return executions != null && executions >= maxExecutions;
    }

    private void registerExecution() {
        Integer executions = EXECUTIONS_BY_HANDLER.get(handlerName);
        EXECUTIONS_BY_HANDLER.put(handlerName, executions == null ? 1 : executions + 1);
    }

    // design-kit:ignore DSN005 — roteamento de um enum fechado da plataforma; não é variação de negócio
    private void dispatch() {
        switch on operation {
            when BEFORE_INSERT { beforeInsert(); }
            when BEFORE_UPDATE { beforeUpdate(); }
            when BEFORE_DELETE { beforeDelete(); }
            when AFTER_INSERT { afterInsert(); }
            when AFTER_UPDATE { afterUpdate(); }
            when AFTER_DELETE { afterDelete(); }
            when AFTER_UNDELETE { afterUndelete(); }
        }
    }

    public class TriggerHandlerException extends Exception {}
}
