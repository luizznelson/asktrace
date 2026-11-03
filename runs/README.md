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
