# Registros de execução publicados

Os dois relatórios JSON atuais auditam as mesmas amostras com versões diferentes do auditor:

- `sample-audit.json`: execução inicial da etapa de preparação.
- `precommit-audit-20261102.json`: execução após a revisão do auditor, com validações adicionais e códigos de erro.

Ambos registram o arquivo vazio do Querido Diário como inválido. Não são dois experimentos independentes, resultados de um agente ou ingestões completas. A execução retorna código 1 quando encontra arquivo inválido, como esperado neste conjunto.

Para reproduzir com um novo nome de saída:

```powershell
python scripts/audit_samples.py amostras --output runs/audit-replay.json
```

Compare os hashes e diagnósticos, considerando a evolução do código. Os relatórios publicados não devem ser sobrescritos silenciosamente. Novos arquivos em `runs/` passam a aparecer no Git: revise cada inclusão antes de commitá-la e não publique credenciais, dados particulares, bancos ou arquivos grandes.

## Execuções de ingestão

- `pncp-287e5086-3ed6-47ae-95b8-c965cb13502d`: validação histórica de 50 registros, modo amostra; não é coleta de 2026.
- `pncp-13037e9b-fbca-488c-a435-9b327710276a`: teste real limitado a uma página; status failed por orçamento de páginas, não por indisponibilidade do PNCP.
- `pncp-3020d59b-d274-4f4c-be4f-d59e8be30101`: coleta real concluída, 1.081 registros e 23 páginas, com conferência da carga no PostgreSQL.

Os JSONs brutos e normalizados dessas execuções ficam em data/raw e data/processed, fora do Git; os manifestos registram seus hashes e caminhos. Não some as amostras aos resultados reais. [Método e reprodução](../docs/ingestion.md).

## Piloto de contratos

[contracts-a6fa16c6-13c4-4205-94e9-cd01e9322636/manifest.json](contracts-a6fa16c6-13c4-4205-94e9-cd01e9322636/manifest.json): 12 compras tentadas, 11 respostas 503,
uma falha sem status HTTP, nenhum contrato validado; não carregado no banco.
Veja [método e interpretação](../docs/contracts.md). Preservar esta tentativa, mesmo após novas coletas.

## Atualização de contratos em 03/11/2026

Diagnóstico preservado em `contracts-4e458e67-f581-448d-b28a-2362deda4d93` (400 por falta de página) e `contracts-f5d0d7be-60fe-43d7-9007-666f868aeeca` (paginação corrigida, 404 ainda genérico). Nenhum deles foi carregado.

[Piloto validado](contracts-52c725b6-9b6f-42a6-b65e-e3858060c9ed/manifest.json): 12 compras, um contrato e 11 mensagens explícitas de nenhum contrato publicado. [Verificação no banco](contracts-52c725b6-9b6f-42a6-b65e-e3858060c9ed/database-load.json). [Guia de interpretação](../docs/contracts.md).

## Ampliação para 100 compras

[contracts-78f81b23-e1b7-4fbf-b8dc-a442b64fe259/manifest.json](contracts-78f81b23-e1b7-4fbf-b8dc-a442b64fe259/manifest.json): Lote completo e carregado: 6 compras com contratos, 94 sem registros retornados, 6 contratos. Uma exclusão por localizador inválido na população. [Método](../docs/contract-expansion.md).

## Retomada de contratos

O plano `contracts-resume-88d30f38-2d39-4a7c-a0e5-782f10ca128e` não terminou por indisponibilidade do banco. `contracts-resume-f93f55c8-753a-4d8d-a505-843bc7deb32e/coverage.json` registra a tentativa seguinte: lote `contracts-3eec93d4-abbc-4072-8f7b-66194aa4d685` pendente por 40 falhas de conexão, sem carga. [Método e cobertura consolidada](../docs/contract-resumption.md).

## Nova tentativa da retomada

[contracts-resume-d88d70d6-06d1-44ee-8923-5d9b17eb364a/coverage.json](contracts-resume-d88d70d6-06d1-44ee-8923-5d9b17eb364a/coverage.json): O lote terminou completo, foi carregado e a carga repetida não duplicou registros. A cobertura confirmada passou a 200 compras distintas e 12 contratos distintos. Restam 880 compras elegíveis e uma exclusão por ano inválido.

## Consolidação dos lotes restantes

[contracts-resume-c1345679-59ea-49ad-af35-be2cc924ceab/coverage.json](contracts-resume-c1345679-59ea-49ad-af35-be2cc924ceab/coverage.json): 1.080 compras distintas confirmadas. 125 contratos distintos e 0 compras elegíveis pendentes. [Conferência no banco](contracts-resume-c1345679-59ea-49ad-af35-be2cc924ceab/database-verification.json). [Interpretação](../docs/contract-coverage.md).

## Perguntas de negócio

[queries-ee5ffc31-e565-4e75-8ce4-cfa6aac17046/verification.json](queries-ee5ffc31-e565-4e75-8ce4-cfa6aac17046/verification.json): consultas reais com login somente leitura, contagens conferidas e escrita negada. Exemplos em summary.json, municipalities.json e purchase.json; o texto livre do objeto foi omitido do exemplo de rastreio. [Método](../docs/business-queries.md).

## Avaliação de perguntas

[agent-eval-3ad8ae41-4327-4033-ae56-2c59a60e451d/evaluation.json](agent-eval-3ad8ae41-4327-4033-ae56-2c59a60e451d/evaluation.json): baseline final, 60/60 casos curados, zero LLM. As execuções anteriores `agent-eval-56477761-a3a6-41de-bfb1-49f5a8a9a6e6` e `agent-eval-eb123db5-c11b-4efa-8926-752a0e39af4f` foram preservadas. [Interpretação](../docs/agent-evaluation.md).

## Teste real Gemini

[agent-eval-e1b0aef5-858d-4a16-8f52-bb881fc16585/evaluation.json](agent-eval-e1b0aef5-858d-4a16-8f52-bb881fc16585/evaluation.json): três perguntas reais, três aprovadas,
zero erros; resumo, municípios e rastreio. [agent-eval-e1b0aef5-858d-4a16-8f52-bb881fc16585/verification.json](agent-eval-e1b0aef5-858d-4a16-8f52-bb881fc16585/verification.json)
confere hashes e metadados de uso (840 tokens totais). Custo monetário desconhecido. Não representa
a suíte completa de 60 casos com Gemini. [Interpretação](../docs/agent-evaluation.md).

## Avaliação Gemini interrompida

[agent-eval-6908e93c-b894-4638-8ddf-96d21200a3c8/evaluation.json](agent-eval-6908e93c-b894-4638-8ddf-96d21200a3c8/evaluation.json): 11 executados, nove aprovados, uma recusa indevida e uma falha técnica sem status preservado. [agent-eval-6de25618-3cbe-4252-95ab-4620422340e8/evaluation.json](agent-eval-6de25618-3cbe-4252-95ab-4620422340e8/evaluation.json): novo prompt, sete executados, seis aprovados e um HTTP 429; 53 não executados. Não somar resultados. [Conferência](agent-eval-6de25618-3cbe-4252-95ab-4620422340e8/verification.json) e [continuação](../docs/agent-evaluation.md).
