# Retomada da coleta de contratos

## Problema resolvido

Executar novamente o coletor inicial selecionava as mesmas compras. Agora a retomada encontra o
primeiro intervalo ainda não coberto por lotes completos, verificados e carregados no PostgreSQL.
Lotes sobrepostos não são somados: cada compra conta uma vez, usando o snapshot mais recente.
Respostas de momentos diferentes não representam um retrato simultâneo do portal.

## Como executar

Com PostgreSQL ativo e downloads anteriores disponíveis localmente:

```powershell
docker compose up -d --wait
.venv/Scripts/python.exe -m asktrace.contracts resume runs/pncp-3020d59b-d274-4f4c-be4f-d59e8be30101/manifest.json --max-batches 1
```

O padrão é um lote de até 100 compras. `--max-batches` aceita de 1 a 20 e limita o trabalho autorizado
na execução. Cada nova execução verifica novamente os arquivos, hashes, seleção e carga anterior.
O comando retorna código 1 se encontrar um lote que precise de revisão e interrompe a sequência.
Não usar `collect --limit 100` para avançar: esse comando continua servindo para reconsultar o início.

## Semântica de retomada

- Compras em lotes completos e carregados são puladas.
- O intervalo para antes de outra compra já coberta, evitando repetir trabalho consolidado.
- Um lote com falhas não é carregado nem contado como cobertura confirmada.
- A tentativa seguinte repete o lote incompleto inteiro, incluindo suas respostas válidas: a carga é
  atômica por lote. Ainda não há retomada individual de respostas de lotes incompletos.
- Fonte, offset, páginas, hashes e resultados permanecem no manifesto. Alterar offset ou seleção
  impede a carga. Evidência faltante ou alterada bloqueia a retomada, sem pular silenciosamente.
- É uma ferramenta de execução local única. Não executar dois comandos de retomada em paralelo:
  ainda não há bloqueio de aquisição concorrente, embora a carga no banco seja transacional.

`runs/contracts-resume-*/plan.json` registra o início. Cada lote gera `batch-NNN.json`; ao terminar,
`coverage.json` registra a cobertura consolidada por compra e os manifestos usados com seus hashes.
Um plano sem relatório final representa uma execução que não terminou; não comprova cobertura.
São necessárias as respostas locais ignoradas em `data/raw/` para verificar os snapshots históricos.

## Execução real em 03/11/2026

Uma primeira execução não passou da preparação porque PostgreSQL estava indisponível;
[o plano foi preservado](../runs/contracts-resume-88d30f38-2d39-4a7c-a0e5-782f10ca128e/plan.json).
Depois de reiniciar o banco, a retomada selecionou as posições 100 a 199 da ordenação elegível,
sem sobreposição com as 100 compras já consolidadas.

O [novo lote](../runs/contracts-3eec93d4-abbc-4072-8f7b-66194aa4d685/manifest.json)
teve 59 respostas de nenhum contrato publicado, uma compra com dois contratos e 40 falhas de conexão
(status local 0, sem resposta HTTP). Sua classificação é `needs_review`: não foi carregado.
Não atribuímos a falha a uma causa específica nem interpretamos isso como ausência de contrato.

A [cobertura consolidada](../runs/contracts-resume-f93f55c8-753a-4d8d-a505-843bc7deb32e/coverage.json)
continua em **100 compras confirmadas**, seis com contratos e 94 sem publicação retornada.
São seis contratos distintos consolidados. As 60 respostas válidas do novo lote são evidência parcial,
não cobertura carregada. Restam 980 compras elegíveis e uma exclusão por ano inválido na fonte.
Não somar os dois contratos parciais aos seis consolidados para apresentar um resultado do banco.

## Validação

Os 46 testes locais passaram com PostgreSQL ativo. Os cinco testes novos verificam intervalos,
limite de lote, snapshots sobrepostos contados uma vez, compras concluídas não consultadas novamente,
parada por falha e rejeição de evidências alteradas. A primeira tentativa da suíte encontrou o banco
desligado; a suíte completa foi repetida com sucesso após a reinicialização. CI remoto não verificado.

## Próximo passo

Repetir o comando de retomada quando a conexão com PNCP estiver disponível. Ele selecionará o lote
pendente; depois de uma carga bem-sucedida, avançará automaticamente para o próximo intervalo.
O agente e a interface ainda não estão implementados. Este resultado não mede pagamentos ou economia.
