# Como verificar o que foi feito

## Três perguntas diferentes

| Pergunta | Verificação disponível |
| --- | --- |
| O software reage corretamente? | Testes de regras e falhas, Ruff e integração PostgreSQL. |
| A coleta observada corresponde à carga? | Manifesto, hashes, contagem por mês e conferência no banco. |
| Um agente responde corretamente? | Ainda não há agente nem avaliação de respostas. Os testes atuais não medem isso. |

## Verificação local registrada

Em 02/11/2026, passaram 27 testes, incluindo dois de integração com PostgreSQL em `asktrace_test`. Foram conferidos Ruff, formatação, Compose e leitura dos 1.081 registros a partir das 23 páginas preservadas. Os números descrevem essa verificação, não uma promessa de ausência de falhas.

Os testes cobrem paginação variável, falha de rede, limite de páginas, interrupção, filtro de estado/modalidade/data, duplicados, precisão decimal, hash divergente, caminhos fora da execução, idempotência e rollback da transação. O banco de testes é separado dos dados reais.

## Como reproduzir

Instale o ambiente conforme o [README](../README.md). Testes sem PostgreSQL:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check .
docker compose config --quiet
```

Para os dois testes PostgreSQL, siga a configuração de `asktrace_test` e a variável `ASKTRACE_TEST_DATABASE` no [guia de ingestão](ingestion.md). Sem essa opção, a suíte informa dois testes ignorados, em vez de alegar que foram executados.

O [workflow](../.github/workflows/quality.yml) instala dependências fixadas com hashes e provisiona PostgreSQL para integração. O badge do README mostra o estado remoto informado pelo GitHub; a configuração da CI não é, por si só, confirmação de uma execução aprovada.

## Evidências e limites

As amostras históricas e os relatórios iniciais têm contexto próprio. Consulte [runs](../runs/README.md) para distinguir teste limitado, amostra e coleta concluída. Não some essas execuções.

Os bytes completos de dados reais ficam locais em pastas ignoradas pelo Git. Os manifestos publicados permitem verificar uma cópia disponível, mas não substituem sua disponibilização. Uma nova consulta pode retornar conteúdo atualizado, com hashes diferentes.

Não foram medidos produtividade, desempenho sob carga, acurácia de respostas ou cobertura de todas as compras públicas. Nenhuma afirmação de irregularidade ou aprovação financeira decorre desta etapa.

## Contratos: validação adicional em 02/11/2026

Após a implementação do coletor de contratos, a suíte completa passou com **36 testes**,
incluindo PostgreSQL. Os 27 testes citados acima correspondem à entrega anterior.
Os nove novos testes cobrem relações, integridade, falhas, valores e transações.
O piloto real não validou vínculos por falhas de consulta; testes sintéticos não substituem essa etapa.
Veja [relatório e reprodução](contracts.md). A execução remota do CI não foi verificada nesta entrega.

## Validação de contratos em 03/11/2026

A suíte atual passou com **39 testes**, incluindo PostgreSQL. Foram acrescentados testes de múltiplas páginas, totais alterados, páginas repetidas ou faltantes e o 404 específico de nenhum contrato publicado. O piloto real foi validado e carregado, com carga repetida idempotente. [Evidências e limites](contracts.md). Os números anteriores descrevem entregas anteriores. CI remoto não verificado.

## Ampliação de contratos em 03/11/2026

Suíte atual: **41 testes locais passaram**, incluindo PostgreSQL. A exclusão por localizador inválido e sua integridade são testadas. [Resultado da ampliação](contract-expansion.md).
