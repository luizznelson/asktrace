# Interface: entender, perguntar, interpretar e conferir

## Entrada

A aplicação se apresenta como assistente de compras públicas. O visitante vê o recorte,
três números da base e seis caminhos: panorama, municípios, compra por ID, meses, órgãos
e qualidade. A data indica quando a cobertura foi consolidada, em horário de Brasília,
sem apresentar o snapshot como consulta em tempo real.

Os cartões preenchem uma pergunta editável. O exemplo de compra usa um identificador
válido com contratos na base selecionada. Clicar não envia automaticamente nem consome API.

## Resposta em ordem de leitura

1. **Leitura principal:** frase calculada das linhas retornadas, com o achado relevante.
   Na série atual, junho tem o maior volume mensal: 527 compras publicadas.
2. **Indicadores da pergunta:** até três cartões, sem repetir toda a cobertura em cada análise.
3. **Visualização:** meses em ordem; rankings com prévia de até cinco grupos e limite de
   tabela explícito. Quantidades aparecem em texto, além do comprimento das barras.
4. **Tabela completa:** expansível nos gráficos, aberta no rastreio e na qualidade dos dados.
5. **Cobertura e campos ausentes:** detalhe expansível; abre no panorama, que trata desse assunto.
6. **Origem e rastro:** arquivos, hash, plano e execução para conferir a resposta.
7. **Exportação e continuidade:** JSON completo, CSV contextualizado e sugestões de próximas perguntas.

As barras são elementos HTML/CSS com rótulos e contagens; não dependem de bibliotecas
externas ou de uma segunda chamada ao modelo. A tabela continua disponível, sem limitar
o acesso aos valores originais. Empates e nomes ausentes recebem explicações próprias.

## Linguagem e limites

O seletor distingue “Perguntar com IA” de “Consultar sem IA · regras locais”. A ajuda
“Como interpretar os dados” explica valor estimado, homologado, recorte e busca sem
publicação. A interface não apresenta biografia ou menções a portfólio.

PT-BR e inglês cobrem navegação, estados, valores, datas, gráficos e ajuda. Perguntas
de negócio continuam suportadas em português. A IA seleciona um plano permitido; os
números vêm das consultas de leitura e não são redação livre do modelo.

## Histórico e privacidade

Até 20 resultados ficam no `sessionStorage` da aba. Nova exploração limpa o histórico.
Cada pergunta é independente: não há memória conversacional nem resolução automática
de “e essa?”. Resultados de outro hash de cobertura recebem aviso de versão anterior e
não são restaurados automaticamente como se fossem atuais.

No modo IA, somente pergunta e catálogo do planejador são enviados ao provedor configurado.
Os resultados do banco e as chaves ficam no servidor local. Evite inserir dados pessoais.
Uma indisponibilidade da IA informa que o banco não foi consultado e oferece tentativa
local explícita, sem troca silenciosa de modo ou redefinição de quota.

## Executar

Com PostgreSQL, downloads verificados, snapshots carregados e leitor configurado:

```powershell
.venv/Scripts/python.exe -m asktrace.web
```

Abra `http://127.0.0.1:8010`. O servidor não prepara os dados nem inicia Docker por conta
própria; [desenvolvimento](development.md) explica os pré-requisitos. O aplicativo é local,
sem autenticação multiusuário para hospedagem pública.

## Verificação

[Registro atual](../runs/application-review-7aa7ebba-442d-466f-9642-5b62647dd32e/verification.json): suíte Python, contratos Node, HTTP e PostgreSQL passaram.
Os comportamentos foram verificados sem inspeção visual em navegador. A gravação de
vídeo ficou para uma etapa posterior.

[Histórico da interface](history/interface-log.md) · [Qualidade](quality.md) ·
[Análises e interpretação](analytics.md) · [Cobertura concluída](contracts-expanded-coverage.md).
