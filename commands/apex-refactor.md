---
description: Refatora código Apex legado para o padrão do kit com segurança (testes de caracterização primeiro)
argument-hint: <arquivo ou classe/trigger>
---

Refatore para o padrão do kit: $ARGUMENTS

Sequência obrigatória (passos pequenos, testes verdes a cada passo):
1. Leia o código e liste as responsabilidades misturadas (consulta, filtro, validação, enriquecimento, integração, DML).
2. Escreva **testes de caracterização** que travem o comportamento atual (integrados, se não houver).
3. Extraia, nesta ordem: Repository → Filter → Validator/Enricher com nome de intenção → Publisher/assíncrono → Handler; trigger com uma linha.
4. Adicione testes mockados para as classes novas (skill `apex-testing`).
5. Rode `apex_lint.py` e corrija.
6. Mostre o antes/depois (estrutura de classes) e o que mudou em termos de limites e testabilidade.

Não altere comportamento funcional sem avisar. Se encontrar bug, registre e pergunte antes de corrigir.
