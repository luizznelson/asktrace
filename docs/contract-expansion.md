# Ampliação de contratos — 03/11/2026

## Resultado

Lote completo e carregado: 6 compras com contratos, 94 sem registros retornados, 6 contratos.

[Manifesto](../runs/contracts-78f81b23-e1b7-4fbf-b8dc-a442b64fe259/manifest.json) · [Verificação da carga](../runs/contracts-78f81b23-e1b7-4fbf-b8dc-a442b64fe259/database-load.json).

## Cobertura e exclusão

O lote selecionou 100 compras com localizadores válidos da população de 1.081. A seleção alterna
meses de publicação e ordena os identificadores dentro do mês, sem usar resultados de contratos.
Inclui as 12 compras do piloto anterior: a cobertura deste lote é 100, não 112.
As respostas são snapshots da consulta, sujeitos a publicações e retificações posteriores.

A compra `01612569000170-1-000001/20226` informa ano `20226` na fonte. O coletor não troca esse valor
por 2026: registra a exclusão com identificador, motivo, hash e posição na página original.
A compra continua preservada na base original; apenas sua consulta de contratos foi excluída.
Restam 980 compras com localizadores válidos fora deste lote e uma exclusão por dado inválido.
O manifesto publica a exclusão na população inteira, mesmo que ela não fosse selecionada no lote.

## Reprodução

```powershell
.venv/Scripts/python.exe -m asktrace.contracts collect runs/pncp-3020d59b-d274-4f4c-be4f-d59e8be30101/manifest.json --limit 100
```

Não somar snapshots. Filtrar `contract_runs.run_id` e a coleta original ao analisar o banco.
`pilot_complete` descreve as consultas selecionadas, não a população completa. O esquema mantém esse
nome de estado por compatibilidade, inclusive para este lote ampliado. Só lotes completos são carregados;
falhas e respostas inválidas permanecem em `runs/` para revisão. Ver [interpretação das respostas](contracts.md).

O resultado não mede pagamentos, economia, irregularidades ou contratação efetiva fora do portal.
Os downloads completos ficam locais; o Git contém relatórios sem nomes ou CPF de fornecedores.
Os 41 testes locais passaram, incluindo PostgreSQL, integridade das exclusões e ano inválido.
CI remoto não verificado nesta entrega.

## Próximo passo

Adicionar processamento dos lotes restantes com retomada, limite de requisições e cobertura consolidada
por compra, sem reconsultar a mesma seleção inicial. O limite atual de 100 por execução é intencional.
Antes do agente, criar consultas somente leitura que sempre informem recorte e registros não consultados.

A retomada por lotes está implementada. Veja [execução mais recente e limitações](contract-resumption.md). A cobertura confirmada permanece em 100 compras enquanto o lote seguinte requer revisão.
