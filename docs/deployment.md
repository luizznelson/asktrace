# Publicação do AskTrace

**Publicado e verificado:** [aplicação](https://asktrace-pyop.onrender.com), commit `59ca88d`.
[Resultados da atualização e da nova instância](../runs/render-performance-59ca88d-verified/verification.json).

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
manifestos, páginas e normalização como no ambiente local. A versão otimizada mantém os
metadados verificados em memória imutável por instância; perguntas continuam consultando
o banco e conferindo os totais. Atualizar a base exige novo pacote e reinicialização,
conforme a [decisão de arquitetura](architecture.md#adr-002--verificar-evidências-no-startup-público-e-consultar-o-banco-por-pergunta).
Não faz nova coleta no PNCP.
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
- [x] Segredos de execução cadastrados; credencial administrativa ausente do serviço.
- [x] Startup restaura o pacote com o hash esperado e saúde retorna 200.
- [ ] Seis consultas, recusas, histórico, troca de idioma e downloads conferidos na URL pública.
- [x] Nova instância após redeploy do mesmo commit: orçamento preservado e token antigo rejeitado.
- [ ] Retomada após suspensão por inatividade conferida separadamente.
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

## Publicação verificada em 05/11/2026

Aplicação: [https://asktrace-pyop.onrender.com](https://asktrace-pyop.onrender.com). Serviço `asktrace-pyop`, plano Free,
Ohio, um worker. Commit publicado: `bfa7dc928c5e6dab2cc4b12c91504e5c2debbf8b`.
Deploy `dep-dbm7l7l6e07s73bdc3mg` confirmado como `live` pelo Render.
Sincronização automática e publicação automática por push permanecem desativadas.

[Evidência HTTP](../runs/render-verification-5c4ad84a-6be1-46af-a81b-5965ccc471f6/verification.json): saúde 200 em 0,807 segundo, arquivos da interface,
cabeçalhos de segurança, doze consultas nas duas bases, recusa de pergunta sem suporte,
rejeição sem token e bloqueio do arquivo privado `.env`. Uma solicitação pública com IA
real retornou o panorama esperado. Essa conferência não equivale a uma auditoria completa
de segurança nem à repetição da avaliação de 60 casos.

Na interface hospedada, foram conferidos a página inicial em tela estreita de 390 px,
a troca PT-BR/EN, uma resposta por regras, o histórico da aba e o download CSV.
[Captura real](assets/asktrace-public-response.jpg). Não se afirma revisão visual de
todas as telas, teste completo de acessibilidade ou gravação de vídeo.

As consultas por regras da base maior levaram 20,494–22,903 segundos; na original,
5,226–5,919 segundos. A consulta com IA levou 43,401 segundos. Os tempos incluem o
percurso HTTP desta execução; ainda não isolam as causas. A revalidação das evidências
a cada pergunta é uma hipótese a medir antes de alterar a implementação. Otimização,
reinício do serviço hospedado e retomada após inatividade continuam pendentes.

## Referências oficiais

[Render: FastAPI](https://render.com/docs/deploy-fastapi) ·
[Neon: conexões seguras](https://neon.com/docs/connect/connect-securely) ·
[FastAPI: execução com Uvicorn](https://fastapi.tiangolo.com/deployment/server-workers/) ·
[Condições de hospedagem e limites consultados](hosting-options.md).


## Histórico: atualização de desempenho preparada

A versão local otimizada reutiliza evidências verificadas na inicialização pública,
sem armazenar respostas de usuários. Naquela etapa, o código ainda precisava ser commitado, enviado e implantado.
A publicação foi concluída na etapa registrada abaixo. Não é necessário repetir a importação do
Neon nem gerar novas credenciais. A atualização preserva os limites já gravados no banco.

Em 05/11/2026 às 13:10 UTC, a versão pública anterior respondeu `/healthz` com 200 em
0,801 segundo após um intervalo sem requisições desta sessão. Não houve confirmação de
suspensão por inatividade, e outros visitantes não foram excluídos; isso não comprova
um cold start. [Registro](../runs/render-verification-5c4ad84a-6be1-46af-a81b-5965ccc471f6/idle-response.json).


## Otimização publicada e nova instância verificada

O commit `59ca88dfaab2c842da4b70534ca98b3c5e50fdb7` está publicado. O primeiro deploy
`dep-dbm8hobm8hqs73f1tabg` e o redeploy controlado `dep-dbm8it5bedkc73bi3pjg` chegaram
a `live`. A nova instância restaurou e verificou os dados antes de receber tráfego.
[Conferência HTTPS](../runs/render-performance-59ca88d-verified/verification.json): doze caminhos, contagens esperadas, recusa de pergunta
fora do escopo, token antigo rejeitado e orçamento diário/IA inalterado na troca.

Base maior: 0.563–0.940 segundos por consulta por regras nesta rodada; a rodada
anterior levou 20–23 segundos. Uma solicitação com IA real levou 1.884 segundos.
As duas execuções usam o endereço público, mas não são teste controlado de carga.

Uma primeira comparação de tokens foi inválida porque o checkpoint já pertencia à
instância publicada; esse registro foi preservado e não representa falha estabelecida
da aplicação. A comparação foi repetida através de um novo deploy do mesmo commit.
Não foi necessário importar novamente a base ou trocar credenciais.

Essa conferência resolve a pendência de iniciar uma nova instância hospedada da versão
otimizada. Não esclarece a causa da falha anterior do cliente ASGI local. Retomada após
suspensão por inatividade, revisão visual completa e vídeo continuam separados.

As recusas intermediárias de uma pergunta no roteiro público foram provocadas por uma
conversão incorreta dos acentos no próprio arquivo de verificação no Windows. O roteiro
foi corrigido, as tentativas anteriores foram preservadas e a rodada final passou. Não
foi necessária alteração do código da aplicação para essa ocorrência.
