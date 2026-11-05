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

## Execução local e publicação

O servidor local da biblioteca padrão permanece limitado a `127.0.0.1`. A entrada pública
é `asktrace.public:create_app`, servida por Uvicorn. Ambos compartilham o catálogo e o
executor de consultas; as fronteiras HTTP têm testes separados.

Na publicação, um login lê os dados e o pacote de evidências; outro atualiza somente
os dois registros de estado operacional. A credencial administrativa pertence à carga
fora do servidor. O startup confere permissões e restaura o artefato privado identificado
por SHA-256 antes de disponibilizar a aplicação. Quotas não dependem do disco efêmero.
[Configuração, limites e pendências externas](deployment.md).


## ADR-002 — verificar evidências no startup público e consultar o banco por pergunta

**Problema observado:** a primeira versão hospedada gastou 20–23 segundos por consulta
por regras na base maior. Um perfil local mostrou releituras de milhares de arquivos,
incluindo a validação repetida do mesmo snapshot de compras em cada lote de contratos.
Os tempos locais e do Render não são diretamente comparáveis.

**Decisão:** o startup público continua restaurando o pacote fixado por SHA-256 e
validando manifestos, fontes, contratos e cobertura. Depois guarda metadados verificados
em bytes imutáveis na memória daquela instância. Cada pergunta recebe uma cópia própria,
limitada à raiz e ao relatório selecionado. O planejador usa o mesmo recorte verificado
que a ferramenta de consulta. Não há cache de respostas de usuários nem de resultados SQL.

Cada pergunta ainda executa SQL somente leitura e confere os totais contra a cobertura
verificada. Uma divergência é recusada. As ferramentas de auditoria e o servidor local
continuam verificando os arquivos. Dentro de uma operação completa, o índice de compras
é verificado uma vez e compartilhado entre os lotes; hashes de cada página de contratos
permanecem obrigatórios. A próxima operação de auditoria volta a ler os arquivos.

**Ciclo de vida:** a cópia em memória vale somente para a instância iniciada com aquela
configuração. Atualizar a base exige preparar/publicar o novo pacote e reiniciar a
aplicação; editar arquivos depois do startup não atualiza essa cópia. O hash não é uma
assinatura contra alguém com controle do servidor. A aplicação pública não expõe uma
rota para editar arquivos, trocar snapshots ou invalidar esse estado.

**Consequências:** o custo de ler os arquivos fica concentrado na inicialização e há
uso adicional de memória. Reinícios continuam sujeitos ao tempo de restauração e
validação. A melhoria foi medida na [URL pública](../runs/render-performance-59ca88d-verified/verification.json) após
o deploy. O benchmark anterior com ASGI/Neon permanece separado dessa medição hospedada.

Os testes cobrem alterações de arquivos entre operações de auditoria, hash de contrato,
isolamento das cópias, seleção da base, caminho relativo à aplicação e divergência do banco.
