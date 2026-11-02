# Amostras públicas usadas no desenvolvimento

Estes arquivos são páginas parciais de consultas ao PNCP referentes a outubro de 2025. Não representam o recorte de agosto a outubro de 2026 planejado para a ingestão.

| Arquivo | Conteúdo |
| --- | --- |
| `pncp-contratacoes-pi.json` | Primeira página de pregões eletrônicos do Piauí: 50 registros; resposta informa 454 resultados. |
| `pncp-contratacoes.json` | Primeira página de contratações da consulta nacional: 50 registros. |
| `pncp-contratos.json` | Primeira página de contratos da consulta nacional: 50 registros. |
| `diarios-picos.json` | Arquivo vazio deixado pela tentativa sem sucesso de obter diários de Picos. Não é uma resposta válida nem evidência de ausência de publicações. |

Origem: PNCP, API de consulta em https://pncp.gov.br/api/consulta/swagger-ui/index.html. O inventário em [docs/sample-inventory.json](../docs/sample-inventory.json) preserva os hashes dos bytes recebidos. A data exata da aquisição e os parâmetros completos não foram registrados automaticamente na coleta original; o período vem da conversa de aquisição, não de um manifesto completo.

As amostras de contratações foram preservadas sem alteração. O original de contratos permanece local e ignorado pelo Git por conter fornecedores pessoa física. A cópia em `publicadas/pncp-contratos.json` mascara os campos estruturados de identificação e nome de fornecedores/subcontratados pessoa física; não é idêntica ao original. `publicadas/proveniencia.json` registra os hashes de origem e da cópia. Os relatórios em `runs/` descrevem os originais locais, cujos hashes podem diferir das cópias publicadas. Registros públicos podem ser corrigidos na origem; estas são fotografias históricas de páginas. A origem dos dados é o PNCP, não o autor do projeto. O trabalho do projeto é a aquisição, tratamento, auditoria e interpretação com limites explícitos.
