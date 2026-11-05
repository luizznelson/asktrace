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
- [x] Commit da otimização publicado no Render; doze caminhos e IA real verificados com latência registrada.
- [x] Conferir nova instância da versão otimizada no Render: orçamento preservado e token anterior rejeitado.
- [x] Retomada após suspensão por inatividade conferida nos logs do Render: startup de ~22 s; o tempo total percebido não foi cronometrado ([registro](docs/deployment.md#retomada-após-suspensão-por-inatividade)).
- [x] Commit `5b2f47e` implantado manualmente no Render (autoDeploy desligado); selo e rótulos em inglês conferidos no endereço público.
- [ ] Concluir revisão visual das telas restantes: rastreio por ID e seletor da base original. Já conferidos no app publicado: apresentação inicial, perguntas sugeridas, resposta mensal com gráfico, origem dos dados, qualidade dos dados, inglês, histórico e celular.
- [x] Vídeo de demonstração em PT e EN, montado a partir de capturas reais do app publicado, com links nos READMEs (`scripts/build_demo.py`, `docs/media/storyboard.json`).
- [x] CI observada no GitHub Actions: o commit do vídeo falhou no `ruff`; o commit de correção passou. Testes locais não substituem a execução remota.

## Como conferir

[Publicação](docs/deployment.md) · [Qualidade](docs/quality.md) ·
[Avaliação](docs/agent-evaluation.md) · [Evidências](runs/README.md).

O [histórico do plano](docs/history/plan-log.md) foi preservado para auditoria. RAG,
MCP e fluxos de automação adicionais ficam para o terceiro projeto, conforme combinado.
