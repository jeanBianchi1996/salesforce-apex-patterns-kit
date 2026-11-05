/**
 * Base de todos os Repositories: concentra o DML genérico para qualquer SObject (DRY).
 * Repositories concretos só acrescentam os findByXxx do seu objeto.
 *
 *   public inherited sharing virtual class AccountRepository extends AbstractRepository {
 *       public virtual List<Account> findByIds(Set<Id> ids) {
 *           return (List<Account>) query('SELECT Id, Name FROM Account WHERE Id IN :ids',
 *                                        new Map<String, Object>{ 'ids' => ids });
 *       }
 *   }
 *
 * Decisões:
 *  - save() separa inserts (Id nulo) de updates: upsert em List<SObject> genérica
 *    falha em tempo de execução.
 *  - save(records, externalIdField) converte para lista tipada antes do Database.upsert.
 *  - Modo de acesso configurável por instância: system mode (padrão, triggers/batches)
 *    ou user mode (entradas de UI/API) via withUserMode().
 *  - Tudo virtual para permitir Mocks por herança.
 */
public inherited sharing virtual class AbstractRepository {

    protected System.AccessLevel accessLevel = System.AccessLevel.SYSTEM_MODE;

    public virtual AbstractRepository withUserMode() {
        this.accessLevel = System.AccessLevel.USER_MODE;
        return this;
    }

    public virtual AbstractRepository withSystemMode() {
        this.accessLevel = System.AccessLevel.SYSTEM_MODE;
        return this;
    }

    // ------------------------------------------------------------------- save

    public virtual SObject save(SObject record) {
        save(new List<SObject>{ record });
        return record;
    }

    public virtual List<SObject> save(List<SObject> records) {
        if (records == null || records.isEmpty()) {
            return records;
        }
        List<SObject> newRecords = new List<SObject>();
        List<SObject> existingRecords = new List<SObject>();
        for (SObject record : records) {
            if (record.Id == null) {
                newRecords.add(record);
            } else {
                existingRecords.add(record);
            }
        }
        if (!newRecords.isEmpty()) {
            Database.insert(newRecords, true, accessLevel);
        }
        if (!existingRecords.isEmpty()) {
            Database.update(existingRecords, true, accessLevel);
        }
        return records;
    }

    public virtual List<SObject> save(List<SObject> records, Schema.SObjectField externalIdField) {
        if (records == null || records.isEmpty()) {
            return records;
        }
        Database.upsert(toTypedList(records), externalIdField, true, accessLevel);
        return records;
    }

    // ----------------------------------------------------------------- remove

    public virtual void remove(SObject record) {
        remove(new List<SObject>{ record });
    }

    public virtual void remove(List<SObject> records) {
        if (records == null || records.isEmpty()) {
            return;
        }
        Database.delete(records, true, accessLevel);
    }

    // ------------------------------------------------------------------ query

    /**
     * SOQL dinâmico seguro: sempre com binds, nunca com concatenação de valores.
     */
    protected virtual List<SObject> query(String soql, Map<String, Object> binds) {
        return Database.queryWithBinds(soql, binds == null ? new Map<String, Object>() : binds, accessLevel);
    }

    // ---------------------------------------------------------------- interno

    /**
     * Garante que a lista tenha o tipo concreto (List<Account>, List<Order>...) exigido pelo upsert.
     * Todos os registros devem ser do mesmo SObjectType.
     */
    protected List<SObject> toTypedList(List<SObject> records) {
        Schema.SObjectType sObjectType = records.get(0).getSObjectType();
        List<SObject> typedRecords = (List<SObject>) Type.forName('List<' + sObjectType + '>').newInstance();
        typedRecords.addAll(records);
        return typedRecords;
    }
}
