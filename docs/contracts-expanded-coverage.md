# Contratos: cobertura concluída da base ampliada

## O que mudou

A base contém 2.537 compras publicadas entre maio e outubro de 2026, no recorte de
pregões eletrônicos de unidades do Piauí. A busca de contratos foi concluída para
**todas as 2.536 compras com identificador válido**. Uma compra continua excluída porque
o ano informado na fonte é `20226`; esse dado não foi corrigido por inferência.

| Medida | Resultado verificado |
| --- | ---: |
| Compras na base | 2.537 |
| Compras aptas com contratos pesquisados | 2.536 |
| Compras aptas ainda pendentes | 0 |
| Compras com contratos encontrados | 370 |
| Contratos distintos encontrados | 679 |
| Compras pesquisadas sem publicação retornada | 2.166 |
| Compras excluídas da pesquisa por ano inválido | 1 |
| Compras sem valor homologado informado na fonte | 1.354 |

As 2.166 respostas sem publicação são diferentes de uma falha de consulta ou de uma
compra ainda não pesquisada. Não comprovam inexistência de contrato. Uma compra pode
ter vários contratos, por isso 370 compras resultaram em 679 contratos. Publicação e
valores estimados/homologados não comprovam pagamento ou execução financeira.

## Como a coleta foi concluída

Partimos das 100 compras já pesquisadas. A retomada fez 25 novos lotes: 24 de 100 compras
e um de 36, com pausa de um segundo por página e tentativas limitadas no transporte.
Os 25 lotes terminaram completos, foram validados e carregados. Isso não significa que
nenhuma tentativa de rede tenha precisado de repetição; o transporte pode repetir
falhas transitórias antes de registrar a resposta final.

[Diário da execução](../runs/contracts-completion-d5e1399d-480d-4b8e-b388-388fcdb67f9a/progress.json) · [Consolidação final](../runs/contracts-resume-9a175343-9dde-49dc-b1e5-dcf5e760d139/coverage.json).
O diário contém uma consolidação intermediária de 2.100 compras e a final de 2.536.
Os relatórios anteriores não foram alterados ou somados como bases independentes.

Cada lote preserva resposta original local, URL, horário, hash e relacionamento com a
compra. Os arquivos brutos ficam fora do Git; os manifestos publicados minimizam os
campos e não incluem nomes/identificadores de fornecedores. O relatório final referencia
26 snapshots: o lote anterior e os 25 novos.

## Validação antes de atualizar a aplicação

O publicador conferiu hashes e relações dos snapshots, comparou as contagens com
PostgreSQL e repetiu a carga dos 26 lotes: todos retornaram `already_loaded`, sem
duplicação. Conferiu uma compra com contratos e outra sem publicação retornada.
Só depois atualizou `config/datasets.json` por substituição atômica.

[Conferência de publicação e idempotência](../runs/contracts-publication-10f50cf9-aedd-47ba-a17c-1e56f36391d4/verification.json). O recorte original de
agosto–outubro permanece separado, com sua cobertura anterior e 125 contratos;
não é somado à base ampliada. A aplicação local foi reiniciada e seu `/api/session`
confirmou 2.537 compras, 2.536 pesquisas, 679 contratos e uma exclusão.

O histórico da aba não muda os resultados já salvos. Respostas de um hash de cobertura
anterior recebem a indicação **“base anterior”** e não são restauradas automaticamente
como atuais. Ao abri-las, a tela explica que uma nova pergunta é necessária para usar
a cobertura atual. JSON e CSV preservam a origem daquela resposta.

## Verificações de software

**112 testes Python passaram**, incluindo quatro proteções da publicação: conferência
correta, divergência no banco, carga inesperada e evidência inválida. Passaram os testes
Node de histórico, formatação e CSV, Ruff e as consultas HTTP reais com PostgreSQL.
[Registro completo](../runs/application-review-fbea3361-f186-4701-97a3-74c4a8af80c8/verification.json). O [corpus local continuou 12/12](../runs/analytics-verification-7dd8ee71-5160-463b-992c-6db043f4dd4a/verification.json), sem
novas chamadas de IA. Não foi realizada inspeção visual em navegador nesta etapa.

## Como repetir com segurança

```powershell
# Retoma apenas compras pendentes; se já estiver completo, não consulta novas compras.
.venv/Scripts/python.exe -m scripts.complete_contract_coverage

# Verifica o relatório e seleciona a cobertura na aplicação somente após conferência.
.venv/Scripts/python.exe -m scripts.publish_contract_coverage runs/contracts-resume-9a175343-9dde-49dc-b1e5-dcf5e760d139/coverage.json

# Verificação de software, HTTP, banco e credenciais locais ignoradas.
.venv/Scripts/python.exe -m scripts.verify_application_review
```

Não execute várias retomadas simultaneamente para o mesmo snapshot. O script de
conclusão respeita lotes de até 100, grupos de até 20 lotes e até três lotes consecutivos
com falha antes de encerrar com pendência explícita. Não altera dados publicados na fonte.

Cobertura concluída significa que todas as compras **aptas deste snapshot** foram
pesquisadas e carregadas. Não significa que o PNCP contenha todos os contratos existentes,
que novos contratos não possam ser publicados depois, nem que o recorte represente o
Piauí inteiro. Uma atualização futura deve gerar novas evidências, preservando esta versão.
