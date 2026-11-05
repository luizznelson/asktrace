# Visão de negócio e critérios de apresentação

## Proposta em uma frase

Apoiar a preparação de relatórios de acompanhamento de compras públicas: comparar
publicações de um recorte do PNCP, escolher o que conferir e levar resultados com fontes.

## Público, tarefa e decisão

**Público proposto:** analista que prepara um relatório de acompanhamento de publicações
de compras públicas. É uma hipótese de produto; não representa um cliente entrevistado
ou uma necessidade de mercado validada.

**Tarefa proposta:** descrever onde e quando se concentram as publicações do recorte e
conferir registros que serão citados no relatório. O problema de negócio formulado é
transformar uma pergunta de acompanhamento em uma comparação documentada que ajude
a escolher o próximo registro a examinar.

**Decisão apoiada:** por onde aprofundar a leitura. O app fornece comparações; não escolhe
prioridades pelo usuário. Quantidade de publicações não mede gasto, relevância ou risco.

**Entrega utilizável:** resumo, gráfico quando aplicável, tabela, CSV e JSON com recorte
e evidências. Isso é uma capacidade implementada, não um ganho de produtividade medido.

## O que já existe no contexto do problema

O [PNCP oficial](https://www.gov.br/pncp/pt-br/pncp) centraliza publicações e oferece busca,
filtros, documentos, painel estatístico e dados abertos com APIs. Portanto, a justificativa
do AskTrace não é falta de acesso ou inexistência de ferramentas de análise. A proposta
é complementar esses recursos com perguntas sobre uma base histórica delimitada.

O portal atribui aos órgãos e entidades contratantes a responsabilidade pelas informações
publicadas. A integridade da cópia coletada não comprova a correção de todo registro da fonte.

Referência consultada em 04/11/2026. Nenhum estudo de concorrência, demanda ou disposição
a pagar foi realizado. O projeto demonstra uma solução técnica para um cenário proposto;
a viabilidade de mercado permanece em aberto.

## Perguntas, saídas e uso possível

| Pergunta de análise | Saída implementada | Uso possível no relatório | Limite |
| --- | --- | --- | --- |
| Qual é a dimensão da base? | Resumo de compras, contratos e cobertura | Declarar o universo analisado | É um snapshot, não todo o PNCP |
| Onde há mais publicações? | Ranking de municípios | Descrever distribuição geográfica | Até 20 grupos; não mede qualidade ou risco |
| Quais órgãos concentram publicações? | Ranking de órgãos compradores | Escolher um órgão para leitura posterior | Até 20; sem filtro dos registros desse órgão |
| Como o volume varia no período? | Série por mês de publicação | Descrever distribuição mensal | Não é data de execução ou pagamento |
| Quais contratos estão ligados a esta compra? | Consulta por ID PNCP explícito | Conferir um registro escolhido pelo analista | Não descobre automaticamente o ID a partir do ranking |
| Quais campos não foram informados? | Contagens de preenchimento | Declarar limites da interpretação | Campos podem se sobrepor; não somar contagens |

Não estão implementados filtros livres, análise por categoria de produto, alertas de
editais abertos, recomendação de licitações, avaliação de fornecedores, pagamentos ou
detecção de irregularidades. Nada disso deve ser prometido na apresentação.

## Como a IA participa

A linguagem natural é uma entrada alternativa para selecionar uma das seis consultas
permitidas. O modelo não escreve SQL e não calcula os números. As mesmas consultas podem
ser selecionadas por regras locais, sem API externa. A comparação com esse modo é o
ponto de partida para avaliar se a IA traz utilidade adicional para a tarefa proposta.
Não há recuperação de documentos para geração de texto: o projeto não deve ser chamado RAG.

## Fatos, hipóteses e impacto

| Afirmação | Estado | Evidência ou próximo passo |
| --- | --- | --- |
| Há 2.537 compras e 679 contratos na base padrão | Medido neste snapshot | [Cobertura e conferência](contracts-expanded-coverage.md) |
| A interface oferece seis consultas e exportação | Implementado e testado por código | [Análises](analytics.md), [qualidade](quality.md) |
| Um analista usaria isso ao preparar relatórios | Hipótese de uso | Entrevistar pessoas que executam essa tarefa |
| A linguagem natural facilita a análise | Hipótese de benefício | Comparar tarefas com IA, regras locais e recursos usuais |
| A solução reduz tempo, custo ou erros no trabalho | Não medido | Não publicar percentuais ou economia sem estudo |
| Existe demanda comercial ou adoção em organização | Não demonstrado | Pesquisa com público e piloto autorizado |

Os resultados de software e roteamento não substituem testes de usabilidade, qualidade
da análise humana ou impacto de negócio. Volume coletado não é ROI.

## Validação de negócio proposta — ainda não executada

1. Conversar com profissionais que preparam relatórios sobre compras públicas para
   conferir a tarefa, dificuldades reais e recursos já utilizados. Registrar consentimento
   e observações sem atribuir falas ou resultados fictícios.
2. Usar a mesma base em tarefas delimitadas: descrever a série mensal, identificar o
   primeiro órgão no ranking e conferir os contratos de um ID fornecido. Repetir nos modos
   IA e regras locais, alternando a ordem; comparar com o recurso usual apenas quando
   houver dados equivalentes. Registrar versão da base e do modelo.
3. Medir conclusão correta, tempo por tarefa, tentativas e capacidade de localizar a fonte.
   Conferir as respostas com o banco; registrar falhas, quotas e consultas recusadas.
4. Avaliar latência e custo observados separadamente da satisfação e da compreensão.
   Definir critérios com os participantes antes do piloto. Publicar método, tamanho da
   amostra e limitações, sem generalizar testes exploratórios para todo o mercado.

## Referências para a apresentação do projeto

- [Andrew Ng / DeepLearning.AI, How to Build Your Career in AI](https://home-wordpress.deeplearning.ai/wp-content/uploads/2022/10/eBook-How-to-Build-a-Career-in-AI.pdf),
  capítulos 4 e 6: partir de um problema de negócio, considerar o domínio, comunicar o
  valor pretendido e explicar o que foi realizado. É orientação de carreira; não é estudo
  estatístico de contratação de juniores no Brasil.
- [GitHub Docs, About READMEs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes):
  explicar o que o projeto faz, sua utilidade e como começar; detalhes extensos podem
  ficar na documentação.
- [PNCP, Sobre o portal](https://www.gov.br/pncp/pt-br/pncp): contexto oficial, recursos
  existentes e responsabilidade pelas informações. Sustenta o contexto dos dados, não
  uma demanda validada pelo AskTrace.

**Aplicação dessas referências:** apresentar público e tarefa → decisão apoiada → exemplo
de uso → entregas verificadas → arquitetura → avaliações e limites. Esta sequência é
uma decisão editorial do projeto, não uma regra universal nem promessa de contratação.
