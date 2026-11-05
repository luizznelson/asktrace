# AskTrace — conclusão da primeira versão

## Escopo fechado

Assistente para explorar um recorte histórico de publicações do PNCP, com seis consultas:
panorama, municípios, meses, órgãos, qualidade e uma compra com ID explícito.
Base padrão: maio–outubro/2026, modalidade 6, unidades do Piauí. O recorte original de
agosto–outubro permanece separado. Sem filtros livres, memória no modelo ou novas fontes.

## Entregas implementadas

- [x] Coleta e validação das duas bases com evidências preservadas.
- [x] Cobertura das 2.536 compras aptas da base padrão: 679 contratos, uma exclusão explícita.
- [x] PostgreSQL e consultas controladas com acesso somente leitura.
- [x] Roteador por regras e integração com LLMs, com contingência e falhas explícitas.
- [x] Interface PT-BR/EN, histórico da aba, gráficos, tabelas e exportação contextualizada.
- [x] Narrativa de negócio, estudo de caso e mapa de habilidades com evidências.
- [x] Entrada pública ASGI, TLS no banco, logins separados e restauração privada dos dados.
- [x] Limites de consulta e espera de provedores persistidos no PostgreSQL.
- [x] Corpus final de 60 perguntas congelado antes da execução; regras locais: 60/60.

## Fechamento pendente

- [x] Avaliação do catálogo atual: 60 aprovações em 61 execuções; uma falha preservada e retomada explícita.
- [x] Banco Neon carregado; duas bases, logins restritos, restauração e limites persistentes verificados.
- [x] Publicar no Render Free; seis consultas de ambas as bases e uma consulta com IA verificadas.
- [x] Otimizar a validação repetida; medir os doze caminhos ASGI com Neon.
- [ ] Enviar o commit da otimização, atualizar o Render e medir a latência pública.
- [ ] Conferir reinício da versão otimizada e retomada após suspensão no serviço hospedado.
- [ ] Concluir revisão visual de todas as telas. Navegador disponível; apresentação inicial, idioma, resposta, histórico e CSV já conferidos.
- [ ] Gravar o vídeo com a aplicação hospedada e acrescentar capturas reais ao README.
- [ ] Observar a CI do commit publicado; não equiparar testes locais à execução remota.

## Como conferir

[Publicação](docs/deployment.md) · [Qualidade](docs/quality.md) ·
[Avaliação](docs/agent-evaluation.md) · [Evidências](runs/README.md).

O [histórico do plano](docs/history/plan-log.md) foi preservado para auditoria. RAG,
MCP e fluxos de automação adicionais ficam para o terceiro projeto, conforme combinado.
