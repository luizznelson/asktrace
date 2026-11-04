# Como explorar o AskTrace

## Se você tem 5 minutos

1. Leia “Em 1 minuto” e “O que os dados permitem afirmar” no [README](../README.md).
2. Abra o [estudo de caso](case-study.md) para entender a pergunta e os riscos de interpretação.
3. Veja [arquitetura](architecture.md) e uma decisão ligada ao código.
4. Confira [qualidade](quality.md) e os comandos de [reprodução](ingestion.md).

## Por pergunta

| O que você quer entender? | Comece aqui |
| --- | --- |
| Para quem serve e qual problema trata? | [Estudo de caso](case-study.md) |
| O que já foi coletado e como? | [Ingestão, evidências e limites](ingestion.md) |
| Como compras se ligam a contratos e qual a cobertura? | [Piloto de contratos](contracts.md) |
| Por que o código está organizado assim? | [Decisões de arquitetura](architecture.md) |
| Os testes comprovam o quê? | [Qualidade](quality.md) |
| Como executar e preparar commits? | [Desenvolvimento](development.md), [contribuição](../CONTRIBUTING.md) |
| O que são os arquivos de exploração? | [Amostras](../amostras/README.md), [inventário](sample-inventory.json) |
| Onde estão as execuções publicadas? | [Índice de runs](../runs/README.md) |
| O que ainda será feito? | [Plano](../PLANO.md) |

O README apresenta o projeto; os guias técnicos explicam a reprodução. Os relatórios de `runs/` preservam evidências de execuções específicas. Números de amostras históricas não são somados à coleta real de 2026.

A cobertura mais recente de contratos está na [ampliação para 100 compras](contract-expansion.md).

[Retomada da coleta e cobertura consolidada](contract-resumption.md): executar lotes sem repetir compras já consolidadas.

[Resultado mais recente da retomada](contract-progress.md).

[Contrato: cobertura consolidada mais recente](contract-coverage.md).

[Perguntas de negócio com acesso somente leitura](business-queries.md): comandos, permissões e exemplos reais.

[Roteador limitado e avaliação de perguntas](agent-evaluation.md): baseline medido e estado da integração Gemini.

[Contingência de provedores](provider-contingency.md): configuração em arquivo, modelos ativos, limites e evidências.

[Interface local](interface.md): percurso, comandos, proteções e verificação HTTP.
