# Como verificar o que foi feito

## Três perguntas diferentes

| Pergunta | Verificação disponível |
| --- | --- |
| O software reage corretamente? | Testes de regras e falhas, Ruff e integração PostgreSQL. |
| A coleta observada corresponde à carga? | Manifesto, hashes, contagem por mês e conferência no banco. |
| Um agente responde corretamente? | Ainda não há agente nem avaliação de respostas. Os testes atuais não medem isso. |

## Verificação local registrada

Em 02/11/2026, passaram 27 testes, incluindo dois de integração com PostgreSQL em `asktrace_test`. Foram conferidos Ruff, formatação, Compose e leitura dos 1.081 registros a partir das 23 páginas preservadas. Os números descrevem essa verificação, não uma promessa de ausência de falhas.

Os testes cobrem paginação variável, falha de rede, limite de páginas, interrupção, filtro de estado/modalidade/data, duplicados, precisão decimal, hash divergente, caminhos fora da execução, idempotência e rollback da transação. O banco de testes é separado dos dados reais.

## Como reproduzir

Instale o ambiente conforme o [README](../README.md). Testes sem PostgreSQL:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check .
docker compose config --quiet
```

Para os dois testes PostgreSQL, siga a configuração de `asktrace_test` e a variável `ASKTRACE_TEST_DATABASE` no [guia de ingestão](ingestion.md). Sem essa opção, a suíte informa dois testes ignorados, em vez de alegar que foram executados.

O [workflow](../.github/workflows/quality.yml) instala dependências fixadas com hashes e provisiona PostgreSQL para integração. O badge do README mostra o estado remoto informado pelo GitHub; a configuração da CI não é, por si só, confirmação de uma execução aprovada.

## Evidências e limites

As amostras históricas e os relatórios iniciais têm contexto próprio. Consulte [runs](../runs/README.md) para distinguir teste limitado, amostra e coleta concluída. Não some essas execuções.

Os bytes completos de dados reais ficam locais em pastas ignoradas pelo Git. Os manifestos publicados permitem verificar uma cópia disponível, mas não substituem sua disponibilização. Uma nova consulta pode retornar conteúdo atualizado, com hashes diferentes.

Não foram medidos produtividade, desempenho sob carga, acurácia de respostas ou cobertura de todas as compras públicas. Nenhuma afirmação de irregularidade ou aprovação financeira decorre desta etapa.

## Contratos: validação adicional em 02/11/2026

Após a implementação do coletor de contratos, a suíte completa passou com **36 testes**,
incluindo PostgreSQL. Os 27 testes citados acima correspondem à entrega anterior.
Os nove novos testes cobrem relações, integridade, falhas, valores e transações.
O piloto real não validou vínculos por falhas de consulta; testes sintéticos não substituem essa etapa.
Veja [relatório e reprodução](contracts.md). A execução remota do CI não foi verificada nesta entrega.

## Validação de contratos em 03/11/2026

A suíte atual passou com **39 testes**, incluindo PostgreSQL. Foram acrescentados testes de múltiplas páginas, totais alterados, páginas repetidas ou faltantes e o 404 específico de nenhum contrato publicado. O piloto real foi validado e carregado, com carga repetida idempotente. [Evidências e limites](contracts.md). Os números anteriores descrevem entregas anteriores. CI remoto não verificado.

## Ampliação de contratos em 03/11/2026

Suíte atual: **41 testes locais passaram**, incluindo PostgreSQL. A exclusão por localizador inválido e sua integridade são testadas. [Resultado da ampliação](contract-expansion.md).

## Retomada por lotes

Suíte atual: **46 testes locais passaram** com PostgreSQL ativo. Cinco testes cobrem seleção de intervalos, deduplicação de cobertura, parada por falha e integridade da retomada. [Evidências](contract-resumption.md).

## Consultas de negócio

Suíte atual: **51 testes locais passaram**, incluindo PostgreSQL. Cinco testes novos validam consultas fixas, totais, nulos, rastreabilidade, parametrização, permissões e integridade da cobertura. [Evidências](business-queries.md).

## Roteamento e avaliação

Suíte de software: **59 testes locais passaram**, incluindo PostgreSQL. Oito novos testes cobrem limites, planos, provedor e avaliador. Separadamente, o baseline passou nos 60 casos curados de desenvolvimento; isso não mede um LLM real. [Método e limitações](agent-evaluation.md).

## Teste de integração real Gemini

Três perguntas suportadas passaram em chamadas reais ao Gemini 2.5 Flash: resumo, municípios e rastreio.
Não equivale à suíte completa nem a testes de recusa do modelo. Os 59 testes de software anteriores
não foram repetidos nesta execução sem alterações de código. [Rastros e limites](agent-evaluation.md).

## Diagnóstico da avaliação Gemini

Suíte atual: **61 testes locais passaram**, incluindo PostgreSQL. Dois testes novos cobrem HTTP 429 preservado e continuação por posição com journal por caso. A avaliação do modelo está incompleta: última tentativa com seis aprovados, um erro 429 e 53 casos não executados. [Evidências](agent-evaluation.md).

## Continuação e diagnóstico de quota

Suíte de software: **62 testes locais passaram**, incluindo PostgreSQL. O novo teste verifica minimização dos detalhes de quota. Separadamente, 28/60 casos de desenvolvimento foram aprovados na consolidação Gemini por segmentos, com 29 tentativas de LLM e 0 recusas locais observadas nesses segmentos. A avaliação continua parcial. [Evidências e limitações](agent-evaluation.md).

## Contingência e preservação de evidências

O código atual passou em **79 testes locais**, incluindo PostgreSQL. A avaliação de contingência aprovou 60 casos curados em dois trechos compatíveis e oito adicionais; são métricas distintas dos testes. Troca controlada: falha inicial simulada e uma chamada real de reserva. Os relatórios históricos foram mantidos idênticos ao Git, com cópias dos bytes de execução para verificar hashes no Windows. [Método e limites](provider-contingency.md).

## Interface local

Suíte atual: **86 testes locais passaram**, incluindo PostgreSQL. Sete testes novos cobrem fronteiras HTTP, sessão e limites. Seis fluxos HTTP reais passaram; sintaxe JS verificada. Inspeção visual e interação no navegador pendentes: prévia local desativada no ambiente. [Detalhes](interface.md).

## Experiência de assistente

86 testes Python passaram novamente. Contrato DOM em Node verifica descoberta, envio, resposta, sugestões, histórico, idioma, reinício e sessão com elementos simulados; não é inspeção de layout. Seis fluxos HTTP reais passaram após o redesenho. Checks de Node adicionados ao CI, execução remota não verificada. [Evidências](interface.md).

## Recortes e sessão restaurável

Passaram **89 testes Python locais**, incluindo PostgreSQL. Três novos testes cobrem IDs de base permitidos, caminho correto do recorte e isolamento do período no planejador. Contrato DOM cobre restauração sem nova API e histórico inválido. HTTP real validou resumo original, ampliado e ampliado com IA. Não transfere a pontuação do corpus antigo ao novo recorte. [Evidências](dataset-expansion.md).

## Indisponibilidade do planejador

91 testes Python passaram; dois testes novos distinguem cooldown de falha do banco e garantem que nenhuma ferramenta roda antes do plano. Contrato DOM verifica fontes vazias ocultas e recuperação por clique, sem fallback silencioso. [Cenário controlado com banco real](../runs/recovery-verification-da469824-8e8f-43dd-b8ec-f0f220c19af1/verification.json).

## Diagnóstico e aviso prévio de limites

95 testes Python locais passaram. Quatro novos testes cobrem prazos de quota minimizados, entrada inválida e disponibilidade sem executar pergunta. O contrato DOM verifica aviso e escolha local sem chamada oculta. [Verificação real dos municípios por regras locais](../runs/availability-diagnosis-6d8f3e82-c79c-4319-9687-6a1b52674168/verification.json), sem chamada de provedor.

## Revisão da aplicação e regressões

102 testes Python, contrato DOM, Ruff e verificações HTTP/banco passaram. O aviso de IA deixou de aparecer na entrada sem pergunta. Validação de requisições, histórico e quotas recebeu cenários de falha; redirecionamentos com credenciais são bloqueados. [Correções, reprodução e limites](application-review.md).

## Apresentação de números e contratos

102 testes Python passaram, incluindo o novo arquivo estático servido pela allowlist HTTP.
Os contratos Node de formatação e interface conferem moeda com precisão decimal,
quantidades, datas sem deslocamento de fuso, campos ausentes e contratos em tabela.
Valores acima de 2^53 e arredondamento nos limites de centavos têm casos explícitos.
As evidências originais não são alteradas para produzir os textos da tela.
[Registro final](../runs/application-review-348a9663-dda0-42ca-bd0b-bf32bb2d84cb/verification.json); consultas reais por regras locais nos dois recortes,
sem chamadas externas de IA e sem inspeção visual.

## Cobertura compreensível e interface de produto

102 testes Python e os contratos Node passaram. Os novos cenários DOM conferem
2.436 pendências e uma exclusão na base ampliada, zero pendências na base original,
troca PT/EN e ausência de mistura entre relatórios históricos e metadados atuais.
Uma verificação textual impede regressões de menções a portfólio na aplicação.
[Evidência](../runs/application-review-8ae90c1e-92fe-4782-855c-9c8d76817734/verification.json): consultas HTTP reais por regras locais nos dois recortes,
sem chamadas externas de IA. Não houve inspeção visual em navegador.

## Análises ampliadas

108 testes Python passaram. A regressão cobre nome variante de órgão sem divisão de CNPJ, soma de compra sem multiplicação por contratos e zero versus ausência. Contratos Node validam CSV e novos resultados; HTTP real confere meses, órgãos e qualidade. O corpus local novo passou 12/12; três testes iniciais reais da IA v3 passaram. [Escopo das verificações](analytics.md).
