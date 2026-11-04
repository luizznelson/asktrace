# Avaliação de perguntas de negócio

`business-v1.json` contém 60 casos curados de desenvolvimento e respostas esperadas para o snapshot
fixo de 1.081 compras. Distribuição: 20 resumo, 12 municípios, oito rastreios da mesma compra e 20 recusas.
Não é teste cego nem amostra representativa de perguntas reais. Não editar casos antigos apenas para
melhorar uma pontuação; alterações de escopo ou cobertura exigem uma versão nova.

O modo baseline não usa LLM. O adaptador Gemini tem avaliação independente e não deve herdar o
resultado do baseline. Os testes de software ficam em `tests/`; execuções e rastros em `runs/`.
Veja [método, comandos e limitações](../docs/agent-evaluation.md).

`business-additional-v1.json` contém oito perguntas congeladas antes da primeira execução, incluindo um registro ausente e uma recusa dependente do modelo. Autoria interna: não é benchmark externo cego. Novas execuções preservam `corpus.source.json` para verificar exatamente os bytes usados, independentemente das quebras de linha do sistema. [Contingência e evidências](../docs/provider-contingency.md).
