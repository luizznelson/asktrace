# Interface local: da pergunta à evidência

## Jornada apresentada

1. **Entender o problema e o recorte:** pregões de unidades do Piauí publicados entre agosto e outubro
   de 2026. A base reúne 1.081 compras, com 1.080 consultas de contratos e uma exclusão por ano inválido.
2. **Escolher uma pergunta:** resumo, agrupamento municipal ou rastreio de compra com ID explícito.
3. **Ler a resposta:** texto, tabela quando aplicável e contagens de cobertura.
4. **Conferir a origem:** período, modalidade, manifesto, hash e dados da compra.
5. **Acompanhar a execução:** decisão de política, plano, tentativas de provedores e consulta de leitura.

A apresentação usa linguagem de negócio e mantém o registro técnico em uma área expansível.
Os números de abertura são resultados do snapshot fixo documentado, não um monitoramento em tempo
real. Uma nova coleta exige atualizar a referência de cobertura e a apresentação.

## Executar

Com as dependências instaladas, downloads locais preservados e credencial de leitura configurada:

```powershell
docker compose up -d --wait
.venv/Scripts/python.exe -m asktrace.web
```

Abra [http://127.0.0.1:8010](http://127.0.0.1:8010). Para outro porto local, use `--port 8011`.
Encerrar o processo com Ctrl+C fecha o servidor. Ele não inicia Docker nem reinstala dependências.
Se ainda necessário, configurar o leitor com `python -m asktrace.query setup-reader`.

O modo inicial é **regras locais**, sem consumo de API. O seletor **IA com contingência** usa as chaves
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
- Fontes e rastro podem ser expandidos. O manifesto aberto pela interface é uma rota fixa.
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
Não se aceita caminho de arquivo, SQL, cobertura ou endpoint enviado pelo usuário.

As rotas GET são fixas: página, dois assets, sessão e manifesto de cobertura. `.env`, SQL e respostas
brutas não são servidos. CSP restringe recursos ao próprio servidor, bloqueia incorporação em frames
e base externa; `nosniff`, `no-store` e política de referência são enviados. Dados dinâmicos são
inseridos com `textContent`, sem interpretar HTML retornado pelo modelo ou pelo banco.

O token limita pedidos originados de outras páginas; ele não autentica usuários nem protege contra
outros processos da mesma máquina. Não é uma solução pronta para exposição pública. Antes de
hospedar, são necessários servidor apropriado, política de acesso/abuso e armazenamento/configuração
para o ambiente hospedado. O servidor padrão não é apresentado como infraestrutura de produção.
Não há coordenação distribuída ou login de usuário nesta etapa.

## Verificação

[Relatório HTTP real](../runs/web-verification-2179defe-b152-4eaa-b1f6-85f8b39ba5c5/verification.json): seis fluxos aprovados, usando PostgreSQL e,
em um caso, contingência real de modelo. Exemplos de resposta e seus rastros estão na mesma pasta.
O relatório registra hashes do backend e dos assets e omite o token de sessão.

Passaram **86 testes locais**, incluindo PostgreSQL. Os sete novos testes exercitam rotas fixas,
sessão/Host/Origin, corpo e pergunta limitados, provedor permitido, uma consulta por processo,
falha sem vazamento e uso do manifesto fixo. `node --check` validou a sintaxe JS; Ruff e formatação
validaram Python. Nenhuma chave configurada aparece nos arquivos versionáveis.

A prévia automatizada do navegador foi impedida pela configuração “Local browser use is disabled
in Work settings”. Por isso, **não foi feita inspeção visual no navegador nem teste de interação DOM**.
O CSS inclui layouts responsivos, foco visível, labels, link de salto, região de status e redução de
movimento; não afirmamos uma auditoria de acessibilidade ou compatibilidade móvel concluída.
CI remoto não verificado nesta entrega.

Para repetir os fluxos HTTP com o servidor em execução:

```powershell
.venv/Scripts/python.exe -m scripts.verify_web
```

O comando executa cinco exemplos por regras e um com IA, consumindo quota nesse último.

## Próximo passo

Revisar visualmente em desktop e celular, testar os estados por interação de navegador e ajustar o
layout a partir dessa revisão. Depois, preparar a hospedagem com backend, banco e limites de acesso.
O portfólio deve apresentar os resultados medidos e as limitações reais de cada modo.
