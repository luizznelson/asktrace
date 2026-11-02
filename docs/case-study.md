# Antes de responder, saber o que foi coletado

## Um risco concreto

A primeira página de uma consulta histórica do PNCP trouxe 50 pregões do Piauí. A própria resposta informava 454 resultados em 10 páginas. Um sistema que encerrasse ali poderia responder com segurança aparente sobre uma base incompleta.

O usuário proposto é alguém investigando compras públicas e comparando publicações por órgão, município, período e objeto. Precisa conseguir perguntar “de onde veio essa resposta?” e “o que ficou de fora?”. Não há implantação comprovada em uma organização nem economia de trabalho medida.

## Como a primeira entrega responde a esse risco

1. Fixar UF, modalidade e período de publicação antes da consulta.
2. Dividir o período em meses e percorrer as páginas informadas.
3. Preservar os bytes recebidos e seus hashes.
4. Conferir o recorte novamente nos registros e separar ausências de zeros.
5. Carregar um snapshot em transação, sem duplicar ao repetir a carga.
6. Publicar um manifesto e comparar os números com o banco.

## Resultado concreto

A coleta de agosto a outubro de 2026 recebeu 1.081 pregões em 23 páginas. PostgreSQL confirmou a mesma contagem. A ausência de valor homologado em 749 registros permanece explícita, impedindo interpretar esses campos como zero ou como pagamentos.

O [registro de conferência](../runs/pncp-3020d59b-d274-4f4c-be4f-d59e8be30101/database-load.json) liga o resumo ao snapshot. O teste intencional limitado a uma página também está preservado e identificado como falha por orçamento: ele não entra no resultado completo.

## O que isso ainda não responde

Não se pode concluir quais órgãos economizaram mais, quem recebeu pagamentos ou se houve irregularidade. Comparar valores depende de unidade, cobertura, situação e relações entre compras e contratos. Uma contratação pode gerar vários contratos; um contrato não deve ser comparado automaticamente ao orçamento inteiro da compra.

A próxima camada será o agente, com ferramentas limitadas e avaliação de perguntas. A base atual prepara evidências; ainda não demonstra qualidade de respostas de IA.

## Roteiro de apresentação

Mostre o caso de 50 registros versus 454 resultados. Abra o manifesto da coleta real, escolha uma página e localize o hash e seus filtros. Mostre a mesma contagem no banco e o comportamento de carga repetida. Termine explicando um teste de rollback e uma pergunta que ainda não pode ser respondida.
