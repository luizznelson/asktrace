# Como explorar o AskTrace

## Percurso recomendado

Comece pelo problema e pelo exemplo de uso. Depois confira as decisões, o código e os
resultados de avaliação. Os registros históricos ficam ao final deste índice para que
a evolução seja auditável sem interromper a apresentação do estado atual.

| O que você quer avaliar | Por onde começar | Onde aprofundar |
| --- | --- | --- |
| Clareza de negócio e comunicação | [README](../README.md), [estudo de caso](case-study.md) | [Visão de negócio e hipóteses](business-case.md) |
| Capacidade de construir a solução | [Habilidades e evidências](../README.md#habilidades-demonstradas-e-onde-conferir) | [Arquitetura](architecture.md), [ingestão](ingestion.md), [consultas](business-queries.md) |
| Cuidado com qualidade e limites | [Qualidade](quality.md) | [Avaliação do agente](agent-evaluation.md), [execuções](../runs/README.md) |
| Reprodução do trabalho | [Desenvolvimento](development.md) | [Base concluída](contracts-expanded-coverage.md), [contribuição](../CONTRIBUTING.md) |

## Entender o produto

1. [Visão de negócio](business-case.md): público proposto, tarefa, decisões, fontes e validação pendente.
2. [README](../README.md): problema, perguntas, resultados atuais e funcionamento.
3. [Estudo de caso](case-study.md): uma investigação completa e decisões de implementação.
4. [Análises](analytics.md): seis consultas, exportação e interpretação dos números.
5. [Interface](interface.md): uso, histórico e fontes.

## Conferir a implementação

| Pergunta | Documento |
| --- | --- |
| Como o fluxo completo foi organizado? | [Arquitetura e decisões](architecture.md) |
| Qual a cobertura atual dos contratos? | [Base ampliada concluída](contracts-expanded-coverage.md) |
| O que os testes e avaliações comprovam? | [Qualidade](quality.md), [avaliação do agente](agent-evaluation.md) |
| Como a aplicação trata quotas e falhas? | [Contingência](provider-contingency.md), [revisão da aplicação](application-review.md) |
| Como executar e configurar segredos? | [Desenvolvimento](development.md) |
| Como coletar e carregar os dados? | [Ingestão](ingestion.md), [contratos](contracts.md), [consultas de leitura](business-queries.md) |
| Onde conferir as execuções? | [Índice de runs](../runs/README.md) |
| O que entra no Git? | [Contribuição](../CONTRIBUTING.md), [amostras](../amostras/README.md) |
| Onde hospedar gratuitamente e o que falta para publicar? | [Avaliação de hospedagem](hosting-options.md) |
| O que ainda está pendente? | [Plano](../PLANO.md) |

O padrão é maio–outubro/2026: 2.537 compras, 2.536 pesquisas de contratos e 679 contratos.
A exclusão por ano inválido permanece explícita. Os documentos abaixo registram a
evolução; suas quantidades não devem ser somadas ou lidas como o estado atual.

## Histórico preservado

[Piloto](contracts.md) → [100 compras](contract-expansion.md) →
[retomada](contract-resumption.md) → [progresso](contract-progress.md) →
[cobertura do recorte original](contract-coverage.md) → [ampliação para seis meses](dataset-expansion.md) →
[cobertura ampliada concluída](contracts-expanded-coverage.md).

[Inventário das amostras](sample-inventory.json) e manifestos em `runs/` mantêm a evidência
da construção sem transformar o README em um diário de entregas.

[Histórico de qualidade](history/quality-log.md) · [Histórico da interface](history/interface-log.md).
