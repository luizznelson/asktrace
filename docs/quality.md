# Qualidade: o que foi verificado e o que permanece pendente

## Estado atual

| Camada | Verificação | Limite |
| --- | --- | --- |
| Software | 131 testes Python com PostgreSQL isolado; Ruff e formatação | Não prova ausência de falhas ou implantação em produção |
| Apresentação | Contratos Node de gráficos, empates, moeda, histórico, CSV e PT/EN | Não é inspeção visual em navegador |
| Dados reais | Consultas HTTP, contagens de seis meses, permissões e integridade dos snapshots | O PNCP não fornece uma transação única para toda a coleta |
| Cobertura | 2.536 compras aptas pesquisadas; 679 contratos; 26 cargas repetidas sem duplicação | Uma exclusão por ano inválido; ausência de publicação não prova ausência de contrato |
| Regras locais v3 | 60/60 casos do corpus final | Casos do autor, não benchmark cego |
| Contingência IA v3 | 60 aprovações em 61 execuções; uma falha preservada e retomada | Pool de provedores, corpus de desenvolvimento e um ID de compra repetido; não é acurácia geral |

[Verificação da apresentação atual](../runs/application-review-da5c0e4f-e3c9-435a-9342-f10b5163e0b1/verification.json) ·
[Cobertura e idempotência](contracts-expanded-coverage.md) · [Avaliação do roteador](agent-evaluation.md).

## Como conferir

Com o ambiente instalado, os testes com fixtures não exigem baixar o PNCP novamente:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -q
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check .
node tests/test_display_formatters.cjs
node tests/test_result_presentation.cjs
node tests/test_assistant_ui.cjs
```

Para incluir integração, prepare `asktrace_test` e defina `ASKTRACE_TEST_DATABASE=1`.
Sem opt-in, os testes de banco são explicitamente ignorados; esse resultado não equivale
à execução completa registrada. [Ambiente e segredos](development.md).

O verificador completo também exige a base real preparada:

```powershell
.venv/Scripts/python.exe -m scripts.verify_application_review
```

Ele executa a suíte, os contratos Node, consultas HTTP e verificações de permissões e
credenciais conhecidas nos arquivos atuais. Não faz chamadas de IA, não escaneia todo
o histórico Git e não substitui auditoria independente. Seu relatório registra hashes
dos arquivos de aplicação e teste verificados.

## O que os testes de apresentação exercitam

- O gráfico mensal usa as mesmas linhas da tabela e conserva a ordem de publicação.
- O destaque de maior volume calcula a contagem e identifica empates sem inventar um líder.
- Rankings mostram até cinco grupos no gráfico e deixam explícito o limite de 20 na tabela.
  Não somam rankings truncados como se fossem o total da base.
- Zero, campo ausente, nome não informado, resultado vazio e erro têm caminhos próprios.
- A formatação monetária preserva o decimal original e separa o arredondamento da tela.
- A troca de idioma atualiza títulos, meses, rótulos, valores e data da consolidação.
- O exemplo de rastreio vem de uma compra com contratos no recorte selecionado.
- Resultados anteriores mantêm os valores originais e recebem aviso de versão antiga.
- O CSV trata textos que poderiam virar fórmulas de planilha e inclui período/hash.

## Verificações que ainda faltam

Não houve acesso ao navegador nesta etapa, portanto não se afirma que layout, contraste,
leitores de tela ou dispositivos reais foram visualmente validados. O vídeo de demonstração ainda não foi publicado. A CI inclui os novos testes;
o resultado remoto precisa ser observado após o push.

A busca de contratos foi concluída para o snapshot apto, não para todas as contratações
existentes no estado. Os limites do servidor local e do planejador permanecem documentados
em [revisão da aplicação](application-review.md) e [análises](analytics.md).

[Histórico das verificações](history/quality-log.md): resultados de etapas e versões
anteriores foram preservados; suas contagens não são somadas à suíte atual.

## Histórico: revisão móvel inicial e pesquisa de hospedagem

112 testes Python e os contratos Node passaram. O histórico móvel foi conferido sem nova consulta, junto da marcação de resultados antigos e limpeza da sessão. A revisão por código ampliou controles e rótulos; inspeção visual real continua pendente de habilitar o navegador. [Verificação](../runs/application-review-7c025c56-38fc-495c-80b3-be4ae22717d0/verification.json) · [Hospedagem gratuita e adaptações necessárias](hosting-options.md).

## Fechamento local da primeira versão

[Síntese verificável](../runs/release-readiness-411e550a-cfc1-4cd5-bac5-a73e3ba2cf33/verification.json): 130 testes Python, contratos Node,
permissões no banco de testes, restauração de dados e os 12 caminhos reais pelas rotas ASGI.
O pacote de dados privados não está no Git. [Publicação](deployment.md).

Uma rodada intermediária falhou em uma asserção HTTP, sem diagnóstico de causa estabelecido.
As cinco consultas isoladas e a repetição completa passaram; o evento permanece registrado
na síntese. Isso não equivale a uma garantia de ausência de falhas.

O banco remoto foi verificado no Neon; URL pública, inspeção visual e vídeo continuam pendentes.

## Banco remoto e isolamento dos testes

[Neon verificado](../runs/neon-verification-187bed11-8da5-4be2-8712-d694a4ea11a0/verification.json): doze consultas, conexão TLS no cliente,
logins restritos, restauração e limites após reinicialização da aplicação de teste.
A regressão com uma URL de produção configurada comprova que testes opt-in usam somente
`asktrace_test` local. Após a correção, 131 testes Python passaram. O incidente e a limpeza
dos cinco registros sintéticos estão documentados no [guia de publicação](deployment.md).
