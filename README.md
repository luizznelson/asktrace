# AskTrace

Projeto de portfólio em preparação: responder perguntas sobre compras públicas do Piauí e mostrar os dados, consultas e ferramentas usados para chegar a cada resposta.

## O problema proposto

Registros de contratações e contratos estão distribuídos em páginas e contêm descrições em texto livre. O objetivo é facilitar a investigação sem esconder os filtros, o período, a cobertura dos dados ou as contas executadas.

Perguntas iniciais: quais órgãos publicaram compras em determinado período? Quais objetos mencionam um produto? Que contratos estão relacionados a uma contratação? Quais registros têm valores ou datas ausentes?

## Estado verificado

Há um plano e três amostras JSON válidas do PNCP, com 50 registros em cada arquivo. A consulta filtrada do Piauí informa 454 pregões para outubro de 2025, distribuídos em 10 páginas; a amostra contém somente a primeira página. Os totais nacionais de 201.691 contratos e 38.545 contratações são metadados das consultas históricas fornecidas, não volume já ingerido pelo projeto.

O arquivo do Querido Diário está vazio. O relato anterior registra falhas TLS, mas não permite atribuir definitivamente a causa ao servidor. Essa fonte permanece opcional; a verificação de certificados não será desativada.

A ingestão paginada e a carga PostgreSQL foram implementadas e executadas para agosto a outubro de 2026. Agente, avaliação de perguntas e demonstração ainda não existem. O [inventário dos arquivos](docs/sample-inventory.json) registra tamanho, hash e paginação sem reproduzir dados de fornecedores.

## Próxima entrega

Ampliar a base com uma estratégia própria para contratos e atas, antes de implementar as ferramentas do agente. Banco e período confirmados: PostgreSQL via Docker e agosto a outubro de 2026. A primeira coleta completa do recorte de pregões retornou 1.081 registros em 23 páginas.

A primeira versão deve distinguir resultado vazio, falha de rede e download incompleto. Valores financeiros serão tratados com precisão decimal. A relação entre compra e contratos não autoriza comparar um contrato isolado com o orçamento total da compra; a granularidade e a cobertura precisam ser verificadas.

## Organização

- `PLANO.md`: plano recebido, ainda sujeito à revisão de escopo.
- `docs/sample-inventory.json`: inventário verificável das amostras disponíveis.
- `amostras/`: amostras públicas parciais preservadas no Git, com origem e limitações documentadas.

A documentação e a implementação devem separar objetivo, evidência disponível e resultado medido. Não serão afirmadas acurácia, economia de trabalho ou cobertura estadual completa antes de avaliação própria.

## Conferir a primeira etapa

```powershell
python -m unittest discover -s tests -v
python scripts/audit_samples.py amostras --output runs/sample-audit.json
```

A auditoria retorna código de saída 1 se encontrar arquivo inválido, inclusive o arquivo vazio do Querido Diário. Isso é um diagnóstico esperado, não um download concluído.

Com Docker Desktop aberto, use `docker compose up -d` e `docker compose ps`. A configuração usa PostgreSQL 17, porta local 15432 e volume persistente. A senha local está no `.env` ignorado pelo Git; não publique esse arquivo. O esquema registra execuções, páginas, órgãos e contratações normalizadas. O agente ainda será implementado.

[Verificações de desenvolvimento, arquivos do commit e limites atuais](docs/development.md).

## Primeira ingestão concluída

**1.081 pregões eletrônicos** publicados no Piauí entre agosto e outubro de 2026 foram coletados e carregados no PostgreSQL. A conferência por mês resultou em 412, 373 e 296 registros. Em 749 deles, o valor homologado não foi informado: o campo permanece NULL, sem assumir zero ou pagamento.

Veja [método, evidências, limitações e reprodução](docs/ingestion.md). A coleta da modalidade 6 não representa todas as compras públicas do Piauí.
