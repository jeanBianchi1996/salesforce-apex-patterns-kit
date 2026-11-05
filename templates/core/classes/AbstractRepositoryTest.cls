@IsTest
private class AbstractRepositoryTest {

    // Repository é testado de forma INTEGRADA: o propósito dele é falar com o banco.
    private class AccountTestRepository extends AbstractRepository {
        public List<Account> findByName(String name) {
            return (List<Account>) query(
                'SELECT Id, Name FROM Account WHERE Name = :name',
                new Map<String, Object>{ 'name' => name }
            );
        }
    }

    @IsTest
    static void givenNewAndExistingRecordsWhenSaveThenInsertAndUpdate() {
        AccountTestRepository repository = new AccountTestRepository();
        Account existing = (Account) repository.save(new Account(Name = 'Existente'));
        existing.Name = 'Existente Atualizada';
        Account newAccount = new Account(Name = 'Nova');

        Test.startTest();
        repository.save(new List<SObject>{ existing, newAccount });
        Test.stopTest();

        Assert.isNotNull(newAccount.Id, 'Registro novo deve receber Id');
        Assert.areEqual(1, repository.findByName('Existente Atualizada').size());
        Assert.areEqual(1, repository.findByName('Nova').size());
    }

    @IsTest
    static void givenEmptyOrNullListWhenSaveThenReturnWithoutDml() {
        AbstractRepository repository = new AbstractRepository();

        Test.startTest();
        List<SObject> emptyResult = repository.save(new List<SObject>());
        List<SObject> nullResult = repository.save((List<SObject>) null);
        Test.stopTest();

        Assert.isTrue(emptyResult.isEmpty());
        Assert.isNull(nullResult);
        Assert.areEqual(0, Limits.getDmlStatements());
    }

    @IsTest
    static void givenGenericListWhenConvertToTypedListThenReturnConcreteListType() {
        AccountTestRepository repository = new AccountTestRepository();
        List<SObject> records = new List<SObject>{ new Account(Name = 'Tipada') };

        List<SObject> typedRecords = repository.toTypedList(records);

        Assert.isInstanceOfType(typedRecords, List<Account>.class);
        Assert.areEqual(records.get(0), typedRecords.get(0));
    }

    @IsTest
    static void givenStoredRecordWhenRemoveThenDelete() {
        AccountTestRepository repository = new AccountTestRepository();
        Account account = (Account) repository.save(new Account(Name = 'Remover'));

        Test.startTest();
        repository.remove(account);
        Test.stopTest();

        Assert.isTrue(repository.findByName('Remover').isEmpty());
    }
}
