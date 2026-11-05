# CLAUDE.md — manutenção do próprio kit

Este repositório é um plugin do Claude Code + kit vendorizável. Ao alterá-lo:

- Mantenha a estrutura de plugin: `.claude-plugin/plugin.json`, `skills/*/SKILL.md`, `agents/*.md`, `commands/*.md`, `hooks/hooks.json` (scripts referenciados via `${CLAUDE_PLUGIN_ROOT}`).
- Conteúdo em português, escrito com palavras próprias — nunca copie trechos dos livros.
- Toda mudança em `templates/` ou `hooks/scripts/apex_lint.py` deve manter `bash scripts/selftest.sh` verde (código gerado precisa passar limpo no linter em modo `--strict`).
- Novas regras do linter: adicione em `RULES`, documente no README e em `skills/apex-code-review/SKILL.md`.
- Mudou as regras de arquitetura? Atualize juntos: `knowledge/`, `llm/AGENTS.md`, `hooks/scripts/session_context.py` e a skill correspondente.
- Versione em `plugin.json` (semver).
