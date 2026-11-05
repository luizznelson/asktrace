# AskTrace

**[Abrir demonstração](https://asktrace-pyop.onrender.com)**

**Prepare uma análise de compras públicas: compare publicações, escolha o que conferir e leve as fontes.**

[English](README.en.md) · [Estudo de caso](docs/case-study.md) · [Arquitetura](docs/architecture.md) · [Documentação](docs/README.md)

![Visão geral do AskTrace: 2.537 compras no recorte, 2.536 compras aptas pesquisadas e 679 contratos encontrados](docs/assets/asktrace-overview-pt.svg)

[![Quality](https://github.com/luizznelson/asktrace/actions/workflows/quality.yml/badge.svg?branch=main)](https://github.com/luizznelson/asktrace/actions/workflows/quality.yml)

O AskTrace apoia a preparação de relatórios de acompanhamento de compras públicas.
A pessoa que faz essa análise precisa entender o panorama, escolher o que conferir com
mais detalhe e explicar quais dados sustentam suas conclusões. O aplicativo reúne
comparações de publicações, consulta de uma compra identificada e exportação com fontes,
usando um recorte histórico do Portal Nacional de Contratações Públicas (PNCP).

## Escolha seu percurso de leitura

- **Entender a proposta:** cenário, perguntas e exemplo nas seções abaixo; depois o [estudo de caso](docs/case-study.md).
- **Avaliar a engenharia:** [habilidades e evidências](#habilidades-demonstradas-e-onde-conferir), [arquitetura](docs/architecture.md) e [qualidade](docs/quality.md).
- **Executar ou reproduzir:** [instruções neste README](#executar-e-reproduzir) e [preparação do ambiente e da base](docs/development.md).

## Uma situação que explica a proposta

**Cenário ilustrativo:** uma equipe quer um panorama das compras publicadas no período.
O responsável pelo relatório precisa responder: onde as publicações se concentram,
como se distribuem ao longo dos meses e quais informações precisam de conferência?

A tarefa envolve mais do que mostrar um total. É preciso comparar os registros, separar
informações conhecidas das ausentes e manter a origem dos números disponível. Sem essas
distinções, o relatório pode tratar uma publicação como pagamento ou apresentar um campo
desconhecido como zero. São riscos de interpretação que o projeto trata explicitamente,
sem atribuir sua frequência a organizações que não foram estudadas.

O AskTrace organiza essa tarefa em um percurso: **perguntar, comparar, conferir e levar
o resultado para o relatório**. O usuário recebe um resumo, visualizações quando cabíveis,
uma tabela e arquivos de exportação com contexto. A análise e a escolha do que merece
aprofundamento continuam com a pessoa.

## O valor da entrega para cada público

| Quem lê ou usa | O que precisa entender | O que o projeto entrega |
| --- | --- | --- |
| Gestão | O que o panorama permite dizer e onde aprofundar a leitura | Comparações de publicações, contexto e limites da conclusão |
| Análise | Como conferir e incorporar os números no relatório | Tabelas, identificadores, fontes e exportação CSV/JSON |
| Engenharia | Como o sistema mantém os resultados consistentes | Consultas controladas, evidências da coleta e testes documentados |

O benefício pretendido é apoiar uma análise explicável e conferível. **Não houve ainda
validação com usuários ou medição de economia de tempo, custo ou redução de erros.**
O público descrito é proposto, não uma carteira de clientes. O
[PNCP já oferece busca e painéis](https://www.gov.br/pncp/pt-br/pncp); o AskTrace apresenta
uma forma adicional de explorar o recorte por perguntas. As hipóteses e o plano de
validação estão na [visão de negócio](docs/business-case.md).

## Da pergunta à decisão de análise

| Necessidade do relatório | Pergunta atendida | Como usar o resultado |
| --- | --- | --- |
| Escolher onde aprofundar a leitura | Quais órgãos ou municípios têm mais compras? | Comparar volumes de publicações; o ranking é limitado a 20 grupos |
| Descrever a distribuição no período | Como evoluíram as compras por mês de publicação? | Apresentar a série mensal, sem confundir publicação com pagamento |
| Conferir uma compra já identificada | Rastreie a compra pelo ID PNCP | Examinar contratos vinculados e sua origem; exige informar o ID |
| Explicitar limites do relatório | Como está o preenchimento dos dados? | Mostrar campos desconhecidos e cobertura, sem convertê-los em zero |

**Percurso:** conferir o recorte → comparar publicações → consultar uma compra pelo ID
→ conferir fontes → exportar CSV/JSON. As consultas são independentes: o ranking não
abre uma lista filtrada de compras por órgão. O usuário escolhe o registro a conferir.

## Onde entra a IA

A IA interpreta uma pergunta em português e escolhe entre seis consultas permitidas.
Os cálculos e as respostas numéricas vêm do banco. Existe um modo por regras locais,
sem API externa, para o mesmo catálogo. O valor adicional da linguagem natural ainda
precisa ser comparado com esse modo em tarefas com usuários. Não é um sistema RAG.
Interface em PT-BR e inglês; perguntas suportadas em português. Execução atual local.

## Experimente uma investigação

| Pergunte | O que você recebe | Como conferir |
| --- | --- | --- |
| Como evoluíram as compras por mês de publicação? | Resumo calculado, seis meses em gráfico e tabela | Junho tem 527 publicações; a série soma 2.537 compras |
| Quais órgãos têm mais compras na base? | Até 20 órgãos por quantidade, com prévia dos cinco primeiros | CNPJ do órgão, valores estimados e campos ausentes |
| Rastreie a compra 00394452000103-1-011584/2026. | Dados da compra e contratos vinculados | Identificadores, índices e hashes das páginas de origem |

Também estão disponíveis panorama da cobertura, municípios e qualidade dos dados.
Os resumos e gráficos são calculados a partir das linhas retornadas, sem uma segunda
chamada de IA. JSON e CSV preservam contexto e valores originais.

## Entregas verificadas: cobertura dos dados

| Base padrão: publicações de maio–outubro/2026, modalidade 6, unidades do Piauí | Quantidade |
| --- | ---: |
| Compras na base | 2.537 |
| Compras aptas com contratos pesquisados | 2.536 |
| Contratos vinculados a 370 compras | 679 |
| Compras pesquisadas sem publicação retornada | 2.166 |
| Compras aptas pendentes | 0 |
| Exclusão por ano inválido na fonte | 1 |

São contagens deste snapshot, não indicadores de impacto financeiro. Publicação não
comprova pagamento; ausência no portal não comprova ausência de contrato. Os 1.354 valores
homologados não informados permanecem desconhecidos. O recorte original de agosto–outubro
é separado e nunca é somado à base padrão.

[Conferência da cobertura e do banco](docs/contracts-expanded-coverage.md) · [O que as análises permitem concluir](docs/analytics.md)

## Como funciona

```mermaid
flowchart LR
    P[PNCP: publicações e contratos] --> C[Coleta paginada e validação]
    C --> E[Arquivos de origem e hashes]
    C --> D[(PostgreSQL por snapshot)]
    U[Pergunta na interface] --> R[Regras locais ou planejador de IA]
    R --> V[Plano validado: seis consultas permitidas]
    V --> Q[Consulta parametrizada somente leitura]
    D --> Q
    Q --> A[Resumo, gráfico e tabela]
    E --> F[Fontes, cobertura e rastro]
    A --> F
```

O modelo escolhe uma consulta do catálogo; não escreve SQL nem inventa o resultado
numérico. Os dados do banco não são enviados ao planejador. Sem API externa, o modo por
regras atende os mesmos seis caminhos. O histórico organiza a aba, sem memória
conversacional no modelo, e identifica respostas de versões anteriores da base.

## Habilidades demonstradas e onde conferir

As decisões abaixo conectam a tarefa de negócio à implementação. Os links permitem
examinar o trabalho realizado, seus testes e suas limitações.

| Habilidade | Como aparece no projeto | Evidência para avaliação |
| --- | --- | --- |
| Comunicar problema, solução e limites | Cenário de uso, perguntas de negócio e interpretação de um resultado real | [Estudo de caso](docs/case-study.md), [visão de negócio](docs/business-case.md) |
| Trabalhar com dados de uma fonte real | Coleta paginada, validação, hashes e carga sem duplicar registros | [Ingestão](docs/ingestion.md), [cobertura concluída](docs/contracts-expanded-coverage.md), [integridade](asktrace/evidence.py) |
| Integrar LLMs com comportamento delimitado | Catálogo de consultas, validação do plano e recusas fora do escopo | [Agente](asktrace/agent.py), [método de avaliação](docs/agent-evaluation.md) |
| Projetar consultas e preservar valores | Agregações por compra, precisão decimal, ausências e acesso de leitura | [Consultas](asktrace/query.py), [permissões](sql/004_reporting.sql), [formatação](web/formatters.js) |
| Construir uma experiência utilizável | Interface PT-BR/EN, histórico da aba, resumos, gráficos e exportação contextualizada | [Interface](docs/interface.md), [análises](docs/analytics.md), [código da interface](web/app.js) |
| Verificar qualidade e lidar com falhas | Testes de software, avaliação de roteamento, tentativas limitadas e espera por provedor | [Qualidade](docs/quality.md), [contingência](docs/provider-contingency.md), [execuções](runs/README.md) |

A contribuição está na integração dessas partes e nas decisões documentadas. Os testes
comprovam comportamentos delimitados; os dados coletados comprovam cobertura. A utilidade
com usuários e a operação pública ainda precisam de validação. A assistência de IA no
desenvolvimento está declarada ao final deste README.

## Qualidade: software e IA são verificações diferentes

- **Software:** 137 testes Python na última suíte, com PostgreSQL isolado; contratos Node
  para interface, gráficos, formatação e CSV. [Como reproduzir e interpretar](docs/quality.md).
- **Roteamento local v3:** 60/60 casos do corpus final curado, incluindo as seis consultas e recusas.
- **Contingência de IA v3:** 60 aprovações em 61 execuções, com uma falha preservada.
  Os 60 casos foram concluídos após uma retomada explícita do caso que falhou.
  [Método, execuções e limites](docs/agent-evaluation.md#avaliação-final-do-catálogo-v3).
- **Restauração e rotas públicas:** dados restaurados sem coleta e 12 consultas reais
  pelas rotas ASGI, usando o PostgreSQL local. [Conferência final](runs/release-readiness-411e550a-cfc1-4cd5-bac5-a73e3ba2cf33/verification.json).
- **Publicação:** seis consultas das duas bases conferidas pela URL pública, além de
  recusa, proteção de sessão e uma consulta com IA real. [Registro do Render](runs/render-verification-5c4ad84a-6be1-46af-a81b-5965ccc471f6/verification.json).
- **Interface:** página inicial, troca PT-BR/EN, pergunta, histórico e download CSV
  conferidos no navegador publicado. Revisão visual completa e vídeo ainda pendentes.

Não há promessa de acurácia geral baseada nos testes curados, nem economia de trabalho medida.

## Executar e reproduzir

Para testar o código com fixtures locais, sem baixar novamente o PNCP:

```powershell
uv venv --python 3.14
uv pip install --python .venv/Scripts/python.exe --require-hashes -r requirements.txt
uv pip install --python .venv/Scripts/python.exe -r requirements-dev.txt
.venv/Scripts/python.exe -m unittest discover -s tests -q
node tests/test_display_formatters.cjs
node tests/test_result_presentation.cjs
node tests/test_assistant_ui.cjs
```

O código usa Python 3.14; os testes JavaScript usam Node 22 na CI. Testes de banco exigem
PostgreSQL e opt-in explícito. A CI está configurada; o badge acima reflete a execução remota.

**Rodar o app com a base real exige preparação adicional:** PostgreSQL, downloads
brutos/processados verificados e carga dos snapshots. Esses downloads não estão no Git.
Os hashes publicados não substituem os arquivos e uma nova coleta pode retornar bytes
diferentes. Siga [desenvolvimento](docs/development.md), [ingestão](docs/ingestion.md) e
[contratos](docs/contracts-expanded-coverage.md). A chave de IA é opcional no modo local;
segredos ficam no `.env` ignorado, nunca no `.env.example` versionado.

Com a base preparada, execute `.venv/Scripts/python.exe -m asktrace.web` e abra
`http://127.0.0.1:8010` para a prévia local.

**Aplicação publicada:** [Render Free](https://asktrace-pyop.onrender.com), com PostgreSQL no Neon, credenciais
separadas, restauração das evidências e limites persistentes. O endereço externo foi
verificado em 05/11/2026. Siga o [guia de publicação](docs/deployment.md).

**Desempenho observado no Render:** após a otimização, as seis consultas por regras
da base maior levaram 0.563–0.940 segundos; antes, 20–23 segundos. Uma pergunta com IA
levou 1.884 segundos. São duas execuções observadas, sem garantia de desempenho.
[Evidências e comparação](runs/render-performance-59ca88d-verified/verification.json).

O banco no Neon também foi carregado e verificado: os seis caminhos das duas bases
passaram com os logins restritos, as evidências foram restauradas do banco e o limite
persistiu após reinicializar a aplicação de teste. [Verificação remota](runs/neon-verification-187bed11-8da5-4be2-8712-d694a4ea11a0/verification.json).
A conferência do endereço público está registrada separadamente no [Render](runs/render-verification-5c4ad84a-6be1-46af-a81b-5965ccc471f6/verification.json).

**Otimização publicada e conferida:** commit `59ca88d`, doze consultas nas duas bases,
uma solicitação com IA real, nova instância com o mesmo orçamento de uso e rejeição do
token da instância anterior. [Conferência pública](runs/render-performance-59ca88d-verified/verification.json). A retomada após suspensão
por inatividade permanece separada e ainda não foi comprovada.

## Para aprofundar

[Caso de uso e percurso](docs/case-study.md) · [Arquitetura e decisões](docs/architecture.md) ·
[Análises e exportação](docs/analytics.md) · [Índice de evidências](runs/README.md) · [Plano](PLANO.md)

O histórico da construção permanece na documentação e em `runs/`; o README descreve o
estado atual. Fonte: [PNCP](https://www.gov.br/pncp/pt-br). [Licença do código](LICENSE):
não determina a licença dos dados de terceiros. Houve assistência de IA no desenvolvimento;
a responsabilidade por compreender, revisar e verificar o código é do mantenedor.
