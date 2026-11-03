# Perguntas de negócio com acesso somente leitura

## O que já pode ser respondido

| Pergunta | Comando | Resultado e limite |
| --- | --- | --- |
| Qual a cobertura do recorte e onde faltam valores? | `summary` | 1.081 compras; 1.080 consultas confirmadas, 125 contratos, 749 valores homologados desconhecidos |
| Como as compras se distribuem por município? | `municipalities` | Até 20 grupos, ordenados por quantidade; estimativas somadas uma vez por compra, com quantidade de valores desconhecidos |
| Quais dados e contratos sustentam uma compra? | `purchase --purchase-id ID` | Compra, valores, cobertura, identificadores de contratos, hashes e posições na fonte |

Essas são consultas fixas, não um agente de linguagem natural. Não recebem SQL do usuário ou de LLM.
Nenhum deploy, interface ou credencial de serviço externo é necessário nesta etapa.

## Executar

Com PostgreSQL e dependências instalados, configure o acesso uma vez:

```powershell
.venv/Scripts/python.exe -m asktrace.query setup-reader
```

O comando aplica `sql/004_reporting.sql` usando a credencial de manutenção já configurada e gera
uma senha local para `asktrace_reader`, salva apenas no `.env` ignorado. Não imprime a senha.
Não editar o `.env.example` com a senha real. Em outra máquina, executar esse comando localmente.

```powershell
.venv/Scripts/python.exe -m asktrace.query summary --coverage runs/contracts-resume-c1345679-59ea-49ad-af35-be2cc924ceab/coverage.json
.venv/Scripts/python.exe -m asktrace.query municipalities --coverage runs/contracts-resume-c1345679-59ea-49ad-af35-be2cc924ceab/coverage.json
.venv/Scripts/python.exe -m asktrace.query purchase --purchase-id "01612601000118-1-000044/2026" --coverage runs/contracts-resume-c1345679-59ea-49ad-af35-be2cc924ceab/coverage.json
```

As respostas JSON contêm recorte, contagens de cobertura, hash e caminhos dos manifestos, resultado
e limites de interpretação. Um ID fora da base retorna `not_found_in_scope`, sem afirmar que a compra
não existe no PNCP. Falhas de integridade ou divergências de contagens no banco impedem a resposta.

## Como a resposta é construída

O relatório de cobertura é explícito: não existe seleção implícita de “última coleta” global.
Antes da consulta, o código verifica os manifestos, páginas preservadas, hashes, vínculos e a cobertura
por compra. Os snapshots são ordenados como na retomada para reconstituir a observação mais recente
incluída naquele relatório. A consulta seleciona o run de contratos correspondente a cada compra.
Isso evita somar as mesmas compras ou contratos em snapshots sobrepostos.

As agregações por município partem das compras, sem multiplicar estimativas por quantidade de
contratos. Valores monetários usam decimais e são serializados como texto; ausências continuam nulas.
`sum` retorna nulo quando todos os valores do grupo são desconhecidos. Não é arredondamento em float.
O resultado municipal é limitado a 20 grupos: não é a lista completa do estado nem cobertura por domicílio
do fornecedor. O agrupamento usa código e nome informados pela fonte, sem corrigir grafias.

O rastreio liga a compra à página original por hash e índice; os contratos apontam ao snapshot,
à sequência de páginas e ao índice lógico. As páginas e URLs estão nos manifestos referenciados.
A coluna `contract_pages_sha256` é o hash da concatenação dos hashes das páginas, não o hash de um PDF.

## Permissões e segurança

As consultas conectam como `asktrace_reader`, uma credencial distinta da manutenção. O login não é
superusuário e não pode criar bancos ou papéis. Recebe apenas SELECT nas três visões de relatório,
com filtro para coletas reais completas; não recebe acesso direto às tabelas. O recorte específico
é aplicado por parâmetros nas consultas fixas. As visões não são isolamento por usuário ou cliente.

O PostgreSQL impõe timeout de dez segundos e leitura por padrão para esse login. As respostas usam
transação somente leitura e valores parametrizados. Os testes tentam escrita mesmo desativando o
padrão somente leitura: privilégios e definição das visões continuam bloqueando a alteração.
O usuário de manutenção permanece administrativo e não deve ser usado futuramente pelo agente.
Não há endpoint HTTP ou autenticação web nesta entrega. As verificações de arquivos ocorrem antes
do timeout SQL e precisam dos downloads locais, não publicados no Git.

## Evidências e validação

- [Resumo real](../runs/queries-ee5ffc31-e565-4e75-8ce4-cfa6aac17046/summary.json).
- [Municípios: até 20 grupos](../runs/queries-ee5ffc31-e565-4e75-8ce4-cfa6aac17046/municipalities.json).
- [Exemplo de uma compra com múltiplos contratos](../runs/queries-ee5ffc31-e565-4e75-8ce4-cfa6aac17046/purchase.json).
- [Verificação real e testes](../runs/queries-ee5ffc31-e565-4e75-8ce4-cfa6aac17046/verification.json).

O exemplo publicado de rastreio omite o texto livre do objeto, com indicação no arquivo; os demais
campos são resultados reais. Nomes ou CPF de fornecedores não são consultados. O relatório de
verificação comprova que a credencial de leitura teve escrita negada também no banco do projeto.

Passaram 51 testes locais com PostgreSQL. Os cinco novos testes cobrem catálogo de perguntas,
totais sem multiplicação, nulos, origem, identificador com tentativa de injeção, permissões e cobertura
alterada. Ruff e formatação também foram verificados. CI remoto ainda não foi verificado.

## Limites e próxima etapa

As 995 respostas sem publicação não comprovam ausência de contrato fora do portal. Os 125 contratos
não são pagamentos ou execução financeira. Não calcular economia entre um contrato e o orçamento
inteiro da compra. A exclusão por ano inválido permanece fora da cobertura de contratos.

A verificação de fontes não prova que os dados informados no PNCP estejam corretos nem impede
alterações feitas por um administrador no banco. Não há classificação automática de irregularidades.
Próximo passo: avaliar um conjunto de perguntas e ligar estas funções a um agente limitado, com
rastro de chamadas e recusas para perguntas que o recorte não permite responder. Interface continua pendente.
