# 02 — SOQL, DML e segurança

## SOQL essencial
- Navegação filho→pai com ponto (`Account.Owner.Name`); pai→filhos com subquery (`(SELECT Id FROM Contacts)`), usando o nome do relacionamento (custom: `__r`).
- **Bind variables** (`:variavel`) sempre — previnem injeção e aceitam `List`, `Set`, `Date`, `Datetime`.
- Agregações (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX` + `GROUP BY`) retornam `List<AggregateResult>`; leia com `.get('alias')`. **Calcule no banco, não em loop** — economiza heap e CPU.
- Literais de data (`LAST_N_DAYS:n`, `THIS_MONTH`, `TODAY`) evitam aritmética de datas no código.
- Query que espera um único registro e atribui a variável escalar lança exceção se vier vazio. No Repository, prefira **retornar lista** e deixe o chamador decidir.

## DML
- `insert`, `update`, `upsert`, `delete`, `undelete` — sempre em coleções.
- `upsert lista CampoExterno__c` / `Database.upsert(lista, Schema.SObjectField, ...)` para integrações por **chave externa**.
- Relacionar por chave externa sem consultar Id: `order.Account = new Account(ErpCode__c = codigo);` (standard: troque `Id` do nome do campo pelo relacionamento; custom: `__c` → `__r`). Exige DML com a chave externa configurada.
- Mestre-detalhe: o campo mestre não pode ser alterado em update (cheque antes de atribuir); o detalhe herda o compartilhamento do mestre.
- `Database.*` com `allOrNone=false` retorna `SaveResult` por registro — use em cargas parciais e logue as falhas.

## Segurança
O livro cobre bind variables e cita `WITH SECURITY_ENFORCED` (com a observação de custo e de que o autor costuma não usar). **[Sênior+]** Em 2026 o padrão recomendado pela Salesforce é **user mode**:

| Necessidade | Como fazer |
|---|---|
| Respeitar CRUD/FLS/sharing do usuário em query | `[SELECT ... WITH USER_MODE]` ou `Database.query(soql, AccessLevel.USER_MODE)` |
| Respeitar CRUD/FLS em DML | `insert as user lista;` ou `Database.insert(lista, true, AccessLevel.USER_MODE)` |
| Remover campos sem acesso sem falhar | `Security.stripInaccessible(AccessType.READABLE, registros)` |
| SOQL dinâmico | `Database.queryWithBinds(soql, binds, AccessLevel.USER_MODE)` + `String.escapeSingleQuotes` para fragmentos não bindáveis |

Regra prática do kit:
- **Entradas acionadas por usuário via UI/API** (LWC/Aura controllers, `@RestResource`) → **user mode**.
- **Automação de sistema** (triggers, batches de manutenção, integrações com usuário técnico) → system mode, mas com `with sharing` no ponto de entrada quando a regra de negócio for por visibilidade.
- `AbstractRepository` deste kit expõe `withUserMode()`/`withSystemMode()` para escolher por chamada.

## Limites que guiam o design (síncrono / assíncrono)
| Limite | Síncrono | Assíncrono |
|---|---|---|
| Queries SOQL | 100 | 200 |
| Registros retornados por SOQL | 50.000 | 50.000 |
| DML statements | 150 | 150 |
| Heap | 6 MB | 12 MB |
| CPU | 10 s | 60 s |
| Callouts | 100 | 100 |

Consulte sempre o "Apex Governor Limits" da versão de API atual — os números mudam.
