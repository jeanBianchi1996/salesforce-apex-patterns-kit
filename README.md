# salesforce-apex-patterns-kit

Kit plugável de **arquitetura Apex sênior**: base de conhecimento, skills, agentes, comandos, hooks, regras para LLMs e um gerador de código. Baixe o repo, plugue no projeto e todo código Apex novo (seu ou da IA) passa a seguir os mesmos padrões.

Base conceitual: livro *Salesforce APEX: Implemente soluções com padrões e técnicas de Orientação a Objetos* (Eduardo R. de Carvalho "Bisso", Casa do Código, 2024), destilado com palavras próprias e ampliado com práticas atuais marcadas como **[Sênior+]**.

> Complementa o [`design-patterns-apex-kit`](https://github.com/jeanBianchi1996/design-patterns-apex-kit) (22 padrões GoF + SOLID aplicados a Apex).

## O que vem no kit

| Pasta | Conteúdo |
|---|---|
| `knowledge/` | 12 capítulos de referência: camadas, OO em Apex, SOQL/DML/segurança, TriggerHandler, Repository/Filter/Enricher/Validator, sharing, integrações inbound/outbound, assíncrono, testes e mocks, evoluções sênior, nomenclatura + checklist de PR |
| `skills/` | `apex-architecture`, `apex-trigger-framework`, `apex-data-layer`, `apex-integrations`, `apex-async`, `apex-testing`, `apex-code-review` |
| `agents/` | `salesforce-architect`, `apex-developer`, `apex-code-reviewer`, `apex-test-engineer`, `salesforce-integration-specialist` |
| `commands/` | `/apex-design`, `/apex-new-trigger`, `/apex-new-integration`, `/apex-refactor`, `/apex-test`, `/apex-review` |
| `hooks/` | **SessionStart**: injeta as regras em projetos Salesforce · **PostToolUse**: `apex_lint` valida cada `.cls`/`.trigger` salvo e devolve os erros para a IA corrigir · **PreToolUse**: bloqueia deploy em produção sem `--test-level` |
| `templates/core/` | Classes base prontas: `TriggerHandler`, `AbstractRepository` (user/system mode, upsert por chave externa), `IdGenerator`, `RestResponseBuilder`, `RestResponseError` + testes |
| `templates/scaffold/` | Moldes de trigger, camada de dados, outbound, inbound, batch e job (todos com testes) |
| `scripts/` | `scaffold.py` (gerador), `install_into_project.py` (pluga num projeto), `selftest.sh` |
| `llm/AGENTS.md` | Regras universais para qualquer LLM (Claude Code, Codex, Cursor, Copilot…) |

## Como usar em um projeto

### Opção A — Plugin do Claude Code (recomendado para você)
```bash
# dentro do Claude Code (repo privado: precisa estar autenticado no GitHub, ex.: gh auth login)
/plugin marketplace add jeanBianchi1996/salesforce-apex-patterns-kit
/plugin install salesforce-apex-patterns-kit@jean-apex-kit
```
Skills, agentes, comandos e hooks ficam disponíveis em todos os projetos. Em projetos com `sfdx-project.json`, o hook de sessão ativa o "modo arquiteto" automaticamente.

### Opção B — Vendorizar no projeto (time inteiro, qualquer LLM)
```bash
git clone git@github.com:jeanBianchi1996/salesforce-apex-patterns-kit.git ~/kits/salesforce-apex-patterns-kit
python3 ~/kits/salesforce-apex-patterns-kit/scripts/install_into_project.py /caminho/do/projeto --with-core --ci
# opcional, para quem usa Claude Code sem o plugin:
python3 ~/kits/salesforce-apex-patterns-kit/scripts/install_into_project.py /caminho/do/projeto --claude-hooks
```
Isso cria `.apex-kit/` (gerador, linter, templates, knowledge), mescla as regras em `AGENTS.md`, faz o `CLAUDE.md` importar o `AGENTS.md`, escreve `.github/copilot-instructions.md` e `.cursor/rules/salesforce-apex-patterns.mdc`, gera as classes base e o workflow de CI. É idempotente: rode de novo para atualizar.

## Gerador de código
```bash
python3 scripts/scaffold.py core
python3 scripts/scaffold.py trigger Account
python3 scripts/scaffold.py data Invoice__c
python3 scripts/scaffold.py outbound ErpOrder --sobject Order --named-credential ERP
python3 scripts/scaffold.py inbound PurchaseOrder --sobject Order --external-id ErpCode__c
python3 scripts/scaffold.py job PurgeLogs --sobject Log__c        # Schedulable + Batch
```
Opções: `--target`, `--api-version` (padrão 62.0), `--force`, `--dry-run`. Arquivos existentes nunca são sobrescritos sem `--force`.

## Linter de arquitetura
```bash
python3 hooks/scripts/apex_lint.py force-app                 # texto
python3 hooks/scripts/apex_lint.py force-app --format github # anotações no PR
python3 hooks/scripts/apex_lint.py force-app --strict        # avisos também reprovam
```
Regras `APX001`–`APX019`: trigger com lógica, SOQL/DML fora de Repository, SOQL/DML em loop, notação húngara, `Test.isRunningTest()`, `SeeAllData`, teste sem assert, Id/endpoint fixos, sharing ausente ou sem justificativa, indentação > 3, `@future`, `SECURITY_ENFORCED`, SOQL concatenado, nome de teste fora do BDD, callout em loop. Supressão justificada: `// apex-kit:ignore APX002`. Complementa (não substitui) o PMD / Salesforce Code Analyzer.

Variáveis dos hooks: `APEX_KIT_STRICT=1` (avisos bloqueiam), `APEX_KIT_DISABLE=1` (desliga).

## Os padrões em uma tela
```
Trigger (1 linha) → <Obj>TriggerHandler ──► Filter ──► Validator | Enricher | Publisher ──► <Obj>Repository
@RestResource Controller (fino, 400 sem exceção) ──► InboundService (savepoint, log) ──► Transformer ──► Repository
Publisher ──► Async<X>OutboundService (Queueable) ──► <X>OutboundService ──► Transformer + DTOs
```
Testes: Repository e Trigger integrados; todo o resto mockado (herança ou Mocker), `IdGenerator`, `FixtureFactory` por objeto, nomes `given…When…Then…`.

## Windows
- **Node 22+** é obrigatório para o Salesforce CLI (ou use o instalador `.exe` do CLI, que já traz o próprio Node).
- O Claude Code no Windows usa o **Git for Windows** (Git Bash) para rodar os hooks — instale-o.
- Os hooks usam `python3` e, se ele não existir, `python`. Instale o Python 3 em python.org marcando **"Add python.exe to PATH"** e confira com `python --version` no Git Bash.
- No PowerShell, rode os scripts com `python` no lugar de `python3` e use caminhos como `$HOME\kits\...`.

## Observações
- O código Apex dos templates foi escrito para a API 62.0+ (usa `AccessLevel`, `Database.queryWithBinds`, `Assert`). Valide numa scratch org antes do primeiro uso no seu projeto.
- O framework Mocker citado no livro é o [GS Apex Mocking Framework](https://github.com/gscloudsolutions/GS-Apex-Mocking-Framework) e não é distribuído aqui.
- Os PDFs e trechos dos livros **não** fazem parte deste repositório (direitos autorais dos autores/editoras). Compre os livros para a leitura completa.
