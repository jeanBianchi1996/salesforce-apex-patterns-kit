# 05 — Compartilhamento de registros (sharing)

| Declaração | Comportamento |
|---|---|
| `with sharing` | Aplica as regras de compartilhamento do usuário corrente (só vê/edita registros visíveis a ele). |
| `without sharing` | Ignora compartilhamento (modo sistema para visibilidade de registros). **Obrigatório** filtrar corretamente no `WHERE`. |
| `inherited sharing` | Herda do chamador; se for o ponto de entrada da transação, comporta-se como `with sharing`. |
| *(omitido)* | Herda do chamador; se for o ponto de entrada, roda **sem** sharing. Evite em classes de entrada. |

## Regra do kit (alinhada ao livro)
- **Quem está mais perto do usuário decide**: TriggerHandler, Controller, `@RestResource`, Batch → declaram `with sharing` ou `without sharing` explicitamente.
- **Camadas de baixo** (Repository, Filter, Enricher, Service, Transformer) → `inherited sharing`, propagando a decisão da borda.
- `without sharing` só com justificativa em comentário. Exemplos legítimos: Commerce/Experience Cloud (licenças que só enxergam registros próprios) precisando ler aprovadores/preços especiais; rotinas de manutenção (troca de proprietário em massa).

Atenção: um TriggerHandler `with sharing` que faz **contagem/agregação** pode subcontar se o usuário não enxergar todos os registros. Escolha conscientemente.

## [Sênior+]
- Sharing ≠ CRUD/FLS. `with sharing` **não** checa permissão de objeto/campo. Para isso use user mode (ver arquivo 02).
- Triggers rodam em system mode; a palavra-chave da classe do handler define a visibilidade das queries feitas a partir dele.
- `Database.query` / DML com `AccessLevel.USER_MODE` aplica sharing + CRUD + FLS do usuário independentemente da palavra-chave da classe.
