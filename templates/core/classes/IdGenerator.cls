/**
 * Gera Ids falsos e VÁLIDOS (prefixo real do SObject) para testes mockados.
 * Nunca use esses Ids em DML real: eles não existem na org.
 *
 *   Order order = (Order) IdGenerator.generate(new Order());
 *   Id fakeAccountId = IdGenerator.generate(Account.SObjectType);
 *   IdGenerator.generate(orderItems); // preenche só quem está sem Id
 */
@IsTest
public class IdGenerator {

    private static final Integer ID_BODY_LENGTH = 12;
    private static Integer sequence = 0;

    public static Id generate(Schema.SObjectType sObjectType) {
        sequence++;
        String counter = String.valueOf(sequence);
        String keyPrefix = sObjectType.getDescribe().getKeyPrefix();
        return Id.valueOf(keyPrefix + '0'.repeat(ID_BODY_LENGTH - counter.length()) + counter);
    }

    public static SObject generate(SObject record) {
        if (record.Id == null) {
            record.Id = generate(record.getSObjectType());
        }
        return record;
    }

    public static List<SObject> generate(List<SObject> records) {
        for (SObject record : records) {
            generate(record);
        }
        return records;
    }
}
