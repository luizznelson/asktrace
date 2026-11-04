# Avaliação de perguntas de negócio

## Estado atual

O roteador seleciona uma consulta somente leitura; as respostas são produzidas por templates com
dados verificados. Há modos individuais e um modo de contingência com até três tentativas de
planejador, mantendo no máximo uma ferramenta de negócio.

| Medição | Resultado | O que permite afirmar |
| --- | --- | --- |
| Baseline por regras | 60/60 no corpus original | Caminhos locais de desenvolvimento; não usa LLM |
| Qwen / contrato anterior | 52/60 | Oito recusas indevidas motivaram esclarecimentos do catálogo |
| Qwen / contrato v2, individual | 10 aprovados e um erro de rede; restante não executado | Medição parcial, preservada |
| Contingência / contrato v2 | 60/60 em dois trechos sem sobreposição | Mesmo código/configuração/corpus/cobertura; 40 planos LLM e 20 recusas locais |
| Oito perguntas adicionais | 8/8 | Congeladas antes de executar; autoria interna, não teste cego independente |
| GPT-OSS / contrato v2 | 3/3 reais | Teste de integração, não suíte completa do modelo |
| Xing / OpenRouter | 2/3 reais; um 429 | Reserva integrada, disponibilidade variável; rastreio pendente nessa rodada |
| Gemini / contrato anterior | Integração 3/3; depois 28 aprovados, um erro e 31 não executados em segmentos | Avaliação individual ainda incompleta por quota; não herda o resultado de outro modelo |

[Método de contingência, comandos e evidências](provider-contingency.md).

## Corpus, acerto e limites

[`business-v1.json`](../evals/business-v1.json) tem 60 perguntas curadas: 20 de resumo, 12 de
municípios, oito rastreios da mesma compra e 20 recusas. A aprovação exige ação e status esperados,
contagens globais previstas e ID correto no rastreio. Não valida toda frase possível ou toda soma
municipal; as consultas têm testes de software próprios. Os casos são de desenvolvimento e foram
usados para ajustar o catálogo: 60/60 não é estimativa de qualidade em perguntas abertas.

[`business-additional-v1.json`](../evals/business-additional-v1.json) traz oito perguntas distintas,
incluindo sinônimos, compra ausente, pagamento e outro estado/período. Uma recusa é do filtro local;
a recusa de Bahia/2024 depende do modelo. Não chamar as oito de benchmark externo independente.

Os resultados do modo `fallback` registram cada modelo escolhido. Avaliações individuais não
trocam de modelo. Não somar modelos, versões de prompt ou casos sobrepostos como uma nota única.
A consolidação atual verifica dois intervalos distintos, 1–10 e 11–60, com hashes compatíveis.
Os erros e a pontuação anterior foram preservados; os valores esperados não foram alterados.

## Executar

```powershell
.venv/Scripts/python.exe -m asktrace.evaluate --provider fallback --interval 12 --coverage runs/contracts-resume-c1345679-59ea-49ad-af35-be2cc924ceab/coverage.json
.venv/Scripts/python.exe -m asktrace.evaluate --provider groq-gpt-oss --limit 3 --coverage runs/contracts-resume-c1345679-59ea-49ad-af35-be2cc924ceab/coverage.json
.venv/Scripts/python.exe -m asktrace.evaluate --provider fallback --cases evals/business-additional-v1.json --coverage runs/contracts-resume-c1345679-59ea-49ad-af35-be2cc924ceab/coverage.json
```

O padrão da CLI é baseline. `--start-case N` usa posição começando em 1; `--limit N` limita o trecho.
O avaliador para em erro técnico de qualquer modo externo e registra não executados. `case-NNN.json`
preserva cada caso concluído; `corpus.source.json` captura os bytes exatos nas novas execuções.
Os relatórios mantêm hashes do código, corpus, configuração e cobertura. Há cache de consultas,
sem cache do plano externo; as latências não incluem a espera configurada entre casos e não são
medição de produção sem cache. Tentativas e tokens não comprovam custo monetário ou custo zero.

## Histórico e proveniência

- [Conferência atual](../runs/provider-verification-6f377e0f-a72c-4fc3-92ab-e225d79a95e1/verification.json).
- [Contingência 1–10](../runs/agent-eval-00419514-804c-44b4-a62b-fa32633e4094/evaluation.json)
  e [11–60](../runs/agent-eval-b53dbffa-b055-40f8-8b72-77aef201835f/evaluation.json).
- [Adicionais](../runs/agent-eval-69298927-ccd7-4016-99d9-8816a7c91833/evaluation.json).
- [Qwen antes do ajuste](../runs/agent-eval-5b9d5ff9-57ca-4dfc-bb7d-c7fdeac23004/evaluation.json).
- [Gemini parcial histórico](../runs/agent-consolidated-cbf07cd7-7961-4f6d-9b94-b0db226a64d1/verification.json).
- [Baseline histórico](../runs/agent-eval-3ad8ae41-4327-4033-ae56-2c59a60e451d/evaluation.json).

Os registros históricos podem usar hashes de bytes CRLF executados antes da conversão para LF pelo
Git. A [proveniência dos bytes](provider-contingency.md#bytes-de-execução-e-git-no-windows) guarda
cópias exatas e distingue hash de execução do hash publicado. Nenhum relatório antigo foi reescrito.
O resolvedor verifica essa correspondência antes de usar a evidência; não aceita dados alterados.

## Próxima etapa

Construir a interface para pergunta, resposta, recorte, fonte, rastro e motivo de recusa; depois medir
perguntas externas de usuários separadas do corpus de desenvolvimento. A integração local está
implementada. Interface, deploy e demonstração pública continuam pendentes. O software passou em
79 testes locais, incluindo PostgreSQL; CI remoto não verificado nesta entrega.
