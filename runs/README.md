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
