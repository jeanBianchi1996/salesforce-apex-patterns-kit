@IsTest
private class TriggerHandlerTest {

    private class SpyTriggerHandler extends TriggerHandler {
        List<String> calledEvents = new List<String>();

        override protected void beforeInsert() { calledEvents.add('beforeInsert'); }
        override protected void beforeUpdate() { calledEvents.add('beforeUpdate'); }
        override protected void beforeDelete() { calledEvents.add('beforeDelete'); }
        override protected void afterInsert() { calledEvents.add('afterInsert'); }
        override protected void afterUpdate() { calledEvents.add('afterUpdate'); }
        override protected void afterDelete() { calledEvents.add('afterDelete'); }
        override protected void afterUndelete() { calledEvents.add('afterUndelete'); }
    }

    private class DisabledTriggerHandler extends TriggerHandler {
        Boolean called = false;
        override protected Boolean isEnabled() { return false; }
        override protected void afterInsert() { called = true; }
    }

    private static SpyTriggerHandler newHandler(System.TriggerOperation operation) {
        SpyTriggerHandler handler = new SpyTriggerHandler();
        handler.operation = operation;
        return handler;
    }

    @IsTest
    static void givenEachOperationWhenRunThenDispatchToMatchingEvent() {
        Map<System.TriggerOperation, String> expectedEvents = new Map<System.TriggerOperation, String>{
            System.TriggerOperation.BEFORE_INSERT => 'beforeInsert',
            System.TriggerOperation.BEFORE_UPDATE => 'beforeUpdate',
            System.TriggerOperation.BEFORE_DELETE => 'beforeDelete',
            System.TriggerOperation.AFTER_INSERT => 'afterInsert',
            System.TriggerOperation.AFTER_UPDATE => 'afterUpdate',
            System.TriggerOperation.AFTER_DELETE => 'afterDelete',
            System.TriggerOperation.AFTER_UNDELETE => 'afterUndelete'
        };

        for (System.TriggerOperation operation : expectedEvents.keySet()) {
            SpyTriggerHandler handler = newHandler(operation);

            handler.run();

            Assert.areEqual(new List<String>{ expectedEvents.get(operation) }, handler.calledEvents);
        }
    }

    @IsTest
    static void givenBypassedHandlerWhenRunThenSkipEvents() {
        SpyTriggerHandler handler = newHandler(System.TriggerOperation.AFTER_INSERT);
        TriggerHandler.bypass(handler.getHandlerName());

        handler.run();

        Assert.isTrue(handler.calledEvents.isEmpty(), 'Handler em bypass não deveria executar');
        Assert.isTrue(TriggerHandler.isBypassed(handler.getHandlerName()));

        TriggerHandler.clearBypass(handler.getHandlerName());
        handler.run();

        Assert.areEqual(1, handler.calledEvents.size());
    }

    @IsTest
    static void givenMaxLoopCountWhenRunTwiceThenExecuteOnlyOnce() {
        SpyTriggerHandler handler = newHandler(System.TriggerOperation.AFTER_UPDATE);
        handler.setMaxLoopCount(1);

        handler.run();
        handler.run();

        Assert.areEqual(1, handler.calledEvents.size());
    }

    @IsTest
    static void givenDisabledHandlerWhenRunThenSkipEvents() {
        DisabledTriggerHandler handler = new DisabledTriggerHandler();
        handler.operation = System.TriggerOperation.AFTER_INSERT;

        handler.run();

        Assert.isFalse(handler.called);
    }

    @IsTest
    static void givenNoTriggerContextWhenRunThenThrowException() {
        SpyTriggerHandler handler = new SpyTriggerHandler();

        try {
            handler.run();
            Assert.fail('Deveria lançar TriggerHandlerException');
        } catch (TriggerHandler.TriggerHandlerException e) {
            Assert.isTrue(e.getMessage().contains('fora do contexto'));
        }
    }

    @IsTest
    static void givenHandlerWhenGetNameThenReturnClassName() {
        Assert.isTrue(new SpyTriggerHandler().getHandlerName().endsWith('SpyTriggerHandler'));
    }
}
