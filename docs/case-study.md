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

## Como explicar a entrega para a equipe

**Pergunta de negócio:** “Como as publicações se distribuíram ao longo do período?”

Na base padrão, a análise retorna 505 compras em maio, 527 em junho, 424 em julho,
412 em agosto, 373 em setembro e 296 em outubro. A soma é 2.537. A resposta para o
relatório pode ser:

> No recorte analisado, junho teve o maior número de compras publicadas: 527. A série
> descreve o volume de publicações por mês. Esses números não permitem concluir em
> qual mês houve maior pagamento ou explicar a causa da variação.

**Uso possível:** escolher um mês para uma leitura posterior, documentando o critério.
O app não lista compras filtradas por mês nem investiga a causa da variação; essa etapa
exigiria outras consultas ou retorno ao portal. A decisão de aprofundamento é humana.

**Entrega para quem prepara o relatório:** gráfico para entender a distribuição, tabela
para conferir os números e exportação com período, modalidade e origem. Ao compartilhar,
o analista pode indicar exatamente a qual base a conclusão se refere.

## Da necessidade de negócio à escolha técnica

| Necessidade explicada em linguagem de negócio | Escolha de engenharia | Como conferir |
| --- | --- | --- |
| O relatório precisa dizer de onde veio o número | Evidências da coleta, identificadores e hashes | Fontes e registro de execução |
| O mesmo valor não pode ser contado várias vezes por ter vários contratos | Agregação parte das compras, sem multiplicação por contratos | SQL e verificações de totais |
| Um campo desconhecido precisa continuar desconhecido | Preservação de nulos e precisão decimal | Tabela, diagnóstico de campos e testes |
| Uma pergunta não pode alterar os registros | Catálogo de consultas e acesso de leitura | Arquitetura e permissões do banco |
| Uma falha da IA precisa ser distinguida de falta de informação | Estado de erro explícito e consulta local opcional | Interface e testes de falhas |

## Depois, os desafios de implementação

O risco apareceu cedo: uma primeira página histórica tinha 50 registros, mas informava
454 resultados em dez páginas. Esse exemplo permanece nas amostras; não faz parte dos
números atuais. A solução percorre a paginação, verifica os registros e mantém estados
diferentes para coleta concluída, amostra e falha.

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
histórico e CSV. O corpus final v3 teve 60/60 nas regras locais. Com IA houve 60 aprovações
em 61 execuções, com uma falha preservada e retomada explícita; os 60 casos distintos foram
concluídos. A validação visual e a demo hospedada estão pendentes.

[Qualidade](quality.md) · [Método de avaliação](agent-evaluation.md) · [Arquitetura](architecture.md).

## O que a solução não conclui

O app não determina fraude, economia ou pagamentos. A ausência de publicação não prova
ausência de contrato, e este recorte não representa todas as compras do Piauí. Perguntas
com filtros livres ou combinações fora do catálogo não são consultas implementadas.
O histórico não dá memória conversacional ao modelo.

O objetivo demonstrado é construir uma resposta limitada, compreensível e conferível —
da integração com a fonte até a apresentação do resultado.

## Roteiro para a demonstração hospedada — gravação pendente

1. **Problema e tarefa:** explicar que o objetivo é preparar um panorama de publicações
   e sustentar as conclusões de um relatório com fontes.
2. **Pergunta e resultado:** escolher a base e perguntar pela distribuição mensal.
   Mostrar a conclusão, o gráfico e o período usado, sem interpretar publicação como pagamento.
3. **Conferência:** usar o exemplo de compra oferecido pela base; abrir contratos e fontes.
4. **Entrega:** exportar a tabela ou o registro de evidências e mostrar seus limites.
5. **Engenharia:** encerrar no GitHub com a arquitetura e uma decisão ligada ao problema,
   como manter os cálculos no banco e validar o plano do modelo.

O vídeo deve registrar uma execução real na URL publicada. Se o modo IA não estiver
disponível, identificar o modo por regras utilizado; não editar falhas para simular
uma inferência bem-sucedida. O roteiro não substitui a gravação.
