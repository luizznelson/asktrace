# Arquitetura atual e decisões de engenharia

## Fluxo completo

PNCP → coleta/validação → snapshots no PostgreSQL → pergunta → plano validado → consulta
somente leitura → resumo e gráfico determinísticos → tabela, fontes e exportação. O
planejador não gera SQL nem recebe as linhas do banco. A aplicação local tem seis consultas
e interface PT-BR/EN. [Análises](analytics.md) · [Interface](interface.md).

## ADR-001 — separar aquisição, normalização e carga

## Decisão e motivo

Construir a base auditável antes do agente. O coletor preserva respostas, a normalização aplica regras explícitas e o carregador verifica o snapshot antes de gravar. Isso permite repetir uma carga sem fazer novas requisições e investigar uma falha sem substituir a evidência original.

| Área | Responsabilidade | Código |
| --- | --- | --- |
| Auditoria inicial | Conferir arquivos de exploração e paginação | [audit_samples.py](../scripts/audit_samples.py) |
| Coleta | Janelas mensais, páginas, limites, retentativas e estados | [ingest.py](../asktrace/ingest.py): `collect`, `fetch`, `decode` |
| Normalização | Recorte, valores decimais, ausências e origem | [ingest.py](../asktrace/ingest.py): `normalize`, `amount` |
| Carga | Integridade, transação, identidade e idempotência | [database.py](../asktrace/database.py) |
| Banco | Execuções, páginas, órgãos, contratações e visão analítica | [001](../sql/001_schema.sql), [002](../sql/002_purchases.sql) |
| Verificação | Regras isoladas e integração PostgreSQL | [Testes](../tests/) |

## Alternativas e consequências

- **Gravar diretamente a resposta no banco:** teria menos arquivos, mas dificultaria repetir a carga sobre os mesmos bytes. O JSON original foi mantido localmente, com hash no manifesto.
- **Usar float ou converter ausências em zero:** simplificaria certas contas, mas mudaria o significado dos valores. O projeto usa Decimal, NUMERIC e NULL.
- **Atualizar registros por identificador sem snapshot:** consumiria menos histórico, mas poderia ocultar mudanças entre coletas. O banco separa execuções por UUID. Consultas precisam escolher `run_id` para evitar dupla contagem.
- **Carregar parcialmente e continuar após erro:** preservaria algum progresso no banco, mas poderia parecer uma base concluída. A carga usa transação única e é recusada se a coleta não estiver em estado permitido.
- **Acrescentar um agente agora:** permitiria mostrar um chat mais cedo, mas não demonstraria a cobertura da base. Essa foi a ordem inicial de implementação; hoje o roteador, as avaliações e a interface já existem, preservando a separação entre as camadas.

PostgreSQL com Docker foi a escolha confirmada pelo mantenedor. O projeto ainda usa um módulo Python na raiz, executado com `python -m asktrace...`; não há pacote publicado nem necessidade de mover os arquivos para imitar outro repositório.

## Limites de confiança

Hashes detectam divergências em relação ao manifesto; não são assinatura nem prova contra alguém que pode substituir arquivos e hashes. O coletor não obtém uma transação única do PNCP para todas as páginas. A visão de dados reais filtra amostras, mas não substitui autenticação: a coleta/carga usa manutenção administrativa local; as consultas do agente usam `asktrace_reader`, com SELECT nas visões de relatório e transação somente leitura. Isso não é isolamento multiusuário ou autenticação de hospedagem.

O [guia de ingestão](ingestion.md) detalha caminhos, filtros e reprodução.
