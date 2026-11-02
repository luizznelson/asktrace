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
