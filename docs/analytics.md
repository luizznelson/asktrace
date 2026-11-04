# Análises de compras, publicação e preenchimento

## Perguntas que agora podem ser exploradas

| Pergunta de negócio | Consulta | O que o resultado representa |
| --- | --- | --- |
| Quantas compras e contratos há na base? | `summary` | Contagens do recorte e da cobertura de contratos |
| Quais municípios têm mais compras? | `municipalities` | Até 20 grupos, por quantidade de compras |
| Como o volume mudou ao longo dos meses? | `monthly` | Quantidade por mês de **publicação**, estimativas informadas e lacunas |
| Quais órgãos têm mais compras? | `organizations` | Até 20 CNPJs de órgãos, quantidade e estimativas informadas |
| Quais campos estão incompletos? | `quality` | Contagens de ausências, zeros explícitos e identificação incompleta |
| Quais contratos estão ligados a uma compra? | `purchase` | Registro com ID explícito, contratos, valores e origem |

Os seis caminhos aparecem na interface PT-BR/EN. As perguntas continuam suportadas em
português. As três novas análises funcionam tanto com regras locais quanto com o roteador
de IA; nenhuma delas depende de gerar SQL livre ou de enviar os resultados ao modelo.

## Regras de interpretação

- O mês é o da publicação no PNCP, não o de pagamento, execução ou assinatura.
- Os órgãos são agrupados pelo **CNPJ do órgão comprador**, sem análise de fornecedores.
  Se houver variação de nome para o mesmo CNPJ, usa-se o menor nome não vazio em ordem
  textual como rótulo determinístico; não é uma validação do nome oficial atual.
- A classificação de municípios e órgãos é limitada a 20 resultados. Não se somam esses
  rankings para obter o total da base. A evolução mensal abrange os meses com publicações.
- Somas estimadas usam uma linha por compra; contratos não multiplicam esses valores.
  Valores não informados são contados separadamente. Estimativas não são pagamentos.
- O diagnóstico mede preenchimento: um município é incompleto quando falta nome ou código;
  nome de órgão vazio também é contado. Campos monetários explicitamente zero não são nulos.
  As contagens podem se sobrepor, porque uma compra pode ter várias lacunas.
- Combinações como “por mês e município” e filtros livres por nome não foram adicionados.
  O prompt v3 delimita esse catálogo; o roteador local recusa combinações de dimensões.
  A validação do plano garante a estrutura e as ações permitidas, sem ser uma prova de
  interpretação correta para toda pergunta em linguagem natural.
- A cobertura de contratos foi concluída posteriormente: 2.536 compras aptas pesquisadas,
  679 contratos e zero pendências aptas; uma exclusão por ano inválido permanece.
  [Cobertura e interpretação](contracts-expanded-coverage.md).

## Exportação sem perder o contexto

A resposta pode ser baixada como JSON completo ou como CSV da tabela retornada. O CSV
leva o tipo da consulta, UF, início/fim do período e hash do relatório, além dos valores
originais, sem arredondamento monetário de apresentação. Contratos dentro de uma compra
ficam em uma célula JSON no CSV; não são expandidos multiplicando a compra.

O arquivo tem BOM UTF-8, separador vírgula, aspas escapadas e linhas CRLF. Textos que
poderiam virar fórmulas em uma planilha recebem apóstrofo inicial. O CSV é uma exportação
tabular; o JSON é a referência completa para auditoria. Aplicativos de planilha podem
converter identificadores e números ao abrir CSV: importe códigos como texto quando
precisar preservar seu tipo. Exportar não faz outra consulta nem chama um provedor.

## Implementação e verificação

O catálogo de ações é compartilhado pelos adaptadores Gemini/OpenAI-compatible e pelo
validador do agente. Cada pergunta usa no máximo uma consulta de negócio validada, com
credencial de leitura e conferência da cobertura do snapshot. Os campos novos preservam
Decimal no backend e a formatação exata da apresentação.

Passaram **108 testes Python**, os contratos Node de interface/formatação/CSV, Ruff e
verificações HTTP com PostgreSQL real. A consulta mensal confirmou maio a outubro com
505, 527, 424, 412, 373 e 296 compras, somando 2.537. Órgãos respeitam limite/ordem e
identificador único; o diagnóstico confirmou 1.354 homologados não informados.
[Registro completo](../runs/application-review-70417ac8-3c13-466e-a51f-ba200dbabc60/verification.json). Não houve inspeção visual em navegador nesta etapa.

O [corpus novo](../evals/routing-expanded-v3.json) contém 12 casos curados pelo autor.
O [roteador local passou 12/12](../runs/agent-eval-cb312a08-6b4d-4353-ae57-274123b3de97/evaluation.json), incluindo recusas de combinações e
pagamentos. Isso não é benchmark cego nem mede acurácia geral da IA.

Os [três testes reais com IA](../runs/analytics-verification-79a6ac7f-7923-4e9c-8fc8-17ce9c8560e9/verification.json) encaminharam corretamente uma pergunta de cada
nova análise. São testes iniciais do planejador v3, anteriores ao refinamento do
agrupamento de nomes de órgãos; o SQL final foi validado separadamente no registro HTTP.
Os resultados históricos 60/60 do prompt anterior continuam históricos; não são
transferidos ao novo prompt. A avaliação ampla da IA v3 permanece pendente.

```powershell
# Testes, HTTP real, permissões e busca por credenciais configuradas
.venv/Scripts/python.exe -m scripts.verify_application_review

# Corpus curado novo com regras locais; sem chamadas externas
.venv/Scripts/python.exe -m scripts.verify_analytics

# Opcional: até três perguntas reais de IA, respeitando as esperas configuradas
.venv/Scripts/python.exe -m scripts.verify_analytics --live
```

Os testes HTTP de fronteira usam metadados controlados, para não depender de downloads
locais ignorados no Git. Testes de integração e o verificador acima exercitam o banco e
as evidências reais separadamente. A CI passou a executar também os testes de formatação
e CSV; a execução remota da CI ainda depende do push do usuário.
