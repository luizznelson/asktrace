# Contratos vinculados: cobertura antes de análise

## Pergunta de negócio

Quais contratos ou empenhos com força de contrato o PNCP retorna para cada compra consultada?
Uma compra pode gerar vários contratos. Resultado vazio não comprova ausência de contrato;
indisponibilidade não pode ser convertida em resultado vazio.

## O que foi implementado

- Seleção determinística de até 100 compras de uma coleta real íntegra: alternar meses de publicação,
  ordenando pelo identificador dentro de cada mês. O padrão é um piloto de 12 compras.
- Localizadores do órgão, ano e sequencial recuperados das páginas originais, verificadas por hash.
- Consulta oficial por compra, com limite de tamanho, timeout e até três tentativas para falhas transitórias.
- Respostas locais preservadas e relatório público sem nomes ou identificadores de fornecedores.
- Validação do vínculo explícito, valores decimais, duplicações e origem de cada contrato.
- Carga atômica e idempotente em PostgreSQL, com cobertura separada dos contratos.

Este piloto não é amostra estatisticamente representativa. Seu objetivo é validar o caminho de integração.
Nenhum total do piloto deve ser extrapolado às 1.081 compras ou a todos os contratos do Piauí.

## Resultado real em 02/11/2026

[Manifesto do piloto](../runs/contracts-a6fa16c6-13c4-4205-94e9-cd01e9322636/manifest.json): 12 compras selecionadas e tentadas;
11 respostas HTTP 503 e uma falha sem status HTTP capturado. O último caso ficou classificado
genericamente como `invalid_response`; o relatório não permite diagnosticar sua causa.
Nenhum contrato foi validado. Estado `needs_review`; **não houve carga real de contratos**.

Os corpos dos erros HTTP não foram capturados na primeira versão executada deste piloto: seus arquivos
vazios registram apenas os bytes preservados localmente, não o conteúdo enviado pelo servidor.
A versão atual preserva também o corpo do erro HTTP, com limite de tamanho.
Não atribuímos a indisponibilidade a uma causa específica nem afirmamos que as compras não têm contratos.
As respostas 503 foram observadas mesmo após retentativas. Uma nova execução terá outro identificador;
esta evidência não será sobrescrita.

## Como reproduzir

Com as dependências instaladas e a coleta original disponível localmente:

```powershell
.venv/Scripts/python.exe -m asktrace.contracts collect runs/pncp-3020d59b-d274-4f4c-be4f-d59e8be30101/manifest.json --limit 12
```

O comando imprime o caminho do novo manifesto. Somente um piloto `pilot_complete` pode ser carregado:

```powershell
.venv/Scripts/python.exe -m asktrace.contracts load runs/contracts-ID-DA-NOVA-EXECUCAO/manifest.json
```

`pilot_complete` significa que todas as compras selecionadas receberam respostas válidas. Não significa
cobertura de toda a população. HTTP 200 com lista vazia ou 204 vazio gera `none_returned`;
404, 503 e falhas de conexão não são interpretados como ausência de contratos.

O carregador verifica novamente as páginas, o manifesto da compra, os localizadores e a normalização.
A compra original precisa estar carregada e ter o mesmo hash. A migração `sql/003_contracts.sql`
é aplicada na transação; não é necessário apagar o volume. O banco recebe apenas pilotos completos.
Falhas permanecem documentadas em `runs/`, disponíveis para auditoria.

## O que fica no banco e no Git

`contract_runs` identifica o piloto e sua coleta de compras. `contract_coverage` registra cada compra
consultada com sucesso, seu resultado e hash. `contracts` permite vários contratos por compra,
com valores inicial/global e índice na resposta original. As consultas devem filtrar o piloto e a coleta
para não somar snapshots repetidos. A tabela não representa pagamentos nem execução financeira.

`runs/contracts-*/manifest.json` fica no Git: seleção, URLs públicas, datas, estados, hashes e valores
normalizados. Respostas completas ficam em `data/raw/`, ignoradas, pois podem conter dados pessoais.
Um hash publicado não torna o download original disponível no repositório. Nomes, CPF e textos livres
de fornecedores não são incluídos nos registros normalizados publicados.

## Validação e próximos passos

A suíte local tem 36 testes, incluindo testes de contrato e integração em `asktrace_test`:
relações de um para muitos, respostas vazias versus falhas, valores inválidos, alteração de evidências,
retentativas, carga repetida e rollback. Dados sintéticos de teste não comprovam cobertura da API real.

Próximo passo: repetir um piloto pequeno quando a consulta responder, conferir seus vínculos reais e
só então ampliar a coleta. Atas, ferramentas do agente, avaliação de perguntas e interface continuam
pendentes. Não calcular economia ou sobrepreço subtraindo um contrato do orçamento inteiro da compra.

Fontes oficiais consultadas:
- [Consulta de contratos de uma contratação](https://pncp.gov.br/manual/pt-br/latest/contrato_empenho/consultar_contratos_ou_empenhos_de_uma_contratacao.html).
- [Endereços e acesso ao PNCP](https://pncp.gov.br/manual/pt-br/latest/acesso_ao_pncp/index.html).
