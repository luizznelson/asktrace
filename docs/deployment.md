# Publicação do AskTrace

## O que foi preparado

A aplicação mantém o servidor local e tem uma entrada pública com FastAPI/Uvicorn.
Interface e API usam a mesma origem HTTPS. O banco continua PostgreSQL: a configuração
aceita Neon ou outro serviço compatível, com verificação do certificado e do hostname.
O arquivo `render.yaml` descreve uma demonstração Free, com um único worker.

**Estar preparado para publicação não significa estar publicado.** A verificação de um
endereço externo, a revisão visual real e o vídeo precisam ser registrados após o deploy.

## Credenciais com responsabilidades diferentes

| Configuração | Onde usar | Permissão |
| --- | --- | --- |
| `ASKTRACE_ADMIN_DATABASE_URL` | Somente no computador, para preparar o banco de destino | Migrações e importação |
| `ASKTRACE_DATABASE_URL` | Segredo do serviço publicado | Login de leitura dos dados e do pacote privado |
| `ASKTRACE_STATE_DATABASE_URL` | Segredo do serviço publicado | Ler e atualizar somente os limites da demonstração e a espera de provedores |
| `ASKTRACE_DATA_SHA256` | Configuração do serviço; não é senha | Identificar exatamente o pacote de evidências esperado |

A aplicação pública rejeita a credencial administrativa em sua configuração e confere
as permissões dos logins de execução. Conexões remotas usam `sslmode=verify-full` e
certificados do pacote `certifi`, mesmo que a URL copiada do provedor peça um modo menos
restritivo. Senhas, URLs privadas e chaves de API não pertencem ao Git nem ao chat.

## Como os dados sobrevivem a reinícios

O PostgreSQL guarda os registros e uma cópia compactada dos arquivos de origem necessários
às duas bases. Esse pacote é privado: não fica no Git, não é um arquivo público do site
e não é enviado aos modelos. Seu hash é fixado na configuração da publicação.

Na inicialização, o servidor verifica os logins, lê esse pacote do banco, confere seu
hash e restaura apenas caminhos de `data/raw` e `data/processed`. Em seguida verifica
manifestos, páginas e normalização como no ambiente local. Não faz nova coleta no PNCP.
O conteúdo do disco pode desaparecer sem apagar a cópia persistida no banco.

O pacote tem limites de tamanho, rejeita nomes duplicados, travessia de diretórios e
links simbólicos. Ele contém os bytes originais para conferir hashes; a verificação
não transforma o conteúdo da fonte em informação certificada.

## Preparar o banco de destino

Com o ambiente instalado e os dados locais verificados:

1. Criar um projeto PostgreSQL em um plano escolhido conscientemente. Para o Neon,
   selecionar o Free e obter a conexão administrativa do projeto dedicado ao AskTrace.
2. Adicionar `ASKTRACE_ADMIN_DATABASE_URL` ao `.env` local. Não substituir as credenciais
   do banco local. Não executar a manutenção apontando para o ReceiptTrace ou outro projeto.
3. Executar a importação explícita:

```powershell
.venv/Scripts/python.exe -m asktrace.release load
```

O comando verifica os arquivos, importa os snapshots sem duplicar registros, aplica as
migrações e armazena o pacote privado. As credenciais dos logins de execução são geradas
e gravadas em `data/deploy/runtime.env`, ignorado pelo Git. **A execução de `load` gera
novas senhas para esses logins:** ao repeti-la, atualizar os segredos do serviço antes de
reiniciá-lo. Não executá-la durante uma demonstração em andamento.

Para construir e conferir apenas o pacote local, sem tocar no banco remoto:

```powershell
.venv/Scripts/python.exe -m asktrace.release build
```

O zip e seu resumo ficam em `data/deploy`, também fora do Git. Não publicar esse diretório
como anexo ou release pública. No Windows, ele herda as permissões da pasta do usuário;
o ajuste Unix `0600` não substitui as permissões do Windows.

## Configurar o serviço no Render

O Blueprint `render.yaml` instala as dependências com hashes e inicia:

```text
uvicorn asktrace.public:create_app --factory --host 0.0.0.0 --port $PORT --workers 1 --no-access-log --no-proxy-headers
```

Copiar os valores de `data/deploy/runtime.env` para os segredos correspondentes no Render.
Não enviar esse arquivo ao GitHub. O Render fornece `RENDER_EXTERNAL_URL`; em outro host,
definir `ASKTRACE_PUBLIC_ORIGIN=https://dominio-exato`, sem barra final. O servidor aceita
somente esse Host e essa Origin, sem confiar em cabeçalhos encaminhados pelo cliente.

O health check é `/healthz`: confere conexão e permissões, devolvendo apenas `ok` ou
`unavailable`. Não mostra endereço do banco, credenciais ou mensagens internas.

## IA e limites da demonstração

O código mantém a IA desligada quando `ASKTRACE_PUBLIC_AI` não é definido. O Blueprint
desta demonstração define `ASKTRACE_PUBLIC_AI=true` e solicita as chaves Groq, OpenRouter
e Gemini, já utilizadas no desenvolvimento. Seus valores são cadastrados como segredos;
nenhuma chave fica no YAML. O modo por regras permanece disponível sem chamadas externas.

O arquivo `data/deploy/runtime.env` contém somente as duas conexões de execução e o hash
dos dados. A escolha de habilitar IA pertence ao Blueprint. Para manter outra escolha
em futuras sincronizações, alterar o valor no `render.yaml`, em vez de criar configurações
divergentes no painel.

O limite padrão é **10 solicitações de IA por dia UTC**, compartilhadas entre visitantes.
Cada solicitação pode tentar até três candidatos, respeitando a espera por provedor;
10 solicitações não significam 10 chamadas externas. Há também limites globais de
30 solicitações de consulta por minuto e 2.000 por dia. Falhas após a reserva consomem
essa reserva; limites não são recuperados por abrir outra aba ou reiniciar o servidor.
O dia é UTC para manter a contagem consistente entre instâncias.

Os limites e a espera ficam no PostgreSQL, sem guardar perguntas ou IPs nesse registro.
Sem acesso ao estado persistente, a consulta pública falha de maneira explícita. O token
de sessão é uma proteção de mesma origem; não representa autenticação de usuário e não
torna o serviço privado. A configuração suportada nesta versão é um worker e uma instância.

Planos gratuitos têm cotas e podem suspender o serviço. Conferir as condições vigentes
antes de criar recursos; a aplicação não comprova a gratuidade da conta dos provedores.

## Checklist de publicação

- [x] Banco Neon preparado e totais das duas bases conferidos.
- [ ] Segredos de execução cadastrados; credencial administrativa ausente do serviço.
- [ ] Startup restaura o pacote com o hash esperado e saúde retorna 200.
- [ ] Seis consultas, recusas, histórico, troca de idioma e downloads conferidos na URL pública.
- [ ] Reinício e retomada após inatividade conferidos; limites não são apagados.
- [ ] Inspeção visual de desktop e celular realizada, sem afirmar certificação de acessibilidade.
- [ ] URL, capturas reais e vídeo adicionados ao README; pendências atualizadas.

## Verificação executada no Neon

[Registro completo](../runs/neon-verification-187bed11-8da5-4be2-8712-d694a4ea11a0/verification.json): conexão com certificado validado, leitura
e estado com permissões separadas, restauração do artefato privado e doze consultas reais.
Base padrão: 2.537 compras, 2.536 pesquisas e 679 contratos. Base original: 1.081 compras,
1.080 pesquisas e 125 contratos, sem somar os recortes. Uma nova instância manteve o
orçamento persistido e rejeitou o token da instância anterior.

Durante a preparação, testes herdaram a conexão administrativa e criaram cinco registros
sintéticos no banco novo. A execução foi interrompida; somente esses cinco registros foram
identificados e removidos em transação. A verificação final confirmou zero registros
sintéticos. A correção bloqueia conexões remotas quando os testes de integração estão
habilitados e exige o banco local `asktrace_test`; 131 testes passaram após a correção.

As inserções da carga usam pipeline dentro da transação original para evitar uma espera
de rede por registro. Validação dos arquivos, integridade e comportamento contra duplicação
foram preservados. A carga administrativa não é executada no startup do serviço.

Para repetir a conferência remota antes de receber tráfego público:

```powershell
.venv/Scripts/python.exe -m scripts.verify_remote
```

Essa verificação consome doze consultas do orçamento compartilhado e usa o arquivo privado
de execução. Ela não chama modelos nem representa um teste da URL pública do Render.

## Referências oficiais

[Render: FastAPI](https://render.com/docs/deploy-fastapi) ·
[Neon: conexões seguras](https://neon.com/docs/connect/connect-securely) ·
[FastAPI: execução com Uvicorn](https://fastapi.tiangolo.com/deployment/server-workers/) ·
[Condições de hospedagem e limites consultados](hosting-options.md).
