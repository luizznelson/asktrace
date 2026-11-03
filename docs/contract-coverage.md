# Contratos vinculados: cobertura consolidada

## Cobertura elegível concluída

1.080 compras distintas confirmadas. 125 contratos distintos e 0 compras elegíveis pendentes.

| Medida | Resultado |
| --- | ---: |
| Compras na coleta original | 1081 |
| Compras com localizador válido | 1080 |
| Compras consultadas, verificadas e carregadas | 1080 |
| Compras com contratos retornados | 85 |
| Compras sem publicação retornada | 995 |
| Contratos distintos consolidados | 125 |
| Compras elegíveis ainda pendentes | 0 |
| Exclusões por localizador inválido | 1 |

[Cobertura por compra](../runs/contracts-resume-c1345679-59ea-49ad-af35-be2cc924ceab/coverage.json) ·
[Conferência no PostgreSQL](../runs/contracts-resume-c1345679-59ea-49ad-af35-be2cc924ceab/database-verification.json).

## O que foi feito nesta etapa

A retomada executou até nove lotes, continuando depois das 200 compras anteriores. Apenas lotes
completos entraram no banco. Os manifestos anteriores, inclusive tentativas com falhas, foram preservados.
Cada snapshot usado na consolidação teve sua integridade verificada; as contagens e resultados por
compra foram confrontados com PostgreSQL. Cargas repetidas dos novos lotes não duplicaram registros.
O relatório registra o resultado de cada repetição.

## O alcance da cobertura

O recorte original reúne pregões eletrônicos (modalidade 6), UF da unidade igual a PI e publicação
entre agosto e outubro de 2026. Esta coleta procura os contratos vinculados a essas compras, não todos
os contratos do estado. Os contratos retornados não são limitados artificialmente pelo mês de publicação
da compra. Uma compra pode ter mais de um contrato; nenhum desses registros comprova pagamento.

O registro `01612569000170-1-000001/20226` informa ano `20226` na fonte. Permanece preservado como
compra, mas excluído da consulta de contratos. O ano não foi corrigido por suposição.
Ausência de publicação retornada não comprova ausência de contrato fora do portal nem irregularidade.
Não calcular economia subtraindo um contrato do orçamento inteiro da compra.

As respostas foram capturadas em momentos diferentes. A cobertura consolida a observação mais recente
disponível por compra entre os snapshots verificados e carregados; não representa o portal em um instante
único. Lotes sobrepostos não são somados. Dados podem ser publicados ou retificados posteriormente.

## Reprodução e arquivos

O [guia da retomada](contract-resumption.md) contém os comandos. Sem pendências, repetir `resume`
verifica a cobertura e não faz novas consultas de contratos. Isso não é uma atualização periódica:
reconsultar dados já confirmados exige uma nova coleta explícita.

Respostas completas ficam em `data/raw/`, ignoradas pelo Git. Manifestos, hashes, seleção e cobertura
ficam publicados em `runs/`, sem nomes ou CPF de fornecedores. Hashes não tornam os downloads
originais remotamente disponíveis. [Histórico da coleta](contract-progress.md).

Nenhum código do coletor foi alterado nesta etapa. A suíte anterior de 46 testes locais aprovados não
foi repetida; esta entrega verificou integridade, carga idempotente e contagens reais no banco.

## Próximo passo

Criar consultas somente leitura que respondam perguntas de negócio e sempre apresentem recorte,
cobertura e identificadores de origem. Depois, usar essas consultas como ferramentas do agente.
Agente, avaliação de perguntas e interface continuam pendentes; atas ainda não foram coletadas.
