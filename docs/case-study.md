# Da pergunta à fonte: investigar publicações de compras

## Primeiro, a necessidade de análise

**Cenário proposto:** um analista prepara um relatório de acompanhamento de compras
públicas e precisa escolher o que examinar com mais detalhe. Quer comparar a distribuição
das publicações e sustentar as conclusões com registros conferíveis. Não houve observação
desse fluxo em organização: a persona e a necessidade ainda precisam ser validadas.

**Decisão apoiada:** por onde aprofundar a leitura dentro deste recorte. Volume de
publicações ajuda a descrever a base; sozinho não determina relevância, risco ou gasto.
O usuário pode conferir uma compra cujo ID já conhece e exportar os resultados para
seu relatório. Não existe navegação automática do ranking para compras de um órgão.

O PNCP já oferece busca e painéis. A proposta do AskTrace é uma forma adicional de
explorar um recorte histórico por perguntas, não uma substituição do portal. Veja a
[visão de negócio e suas fontes](business-case.md) para separar fatos, hipóteses e
benefícios que ainda precisam de medição.

## Depois, os desafios de implementação

O risco apareceu cedo: uma primeira página histórica tinha 50 registros, mas informava
454 resultados em dez páginas. Esse exemplo permanece nas amostras; não faz parte dos
números atuais. A solução percorre a paginação, verifica os registros e mantém estados
diferentes para coleta concluída, amostra e falha.

## Uma investigação de ponta a ponta

1. **Escolher o recorte:** maio–outubro/2026, pregões eletrônicos, unidades do Piauí.
2. **Perguntar:** “Como evoluíram as compras por mês de publicação?”
3. **Ler a conclusão:** junho teve o maior volume na série, com 527 publicações. Os seis
   meses somam 2.537 compras. Isso descreve publicação, não pagamento ou execução.
4. **Explorar:** o gráfico mostra os meses em ordem; a tabela permite conferir estimativas
   e quantidades ausentes. Rankings de órgãos/municípios têm limite explícito de 20.
5. **Auditar:** abrir fontes, rastro e cobertura; exportar JSON completo ou CSV contextualizado.

A conclusão e o gráfico usam as mesmas linhas da tabela. Não há segunda chamada de IA
para redigir a explicação e não são inferidos ganhos financeiros.

## Resultado construído

A base contém 2.537 compras. Todas as 2.536 compras com identificador válido tiveram a
busca de contratos concluída, com 679 contratos ligados a 370 compras. Em 2.166 pesquisas
não retornou publicação; uma compra foi excluída por ano inválido. Os 1.354 valores
homologados não informados permaneceram desconhecidos.

[Cobertura e conferência no PostgreSQL](contracts-expanded-coverage.md).

## Decisões que sustentam a experiência

| Desafio | Escolha | Resultado verificável |
| --- | --- | --- |
| Dados mudam e páginas podem faltar | Bytes originais, hashes e verificação de paginação | Falhas e orçamento limitado não viram sucesso |
| Dinheiro perde precisão em float | Decimal e NUMERIC; texto decimal nas respostas | Valor original preservado, apresentação em centavos separada |
| Uma compra pode ter vários contratos | Agregações partem das compras e usam snapshot explícito | Estimativas não multiplicadas por número de contratos |
| Um modelo pode gerar comandos inadequados | Catálogo fixo e validação do plano; login de leitura | O modelo não escreve SQL e o banco bloqueia escrita |
| Serviços gratuitos podem falhar | Contingência limitada e espera compartilhada por provedor | Falha da IA não é apresentada como ausência de dados |
| O histórico pode ficar antigo | Hash do recorte acompanha cada resposta | Uma resposta anterior não é restaurada como cobertura atual |

## O que foi avaliado

Software, interface e roteamento têm verificações separadas. A suíte Python inclui banco
isolado e falhas controladas. Os testes Node conferem gráficos, empates, limites, moeda,
histórico e CSV. O corpus local v3 teve 12/12; o planejador de IA v3 teve três testes
iniciais reais. A avaliação ampla v3, validação visual e demo hospedada estão pendentes.

[Qualidade](quality.md) · [Método de avaliação](agent-evaluation.md) · [Arquitetura](architecture.md).

## O que a solução não conclui

O app não determina fraude, economia ou pagamentos. A ausência de publicação não prova
ausência de contrato, e este recorte não representa todas as compras do Piauí. Perguntas
com filtros livres ou combinações fora do catálogo não são consultas implementadas.
O histórico não dá memória conversacional ao modelo.

O objetivo demonstrado é construir uma resposta limitada, compreensível e conferível —
da integração com a fonte até a apresentação do resultado.
