# AskTrace — escopo de trabalho

## Decisões confirmadas

- PostgreSQL com Docker, exposto apenas no computador local.
- Primeiro período: 01/08/2026 a 31/10/2026, três meses completos.
- PNCP como fonte principal; Querido Diário opcional, sem contornar verificação TLS.
- Primeiro recorte de contratações: pregões eletrônicos do Piauí (modalidade 6), conforme as amostras. Isso não representa todas as modalidades de compras públicas.

## Sequência

1. Validar fontes e cobertura, preparar PostgreSQL e auditar as amostras.
2. Implementar aquisição paginada e normalização, com manifestos, hashes, datas e falhas explícitas.
3. Definir a coleta de contratos e atas sem presumir filtro estadual inexistente.
4. Construir ferramentas de consulta somente leitura, cálculo exato e busca semântica.
5. Avaliar 50–80 perguntas com respostas esperadas, recusas, custo e limites de passos.
6. Apresentar respostas e seus rastros em interface simples PT-BR/EN.

## Cobertura e interpretação

A especificação oficial consultada em 02/11/2026 aceita `uf` em contratações/publicacao, mas não nos endpoints contratos e atas. Não usar um parâmetro ignorado para afirmar cobertura estadual. Contratos de órgãos que não aparecem no recorte de pregões podem ficar de fora de uma coleta baseada só nesses órgãos; essa limitação deve ser explícita.

O vínculo contrato → compra permite rastrear registros, mas uma compra pode gerar múltiplos contratos. Não chamar a diferença entre um contrato e o orçamento inteiro de economia ou sobrepreço.

As três amostras válidas têm 50 registros cada e descrevem consultas de outubro de 2025. Seus totais de paginação não são dados já ingeridos. O arquivo do Querido Diário está vazio; a causa das falhas TLS não foi diagnosticada definitivamente.

Fonte técnica: https://pncp.gov.br/api/consulta/v3/api-docs

## Estado atual

Criados inventário, auditor local de amostras, testes e configuração inicial de PostgreSQL. Docker e PostgreSQL foram validados. Ingestão de pregões de agosto a outubro de 2026 concluída: 1.081 registros. Agente ainda não implementado. Veja docs/ingestion.md para evidências e limites. As pequenas amostras públicas e os relatórios de auditoria ficam no Git; credenciais e downloads completos permanecem fora.

## Atualização: piloto de contratos em 03/11/2026

Piloto de 12 compras validado e carregado: um contrato e 11 respostas explícitas de nenhum contrato
publicado no PNCP. Paginação e tratamento do 404 específico corrigidos conforme evidências reais.
Ampliar gradualmente às compras restantes; atas ainda pendentes. [Método e limites](docs/contracts.md).

## Ampliação para 100 compras

Lote completo e carregado: 6 compras com contratos, 94 sem registros retornados, 6 contratos. Uma exclusão por ano inválido na fonte. [Limites e sequência](docs/contract-expansion.md).

## Retomada implementada

Lotes completos são verificados e pulados; o lote seguinte teve 40 falhas de conexão e não foi carregado. Repetir a retomada após normalizar a consulta ao PNCP. [Evidências](docs/contract-resumption.md).

## Cobertura atualizada

O lote terminou completo, foi carregado e a carga repetida não duplicou registros. A cobertura confirmada passou a 200 compras distintas e 12 contratos distintos. Restam 880 compras elegíveis e uma exclusão por ano inválido. [Relatório](docs/contract-progress.md).

## Consolidação de contratos vinculados

Cobertura elegível concluída: 1.080 compras distintas confirmadas. 125 contratos distintos e 0 compras elegíveis pendentes. Uma exclusão por ano inválido permanece explícita. Próxima etapa: consultas somente leitura com origem e cobertura, antes do agente. [Evidências](docs/contract-coverage.md).

## Consultas de negócio implementadas

Resumo, municípios e rastreio por compra disponíveis com credencial de leitura. Totais e permissões verificados; 51 testes locais passaram. Próximo passo: avaliação de perguntas e integração limitada com agente. [Evidências](docs/business-queries.md).

## Roteador limitado e corpus de avaliação

Baseline de uma etapa avaliado em 60 casos curados (60 aprovados). Gemini 2.5 Flash validado em três perguntas reais, sem erros e com rastro revisado. Próximo passo: avaliação completa separada do baseline, dentro da quota disponível. Interface continua pendente. [Evidências](docs/agent-evaluation.md).

## Avaliação completa pendente por limite do provedor

A primeira tentativa identificou recusa indevida e erro técnico. O prompt foi esclarecido e o status HTTP corrigido. Nova tentativa com espaçamento parou em HTTP 429: seis casos aprovados e 53 não executados. Continuar do caso sete quando a quota permitir. Não somar tentativas com prompts diferentes. Suíte de software: 61 testes aprovados. [Evidências](docs/agent-evaluation.md).

## Continuação da avaliação em 04/11/2026

Consolidação parcial por segmentos: 28 casos aprovados, um erro de provedor e 31 casos não executados. Mesmo prompt, modelo e fontes; diagnóstico aprimorado entre segmentos. O provedor informou limite diário gratuito de 20 requisições por projeto/modelo. Próximo passo: retomar do caso 29 após liberação da quota; são 32 casos pendentes incluindo o que falhou. [Evidências](docs/agent-evaluation.md).

## Contingência implementada em 04/11/2026

Pool revisado: Qwen/GPT-OSS na Groq, Xing gratuito no OpenRouter, Gemini após quota; opção Ollama desativada. Limites, espera, rastro e consultas somente leitura mantidos. Corpus de contingência 60/60 em trechos compatíveis e oito adicionais aprovados; GPT-OSS 3/3 em teste inicial e OpenRouter 2/3 com 429. Software: 79 testes locais. Próximo passo: interface com evidências e avaliação de perguntas externas. [Detalhes](docs/provider-contingency.md).

## Interface local implementada

Fluxo PT-BR/EN: contexto → pergunta → resposta → cobertura/fontes → rastro. Seis exemplos HTTP reais e 86 testes de software aprovados. Revisão visual de navegador pendente por prévia desativada. Próximo passo: verificar desktop/celular, ajustar o necessário e preparar hospedagem. [Comandos](docs/interface.md).

## Interface revisada como assistente

Aplicação com navegação lateral, histórico da aba, sugestões por assunto e próximas perguntas, observações de cobertura e evidências expansíveis. Padrão IA com contingência. Perguntas independentes, sem memória no modelo. Seis fluxos HTTP e contrato DOM passaram; inspeção visual ainda pendente por navegador desativado. [Detalhes](docs/interface.md).
