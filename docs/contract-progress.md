# Nova tentativa do lote pendente

O lote terminou completo, foi carregado e a carga repetida não duplicou registros.

A cobertura confirmada passou a 200 compras distintas e 12 contratos distintos. Restam 880 compras elegíveis e uma exclusão por ano inválido.

[Cobertura consolidada](../runs/contracts-resume-d88d70d6-06d1-44ee-8923-5d9b17eb364a/coverage.json) e [verificação no banco](../runs/contracts-resume-d88d70d6-06d1-44ee-8923-5d9b17eb364a/database-verification.json).

Os snapshots anteriores e as tentativas com falhas foram preservados. As contagens são por compra
distinta; lotes sobrepostos não são somados. Contrato publicado não comprova pagamento, economia
ou execução financeira. As respostas são observações do portal em momentos diferentes.

## Continuação

```powershell
.venv/Scripts/python.exe -m asktrace.contracts resume runs/pncp-3020d59b-d274-4f4c-be4f-d59e8be30101/manifest.json --max-batches 1
```

O comando avança somente após verificar e carregar o lote completo. Caso encontre falhas, para e
deixa o intervalo pendente. Consulte [limites da retomada](contract-resumption.md). Nenhum código
do coletor foi alterado nesta execução; a suíte de 46 testes da entrega anterior não foi repetida.

## Consolidação posterior

A execução acima é histórica. Consulte a [cobertura consolidada mais recente](contract-coverage.md).
