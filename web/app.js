"use strict";
const $ = (id) => document.getElementById(id);
const text = {
    pt: {
        skip: "Ir para a consulta",
        local: "PRÉVIA LOCAL",
        navMethod: "Como funciona",
        navAsk: "Consultar",
        eyebrow: "COMPRAS PÚBLICAS · DADOS DO PNCP",
        title: "Uma pergunta.\nUm caminho até a fonte.",
        lede: "Investigue compras públicas sem perder de vista de onde vieram os números — e o que eles permitem concluir.",
        start: "Explorar o recorte ↗",
        scope: "Pregões eletrônicos · Piauí · Publicação de ago–out/2026",
        snapshot: "RECORTE VERIFICADO",
        purchases: "compras na base original",
        queried: "Compras consultadas para contratos",
        contracts: "Contratos vinculados",
        excluded: "Exclusão por ano inválido na fonte",
        scopeNote:
            "Este é um recorte de pregões. Não representa todos os contratos do Piauí.",
        manifest: "Ver evidência do recorte ↗",
        methodLabel: "01 / ENTENDER ANTES DE PERGUNTAR",
        methodTitle: "O número sozinho não conta a história.",
        step1: "Um recorte declarado",
        step1Text:
            "Modalidade, local e período acompanham a resposta. Assim, uma amostra não vira uma conclusão sobre o estado inteiro.",
        step2: "Uma consulta de leitura",
        step2Text:
            "O planejador escolhe uma consulta permitida. Os valores vêm do PostgreSQL, sem SQL livre gerado pelo modelo.",
        step3: "Uma trilha para conferir",
        step3Text:
            "Cobertura, identificadores, hashes e tentativas de modelo ajudam a verificar a resposta e seus limites.",
        askLabel: "02 / EXPLORAR COM EVIDÊNCIAS",
        askTitle: "O que você quer entender?",
        askIntro:
            "Consulte o resumo, compare municípios ou rastreie uma compra pelo identificador PNCP.",
        questionLabel: "Sua pergunta",
        mode: "Modo de consulta",
        baseline: "Consultar sem IA · regras locais",
        fallback: "Perguntar com IA",
        privacy:
            "No modo IA, a pergunta e o catálogo de consultas são enviados aos provedores configurados. A chave e os resultados do banco ficam no servidor da aplicação.",
        submit: "Consultar ↗",
        limitsLabel: "LEIA O RESULTADO COM CONTEXTO",
        limitTitle: "Publicado não significa pago.",
        limitText:
            "Um contrato publicado não comprova pagamento ou execução financeira. O AskTrace não classifica fraude nem calcula economia entre um contrato e o orçamento inteiro da compra.",
        unknown:
            "compras sem valor homologado informado. Ausência não vira zero.",
        availability:
            "As quotas gratuitas podem limitar o modo IA. O modo por regras continua disponível enquanto o banco local estiver ativo.",
        download: "Baixar evidências JSON ↓",
        csvExport: "Exportar tabela CSV ↓",
        monthlyText:
            "A tabela acompanha as compras por mês de publicação no PNCP. Não é uma linha do tempo de execução ou pagamento. Somas usam apenas valores informados.",
        organizationsText:
            "A tabela mostra até 20 órgãos com mais compras. Os valores estimados são somados uma vez por compra e não representam pagamentos.",
        qualityText:
            "Este diagnóstico mostra o preenchimento dos campos da base inteira. Valores zero são contados separadamente dos campos não informados; as contagens podem se sobrepor e não devem ser somadas.",
        responseTitle: "Resposta com contexto",
        sources: "Origem dos dados",
        coverageDetails: "Cobertura e campos ausentes",
        glossaryTitle: "Termos da consulta, sem complicar",
        estimatedTerm: "Valor estimado",
        estimatedDefinition:
            "Previsão de valor informada para a compra. Não é um pagamento e pode diferir do valor homologado.",
        awardedTerm: "Valor homologado",
        awardedDefinition:
            "Valor que o PNCP informa para o resultado homologado da compra. Pode não estar preenchido e não comprova pagamento.",
        scopeTerm: "Recorte",
        scopeDefinition:
            "Publicações selecionadas por período, modalidade e UF da unidade compradora. Não é o portal inteiro.",
        publicationTerm: "Sem publicação retornada",
        publicationDefinition:
            "A busca foi concluída, mas o PNCP não retornou contrato publicado para aquela compra. É diferente de falha ou pesquisa pendente.",
        trace: "Rastro da consulta",
        technical: "Registro técnico completo",
        repo: "Explorar código, método e evidências no GitHub ↗",
        footer: "Projeto independente · Fonte: PNCP · Execução local",
        placeholder: "Pergunte sobre as compras deste recorte…",
        waiting:
            "Consultando e verificando as evidências… O modo IA pode levar mais tempo.",
        ready: "Resposta pronta. Confira abaixo as fontes e os limites.",
        sessionError:
            "Não foi possível iniciar a sessão local. Recarregue a página.",
        busy: "Já há uma consulta em andamento. Aguarde e tente novamente.",
        demoLimit: "A demonstração atingiu um limite compartilhado de consultas. Aguarde para tentar novamente. Se estava usando IA, você também pode tentar o modo por regras.",
        error: "Não foi possível concluir a solicitação. Confira a conexão com a aplicação e tente novamente.",
        answered: "Consulta concluída",
        refused: "Fora das consultas disponíveis",
        not_found_in_scope: "Não encontrado neste recorte",
        refusal:
            "Esta pergunta está fora das consultas disponíveis ou pede uma conclusão que o recorte não sustenta. Tente panorama, municípios, meses, órgãos, qualidade dos dados ou uma compra com ID PNCP.",
        notFound:
            "A compra não foi encontrada neste recorte. Isso não comprova ausência no PNCP.",
        queryError:
            "A consulta não pôde ser concluída. O rastro informa o ponto de falha sem expor credenciais.",
        coverageLabels: [
            "Compras na base",
            "Compras com contratos pesquisados",
            "Contratos vinculados",
            "Pesquisadas sem publicação retornada",
        ],
        scopeLabel: "Recorte",
        reportLabel: "Relatório de cobertura",
        hashLabel: "Hash do relatório",
        plan: "Plano validado",
        policy: "Filtro de escopo",
        tool: "Consulta somente leitura",
        attempt: "Tentativa de provedor",
        failure: "Falha",
        unavailable: "Não informado",
        summaryText: (c) =>
            `A base tem ${displayFormat.integer(c.purchases, lang)} compras. Há ${displayFormat.integer(c.covered_purchases, lang)} consultas de contratos confirmadas e ${displayFormat.integer(c.contracts, lang)} contratos vinculados a ${displayFormat.integer(c.purchases_with_contracts, lang)} compras. Em ${displayFormat.integer(c.none_returned, lang)} compras, não retornou publicação. ${displayFormat.integer(c.unknown_awarded_values, lang)} compras têm valor homologado desconhecido.`,
        municipalityText:
            "A tabela mostra até 20 grupos de municípios por quantidade de compras. Valores estimados são somados uma vez por compra; as somas consideram apenas valores informados. Confira também as compras sem estimativa.",
        purchaseText: (r) =>
            `A compra ${r.control_id} tem ${(r.contracts || []).length} contratos neste snapshot. Situação da consulta: ${r.outcome || "não coberta"}. Os dados de origem estão disponíveis abaixo.`,
        caution:
            "Publicação não comprova pagamento; ausência no portal não comprova ausência de contrato.",
        examples: [
            "Resumo da cobertura",
            "Compras por município",
            "Rastrear uma compra",
            "Evolução mensal",
            "Órgãos com mais compras",
            "Qualidade dos dados",
        ],
        questions: [
            "Qual é o resumo da cobertura?",
            "Quais municípios têm mais compras no recorte?",
            "Rastreie a compra 01612601000118-1-000044/2026.",
            "Como evoluíram as compras por mês de publicação?",
            "Quais órgãos têm mais compras na base?",
            "Como está a qualidade e o preenchimento dos dados?",
        ],
        assistantBrand: "ASSISTENTE DE DADOS PÚBLICOS",
        newSession: "Nova exploração",
        sessionLabel: "NESTA SESSÃO",
        historyEmpty: "Suas perguntas aparecem aqui.",
        mobileHistoryLabel: "Perguntas desta aba",
        projectCode: "Documentação e código",
        runtimeLabel: "Consulta de dados públicos",
        workspaceName: "Área de investigação",
        workspaceData: "Compras públicas",
        scopeShort: "Piauí · Pregões eletrônicos",
        dateShort: "Ago — Out 2026",
        scopeMore: "O que há nesta base? ⓘ",
        scopeTitle: "Dados públicos com um recorte explícito.",
        scopeDetail:
            "Confira o período, a quantidade de compras e o andamento da busca de contratos na base selecionada.",
        welcomeLabel: "ANÁLISE DE COMPRAS PÚBLICAS",
        assistantTitle: "Das publicações de compras\na uma análise que você pode explicar.",
        assistantLede: "O AskTrace ajuda a preparar um panorama de compras públicas e a sustentar o que será apresentado em um relatório. Compare onde e quando as compras foram publicadas, confira registros específicos e leve os resultados com suas fontes.",
        businessLabel: "PARA QUE SERVE",
        businessScopeLabel: "Contexto e limites desta proposta",
        businessTitle: "O que analisar, o que conferir e o que apresentar",
        businessAudience: "Cenário de uso: uma pessoa responsável por acompanhar compras públicas precisa apresentar um panorama para sua equipe. Ela quer saber onde se concentram as publicações e quais informações pode usar para explicar esse panorama.",
        businessOutcome: "O AskTrace reúne comparações por órgão, município e mês, a conferência de uma compra pelo identificador do PNCP e a exportação dos resultados. Assim, você tem uma tabela para o relatório, a origem dos números e os limites que precisam acompanhar a conclusão.",
        businessExampleLabel: "Veja como isso entra em um relatório",
        businessExampleQuestion: "A pergunta da equipe",
        businessExampleQuestionText: "“Quais órgãos publicaram mais compras no período analisado?”",
        businessExampleOutput: "A entrega do aplicativo",
        businessExampleOutputText: "Um ranking de até 20 órgãos por quantidade de compras, com resumo, gráfico dos primeiros colocados e tabela exportável. As fontes e os campos não informados ficam disponíveis para conferência.",
        businessExampleDecision: "O uso na análise",
        businessExampleDecisionText: "Você pode descrever a concentração de publicações e escolher onde aprofundar a leitura. Mais publicações, por si só, não significam maior gasto ou irregularidade. Para examinar uma compra específica, informe seu ID em uma nova pergunta.",
        businessBoundary: "Uso proposto, ainda sem validação com usuários. O PNCP já oferece busca e painéis; aqui você explora um recorte histórico por perguntas, sem acompanhamento em tempo real.",
        statPurchases: "compras na base",
        statContracts: "contratos vinculados",
        statCoverage: "compras com contratos pesquisados",
        exploreLabel: "COMECE POR UMA PERGUNTA",
        suggestionHint: "Selecione, personalize e envie ↘",
        welcomeLimit:
            "Use para explorar publicações e conferir fontes. Contratos não comprovam pagamentos; valores ausentes não viram zero.",
        yourQuestion: "SUA PERGUNTA",
        thinking: "Conferindo sua pergunta e as evidências",
        composerHint:
            "Enter para enviar · Shift + Enter para nova linha · Histórico mantido nesta sessão da aba",
        privacyLabel: "Como sua pergunta é usada",
        englishNote:
            "Interface em português e inglês. As perguntas são suportadas em português.",
        independentNote:
            "O histórico sobrevive à atualização da página nesta aba. Cada pergunta é consultada de forma independente; escreva o assunto e o identificador quando necessário.",
        dataStory: "Como interpretar os dados",
        dataStorySub: "Origem, cobertura e limites",
        story1: "O que é uma compra nesta base?",
        story1text:
            "É um registro publicado no PNCP, dentro do período e da modalidade selecionados. A base não representa todas as compras do Piauí.",
        story2: "Por que há mais compras que contratos?",
        story2text:
            "A busca de contratos é uma etapa separada da coleta de compras. Algumas compras ainda não foram pesquisadas; outras não retornaram publicação. Uma compra também pode ter vários contratos.",
        story3: "O que os valores permitem concluir?",
        story3text:
            "Valores estimados e homologados descrevem etapas diferentes da compra. Eles não comprovam pagamento. Campos não informados continuam desconhecidos; as fontes acompanham a resposta.",
        storyRepo: "Consultar documentação e evidências ↗",
        footerShort: "Fonte: PNCP · Sem vínculo oficial",
        footerLocal: "Ambiente local · Sem dados em tempo real",
        cardTitles: [
            "Entender o panorama",
            "Explorar os municípios",
            "Seguir uma compra",
            "Acompanhar os meses",
            "Conhecer os órgãos",
            "Conferir lacunas",
        ],
        cardDescriptions: [
            "Quantas compras e contratos estão na base?",
            "Onde se concentram as compras do recorte?",
            "Veja contratos, valores e origem de um registro.",
            "Veja o volume por mês de publicação.",
            "Compare até 20 órgãos por quantidade de compras.",
            "Diferencie campos ausentes de valores zero.",
        ],
        followupLabel: "Continue explorando",
        localExecution: "Regras locais",
        localInsight:
            "Os números vêm do recorte consultado. Abra as fontes para conferir origem e cobertura.",
        refusalInsight:
            "Posso ajudar com contagens, municípios ou uma compra com identificador. Escolha uma sugestão para reformular sua pergunta.",
        guideLabel: "UM PERCURSO PARA PREPARAR SUA ANÁLISE",
        guide1: "1. Compare o panorama",
        guide1text: "Confira a base e pergunte quais órgãos ou municípios têm mais publicações, ou como o volume muda por mês.",
        guide2: "2. Confira um registro",
        guide2text: "Com um ID PNCP, consulte os dados da compra e seus contratos. O ranking não filtra automaticamente os registros de um órgão.",
        guide3: "3. Leve a evidência",
        guide3text: "Abra as fontes e exporte a tabela CSV ou o registro JSON. Inclua no relatório o recorte e os campos não informados.",
        datasetLabel: "Base consultada",
        coverageWarning:
            "A cobertura de contratos pode ser parcial. Compras não consultadas não significam compras sem contrato.",
        historyPrivacy:
            "Perguntas e respostas ficam no sessionStorage desta aba, sem ir ao servidor de histórico. Nova exploração limpa esses registros. Evite inserir dados pessoais.",
        storageWarning:
            "O navegador não permitiu guardar o histórico. Ele ficará apenas em memória enquanto a página estiver aberta.",
        pendingLabel: "Compras ainda sem consulta de contratos",
        errorBadge: "Consulta indisponível",
        aiUnavailable: "A IA está temporariamente indisponível",
        aiExplanation:
            "Nenhum modelo de IA pôde planejar esta pergunta agora. Os provedores estão em espera ou indisponíveis. Esta tentativa não consultou o banco, portanto não indica uma falha nos dados.",
        localRetry: "Consultar esta pergunta por regras locais →",
        localRetryHint:
            "Você pode tentar a mesma pergunta sem usar API externa. Esse modo atende panorama, municípios, meses, órgãos, qualidade e rastreio por ID; o banco local precisa estar ativo.",
        nextRetry: "Próxima tentativa de candidato após",
        retryExpired:
            "O período de espera registrado já passou. Você pode tentar a IA novamente, sujeito à disponibilidade da API.",
        retryDisclaimer:
            "Esse horário é uma espera registrada, não garantia de retorno do serviço.",
        sourcesMissing: "Nenhuma fonte foi consultada nesta tentativa.",
        notCompleted:
            "A consulta não foi concluída. Veja abaixo as opções para continuar.",
    },
    en: {
        skip: "Skip to query",
        local: "LOCAL PREVIEW",
        navMethod: "How it works",
        navAsk: "Ask a question",
        eyebrow: "PUBLIC PROCUREMENT · PNCP DATA",
        title: "One question.\nA path to the source.",
        lede: "Explore public procurement while keeping the origin of every number — and the limits of every conclusion — in view.",
        start: "Explore the dataset ↗",
        scope: "Electronic auctions · Piauí, Brazil · Published Aug–Oct 2026",
        snapshot: "VERIFIED SCOPE",
        purchases: "purchases in the original dataset",
        queried: "Purchases queried for contracts",
        contracts: "Linked contracts",
        excluded: "Excluded due to invalid source year",
        scopeNote:
            "This is a selected auction dataset. It does not cover every contract in Piauí.",
        manifest: "View scope evidence ↗",
        methodLabel: "01 / UNDERSTAND BEFORE ASKING",
        methodTitle: "A number alone does not tell the story.",
        step1: "An explicit scope",
        step1Text:
            "Procurement method, location and period accompany the answer. A sample does not become a claim about an entire state.",
        step2: "A read-only query",
        step2Text:
            "The planner selects an allowed query. Values come from PostgreSQL, without unrestricted model-generated SQL.",
        step3: "A verifiable trail",
        step3Text:
            "Coverage, identifiers, hashes and model attempts help you verify the answer and understand its limits.",
        askLabel: "02 / EXPLORE WITH EVIDENCE",
        askTitle: "What would you like to understand?",
        askIntro:
            "View the summary, compare municipalities or trace a purchase by its PNCP identifier. Questions currently support Portuguese.",
        questionLabel: "Your question (Portuguese)",
        mode: "Query mode",
        baseline: "Query without AI · local rules",
        fallback: "Ask with AI",
        privacy:
            "In AI mode, the question and query catalog are sent to configured providers. Keys and database results stay on the application server.",
        submit: "Run query ↗",
        limitsLabel: "READ THE RESULT IN CONTEXT",
        limitTitle: "Published does not mean paid.",
        limitText:
            "A published contract does not establish payment or financial execution. AskTrace does not classify fraud or calculate savings by subtracting one contract from a purchase's full budget.",
        unknown:
            "purchases with no awarded amount reported. Unknown is not zero.",
        availability:
            "Free quotas may limit AI mode. Rule-based queries remain available while the local database is running.",
        download: "Download JSON evidence ↓",
        csvExport: "Export table as CSV ↓",
        monthlyText:
            "This table groups purchases by their PNCP publication month. It is not a timeline of execution or payment. Sums use reported values only.",
        organizationsText:
            "This table shows up to 20 organizations with the most purchases. Estimates are summed once per purchase and do not represent payments.",
        qualityText:
            "This diagnostic describes field completeness across the entire dataset. Zeros are counted separately from missing amounts; counts can overlap and must not be added together.",
        responseTitle: "An answer in context",
        sources: "Data sources",
        coverageDetails: "Coverage and missing fields",
        glossaryTitle: "Query terms, explained simply",
        estimatedTerm: "Estimated amount",
        estimatedDefinition:
            "The purchase estimate reported by the source. It is not a payment and can differ from the awarded amount.",
        awardedTerm: "Awarded amount",
        awardedDefinition:
            "The amount PNCP reports for the purchase's awarded outcome. It may be missing and does not establish payment.",
        scopeTerm: "Dataset scope",
        scopeDefinition:
            "Publications selected by period, procurement method and the purchasing unit's state. This is not the whole portal.",
        publicationTerm: "No publication returned",
        publicationDefinition:
            "The search completed, but PNCP returned no published contract for that purchase. This differs from a failed or pending search.",
        trace: "Query trace",
        technical: "Complete technical record",
        repo: "Explore code, methodology and evidence on GitHub ↗",
        footer: "Independent project · Source: PNCP · Local execution",
        placeholder: "Ask about purchases in this dataset (Portuguese)…",
        waiting: "Querying and verifying evidence… AI mode may take longer.",
        ready: "Answer ready. Review the sources and limitations below.",
        sessionError:
            "Could not initialize the local session. Reload the page.",
        busy: "Another query is running. Wait and try again.",
        demoLimit: "The demo reached a shared query limit. Wait before trying again. If you were using AI, you can also try rules mode.",
        error: "Could not complete the request. Check the application connection and try again.",
        answered: "Query completed",
        refused: "Outside available queries",
        not_found_in_scope: "Not found in this scope",
        refusal:
            "This question is outside the available queries or asks for a conclusion the dataset cannot support. Try a summary, municipalities, months, organizations, data completeness or an explicit purchase ID.",
        notFound:
            "The purchase was not found in this dataset. This does not establish that it is absent from PNCP.",
        queryError:
            "The query could not finish. The trace identifies the failure point without exposing credentials.",
        coverageLabels: [
            "Dataset purchases",
            "Purchases with contracts searched",
            "Linked contracts",
            "Searched with no publication returned",
        ],
        scopeLabel: "Scope",
        reportLabel: "Coverage report",
        hashLabel: "Report hash",
        plan: "Validated plan",
        policy: "Scope filter",
        tool: "Read-only query",
        attempt: "Provider attempt",
        failure: "Failure",
        unavailable: "Not reported",
        summaryText: (c) =>
            `The dataset contains ${displayFormat.integer(c.purchases, lang)} purchases, ${displayFormat.integer(c.covered_purchases, lang)} confirmed contract queries and ${displayFormat.integer(c.contracts, lang)} contracts linked to ${displayFormat.integer(c.purchases_with_contracts, lang)} purchases. No publication was returned for ${displayFormat.integer(c.none_returned, lang)} purchases. ${displayFormat.integer(c.unknown_awarded_values, lang)} purchases have an unknown awarded amount.`,
        municipalityText:
            "The table shows up to 20 municipality groups by purchase count. Estimates are summed once per purchase; sums use reported amounts only. Also check purchases without estimates.",
        purchaseText: (r) =>
            `Purchase ${r.control_id} has ${(r.contracts || []).length} contracts in this snapshot. Query outcome: ${r.outcome || "not covered"}. Source data is shown below.`,
        caution:
            "Publication does not establish payment; no publication returned does not establish absence of a contract.",
        examples: [
            "Coverage summary",
            "Purchases by municipality",
            "Trace a purchase",
            "Monthly trend",
            "Top purchasing organizations",
            "Data completeness",
        ],
        questions: [
            "Qual é o resumo da cobertura?",
            "Quais municípios têm mais compras no recorte?",
            "Rastreie a compra 01612601000118-1-000044/2026.",
            "Como evoluíram as compras por mês de publicação?",
            "Quais órgãos têm mais compras na base?",
            "Como está a qualidade e o preenchimento dos dados?",
        ],
        assistantBrand: "PUBLIC DATA ASSISTANT",
        newSession: "New exploration",
        sessionLabel: "THIS SESSION",
        historyEmpty: "Your questions will appear here.",
        mobileHistoryLabel: "Questions in this tab",
        projectCode: "Documentation and source code",
        runtimeLabel: "Public data queries",
        workspaceName: "Investigation workspace",
        workspaceData: "Public procurement",
        scopeShort: "Piauí · Electronic auctions",
        dateShort: "Aug — Oct 2026",
        scopeMore: "What is in this dataset? ⓘ",
        scopeTitle: "Public data with an explicit scope.",
        scopeDetail:
            "Check the period, purchase count and contract search progress for the selected dataset.",
        welcomeLabel: "PUBLIC PROCUREMENT ANALYSIS",
        assistantTitle: "From procurement publications\nto an analysis you can explain.",
        assistantLede: "AskTrace helps prepare a public procurement overview and substantiate what goes into a report. Compare where and when purchases were published, inspect specific records and take the results with their sources.",
        businessLabel: "WHAT IT IS FOR",
        businessScopeLabel: "Context and limits of this proposal",
        businessTitle: "What to analyze, what to check and what to present",
        businessAudience: "Use scenario: a person monitoring public procurement needs to present an overview to their team. They want to know where publications are concentrated and what information supports that overview.",
        businessOutcome: "AskTrace brings together comparisons by organization, municipality and month, purchase lookup by PNCP identifier, and result exports. You get a table for the report, the origin of the numbers and the limitations that should accompany the conclusion.",
        businessExampleLabel: "See how this fits into a report",
        businessExampleQuestion: "The team’s question",
        businessExampleQuestionText: "“Which organizations published more purchases during the selected period?”",
        businessExampleOutput: "What the application delivers",
        businessExampleOutputText: "A ranking of up to 20 organizations by purchase count, with a summary, a chart of the leading groups and an exportable table. Sources and missing fields are available for inspection.",
        businessExampleDecision: "How to use it in an analysis",
        businessExampleDecisionText: "Describe the concentration of publications and choose where to look more closely. More publications alone do not establish higher spending or irregularities. To inspect a specific purchase, provide its ID in a new question.",
        businessBoundary: "Proposed use, not yet validated with users. PNCP already provides search and dashboards; this app lets you question a historical dataset, without real-time monitoring.",
        statPurchases: "dataset purchases",
        statContracts: "linked contracts",
        statCoverage: "purchases with contracts searched",
        exploreLabel: "START WITH A QUESTION",
        suggestionHint: "Select, customize and send ↘",
        welcomeLimit:
            "Explore publications and verify sources. Contracts do not establish payment; missing amounts are not zero.",
        yourQuestion: "YOUR QUESTION",
        thinking: "Checking your question and the evidence",
        composerHint:
            "Enter to send · Shift + Enter for a new line · History retained for this tab session",
        privacyLabel: "How your question is used",
        englishNote:
            "Portuguese and English interface. Business questions are supported in Portuguese.",
        independentNote:
            "History survives a reload in this tab. Each question is queried independently; include the subject and purchase identifier when needed.",
        dataStory: "How to interpret the data",
        dataStorySub: "Source, coverage and limitations",
        story1: "What is a purchase in this dataset?",
        story1text:
            "It is a PNCP publication within the selected period and procurement method. This dataset does not represent every purchase in Piauí.",
        story2: "Why are there more purchases than contracts?",
        story2text:
            "Searching for contracts is a separate collection step. Some purchases have not been searched yet; others returned no publication. One purchase can also have multiple contracts.",
        story3: "What do the amounts tell you?",
        story3text:
            "Estimated and awarded amounts describe different procurement stages. They do not establish payment. Unreported fields remain unknown, and each answer includes its sources.",
        storyRepo: "Read documentation and evidence ↗",
        footerShort: "Source: PNCP · No official affiliation",
        footerLocal: "Local environment · No real-time data",
        cardTitles: [
            "Understand the overview",
            "Explore municipalities",
            "Follow a purchase",
            "Follow monthly trends",
            "Explore organizations",
            "Check missing data",
        ],
        cardDescriptions: [
            "How many purchases and contracts are in the dataset?",
            "Where are purchases concentrated in this scope?",
            "See contracts, amounts and a record's provenance.",
            "See purchase volumes by publication month.",
            "Compare up to 20 organizations by purchase count.",
            "Distinguish missing fields from zero amounts.",
        ],
        followupLabel: "Keep exploring",
        localExecution: "Local rules",
        localInsight:
            "These numbers come from the queried dataset. Open the sources to verify provenance and coverage.",
        refusalInsight:
            "I can help with counts, municipality groups or a purchase identifier. Choose a suggestion to rephrase your question.",
        guideLabel: "A PATH TO PREPARING YOUR ANALYSIS",
        guide1: "1. Compare the overview",
        guide1text: "Check the dataset and ask which organizations or municipalities have more publications, or how volumes change by month.",
        guide2: "2. Check a record",
        guide2text: "Use a PNCP ID to inspect a purchase and its contracts. Rankings do not automatically filter an organization’s individual records.",
        guide3: "3. Take the evidence",
        guide3text: "Open the sources and export the CSV table or JSON record. Include the scope and unreported fields in your report.",
        datasetLabel: "Selected dataset",
        coverageWarning:
            "Contract coverage may be partial. Unqueried purchases are not purchases without contracts.",
        historyPrivacy:
            "Questions and answers are stored in this tab’s sessionStorage, without a server-side history. New exploration clears them. Avoid personal information.",
        storageWarning:
            "The browser could not save history. It will remain in memory while this page is open.",
        pendingLabel: "Purchases not yet queried for contracts",
        errorBadge: "Query unavailable",
        aiUnavailable: "AI is temporarily unavailable",
        aiExplanation:
            "No AI model could plan this question right now. Providers are cooling down or unavailable. This attempt did not query the database, so it does not indicate a data failure.",
        localRetry: "Try this question with local rules →",
        localRetryHint:
            "You can try the same question without an external API. This mode supports summaries, municipalities, months, organizations, completeness and explicit ID tracing; the local database must be running.",
        nextRetry: "Next candidate attempt after",
        retryExpired:
            "The recorded cooldown has elapsed. You may try AI again, subject to API availability.",
        retryDisclaimer:
            "This is a recorded wait, not a guaranteed service recovery time.",
        sourcesMissing: "No sources were queried in this attempt.",
        notCompleted:
            "The query did not complete. See the options below to continue.",
    },
};
const columns = {
    publication_month: ["Mês da publicação", "Publication month"],
    org_cnpj: ["CNPJ do órgão", "Organization CNPJ"],
    zero_estimates: [
        "Compras com estimativa zero",
        "Purchases with zero estimate",
    ],
    zero_awarded_values: [
        "Compras com valor homologado zero",
        "Purchases with zero awarded amount",
    ],
    unknown_municipalities: [
        "Compras com município incompleto",
        "Purchases with incomplete municipality",
    ],
    unknown_org_names: [
        "Compras sem nome de órgão",
        "Purchases without an organization name",
    ],
    municipality_ibge: ["Código IBGE", "IBGE code"],
    municipality_name: ["Município", "Municipality"],
    purchases: ["Compras", "Purchases"],
    unknown_estimates: [
        "Compras sem estimativa",
        "Purchases without estimates",
    ],
    estimated_value: ["Valor estimado (R$)", "Estimated value (BRL)"],
    unknown_awarded_values: [
        "Compras sem valor homologado",
        "Purchases without awarded amounts",
    ],
    control_id: ["ID da compra", "Purchase ID"],
    org_name: ["Órgão", "Organization"],
    publication_date: ["Publicação", "Publication"],
    awarded_value: ["Valor homologado (R$)", "Awarded value (BRL)"],
    outcome: ["Resultado da consulta", "Query outcome"],
    contracts: ["Contratos vinculados", "Linked contracts"],
    contract_id: ["ID do contrato", "Contract ID"],
    initial_value: ["Valor inicial", "Initial amount"],
    global_value: ["Valor global", "Global amount"],
    source_body_sha256: ["Hash da página original", "Original page hash"],
    source_record_index: ["Índice na fonte", "Source index"],
    contract_run_id: ["Execução de contratos", "Contract snapshot"],
    contract_pages_sha256: ["Hash composto das páginas", "Composite page hash"],
};
let lang = "pt",
    token = null,
    latest = null,
    working = false;
let publicDemo = false;
function environmentLabels() {
    if (!publicDemo) return;
    $("environment-badge").textContent = lang === "pt" ? "DEMONSTRAÇÃO" : "DEMO";
    $("environment-note").textContent = lang === "pt"
        ? "Demonstração pública · Base histórica · Sem atualização em tempo real"
        : "Public demo · Historical dataset · No real-time updates";
}
function applySessionMode(data) {
    publicDemo = data.mode === "public";
    if (Array.isArray(data.providers)) {
        $("ai-option").disabled = !data.providers.includes("fallback");
        if ($("ai-option").disabled) $("provider").value = "baseline";
    }
    environmentLabels();
}
function node(tag, value, cls) {
    const el = document.createElement(tag);
    if (value !== undefined) el.textContent = value;
    if (cls) el.className = cls;
    return el;
}
function languageBase() {
    const t = text[lang];
    document.documentElement.lang = lang === "pt" ? "pt-BR" : "en";
    document.querySelectorAll("[data-i]").forEach((el) => {
        el.textContent = t[el.dataset.i] || el.dataset.i;
    });
    document.querySelector("h1").style.whiteSpace = "pre-line";
    $("language").textContent = lang === "pt" ? "EN" : "PT";
    $("language").setAttribute(
        "aria-label",
        lang === "pt" ? "Switch to English" : "Mudar para português",
    );
    $("question").placeholder = t.placeholder;
    $("examples").replaceChildren();
    t.examples.forEach((label, i) => {
        const button = node("button", label);
        button.type = "button";
        button.addEventListener("click", () => {
            $("question").value = t.questions[i];
            count();
            $("question").focus();
        });
        $("examples").append(button);
    });
    if (latest) render(latest);
    if (working) $("status").textContent = t.waiting;
    environmentLabels();
}
function count() {
    $("count").textContent = `${$("question").value.length} / 1000`;
}
function resultCell(key, value) {
    const cell = node("td");
    if (displayFormat.numeric(key)) cell.className = "numeric-cell";
    if (key.includes("sha256") || key.endsWith("_id"))
        cell.className = "identifier-cell";
    if (key === "contracts") {
        if (!Array.isArray(value) || !value.length) {
            cell.textContent =
                lang === "pt"
                    ? "Nenhum contrato vinculado neste recorte."
                    : "No linked contracts in this dataset.";
            return cell;
        }
        const table = node("table");
        table.className = "contracts-table";
        const keys = [
            "contract_id",
            "initial_value",
            "global_value",
            "source_record_index",
        ];
        const head = node("thead"),
            header = node("tr"),
            body = node("tbody");
        keys.forEach((key) => {
            const th = node("th", columns[key][lang === "pt" ? 0 : 1]);
            th.setAttribute("scope", "col");
            if (displayFormat.numeric(key)) th.className = "numeric-cell";
            header.append(th);
        });
        head.append(header);
        value.forEach((contract) => {
            const row = node("tr");
            keys.forEach((key) => row.append(resultCell(key, contract[key])));
            body.append(row);
        });
        table.append(head, body);
        cell.append(table);
    } else cell.textContent = displayFormat.field(key, value, lang);
    return cell;
}
function renderBase(data) {
    const t = text[lang];
    $("response").hidden = false;
    $("badge").textContent = t[data.status] || data.status;
    const e = data.evidence;
    let content = t.queryError;
    if (data.status === "refused") content = t.refusal;
    else if (data.status === "not_found_in_scope") content = t.notFound;
    else if (e) {
        if (e.question === "summary") content = t.summaryText(e.coverage);
        else if (e.question === "monthly") content = t.monthlyText;
        else if (e.question === "organizations") content = t.organizationsText;
        else if (e.question === "quality") content = t.qualityText;
        else if (e.question === "municipalities") content = t.municipalityText;
        else content = t.purchaseText(e.result[0]);
        content += " " + t.caution;
    }
    $("answer").textContent = content;
    $("coverage").replaceChildren();
    $("sources").replaceChildren();
    $("result-table").replaceChildren();
    if (e) {
        const c = e.coverage;
        [
            c.purchases,
            c.covered_purchases,
            c.contracts,
            c.none_returned,
        ].forEach((n, i) => {
            const item = node("div");
            item.append(
                node(
                    "strong",
                    Number(n).toLocaleString(lang === "pt" ? "pt-BR" : "en"),
                ),
                node("span", t.coverageLabels[i]),
            );
            $("coverage").append(item);
        });
        const s = e.scope;
        const scope = node("p");
        scope.append(
            node("strong", t.scopeLabel + ": "),
            document.createTextNode(
                `${s.uf} · ${s.modality} · ${displayFormat.date(s.date_start, lang)} → ${displayFormat.date(s.date_end, lang)}`,
            ),
        );
        $("sources").append(scope);
        for (const [label, v] of [
            [t.reportLabel, e.sources.coverage_report],
            [t.hashLabel, e.coverage_report_sha256],
        ]) {
            const p = node("p");
            p.append(node("strong", label + ": "), node("span", v));
            $("sources").append(p);
        }
        const link = node("a", t.manifest);
        link.href =
            "/api/evidence?dataset=" + encodeURIComponent(selectedDataset);
        link.target = "_blank";
        link.rel = "noopener";
        $("sources").append(link);
        if (e.result.length && e.question !== "summary") {
            const table = node("table");
            if (
                ["municipalities", "monthly", "organizations"].includes(
                    e.question,
                )
            ) {
                const head = node("tr");
                const keys = Object.keys(e.result[0]);
                keys.forEach((key) => {
                    const th = node(
                        "th",
                        columns[key]?.[lang === "pt" ? 0 : 1] || key,
                    );
                    th.setAttribute("scope", "col");
                    if (displayFormat.numeric(key))
                        th.className = "numeric-cell";
                    head.append(th);
                });
                const thead = node("thead");
                thead.append(head);
                table.append(thead);
                const body = node("tbody");
                e.result.forEach((row) => {
                    const tr = node("tr");
                    keys.forEach((key) => tr.append(resultCell(key, row[key])));
                    body.append(tr);
                });
                table.append(body);
            } else {
                const body = node("tbody");
                Object.entries(e.result[0]).forEach(([key, v]) => {
                    const row = node("tr");
                    row.append(
                        node(
                            "th",
                            columns[key]?.[lang === "pt" ? 0 : 1] || key,
                        ),
                        resultCell(key, v),
                    );
                    body.append(row);
                });
                table.append(body);
            }
            const tableNames = {
                municipalities: [
                    "Compras por município",
                    "Purchases by municipality",
                ],
                monthly: [
                    "Compras por mês de publicação",
                    "Purchases by publication month",
                ],
                organizations: [
                    "Compras por órgão",
                    "Purchases by organization",
                ],
                quality: ["Qualidade dos dados", "Data completeness"],
                purchase: ["Detalhes da compra", "Purchase details"],
            };
            table.setAttribute(
                "aria-label",
                tableNames[e.question]?.[lang === "pt" ? 0 : 1] ||
                    text[lang].responseTitle,
            );
            $("result-table").setAttribute("tabindex", "0");
            $("result-table").setAttribute("role", "region");
            $("result-table").setAttribute(
                "aria-label",
                lang === "pt"
                    ? "Resultados da consulta; role para ver todas as colunas e linhas"
                    : "Query results; scroll to see all rows and columns",
            );
            $("result-table").append(
                table,
                node(
                    "p",
                    e.question === "quality"
                        ? lang === "pt"
                            ? "Contagens da base selecionada. A mesma compra pode ter mais de um campo ausente. Zero e ausência são situações diferentes."
                            : "Counts for the selected dataset. One purchase may have multiple missing fields. Zero and missing values are distinct."
                        : lang === "pt"
                          ? "Valores em reais, exibidos com duas casas decimais. O JSON preserva a precisão original. Não informado é diferente de zero."
                          : "Amounts are in Brazilian reais, displayed to two decimal places. JSON retains original precision. Not reported is different from zero.",
                    "display-note",
                ),
            );
        }
    }
    $("technical").textContent = JSON.stringify(data, null, 2);
}

let sessionHistory = [],
    activeHistory = null;
function fillQuestion(question) {
    $("question").value = question;
    count();
    $("question").focus();
    $("question").scrollIntoView({ block: "center", behavior: "smooth" });
}
function discovery() {
    const t = text[lang];
    $("discovery").replaceChildren();
    ["▤", "⌁", "◎", "↗", "▦", "◉"].forEach((icon, i) => {
        const button = node("button");
        button.type = "button";
        button.append(
            node("span", icon, "card-icon"),
            node("strong", t.cardTitles[i]),
            node("span", t.cardDescriptions[i], "card-description"),
            node("span", "↗", "card-arrow"),
        );
        button.addEventListener("click", () => fillQuestion(t.questions[i]));
        $("discovery").append(button);
    });
}
function isHistoricalResult(data, datasetId = selectedDataset) {
    const selected = datasetCatalog.find((item) => item.id === datasetId);
    const recorded = data.evidence?.coverage_report_sha256;
    return (
        typeof selected?.coverage_sha256 === "string" &&
        typeof recorded === "string" &&
        selected.coverage_sha256 !== recorded
    );
}
function historyView() {
    const entries = sessionHistory
        .filter((item) => item.dataset === selectedDataset)
        .slice()
        .reverse();
    for (const target of ["history", "mobile-history-list"]) {
        $(target).replaceChildren();
        if (!entries.length) {
            $(target).append(node("p", text[lang].historyEmpty));
            continue;
        }
        entries.forEach((item) => {
            const button = node("button", item.data.question);
            button.type = "button";
            button.title = item.data.question;
            if (isHistoricalResult(item.data, item.dataset)) {
                button.textContent +=
                    lang === "pt" ? " · base anterior" : " · earlier dataset";
                button.title +=
                    lang === "pt"
                        ? " — Resultado salvo antes da atualização da base"
                        : " — Result saved before the dataset update";
            }
            if (item.id === activeHistory) button.classList.add("active");
            button.addEventListener("click", () => {
                if (working) return;
                activeHistory = item.id;
                latest = item.data;
                render(latest);
                historyView();
                $("mobile-history").open = false;
                if (target === "mobile-history-list")
                    $("response").scrollIntoView({
                        block: "start",
                        behavior: matchMedia("(prefers-reduced-motion: reduce)")
                            .matches
                            ? "instant"
                            : "smooth",
                    });
            });
            $(target).append(button);
        });
    }
}
function languageAssistant() {
    languageBase();
    discovery();
    historyView();
    $("submit").setAttribute(
        "aria-label",
        lang === "pt" ? "Enviar pergunta" : "Send question",
    );
    $("mobile-reset").setAttribute("aria-label", text[lang].newSession);
    $("new-session").setAttribute("aria-label", text[lang].newSession);
}
function renderAssistant(data) {
    renderBase(data);
    document.body.classList.add("has-result");
    $("conversation").hidden = false;
    $("thinking").hidden = true;
    $("asked-question").textContent = data.question;
    const selected = data.selected_provider;
    $("execution-meta").textContent = selected
        ? selected.model
        : data.provider === "baseline"
          ? text[lang].localExecution
          : data.provider;
    $("insight").hidden = false;
    let insight =
        data.status === "refused"
            ? text[lang].refusalInsight
            : text[lang].localInsight;
    if (data.status === "error") insight = text[lang].queryError;
    $("insight").textContent = insight;
    $("next-questions").replaceChildren();
    const t = text[lang];
    const action = data.evidence?.question;
    const indices =
        action === "summary"
            ? [1, 2]
            : action === "municipalities"
              ? [2, 0]
              : action === "monthly"
                ? [4, 5]
                : action === "organizations"
                  ? [3, 5]
                  : action === "quality"
                    ? [3, 1]
                    : [0, 1];
    indices.forEach((i) => {
        const button = node("button", t.examples[i] + " ↗");
        button.type = "button";
        button.addEventListener("click", () => fillQuestion(t.questions[i]));
        $("next-questions").append(button);
    });
}
$("question").addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
        event.preventDefault();
        if (!working && token && $("question").value.trim())
            $("ask-form").requestSubmit();
    }
});
$("new-session").addEventListener("click", () => {
    if (working) return;
    sessionHistory = [];
    $("mobile-history").open = false;
    activeHistory = null;
    latest = null;
    $("question").value = "";
    count();
    $("status").textContent = "";
    $("response").hidden = true;
    $("conversation").hidden = true;
    document.body.classList.remove("has-result");
    historyView();
    $("question").focus();
    showAvailability(serviceAvailability);
    persistSession();
});

let datasetCatalog = [],
    selectedDataset = "original";
const SESSION_KEY = "asktrace.session.v1";
function persistSession() {
    try {
        sessionStorage.setItem(
            SESSION_KEY,
            JSON.stringify({
                version: 1,
                dataset: selectedDataset,
                language: lang,
                entries: sessionHistory.slice(-20),
            }),
        );
        $("storage-note").textContent = "";
    } catch (_) {
        $("storage-note").textContent = text[lang].storageWarning;
    }
}
function validStoredResult(data) {
    if (
        !data ||
        typeof data.question !== "string" ||
        data.question.length > 1000 ||
        !["answered", "refused", "error", "not_found_in_scope"].includes(
            data.status,
        ) ||
        !Array.isArray(data.trace) ||
        !data.trace.every(
            (step) =>
                step &&
                typeof step === "object" &&
                (step.step !== "plan" || typeof step.plan?.action === "string"),
        )
    )
        return false;
    const e = data.evidence;
    if (!e) return data.status !== "answered";
    return (
        [
            "summary",
            "municipalities",
            "monthly",
            "organizations",
            "quality",
            "purchase",
        ].includes(e.question) &&
        e.coverage &&
        [
            "purchases",
            "covered_purchases",
            "contracts",
            "none_returned",
            "unknown_awarded_values",
        ].every((key) => Number.isFinite(e.coverage[key])) &&
        e.scope &&
        ["uf", "date_start", "date_end"].every(
            (key) => typeof e.scope[key] === "string",
        ) &&
        typeof e.sources?.coverage_report === "string" &&
        Array.isArray(e.result) &&
        e.result.every(
            (row) => row && typeof row === "object" && !Array.isArray(row),
        ) &&
        (e.question !== "purchase" ||
            data.status !== "answered" ||
            e.result.length > 0)
    );
}
function readSession() {
    try {
        const raw = sessionStorage.getItem(SESSION_KEY);
        if (!raw || raw.length > 1500000) return null;
        const saved = JSON.parse(raw);
        if (!saved || saved.version !== 1 || !Array.isArray(saved.entries))
            return null;
        saved.entries = saved.entries
            .filter(
                (item) =>
                    item &&
                    typeof item.id === "string" &&
                    typeof item.dataset === "string" &&
                    validStoredResult(item.data),
            )
            .slice(-20);
        return saved;
    } catch (_) {
        return null;
    }
}
function applyDataset() {
    const d = datasetCatalog.find((item) => item.id === selectedDataset);
    if (!d) return;
    const nf = new Intl.NumberFormat(lang === "pt" ? "pt-BR" : "en");
    $("stat-purchases").textContent = nf.format(d.purchases);
    $("stat-contracts").textContent = nf.format(d.contracts);
    $("stat-covered").textContent = nf.format(d.covered);
    Array.from($("dataset").children).forEach((option, index) => {
        const item = datasetCatalog[index];
        if (item)
            option.textContent = `${displayFormat.date(item.start, lang)} → ${displayFormat.date(item.end, lang)}`;
    });
    if (d.example_purchase_id) {
        for (const language of ["pt", "en"])
            text[language].questions[2] =
                `Rastreie a compra ${d.example_purchase_id}.`;
    }
    const consolidated = d.coverage_finished_at;
    $("dataset-updated").textContent = consolidated
        ? (lang === "pt"
              ? "Cobertura consolidada em "
              : "Coverage consolidated on ") +
          displayFormat.timestamp(consolidated, lang)
        : "";
    const dates = `${displayFormat.date(d.start, lang)} → ${displayFormat.date(d.end, lang)}`;
    document
        .querySelectorAll("[data-i='dateShort']")
        .forEach((el) => (el.textContent = dates));
    $("scope-detail-live").textContent =
        lang === "pt"
            ? `Pregões eletrônicos de unidades do Piauí. Publicação: ${dates}. ${displayFormat.integer(d.purchases, lang)} compras; ${displayFormat.integer(d.covered, lang)} com consulta de contratos confirmada, ${displayFormat.integer(d.purchases - d.covered - d.excluded, lang)} ainda não consultadas e ${displayFormat.integer(d.excluded, lang)} exclusão(ões) por localizador inválido.`
            : `Electronic auctions from units in Piauí. Published: ${dates}. ${displayFormat.integer(d.purchases, lang)} purchases; ${displayFormat.integer(d.covered, lang)} with confirmed contract queries, ${displayFormat.integer(d.purchases - d.covered - d.excluded, lang)} still unqueried and ${displayFormat.integer(d.excluded, lang)} exclusion(s) due to invalid source locators.`;
    $("base-evidence").href =
        "/api/evidence?dataset=" + encodeURIComponent(selectedDataset);
}
function initializeDatasets(session) {
    datasetCatalog = session.datasets || [];
    const saved = readSession();
    selectedDataset =
        saved && datasetCatalog.some((d) => d.id === saved.dataset)
            ? saved.dataset
            : session.default_dataset || "original";
    if (saved) {
        lang = saved.language === "en" ? "en" : "pt";
        sessionHistory = saved.entries;
    }
    $("dataset").replaceChildren();
    datasetCatalog.forEach((item) => {
        const option = node(
            "option",
            `${displayFormat.date(item.start, lang)} → ${displayFormat.date(item.end, lang)}`,
        );
        option.value = item.id;
        $("dataset").append(option);
    });
    $("dataset").value = selectedDataset;
    language();
    const last = sessionHistory
        .filter(
            (item) =>
                item.dataset === selectedDataset &&
                item.data.status !== "error" &&
                !isHistoricalResult(item.data, item.dataset),
        )
        .at(-1);
    if (last) {
        try {
            activeHistory = last.id;
            latest = last.data;
            render(latest);
            historyView();
        } catch (_) {
            latest = null;
            $("response").hidden = true;
        }
    }
    applyDataset();
}
function coverageBreakdown(data) {
    const c = data.evidence.coverage;
    const selected = datasetCatalog.find((item) => item.id === selectedDataset);
    const matches =
        selected &&
        selected.coverage === data.evidence.sources.coverage_report &&
        selected.purchases === c.purchases &&
        selected.covered === c.covered_purchases &&
        selected.start === data.evidence.scope.date_start &&
        selected.end === data.evidence.scope.date_end;
    const remaining = c.purchases - c.covered_purchases;
    const excluded =
        matches &&
        Number.isSafeInteger(selected.excluded) &&
        selected.excluded >= 0 &&
        selected.excluded <= remaining
            ? selected.excluded
            : null;
    return {
        remaining,
        excluded,
        pending: excluded === null ? null : remaining - excluded,
    };
}
function renderDataset(data) {
    renderAssistant(data);
    if (!data.evidence) return;
    const c = data.evidence.coverage,
        b = coverageBreakdown(data);
    const n = (value) => displayFormat.integer(value, lang);
    const pt = lang === "pt";
    const insight = $("insight");
    insight.replaceChildren();
    insight.append(
        node(
            "strong",
            pt
                ? "O que já foi pesquisado nesta base"
                : "What has already been searched in this dataset",
        ),
    );
    const list = node("ul");
    list.append(
        node(
            "li",
            pt
                ? `Já pesquisamos contratos de ${n(c.covered_purchases)} das ${n(c.purchases)} compras. Essa é uma etapa da coleta de dados, não a quantidade de perguntas feitas aqui.`
                : `Contracts have been searched for ${n(c.covered_purchases)} of ${n(c.purchases)} purchases. This is a data collection step, not the number of questions asked here.`,
        ),
    );
    if (b.pending !== null) {
        list.append(
            node(
                "li",
                b.pending === 0
                    ? pt
                        ? "Todas as compras aptas já passaram pela busca de contratos."
                        : "All eligible purchases have been searched for contracts."
                    : pt
                      ? `Ainda falta pesquisar contratos de ${n(b.pending)} compras.`
                      : `Contract searches are still pending for ${n(b.pending)} purchases.`,
            ),
        );
        if (b.excluded > 0)
            list.append(
                node(
                    "li",
                    pt
                        ? b.excluded === 1
                            ? "Uma compra não pôde ser pesquisada porque o ano informado na fonte é inválido."
                            : `${n(b.excluded)} compras não puderam ser pesquisadas porque o ano informado na fonte é inválido.`
                        : b.excluded === 1
                          ? "One purchase could not be searched because its source year is invalid."
                          : `${n(b.excluded)} purchases could not be searched because their source year is invalid.`,
                ),
            );
    } else
        list.append(
            node(
                "li",
                pt
                    ? `${n(b.remaining)} compras ainda não têm busca de contratos concluída. Esta resposta não informa quantas estão pendentes ou foram excluídas.`
                    : `${n(b.remaining)} purchases have no completed contract search. This response does not distinguish pending searches from exclusions.`,
            ),
        );
    list.append(
        node(
            "li",
            pt
                ? `Em ${n(c.none_returned)} compras pesquisadas, o PNCP não retornou publicação de contrato. Isso não comprova que não exista contrato.`
                : `For ${n(c.none_returned)} searched purchases, PNCP returned no contract publication. This does not establish that no contract exists.`,
        ),
    );
    list.append(
        node(
            "li",
            pt
                ? `A fonte não informou o valor homologado de ${n(c.unknown_awarded_values)} compras. Ausência de valor não significa zero nem comprova pagamento.`
                : `The source did not report awarded amounts for ${n(c.unknown_awarded_values)} purchases. Missing amounts do not mean zero or establish payment.`,
        ),
    );
    insight.append(list);
    if (b.pending !== null) {
        const rows = [
            [c.purchases, pt ? "Compras na base" : "Dataset purchases"],
            [
                c.covered_purchases,
                pt
                    ? "Compras com contratos pesquisados"
                    : "Purchases with contracts searched",
            ],
            [
                b.pending,
                pt
                    ? "Compras ainda não pesquisadas"
                    : "Purchases not yet searched",
            ],
            [c.contracts, pt ? "Contratos encontrados" : "Contracts found"],
            [
                c.none_returned,
                pt
                    ? "Pesquisadas sem publicação retornada"
                    : "Searched with no publication returned",
            ],
            [
                b.excluded,
                pt
                    ? "Compras excluídas da busca"
                    : "Purchases excluded from searches",
            ],
        ];
        $("coverage").replaceChildren();
        rows.forEach(([count, label]) => {
            const card = node("div");
            card.append(node("strong", n(count)), node("span", label));
            $("coverage").append(card);
        });
    }
}
$("dataset").addEventListener("change", () => {
    if (working) {
        $("dataset").value = selectedDataset;
        return;
    }
    selectedDataset = $("dataset").value;
    latest = null;
    activeHistory = null;
    $("response").hidden = true;
    $("conversation").hidden = true;
    document.body.classList.remove("has-result");
    $("status").textContent = "";
    historyView();
    applyDataset();
    showAvailability(serviceAvailability);
    persistSession();
});

function readableTrace(data) {
    const t = text[lang];
    $("trace").replaceChildren();
    for (const step of data.trace || []) {
        if (step.step === "provider_attempt" && step.reason === "disabled")
            continue;
        let line = "";
        const name = step.provider || step.candidate || "IA";
        if (step.step === "provider_attempt") {
            if (step.reason === "cooldown")
                line =
                    lang === "pt"
                        ? `${name}: aguardando o período de espera registrado pela aplicação.`
                        : `${name}: waiting for the recorded cooldown.`;
            else if (step.reason === "missing_key")
                line =
                    lang === "pt"
                        ? `${name}: chave não configurada neste ambiente.`
                        : `${name}: key not configured in this environment.`;
            else if (step.outcome === "selected")
                line =
                    lang === "pt"
                        ? `${name}: modelo selecionado para planejar a consulta.`
                        : `${name}: model selected to plan the query.`;
            else
                line =
                    lang === "pt"
                        ? `${name}: tentativa indisponível${step.http_status ? " (HTTP " + step.http_status + ")" : ""}.`
                        : `${name}: attempt unavailable${step.http_status ? " (HTTP " + step.http_status + ")" : ""}.`;
        } else if (step.step === "plan")
            line =
                lang === "pt"
                    ? `Plano validado: ${step.plan.action}.`
                    : `Validated plan: ${step.plan.action}.`;
        else if (step.step === "policy")
            line =
                lang === "pt"
                    ? "A pergunta não passou pelo filtro de escopo; nenhum modelo foi chamado."
                    : "The question was stopped by the scope filter; no model was called.";
        else if (step.step === "read_only_query")
            line =
                lang === "pt"
                    ? "Consulta somente leitura executada com as fontes do recorte selecionado."
                    : "Read-only query executed against the selected dataset.";
        else if (step.step === "failure")
            line =
                lang === "pt"
                    ? "A execução foi encerrada sem produzir uma resposta de dados."
                    : "Execution ended without producing a data answer.";
        if (line) $("trace").append(node("li", line));
    }
}
function render(data) {
    renderPresentation(data);
    const historical = isHistoricalResult(data);
    $("result-freshness").hidden = !historical;
    $("result-freshness").textContent = historical
        ? lang === "pt"
            ? "Resultado salvo de uma versão anterior da base. Os números abaixo preservam aquela consulta. Envie uma nova pergunta para consultar a cobertura atual."
            : "Saved result from an earlier dataset version. The numbers below preserve that query. Ask a new question to use the current coverage."
        : "";
    $("download-csv").hidden =
        data.status !== "answered" || !data.evidence?.result?.length;
    renderDataset(data);
    const explanation = resultPresentation.build(data, lang);
    if (explanation.lead)
        $("answer").textContent = explanation.lead + " " + text[lang].caution;
    showAvailability(serviceAvailability);
    readableTrace(data);
    const t = text[lang];
    const events = (data.trace || []).filter(
        (step) => step.step === "provider_attempt",
    );
    const providerError =
        data.status === "error" &&
        data.tool_calls === 0 &&
        (data.availability?.component === "ai_planner" || events.length > 0);
    $("source-panel").hidden = !data.evidence;
    $("coverage-details").hidden = !data.evidence;
    $("coverage").hidden = !data.evidence;
    $("recovery-actions").hidden = !providerError;
    $("recovery-actions").replaceChildren();
    if (data.status === "error") $("badge").textContent = t.errorBadge;
    if (providerError) {
        $("badge").textContent = t.aiUnavailable;
        $("answer").textContent = t.aiExplanation;
        $("execution-meta").textContent = "";
        $("insight").textContent = t.localRetryHint;
        $("next-questions").replaceChildren();
        const retry = node("button", t.localRetry);
        retry.type = "button";
        retry.addEventListener("click", () => {
            if (working) return;
            $("provider").value = "baseline";
            $("question").value = data.question;
            count();
            $("ask-form").requestSubmit();
        });
        $("recovery-actions").append(retry);
        const waits = events
            .filter(
                (event) =>
                    event.reason === "cooldown" &&
                    Number.isFinite(event.not_before_epoch),
            )
            .map((event) => event.not_before_epoch);
        const at =
            data.availability?.next_candidate_retry_epoch || Math.min(...waits);
        if (Number.isFinite(at)) {
            const message =
                at * 1000 > Date.now()
                    ? t.nextRetry +
                      " " +
                      new Date(at * 1000).toLocaleString(
                          lang === "pt" ? "pt-BR" : "en",
                      ) +
                      ". " +
                      t.retryDisclaimer
                    : t.retryExpired;
            $("recovery-actions").append(node("p", message));
        }
    }
}

let serviceAvailability = null;
function showAvailability(info) {
    serviceAvailability = info;
    // Shared server state is not a failed question in this tab. Show the notice only
    // beside a failed AI attempt, never on the welcome screen or in local mode.
    const failed =
        latest?.status === "error" &&
        latest?.availability?.component === "ai_planner";
    $("availability-notice").hidden = !(
        failed &&
        $("provider").value === "fallback" &&
        info?.can_attempt_ai === false
    );
    $("availability-text").textContent =
        lang === "pt"
            ? "A aplicação registra esperas de tentativas anteriores, compartilhadas entre sessões. Isso não significa que você tenha feito uma pergunta agora. Você pode tentar regras locais; o banco precisa estar ativo."
            : "The application retains cooldowns from previous attempts, shared across sessions. This does not mean you just asked a question. You can try local rules; the database must be running.";
    $("choose-local").textContent =
        lang === "pt" ? "Usar regras locais" : "Use local rules";
    $("refresh-availability").textContent =
        lang === "pt" ? "Atualizar disponibilidade" : "Refresh availability";
}
function language() {
    languageAssistant();
    applyDataset();
    showAvailability(serviceAvailability);
}
$("provider").addEventListener("change", () =>
    showAvailability(serviceAvailability),
);
$("choose-local").addEventListener("click", () => {
    if (working) return;
    $("provider").value = "baseline";
    showAvailability(serviceAvailability);
    $("question").focus();
});
$("refresh-availability").addEventListener("click", async () => {
    const button = $("refresh-availability");
    button.disabled = true;
    try {
        const response = await fetch("/api/availability");
        if (!response.ok) throw new Error("availability_unavailable");
        showAvailability(await response.json());
        $("status").textContent =
            lang === "pt"
                ? "Estado local atualizado. Nenhuma pergunta foi enviada."
                : "Local status refreshed. No question was sent.";
    } catch (_) {
        $("status").textContent =
            lang === "pt"
                ? "Não foi possível atualizar a disponibilidade. Sua pergunta não foi enviada. Tente novamente."
                : "Could not refresh availability. Your question was not sent. Please try again.";
    } finally {
        button.disabled = false;
    }
});
$("language").addEventListener("click", () => {
    lang = lang === "pt" ? "en" : "pt";
    language();
    persistSession();
});
$("question").addEventListener("input", count);
$("download").addEventListener("click", () => {
    if (!latest) return;
    const url = URL.createObjectURL(
        new Blob([JSON.stringify(latest, null, 2)], {
            type: "application/json",
        }),
    );
    const a = node("a");
    a.href = url;
    a.download = "asktrace-response.json";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
});
$("ask-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (working || !token) return;
    working = true;
    latest = null;
    showAvailability(serviceAvailability);
    document.body.classList.add("has-result");
    $("conversation").hidden = false;
    $("asked-question").textContent = $("question").value;
    $("thinking").hidden = false;
    $("response").hidden = true;
    $("submit").disabled = true;
    $("status").textContent = text[lang].waiting;
    try {
        const response = await fetch("/api/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-AskTrace-Token": token,
            },
            body: JSON.stringify({
                question: $("question").value,
                provider: $("provider").value,
                dataset: selectedDataset,
            }),
        });
        if (!response.ok) {
            const failure = await response.json().catch(() => ({}));
            throw new Error(failure.error === "demo_limit" ? "demoLimit"
                : failure.error === "ai_disabled" ? "aiUnavailable"
                : response.status === 429 ? "busy" : "error");
        }
        latest = await response.json();
        activeHistory = Date.now() + "-" + sessionHistory.length;
        sessionHistory.push({
            id: activeHistory,
            dataset: selectedDataset,
            data: latest,
        });
        if (sessionHistory.length > 20) sessionHistory.shift();
        render(latest);
        historyView();
        persistSession();
        $("status").textContent =
            latest.status === "error"
                ? text[lang].notCompleted
                : text[lang].ready;
        $("response").scrollIntoView({
            behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
                ? "instant"
                : "smooth",
            block: "start",
        });
    } catch (error) {
        $("status").textContent = text[lang][error.message] || text[lang].error;
    } finally {
        working = false;
        $("thinking").hidden = true;
        $("submit").disabled = false;
    }
});
$("mobile-reset").addEventListener("click", () => $("new-session").click());
language();
$("submit").disabled = true;
fetch("/api/session")
    .then((r) => {
        if (!r.ok) throw new Error();
        return r.json();
    })
    .then((data) => {
        token = data.token;
        applySessionMode(data);
        initializeDatasets(data);
        showAvailability(data.availability);
        $("submit").disabled = false;
    })
    .catch(() => {
        $("status").textContent = text[lang].sessionError;
    });

$("download-csv").addEventListener("click", () => {
    if (!latest?.evidence?.result?.length || latest.status !== "answered")
        return;
    const e = latest.evidence;
    const rows = e.result.map((row) => ({
        query: e.question,
        scope_uf: e.scope.uf,
        scope_start: e.scope.date_start,
        scope_end: e.scope.date_end,
        coverage_report_sha256: e.coverage_report_sha256,
        ...row,
    }));
    const url = URL.createObjectURL(
        new Blob([displayFormat.csv(rows)], { type: "text/csv;charset=utf-8" }),
    );
    const link = node("a");
    link.href = url;
    link.download = `asktrace-${e.question}.csv`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 100);
});

function renderPresentation(data) {
    const p = resultPresentation.build(data, lang);
    $("result-highlights").replaceChildren();
    $("result-highlights").hidden = !p.metrics.length;
    p.metrics.forEach((item) => {
        const card = node("div");
        card.append(node("strong", item.value), node("span", item.label));
        $("result-highlights").append(card);
    });
    $("result-chart").hidden = !p.chart;
    $("chart-bars").replaceChildren();
    if (p.chart) {
        $("chart-title").textContent = p.chart.title;
        $("chart-note").textContent = p.chart.note;
        const max = Math.max(0, ...p.chart.items.map((item) => item.count));
        p.chart.items.forEach((item) => {
            const row = node("li"),
                label = node("span", item.label, "bar-label"),
                track = node("span", undefined, "bar-track"),
                bar = node("span", undefined, "bar-fill"),
                number = node(
                    "strong",
                    displayFormat.integer(item.count, lang),
                    "bar-value",
                );
            label.title = item.label;
            track.setAttribute("aria-hidden", "true");
            bar.style.width = (max ? (100 * item.count) / max : 0) + "%";
            track.append(bar);
            row.append(label, track, number);
            $("chart-bars").append(row);
        });
    }
    const e = data.evidence;
    $("table-details").hidden = !e?.result?.length || e.question === "summary";
    $("table-details").open = !p.chart;
    $("table-summary").textContent =
        (lang === "pt" ? "Ver tabela completa" : "View complete table") +
        (e?.result?.length
            ? ` · ${displayFormat.integer(e.result.length, lang)} ${lang === "pt" ? "linha(s)" : "row(s)"}`
            : "");
    $("coverage-details").open = e?.question === "summary";
}
