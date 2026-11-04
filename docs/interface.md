# Interface local: da pergunta à evidência

## Experiência de assistente

A tela principal é uma área de exploração, com barra lateral, perguntas e respostas. Uma área expansível explica como interpretar compras, contratos e valores, sem interromper a consulta.

1. O assistente apresenta o recorte e três caminhos: panorama, municípios e rastreio de uma compra.
2. Os cartões preenchem uma pergunta que o visitante pode editar antes de enviar.
3. A pergunta aparece na conversa; o estado de processamento informa a consulta em andamento.
4. A resposta mostra texto, tabela quando aplicável, cobertura e modelo selecionado.
5. Fontes, rastro e registro técnico ficam em áreas expansíveis; há download do JSON original.
6. Perguntas sugeridas permitem continuar a exploração; o histórico permite revisitar resultados.

O histórico guarda até 20 resultados no **sessionStorage da aba**, sobrevivendo à atualização da página durante a sessão.
Nova exploração apaga o histórico visual. Cada pergunta permanece independente no backend: não há
memória conversacional no modelo, resolução de referências como “e essa?” ou inferência sobre perguntas
anteriores. Essa distinção é explicada na interface. É uma experiência de assistente sobre consultas
limitadas, sem apresentar capacidades conversacionais ainda não implementadas.

O modo inicial é IA com contingência, com aviso sobre o envio da pergunta e uso de quota. Regras locais
continuam no seletor. A interface orienta por exemplos, oferece próximos caminhos conforme o tipo de
resposta e calcula uma observação de cobertura a partir dos valores retornados: consultas confirmadas,
compra excluída e homologados desconhecidos. Essas observações usam dados verificados e templates;
não fazem nova chamada LLM ou inferem pagamentos, economia ou irregularidades.

A direção visual combina azul-marinho para orientação, verde-petróleo para ações e evidência e âmbar
nos pontos de rastreio. Os cartões e o recorte usam valores do snapshot fixo, não dados em tempo real.
Layouts menores reduzem a barra lateral; o botão de nova exploração permanece no cabeçalho móvel.
Enter envia, Shift+Enter insere linha; cliques em sugestões não consomem API sem envio.

## Executar

Com as dependências instaladas, downloads locais preservados e credencial de leitura configurada:

```powershell
docker compose up -d --wait
.venv/Scripts/python.exe -m asktrace.web
```

Abra [http://127.0.0.1:8010](http://127.0.0.1:8010). Para outro porto local, use `--port 8011`.
Encerrar o processo com Ctrl+C fecha o servidor. Ele não inicia Docker nem reinstala dependências.
Se ainda necessário, configurar o leitor com `python -m asktrace.query setup-reader`.

O modo inicial é **IA com contingência**. O seletor também oferece **regras locais**, sem consumo de API. O modo IA usa as chaves
do `.env` no servidor e respeita a ordem e a espera de `config/providers.json`. A interface explica
antes da consulta que a pergunta e o catálogo serão enviados ao provedor escolhido.
Não há chave no navegador. Erros de configuração, quota e banco aparecem sem mensagens sensíveis.

Os textos, navegação, resultados formatados e estados da interface estão em PT-BR e inglês.
As perguntas de negócio continuam oficialmente suportadas em português, como informa a interface
em inglês; os exemplos permanecem em português. O JSON original e os nomes de campos técnicos
mantêm o contrato da API, incluindo o texto do agente em português. A tradução visual usa templates
locais baseados nos resultados, sem outra chamada de modelo.

## Resultados e estados

- Três exemplos preenchem a pergunta sem executar automaticamente.
- Durante a consulta, o botão fica indisponível e a resposta anterior é ocultada.
- Resumo mostra números da consulta; municípios mostra até 20 grupos, sem multiplicar estimativas
  pelo número de contratos. Decimais permanecem texto e nulos aparecem como não informados.
- Rastreio mostra valores, contratos, execução e hashes. Compra fora da base é “não encontrada neste
  recorte”, sem afirmar ausência no PNCP.
- Recusa explica o catálogo disponível; erro indica indisponibilidade e preserva o rastro quando houver.
- Fontes e rastro podem ser expandidos. O manifesto aberto pela interface usa o ID do recorte em uma lista configurada.
- O download JSON é gerado no navegador a partir da resposta e não persiste perguntas no servidor.

Publicado não significa pago. A interface não atribui fraude nem calcula economia a partir de um
contrato e do orçamento total. Ausência não é convertida em zero. Esses limites acompanham o uso.

## Limites de acesso

Esta entrega é uma aplicação **local**, com bind exclusivo em `127.0.0.1`; não há deploy ou URL pública.
O servidor usa a biblioteca padrão do Python e está separado do agente e das consultas. Não há novas
dependências externas ou framework de frontend. HTML/CSS/JS estão em `web/`.

O Host é validado. Pedidos de consulta exigem Origin local e token de sessão gerado por processo,
JSON limitado a 8 KiB, pergunta até 1.000 caracteres e provedor em lista permitida. Há somente uma
consulta em andamento por processo; outra recebe 429 sem consumir mais API. Sem CORS aberto.
Não se aceita caminho de arquivo, SQL, manifesto de cobertura ou endpoint enviado pelo usuário. Só é aceito o ID da base configurada.

As rotas GET são fixas: página, dois assets, sessão com catálogo e manifesto de cobertura selecionado por ID permitido. `.env`, SQL e respostas
brutas não são servidos. CSP restringe recursos ao próprio servidor, bloqueia incorporação em frames
e base externa; `nosniff`, `no-store` e política de referência são enviados. Dados dinâmicos são
inseridos com `textContent`, sem interpretar HTML retornado pelo modelo ou pelo banco.

A escolha de base vem de `config/datasets.json`; não se aceitam caminhos de arquivo enviados pelo cliente.
O token limita pedidos originados de outras páginas; ele não autentica usuários nem protege contra
outros processos da mesma máquina. Não é uma solução pronta para exposição pública. Antes de
hospedar, são necessários servidor apropriado, política de acesso/abuso e armazenamento/configuração
para o ambiente hospedado. O servidor padrão não é apresentado como infraestrutura de produção.
Não há coordenação distribuída ou login de usuário nesta etapa.

## Verificação da versão atual

[Relatório HTTP real da versão atual](../runs/web-verification-ce1eb0aa-e3a5-4888-9af2-984c20385ec2/verification.json):
seis exemplos aprovados (resumo, municípios, compra, recusa, registro ausente e contingência real),
com hashes dos assets. O [teste intermediário](../runs/web-verification-8029bb61-a6e2-4df6-9f9d-624c4795be14/verification.json)
e a [primeira interface](../runs/web-verification-2179defe-b152-4eaa-b1f6-85f8b39ba5c5/verification.json)
foram preservados como histórico.

Passaram **86 testes Python locais**, incluindo PostgreSQL. Além deles, o contrato DOM em Node
verifica descoberta, envio, resposta, sugestões, histórico, idioma, reinício e sessão. Esse teste usa
elementos simulados: comprova as transições verificadas, não layout de navegador ou acessibilidade.
Foi incluído no fluxo CI com Node 22, sem novas bibliotecas. Execução remota ainda não verificada.

```powershell
node --check web/app.js
node tests/test_assistant_ui.cjs
```

A prévia continua bloqueada por “Local browser use is disabled in Work settings”. Portanto **não foi
feita inspeção visual de navegador**, teste de viewport real ou auditoria de acessibilidade. O CSS inclui
breakpoints, foco visível e redução de movimento; HTML inclui labels, link de salto e região de status.
Não há screenshot fabricado ou declaração de compatibilidade visual confirmada.

Para repetir os fluxos HTTP com o servidor em execução:

```powershell
.venv/Scripts/python.exe -m scripts.verify_web
```

O comando faz cinco consultas por regras e uma com IA, consumindo quota nesse último caso.

## Próximo passo

Revisar visualmente em desktop e celular, testar os estados por interação de navegador e ajustar o
layout a partir dessa revisão. Depois, preparar a hospedagem com backend, banco e limites de acesso.
O portfólio deve apresentar os resultados medidos e as limitações reais de cada modo.

## Base ampliada e orientação de uso

A introdução explica PNCP, propósito e os três passos de uso. O padrão passou a maio–outubro/2026, com 2.537 compras e cobertura parcial de contratos explícita. O recorte anterior permanece disponível. O histórico é restaurado do sessionStorage sem chamadas externas. [Método e evidências atuais](dataset-expansion.md).

## Quando a IA está em espera

Falhas de contingência antes da ferramenta retornam `availability.component=ai_planner` e
`database_checked=false`. A tela explica que o banco não foi consultado, não sugere que uma quota
seja falha dos dados, esconde fontes/cobertura vazias e oferece uma consulta explícita por regras
locais. O botão preserva pergunta e recorte, muda o modo visível e só então envia outra consulta.
Não há fallback silencioso. Regras locais precisam do banco ativo e respeitam seu catálogo.

Horários de espera são apresentados quando registrados, como possibilidade de nova tentativa,
sem garantia de recuperação. O rastro principal usa linguagem simples; os detalhes e candidatos
desativados continuam no registro técnico completo. Resultados antigos de sessão também recebem
essa apresentação a partir do rastro preservado, sem editar seus dados históricos.

Passaram 91 testes Python e o contrato DOM de recuperação: não há nova chamada ao renderizar erro,
somente após clique; o pedido usa baseline e fontes reaparecem após resposta válida. A
[verificação controlada](../runs/recovery-verification-da469824-8e8f-43dd-b8ec-f0f220c19af1/verification.json) usa falha de IA simulada e PostgreSQL real,
com zero chamadas externas. Não comprova a liberação da quota nem uma indisponibilidade real do
provedor. Não houve inspeção visual de navegador nesta etapa.


## Disponibilidade e a tela inicial

A página lê o estado local ao abrir, sem chamadas externas, mas não apresenta uma espera
compartilhada como falha de uma pergunta ainda não feita. O alerta fica condicionado a
uma tentativa de IA que falhou e desaparece no modo local ou em nova exploração.
Atualizar disponibilidade não envia a pergunta e trata falhas de conexão.

Esperas observadas continuam preservadas. Os detalhes da correção, verificações e
limitações estão na [revisão da aplicação](application-review.md). A
[verificação anterior](../runs/availability-diagnosis-6d8f3e82-c79c-4319-9687-6a1b52674168/verification.json)
registra o diagnóstico de quotas daquela execução; sua apresentação inicial foi substituída.

## Valores que podem ser lidos sem interpretar o formato do banco

A apresentação usa o idioma selecionado: `1571718049.25000000` vira
**R$ 1.571.718.049,25** em português e **R$1,571,718,049.25** em inglês.
Quantidades recebem separadores de milhar, datas civis são localizadas sem mudança de
fuso e identificadores como IBGE/PNCP continuam intactos. Ausência aparece como
“Não informado”; zero monetário aparece como “R$ 0,00”. Os títulos distinguem compras
sem estimativa de compras sem valor homologado, e as somas consideram somente valores
informados, sem converter ausências em zero.

`web/formatters.js` concentra a apresentação. Moedas partem da string decimal original,
com cálculo de centavos em BigInt e arredondamento de apresentação para duas casas
(metade para longe de zero). Não há conversão prévia para ponto flutuante. O backend,
histórico e JSON baixado mantêm os valores originais, inclusive casas adicionais.

Valores numéricos ficam alinhados à direita com algarismos de largura uniforme; o
cabeçalho permanece visível na rolagem. A região da tabela recebe foco por teclado.
Contratos vinculados são apresentados em tabela com ID, valor inicial, valor global e
índice na fonte, em vez de um bloco JSON dentro da célula. Fontes e hashes continuam
disponíveis no registro técnico.

Os testes de formatação cobrem PT/EN, negativos, zero, nulos, arredondamento com
transporte de centavos, quantias acima do limite de inteiros seguros de Number, anos
bissextos e preservação de identificadores. O contrato DOM confere células renderizadas,
troca de idioma, contratos e ausência de mutação das evidências.
[Verificação completa desta etapa](../runs/application-review-348a9663-dda0-42ca-bd0b-bf32bb2d84cb/verification.json). Não houve inspeção visual em navegador.

## Linguagem de produto e andamento da coleta

A interface deixou de apresentar o aplicativo como portfólio ou exibir uma identificação
pessoal na barra lateral. A área “Como interpretar os dados” explica compras, contratos
e valores; documentação e código continuam acessíveis. O HTML inicial usa os mesmos
textos da interface em português, e estatísticas aguardam a leitura da sessão antes de
exibir quantidades, evitando mostrar números antigos no carregamento.

Na base ampliada, os cartões agora distinguem 2.537 compras, 100 com busca de contratos
concluída, 2.436 pendentes e 1 excluída por ano inválido na fonte. Os 21 contratos e as
83 buscas sem publicação retornada continuam explícitos. A explicação abaixo separa
essas situações em itens e esclarece que buscas da coleta não são perguntas do usuário.
Os 1.354 valores homologados não informados são uma lacuna dos dados publicados.

Pendências e exclusões só são separadas quando os metadados do catálogo coincidem com
o relatório de origem, período e contagens da resposta. Um resultado histórico sem
correspondência recebe uma explicação de cobertura incompleta, sem herdar exclusões
da base atual. No recorte original, todas as 1.080 compras aptas foram pesquisadas e
a pendência exibida é zero; a compra excluída permanece separada.

Os testes DOM cobrem as duas bases, ambos os idiomas, metadados incompatíveis e ausência
de menções a portfólio nos arquivos da aplicação. A formatação de HTML e CSS também
facilita a manutenção. [Registro de validação](../runs/application-review-8ae90c1e-92fe-4782-855c-9c8d76817734/verification.json). A coleta não foi ampliada
nesta alteração; os estados apresentados refletem os registros já existentes.

## Seis caminhos e exportação

A descoberta passou a seis cartões. Evolução mensal, órgãos e qualidade têm respostas e tabelas próprias, com sugestões para continuar a exploração. O CSV preserva contexto, precisão original e trata fórmulas de planilha; JSON continua disponível. [Detalhes e limites](analytics.md).

## Atualização da cobertura e histórico anterior

O padrão passou a usar a cobertura concluída de 2.536 compras aptas e 679 contratos. Respostas salvas de outra versão recebem aviso e marca no histórico, sem restauração automática como resultado atual. O botão CSV segue o estilo do JSON. [Dados e testes](contracts-expanded-coverage.md).
