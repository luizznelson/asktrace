# Ingestão de pregões do Piauí

## O que esta etapa responde

A coleta permite investigar pregões eletrônicos publicados no PNCP por unidades do Piauí, de 01/08/2026 a 31/10/2026. O filtro é modalidade 6, UF PI e **data de publicação**. Não representa todas as modalidades, datas de assinatura, gastos pagos, contratos ou atas.

Fonte técnica: [API oficial do PNCP](https://pncp.gov.br/api/consulta/swagger-ui/index.html). A especificação `/api/consulta/v3/api-docs` foi consultada antes da implementação. A consulta de contratações aceita UF; não foi presumido esse filtro em contratos ou atas.

## Resultado verificado em 02/11/2026

| Mês de publicação | Registros |
| --- | ---: |
| Agosto/2026 | 412 |
| Setembro/2026 | 373 |
| Outubro/2026 | 296 |
| Total | 1.081 |

Foram preservadas 23 páginas. Os registros correspondem a 235 CNPJs de órgãos e 179 códigos de municípios distintos presentes na base; isso não significa que todos os municípios do estado publicaram pregões no período. Todos os 1.081 registros foram normalizados e conferidos no PostgreSQL. Não houve IDs duplicados ou registros rejeitados nessa execução.

749 registros não informam valor homologado; nenhum deles foi convertido em zero. A ausência desse campo não comprova que a compra não foi homologada, cancelada ou paga. As fontes podem ser atualizadas posteriormente.

Evidência: [manifesto](../runs/pncp-3020d59b-d274-4f4c-be4f-d59e8be30101/manifest.json), [qualidade](../runs/pncp-3020d59b-d274-4f4c-be4f-d59e8be30101/quality.json) e [conferência no banco](../runs/pncp-3020d59b-d274-4f4c-be4f-d59e8be30101/database-load.json).

## Como reproduzir

Na pasta do projeto, com Docker Desktop aberto:

```powershell
uv venv --python 3.14
uv pip install --python .venv/Scripts/python.exe --require-hashes -r requirements.txt
uv pip install --python .venv/Scripts/python.exe -r requirements-dev.txt
docker compose up -d --wait
.venv/Scripts/python.exe -m asktrace.ingest --start 2026-08-01 --end 2026-10-31
```

O primeiro comando prepara um ambiente novo; se `.venv` já existir e estiver configurado, não é necessário recriá-lo. Cada coleta gera um UUID e informa o caminho do manifesto. Não sobrescreve execuções anteriores.

Para carregar, substitua `ID-DA-EXECUCAO` pelo caminho informado:

```powershell
.venv/Scripts/python.exe -m asktrace.database runs/pncp-ID-DA-EXECUCAO/manifest.json
```

Uma segunda carga do mesmo manifesto retorna `already_loaded`. Uma execução com o mesmo UUID e evidência diferente é recusada. As migrações `001` e `002` são aplicadas explicitamente em transação; não se apaga o volume existente para atualizar o esquema.

Para testar somente a amostra histórica, sem representar os três meses coletados:

```powershell
.venv/Scripts/python.exe -m asktrace.ingest --start 2025-10-01 --end 2025-10-31 --sample amostras/pncp-contratacoes-pi.json
.venv/Scripts/python.exe -m asktrace.database runs/pncp-ID-DA-AMOSTRA/manifest.json --allow-sample
```

## O que a execução preserva

- `data/raw/UUID/`: bytes originais de cada resposta, sem reserializar números.
- `data/processed/UUID/`: cinco campos institucionais/localização, objeto, datas e valores normalizados, além do vínculo à página e ao índice do registro.
- `runs/pncp-UUID/manifest.json`: período, filtros, hashes, páginas, horários UTC, contagens e estado final.
- `quality.json`: resumo de cobertura e campos ausentes ou inválidos, sem expor registros individuais.

Os manifestos e relatórios ficam disponíveis para commit. Os downloads completos em `data/raw/` e os arquivos processados permanecem locais e ignorados pelo Git. Os hashes permitem conferir essas cópias; eles não tornam os arquivos disponíveis remotamente e não garantem que uma nova consulta ao portal retorne os mesmos bytes.

Valores decimais são lidos como Decimal e armazenados em NUMERIC, sem passar por float. Valores ausentes ou inválidos tornam-se NULL na versão normalizada, com contadores separados. O texto original permanece nos arquivos brutos. A normalização não é um validador fiscal nem certifica o significado do objeto.

## Falhas e limites

O cliente usa HTTPS com verificação de certificados, timeout de 30 segundos, corpo máximo de 16 MiB por página e até três tentativas para falhas transitórias. Há intervalo entre páginas, espera limitada para 429 e orçamento de páginas. Não há concorrência de downloads.

O programa confere número de página, totais estáveis dentro da janela mensal, contagem final, identificadores e recorte. Totais divergentes, duplicados conflitantes, falha de rede ou interrupção não viram sucesso. Amostra é `sample_only`; duplicados ou registros rejeitados exigem revisão; falha é `failed` e interrupção é `interrupted`.

Essas verificações detectam vários problemas de paginação, mas a API não oferece uma transação de leitura de todos os registros de uma vez. Igualdade de contagens não prova ausência de mudanças na origem durante a coleta.

A carga valida os hashes e os caminhos antes de acessar o banco, usa parâmetros SQL para valores e uma transação para todas as tabelas da execução. O PostgreSQL guarda snapshots por UUID. A visão `asktrace.live_purchases` exclui amostras, mas ainda exige filtro de `run_id` ao analisar uma execução: somar vários snapshots pode contar uma compra mais de uma vez.

Este guia descreve aquisição e carga com manutenção administrativa local. O roteador, a credencial somente leitura e as avaliações já estão implementados na camada de consultas. Busca semântica não foi adicionada. Consulte [arquitetura](architecture.md) e [consultas](business-queries.md).

## Testes com PostgreSQL

```powershell
docker compose exec -T postgres createdb -U asktrace asktrace_test
$env:ASKTRACE_TEST_DATABASE='1'
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Crie `asktrace_test` somente na primeira vez. Os testes de integração usam esse banco isolado, não os dados reais. Verificam idempotência, exclusão de amostras da visão analítica e rollback da execução inteira diante de violação de restrição. A CI foi configurada para executar esses testes com PostgreSQL; sua execução remota não foi confirmada nesta entrega.

## Contratos vinculados

A aquisição por compra tem [guia próprio de cobertura e reprodução](contracts.md).
O primeiro piloto ficou `needs_review`; o piloto corrigido de 03/11/2026 foi validado e carregado (12 compras, um contrato).
