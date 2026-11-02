# Desenvolvimento e preparação do commit

## Ambiente e verificações

A auditoria e o coletor usam Python 3.14 e biblioteca padrão. A carga usa psycopg e python-dotenv, fixados com hashes em requirements.txt. Ruff é uma ferramenta de desenvolvimento fixada em `requirements-dev.txt`.

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
ruff check .
ruff format --check .
docker compose config --quiet
```

O último comando valida o Compose sem imprimir a configuração interpolada. Não publique a saída de `docker compose config` sem `--quiet`, porque ela pode conter a senha do banco. O workflow de qualidade executa testes e Ruff no GitHub; sua execução remota ainda precisa ser confirmada.

## O que entra no Git

Código, testes, SQL, Compose, regras de formatação e exclusão, dependências de desenvolvimento, documentação, inventário de hashes e `.env.example` sem valores reais.

Não versionar `.env`, caches, ambientes virtuais, dumps de banco e chaves privadas. Por decisão do mantenedor, as pequenas amostras públicas em `amostras/` e os relatórios revisados em `runs/` são versionados, com contexto nos READMEs dessas pastas. Os arquivos locais não precisam ser apagados para ficarem fora do repositório. O inventário não contém registros individuais de fornecedores.

Antes do primeiro commit:

```powershell
git status --short
git add --dry-run .
```

Esses comandos permitem conferir a seleção sem adicionar arquivos ao índice. Após adicionar os arquivos, confira também `git diff --cached --stat`. Exclusões não removem arquivos já rastreados de commits antigos; esta revisão encontrou o projeto ainda sem repositório e inicializou um Git local vazio, sem commits.

## Limites desta entrega

`complete_dataset` descreve somente a paginação informada pelo arquivo. Não atesta atualização, cobertura geográfica, ausência de duplicados ou correção financeira. Duplicados e IDs ausentes são indicadores separados no relatório.

A auditoria não substitui validação do domínio, testes da ingestão ou revisão de SQL executado por agente. O esquema atual é o registro inicial de origem; as tabelas normalizadas foram adicionadas na migração 002. O usuário de consulta somente leitura ainda não foi implementado. A credencial administrativa do Compose não deve ser usada pelo futuro agente.

Os arquivos de `/docker-entrypoint-initdb.d/` inicializam um volume novo. Alterar o SQL não migra um banco existente; mudanças posteriores precisarão de migrações explícitas, sem apagar o volume para atualizar o esquema.

A entrega de ingestão validou o SQL no PostgreSQL 17.11, com testes de integração em asktrace_test. O Compose fixa o digest da imagem observada. A documentação da primeira revisão descrevia o Docker desligado; essa limitação foi resolvida nesta etapa. Veja ingestion.md para comandos de reprodução e evidências.
