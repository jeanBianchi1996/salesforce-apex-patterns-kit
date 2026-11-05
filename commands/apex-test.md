---
description: Cria ou melhora os testes de uma classe Apex (F.I.R.S.T., BDD, fixtures, mocks)
argument-hint: <classe ou arquivo>
---

Crie/melhore os testes de: $ARGUMENTS

Use o agente `apex-test-engineer` e a skill `apex-testing`. Classifique a classe na matriz mockado × integrado, liste cenários (feliz, bordas, falhas), garanta FixtureFactory/Mocks/IdGenerator, escreva os testes com nomes `given...When...Then...` e asserts com mensagem. Se houver org conectada, rode `sf apex run test --tests <Classe>Test --code-coverage --result-format human --synchronous` e reporte cobertura.
