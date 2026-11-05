# Qualidade: o que foi verificado e o que permanece pendente

## Estado atual

| Camada | Verificação | Limite |
| --- | --- | --- |
| Software | 112 testes Python com PostgreSQL isolado; Ruff e formatação | Não prova ausência de falhas ou implantação em produção |
| Apresentação | Contratos Node de gráficos, empates, moeda, histórico, CSV e PT/EN | Não é inspeção visual em navegador |
| Dados reais | Consultas HTTP, contagens de seis meses, permissões e integridade dos snapshots | O PNCP não fornece uma transação única para toda a coleta |
| Cobertura | 2.536 compras aptas pesquisadas; 679 contratos; 26 cargas repetidas sem duplicação | Uma exclusão por ano inválido; ausência de publicação não prova ausência de contrato |
| Regras locais v3 | 12/12 casos curados do catálogo ampliado | Casos do autor, não benchmark cego |
| Planejador IA v3 | Três testes iniciais reais das rotas novas | Avaliação ampla v3 pendente; não herda notas de prompts anteriores |

[Verificação da apresentação atual](../runs/application-review-7aa7ebba-442d-466f-9642-5b62647dd32e/verification.json) ·
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

## Revisão móvel e prontidão de hospedagem

112 testes Python e os contratos Node passaram. O histórico móvel foi conferido sem nova consulta, junto da marcação de resultados antigos e limpeza da sessão. A revisão por código ampliou controles e rótulos; inspeção visual real continua pendente de habilitar o navegador. [Verificação](../runs/application-review-7c025c56-38fc-495c-80b3-be4ae22717d0/verification.json) · [Hospedagem gratuita e adaptações necessárias](hosting-options.md).
