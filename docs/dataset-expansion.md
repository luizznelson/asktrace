# Base de seis meses e orientação do assistente

## Para que serve

AskTrace ajuda a explorar registros publicados no PNCP: entender volumes de compras, comparar
grupos de municípios e conferir os contratos vinculados a uma compra. O visitante começa por uma
pergunta concreta e acompanha resposta, recorte, fontes e rastro. Os dados permitem investigar
publicações; não comprovam pagamentos ou irregularidades.

A introdução agora explica o que é PNCP e apresenta três passos: escolher a base, perguntar e
conferir. Isso evita depender de conhecimento técnico ou da conversa de desenvolvimento para usar
o projeto. As instruções e estados da interface continuam em PT-BR e inglês; as perguntas de negócio
continuam suportadas em português. Cada pergunta é independente no modelo.

## Ampliação real da base

| Medida | Recorte original | Recorte ampliado |
| --- | ---: | ---: |
| Publicação das compras | Ago–out/2026 | Mai–out/2026 |
| Compras normalizadas e carregadas | 1.081 | 2.537 |
| Páginas originais | 23 | 54 |
| Consultas de contratos confirmadas | 1.080 | 100 |
| Contratos no snapshot selecionado | 125 | 21 |
| Compras com contratos retornados | 85 | 17 |
| Compras com resposta sem publicação | 995 | 83 |
| Compras elegíveis ainda não consultadas para contratos | 0 | 2.436 |
| Localizador excluído por ano inválido | 1 | 1 |
| Compras sem valor homologado informado | 749 | 1.354 |

O novo snapshot inclui maio (505 compras), junho (527), julho (424), agosto (412), setembro (373)
e outubro (296). A ampliação acrescenta **1.456 compras** no período e mantém modalidade 6 e UF
da unidade igual a PI. Paginação e contagens foram verificadas; os registros foram carregados em
transação e a repetição da carga retornou `already_loaded`.

O novo recorte contém os três meses anteriores. **Não somar snapshots.** Contratos são observados
em momentos diferentes e ligados explicitamente ao snapshot de compras consultado. Os 125 contratos
do recorte anterior não foram copiados silenciosamente para a base nova, que tem cobertura parcial.
Os 21 contratos do primeiro lote não representam uma redução do total real de contratos.

Há 2.437 compras fora da cobertura de contratos do recorte ampliado: 2.436 ainda não consultadas
e uma excluída por ano inválido na fonte. Não classificar nenhuma delas como “sem contrato”.
O seletor da interface mostra os dois períodos; o novo recorte é o padrão. Estatísticas, período,
manifesto, pergunta e resposta são vinculados à escolha, sem alterar o corpus histórico de avaliação.

## Evidências e reprodução

- [Manifesto de seis meses](../runs/pncp-74d68096-1e27-451d-b423-f8cded554d54/manifest.json).
- [Contagens e carga no PostgreSQL](../runs/pncp-74d68096-1e27-451d-b423-f8cded554d54/database-load.json).
- [Resumo consultado com usuário de leitura](../runs/pncp-74d68096-1e27-451d-b423-f8cded554d54/summary.json).
- [Cobertura de contratos ampliada](../runs/contracts-resume-5237eeaa-49fb-45e8-9d29-407aa6ddb34f/coverage.json).
- [Novo lote de contratos](../runs/contracts-2a0d1e37-dc0e-4006-85bd-f4596efe74dc/manifest.json).
- [Troca de recorte e resposta IA pela API da aplicação](../runs/expanded-interface-57f006b7-e36e-4035-8e8b-cf3988031ae7/verification.json).
- [Configuração explícita dos recortes](../config/datasets.json).

```powershell
.venv/Scripts/python.exe -m asktrace.ingest --start 2026-05-01 --end 2026-10-31
.venv/Scripts/python.exe -m asktrace.contracts resume runs/pncp-74d68096-1e27-451d-b423-f8cded554d54/manifest.json --max-batches 1
```

A primeira linha cria outro snapshot, não sobrescreve a evidência desta entrega. A segunda continua
a cobertura de contratos do snapshot desta entrega. Novos relatórios precisam ser selecionados em
`config/datasets.json` após revisão. Raw e normalizados completos ficam locais e ignorados; manifestos
e relatórios minimizados ficam no Git, conforme a política do projeto.

## Histórico de perguntas da sessão

O histórico guarda pergunta e resposta completa (incluindo evidências e rastro) no `sessionStorage`
da aba, até 20 resultados. Recarregar a página restaura os dados e o idioma sem fazer novas chamadas
ao modelo ou ao banco. O filtro de histórico respeita a base; escolher outro recorte não mistura respostas.
Nova exploração limpa os registros. O JSON não inclui tokens de sessão nem chaves API.

Não é histórico compartilhado entre pessoas, conta autenticada, banco de conversas ou memória do
modelo. O navegador controla a duração da sessão da aba, inclusive restauração de sessão. Dados
ficam acessíveis a quem usa a mesma aba; a interface orienta a evitar dados pessoais e permite limpar.
Se o navegador bloquear armazenamento ou atingir o limite, o histórico fica em memória e um aviso
informa que ele não será restaurado. Registro inválido ou versão desconhecida é ignorado.

## Isolamento de recortes e validação

A API aceita somente IDs configurados, nunca um caminho de manifesto fornecido pelo cliente.
`/api/session` informa o catálogo e as contagens verificadas; `/api/evidence?dataset=ID` serve o
manifesto daquela base. Pedidos antigos sem dataset continuam usando o original para compatibilidade.
O planejador recebe o período do snapshot selecionado com contexto por requisição; o contexto é
restaurado ao encerrar a chamada e não se mistura com outra pergunta. O SQL continua fixo e somente leitura.

Passaram **89 testes Python locais**, incluindo PostgreSQL. Os três testes novos cobrem ID de recorte
inválido, manifesto correspondente ao ID e isolamento do período no planejador. O contrato DOM também
passou, incluindo restauração do histórico sem nova API, limpeza e armazenamento inválido.

Os testes HTTP confirmaram resumo original, resumo ampliado e resumo ampliado com Qwen real via
contingência, com o período correto no prompt e 2.537 compras na resposta. A primeira execução de
verificação terminou antes de gerar relatório final: ficaram dois exemplos baseline em
`expanded-interface-4693e944-1745-4b53-ac60-1c76e9d71b79`, sem comprovação do terceiro resultado.
A execução final acima preserva os três resultados e seus rastros, incluindo possíveis falhas.

Uma instância antiga estava ativa na porta 8010 durante a conferência; a versão atual foi testada na
8011. Reiniciar o servidor após atualizar o código é necessário. Sem inspeção visual por navegador:
a prévia continua desativada no Work. Os testes de elementos simulados não comprovam layout ou
acessibilidade. CI remoto não verificado. A pontuação anterior de 60 casos não é transferida para a
base ampliada sem nova avaliação; nesta entrega foram testados os caminhos e o resumo especificados.

## Uso local

```powershell
docker compose up -d --wait
.venv/Scripts/python.exe -m asktrace.web --port 8011
```

Abra http://127.0.0.1:8011, escolha a base e use uma sugestão. Se quiser comparar, envie a mesma
pergunta em cada recorte e confira as datas. Perguntas como “e essa?” não usam contexto anterior:
inclua o assunto ou o identificador PNCP. Registros originais podem conter erros; a ampliação não
é validação jurídica ou financeira das publicações.

Próximo passo: avançar pelos contratos ainda não consultados do novo snapshot e avaliar novas
perguntas específicas dele, mantendo sempre a cobertura parcial explícita até a conclusão.
