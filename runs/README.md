# Registros de execução publicados

Os dois relatórios JSON atuais auditam as mesmas amostras com versões diferentes do auditor:

- `sample-audit.json`: execução inicial da etapa de preparação.
- `precommit-audit-20261102.json`: execução após a revisão do auditor, com validações adicionais e códigos de erro.

Ambos registram o arquivo vazio do Querido Diário como inválido. Não são dois experimentos independentes, resultados de um agente ou ingestões completas. A execução retorna código 1 quando encontra arquivo inválido, como esperado neste conjunto.

Para reproduzir com um novo nome de saída:

```powershell
python scripts/audit_samples.py amostras --output runs/audit-replay.json
```

Compare os hashes e diagnósticos, considerando a evolução do código. Os relatórios publicados não devem ser sobrescritos silenciosamente. Novos arquivos em `runs/` passam a aparecer no Git: revise cada inclusão antes de commitá-la e não publique credenciais, dados particulares, bancos ou arquivos grandes.

## Execuções de ingestão

- `pncp-287e5086-3ed6-47ae-95b8-c965cb13502d`: validação histórica de 50 registros, modo amostra; não é coleta de 2026.
- `pncp-13037e9b-fbca-488c-a435-9b327710276a`: teste real limitado a uma página; status failed por orçamento de páginas, não por indisponibilidade do PNCP.
- `pncp-3020d59b-d274-4f4c-be4f-d59e8be30101`: coleta real concluída, 1.081 registros e 23 páginas, com conferência da carga no PostgreSQL.

Os JSONs brutos e normalizados dessas execuções ficam em data/raw e data/processed, fora do Git; os manifestos registram seus hashes e caminhos. Não some as amostras aos resultados reais. [Método e reprodução](../docs/ingestion.md).

## Piloto de contratos

[contracts-a6fa16c6-13c4-4205-94e9-cd01e9322636/manifest.json](contracts-a6fa16c6-13c4-4205-94e9-cd01e9322636/manifest.json): 12 compras tentadas, 11 respostas 503,
uma falha sem status HTTP, nenhum contrato validado; não carregado no banco.
Veja [método e interpretação](../docs/contracts.md). Preservar esta tentativa, mesmo após novas coletas.

## Atualização de contratos em 03/11/2026

Diagnóstico preservado em `contracts-4e458e67-f581-448d-b28a-2362deda4d93` (400 por falta de página) e `contracts-f5d0d7be-60fe-43d7-9007-666f868aeeca` (paginação corrigida, 404 ainda genérico). Nenhum deles foi carregado.

[Piloto validado](contracts-52c725b6-9b6f-42a6-b65e-e3858060c9ed/manifest.json): 12 compras, um contrato e 11 mensagens explícitas de nenhum contrato publicado. [Verificação no banco](contracts-52c725b6-9b6f-42a6-b65e-e3858060c9ed/database-load.json). [Guia de interpretação](../docs/contracts.md).

## Ampliação para 100 compras

[contracts-78f81b23-e1b7-4fbf-b8dc-a442b64fe259/manifest.json](contracts-78f81b23-e1b7-4fbf-b8dc-a442b64fe259/manifest.json): Lote completo e carregado: 6 compras com contratos, 94 sem registros retornados, 6 contratos. Uma exclusão por localizador inválido na população. [Método](../docs/contract-expansion.md).

## Retomada de contratos

O plano `contracts-resume-88d30f38-2d39-4a7c-a0e5-782f10ca128e` não terminou por indisponibilidade do banco. `contracts-resume-f93f55c8-753a-4d8d-a505-843bc7deb32e/coverage.json` registra a tentativa seguinte: lote `contracts-3eec93d4-abbc-4072-8f7b-66194aa4d685` pendente por 40 falhas de conexão, sem carga. [Método e cobertura consolidada](../docs/contract-resumption.md).

## Nova tentativa da retomada

[contracts-resume-d88d70d6-06d1-44ee-8923-5d9b17eb364a/coverage.json](contracts-resume-d88d70d6-06d1-44ee-8923-5d9b17eb364a/coverage.json): O lote terminou completo, foi carregado e a carga repetida não duplicou registros. A cobertura confirmada passou a 200 compras distintas e 12 contratos distintos. Restam 880 compras elegíveis e uma exclusão por ano inválido.

## Consolidação dos lotes restantes

[contracts-resume-c1345679-59ea-49ad-af35-be2cc924ceab/coverage.json](contracts-resume-c1345679-59ea-49ad-af35-be2cc924ceab/coverage.json): 1.080 compras distintas confirmadas. 125 contratos distintos e 0 compras elegíveis pendentes. [Conferência no banco](contracts-resume-c1345679-59ea-49ad-af35-be2cc924ceab/database-verification.json). [Interpretação](../docs/contract-coverage.md).

## Perguntas de negócio

[queries-ee5ffc31-e565-4e75-8ce4-cfa6aac17046/verification.json](queries-ee5ffc31-e565-4e75-8ce4-cfa6aac17046/verification.json): consultas reais com login somente leitura, contagens conferidas e escrita negada. Exemplos em summary.json, municipalities.json e purchase.json; o texto livre do objeto foi omitido do exemplo de rastreio. [Método](../docs/business-queries.md).

## Avaliação de perguntas

[agent-eval-3ad8ae41-4327-4033-ae56-2c59a60e451d/evaluation.json](agent-eval-3ad8ae41-4327-4033-ae56-2c59a60e451d/evaluation.json): baseline final, 60/60 casos curados, zero LLM. As execuções anteriores `agent-eval-56477761-a3a6-41de-bfb1-49f5a8a9a6e6` e `agent-eval-eb123db5-c11b-4efa-8926-752a0e39af4f` foram preservadas. [Interpretação](../docs/agent-evaluation.md).

## Teste real Gemini

[agent-eval-e1b0aef5-858d-4a16-8f52-bb881fc16585/evaluation.json](agent-eval-e1b0aef5-858d-4a16-8f52-bb881fc16585/evaluation.json): três perguntas reais, três aprovadas,
zero erros; resumo, municípios e rastreio. [agent-eval-e1b0aef5-858d-4a16-8f52-bb881fc16585/verification.json](agent-eval-e1b0aef5-858d-4a16-8f52-bb881fc16585/verification.json)
confere hashes e metadados de uso (840 tokens totais). Custo monetário desconhecido. Não representa
a suíte completa de 60 casos com Gemini. [Interpretação](../docs/agent-evaluation.md).

## Avaliação Gemini interrompida

[agent-eval-6908e93c-b894-4638-8ddf-96d21200a3c8/evaluation.json](agent-eval-6908e93c-b894-4638-8ddf-96d21200a3c8/evaluation.json): 11 executados, nove aprovados, uma recusa indevida e uma falha técnica sem status preservado. [agent-eval-6de25618-3cbe-4252-95ab-4620422340e8/evaluation.json](agent-eval-6de25618-3cbe-4252-95ab-4620422340e8/evaluation.json): novo prompt, sete executados, seis aprovados e um HTTP 429; 53 não executados. Não somar resultados. [Conferência](agent-eval-6de25618-3cbe-4252-95ab-4620422340e8/verification.json) e [continuação](../docs/agent-evaluation.md).

## Continuação Gemini em 04/11/2026

[agent-consolidated-cbf07cd7-7961-4f6d-9b94-b0db226a64d1/verification.json](agent-consolidated-cbf07cd7-7961-4f6d-9b94-b0db226a64d1/verification.json): 29 casos distintos conferidos, 28 aprovados, 1 erros e 31 não executados. Segmentos com mesmo prompt/modelo/corpus/cobertura; versões de diagnóstico diferem. [Limites](../docs/agent-evaluation.md).

O lote `agent-eval-dfa0933d-2a2f-4bfd-9471-d82f540998f9` aprovou os casos 7–14 e parou em 429 no
15. O reteste `agent-eval-2c284880-8bde-4dd0-9892-0d52f5816f78` aprovou o caso 15.
`agent-eval-ba79adc6-6420-46c9-9e78-59b54f28a0c7` aprovou os casos 16–28 e parou no 29 com quota diária gratuita de 20 requisições.
[Diagnóstico seguro](agent-eval-ba79adc6-6420-46c9-9e78-59b54f28a0c7/quota-observation.json). Restam 32 casos contando o 29 interrompido.

## Contingência de provedores

[provider-verification-6f377e0f-a72c-4fc3-92ab-e225d79a95e1/verification.json](provider-verification-6f377e0f-a72c-4fc3-92ab-e225d79a95e1/verification.json) consolida o corpus principal e as perguntas adicionais, com seleção real de modelos. Há testes individuais, erros de configuração/serviço preservados, troca inicial simulada seguida de GPT-OSS real e catálogo minimizado. A nota principal não representa a qualidade de todas as reservas. [Índice e limites](../docs/provider-contingency.md). O código atual passou em 79 testes; o relatório da medição anterior registra os 75 daquela etapa.

[Proveniência dos bytes](evidence-byte-provenance-412a1cc6-2875-4a33-95d6-152a4ec7626d/manifest.json): os JSON antigos continuam idênticos aos publicados no Git; cópias exatas dos bytes usados nas execuções permitem conferir os hashes após conversão histórica de quebras de linha. Novas evidências têm conversão de texto desativada.

## Interface local

[web-verification-2179defe-b152-4eaa-b1f6-85f8b39ba5c5/verification.json](web-verification-2179defe-b152-4eaa-b1f6-85f8b39ba5c5/verification.json): seis fluxos HTTP reais, incluindo uma pergunta com contingência; hashes do servidor/assets preservados. Não houve inspeção visual: navegador local desativado no ambiente. [Método e limites](../docs/interface.md).

## Redesenho do assistente

[web-verification-ce1eb0aa-e3a5-4888-9af2-984c20385ec2/verification.json](web-verification-ce1eb0aa-e3a5-4888-9af2-984c20385ec2/verification.json): seis exemplos HTTP da versão atual, com hashes de assets. `web-verification-8029bb61-a6e2-4df6-9f9d-624c4795be14` registra uma etapa intermediária. Não houve inspeção visual por navegador; contrato DOM foi testado separadamente. [Método](../docs/interface.md).

## Ampliação de maio a outubro e histórico de sessão

`pncp-74d68096-1e27-451d-b423-f8cded554d54` contém a coleta de seis meses: 2.537 compras, 54 páginas, carga verificada. `contracts-resume-5237eeaa-49fb-45e8-9d29-407aa6ddb34f` registra 100 consultas de contrato, 21 contratos e 2.436 consultas pendentes. `expanded-interface-57f006b7-e36e-4035-8e8b-cf3988031ae7` verifica os dois recortes e IA ampliada. `expanded-interface-4693e944-1745-4b53-ac60-1c76e9d71b79` é uma tentativa sem relatório final, com dois exemplos baseline apenas. [Método](../docs/dataset-expansion.md).

## Recuperação sem API externa

[recovery-verification-da469824-8e8f-43dd-b8ec-f0f220c19af1/verification.json](recovery-verification-da469824-8e8f-43dd-b8ec-f0f220c19af1/verification.json): cooldown injetado antes da rede, nenhuma consulta ao banco nessa tentativa, seguido de baseline com PostgreSQL real. O cenário é simulado e explicitamente identificado; não é ocorrência real de falha do provedor. [Interface](../docs/interface.md).

## Diagnóstico de indisponibilidade

[availability-diagnosis-6d8f3e82-c79c-4319-9687-6a1b52674168/verification.json](availability-diagnosis-6d8f3e82-c79c-4319-9687-6a1b52674168/verification.json): esperas locais observadas, nenhuma chamada externa e consulta real por municípios com 2.537 compras no recorte. Registros antigos não permitem inferir o tipo de quota de Groq/OpenRouter. [Interface](../docs/interface.md).

[Revisão da aplicação](application-review-dbcf1edc-1550-4274-bfb9-fcc210fa104f/verification.json): 102 testes, verificações HTTP por regras locais nos dois recortes, permissões efetivas do banco e busca por credenciais configuradas. Zero chamadas externas de IA; sem inspeção visual.

[application-review-348a9663-dda0-42ca-bd0b-bf32bb2d84cb](application-review-348a9663-dda0-42ca-bd0b-bf32bb2d84cb/verification.json): validação de formatação PT/EN,
contratos em tabela, preservação do JSON, 102 testes Python e consultas locais nos dois
recortes. Inclui testes Node de valores grandes, centavos e datas; sem chamadas de IA.

[application-review-8ae90c1e-92fe-4782-855c-9c8d76817734](application-review-8ae90c1e-92fe-4782-855c-9c8d76817734/verification.json): validação da interface de
produto e separação entre compras pesquisadas, pendentes e excluídas; 102 testes Python,
contratos Node e consultas HTTP locais. Sem nova coleta ou chamadas externas de IA.

[Validação das análises](application-review-70417ac8-3c13-466e-a51f-ba200dbabc60/verification.json): 108 testes Python e consultas reais mensais/órgãos/qualidade. [Corpus local ampliado](agent-eval-cb312a08-6b4d-4353-ae57-274123b3de97/evaluation.json): 12/12. [Testes iniciais com IA](analytics-verification-79a6ac7f-7923-4e9c-8fc8-17ce9c8560e9/verification.json): três rotas novas, sem equivaler à avaliação ampla do modelo.

## Conclusão dos contratos da base ampliada

[Diário](contracts-completion-d5e1399d-480d-4b8e-b388-388fcdb67f9a/progress.json) · [Cobertura final](contracts-resume-9a175343-9dde-49dc-b1e5-dcf5e760d139/coverage.json) · [Publicação/idempotência](contracts-publication-10f50cf9-aedd-47ba-a17c-1e56f36391d4/verification.json) · [112 testes e HTTP](application-review-fbea3361-f186-4701-97a3-74c4a8af80c8/verification.json). São 2.536 compras aptas pesquisadas, 679 contratos, zero pendências aptas e uma exclusão. Todos os 26 snapshots foram verificados; não somar com o recorte original.
