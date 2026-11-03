# Contratos vinculados: da consulta à evidência

## Pergunta de negócio

Quais contratos ou empenhos com força de contrato o PNCP retorna para uma compra selecionada?
Uma compra pode gerar vários contratos. Nenhum registro publicado não comprova ausência de contrato
fora do portal; valor contratado não representa pagamento nem execução financeira.

## Resultado validado em 03/11/2026

O piloto consultou **12 das 1.081 compras** da coleta original, quatro de cada mês de publicação.
Uma compra retornou um contrato com vínculo explícito; as outras 11 receberam a mensagem do PNCP
“Não há contrato publicado no PNCP para esta contratação.” Todos esses resultados foram carregados
no PostgreSQL: 12 registros de cobertura e um contrato. Repetir a carga retornou `already_loaded`.

- [Manifesto do piloto](../runs/contracts-52c725b6-9b6f-42a6-b65e-e3858060c9ed/manifest.json): seleção, páginas, horários, hashes e registros normalizados.
- [Verificação no banco](../runs/contracts-52c725b6-9b6f-42a6-b65e-e3858060c9ed/database-load.json): contagens, integridade e carga repetida.
- [Especificação oficial preservada](pncp-contracts-api.json): parâmetros e formato de resposta consultados.

O piloto valida a integração, **não é uma amostra estatisticamente representativa**. As outras 1.069
compras não foram consultadas nesta execução. Não extrapolar os resultados para todos os contratos
do Piauí, calcular taxa geral de contratação ou interpretar falta de publicação como irregularidade.

## Seleção e paginação

A seleção alterna meses de publicação; em cada mês ordena compras pelo identificador de controle.
Não escolhe compras pelo resultado de contratos. CNPJ do órgão, ano e sequencial vêm das páginas
originais da compra, verificadas por hash, sem dedução a partir de texto livre.

O endpoint oficial exige `pagina`, embora o manual narrativo consultado inicialmente não apresentasse
esse parâmetro. A OpenAPI confirmou `pagina` obrigatória e `tamanhoPagina` entre 10 e 50. O coletor
envia ambos, percorre todas as páginas e verifica os totais, número de página, repetição de contratos e
vínculo com a compra. Há orçamento de até 100 páginas por compra; excedê-lo impede declarar completude.
Timeout, limite de bytes e até três tentativas para falhas transitórias limitam cada aquisição.

## Respostas vazias versus falhas

| Resposta | Interpretação |
| --- | --- |
| 200 com envelope paginado válido e zero registros | `none_returned` |
| 204 sem corpo na primeira e única página | `none_returned` |
| 404 com status 404 no JSON e a mensagem exata de nenhum contrato publicado | `none_returned`, preservando o 404 na evidência |
| 404 genérico, 400, 503 ou falha de conexão | Falha de consulta; não comprova ausência de contratos |
| Páginas faltantes, totais alterados, valores inválidos ou vínculo divergente | Resposta inválida; impede carga do piloto |

A regra do 404 específico foi baseada nas respostas reais do PNCP preservadas neste piloto;
a especificação consultada não descrevia essa resposta. Mudanças na mensagem exigem nova revisão:
o comportamento conservador é tratar como falha, sem inventar ausência de contratos.

## Reproduzir

Com dependências, PostgreSQL e páginas da coleta original disponíveis localmente:

```powershell
.venv/Scripts/python.exe -m asktrace.contracts collect runs/pncp-3020d59b-d274-4f4c-be4f-d59e8be30101/manifest.json --limit 12
```

O comando imprime o manifesto da nova execução. Para carregar um piloto `pilot_complete`:

```powershell
.venv/Scripts/python.exe -m asktrace.contracts load runs/contracts-ID-DA-NOVA-EXECUCAO/manifest.json
```

Cada execução usa outro identificador; relatórios anteriores não são sobrescritos.
O carregador verifica novamente fontes, normalização, seleção e manifesto da compra já carregada.
Falhas provocam rollback de toda a transação. A migração `sql/003_contracts.sql` é aplicada na carga;
não apagar volumes. Valores desconhecidos permanecem nulos e os valores monetários usam decimais.

## Rastreabilidade no banco e no Git

`contract_runs` identifica o piloto e a coleta original. `contract_coverage` registra cada compra
consultada com sucesso. `contracts` permite vários contratos por compra. Filtrar sempre pelo piloto
e pela coleta original para não somar snapshots repetidos.

No manifesto versão 2, cada compra guarda sua lista ordenada de páginas e hashes. A coluna
`contract_coverage.body_sha256` guarda o SHA-256 da concatenação textual dos hashes das páginas,
na ordem da consulta. Não é o hash de uma única resposta. `source_record_index` identifica a posição
do contrato na concatenação lógica dos registros de todas as páginas, começando em zero.

Manifestos publicados excluem nomes, CPF e textos livres de fornecedores. Respostas completas ficam
em `data/raw/`, ignoradas pelo Git. Publicar o hash não disponibiliza esses arquivos remotamente.
Os manifestos contêm identificadores públicos dos órgãos, compras e contratos, além de valores.

## Histórico preservado

| Execução | O que demonstrou |
| --- | --- |
| [02/11: piloto inicial](../runs/contracts-a6fa16c6-13c4-4205-94e9-cd01e9322636/manifest.json) | 11 respostas 503 e uma falha sem status; nenhum contrato validado, sem carga. Os corpos dos erros HTTP não foram capturados nessa versão. |
| [03/11: diagnóstico](../runs/contracts-4e458e67-f581-448d-b28a-2362deda4d93/manifest.json) | Três respostas 400 revelaram a falta de `pagina`; sem carga. |
| [03/11: paginação corrigida](../runs/contracts-f5d0d7be-60fe-43d7-9007-666f868aeeca/manifest.json) | Um contrato retornou, mas 11 respostas 404 ainda eram falhas genéricas; sem carga. |
| [03/11: piloto validado](../runs/contracts-52c725b6-9b6f-42a6-b65e-e3858060c9ed/manifest.json) | Mesmas 12 compras; um contrato e 11 mensagens explícitas de nenhum contrato publicado; carga validada. |

Os relatórios intermediários mantêm a classificação aplicada na execução, sem reescrever o histórico.
O erro inicial do coletor foi corrigido; os testes anteriores usavam listas simples em vez do envelope
paginado real, por isso não detectaram o problema. Os testes agora usam o formato documentado e
cobrem múltiplas páginas, duplicações, totais alterados, orçamento de páginas e o 404 específico.
A suíte completa passou com **39 testes**, incluindo integração em `asktrace_test`. CI remoto não
verificado nesta entrega.

## Próximo passo

Ampliar gradualmente a consulta às compras restantes, mantendo o controle de cobertura e falhas.
Atas, ferramentas de consulta somente leitura, agente, avaliação de perguntas e interface continuam
pendentes. Não chamar a diferença entre um contrato e o orçamento inteiro da compra de economia.

Fontes oficiais: [OpenAPI](https://pncp.gov.br/api/pncp/v3/api-docs),
[manual da consulta por compra](https://pncp.gov.br/manual/pt-br/latest/contrato_empenho/consultar_contratos_ou_empenhos_de_uma_contratacao.html).
