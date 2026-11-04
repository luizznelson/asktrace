// DOM contract tests in Node. No browser or layout simulation is claimed.
const fs = require("node:fs"),
    vm = require("node:vm"),
    assert = require("node:assert/strict");
class Element {
    constructor(tag = "div") {
        this.tagName = tag;
        this.children = [];
        this.events = {};
        this.dataset = {};
        this.value = "";
        this.hidden = false;
        this.style = {};
        this.classList = { add() {}, remove() {} };
        this.textContent = "";
    }
    append(...items) {
        this.children.push(...items);
    }
    replaceChildren(...items) {
        this.children = items;
    }
    addEventListener(name, fn) {
        (this.events[name] ??= []).push(fn);
    }
    setAttribute() {}
    focus() {}
    scrollIntoView() {}
    click() {
        for (const fn of this.events.click || []) fn();
    }
    requestSubmit() {
        return Promise.all(
            (this.events.submit || []).map((fn) => fn({ preventDefault() {} })),
        );
    }
}
const elements = new Map(),
    get = (id) => {
        if (!elements.has(id)) elements.set(id, new Element());
        return elements.get(id);
    };
const html = fs.readFileSync("web/index.html", "utf8");
for (const match of html.matchAll(/id="([^"]+)"/g)) get(match[1]);
get("provider").value = "fallback";
const localized = [];
for (const match of html.matchAll(/data-i="([^"]+)"/g)) {
    const el = new Element();
    el.dataset.i = match[1];
    localized.push(el);
}
const store = new Map();
const storage = {
    getItem: (key) => store.get(key) || null,
    setItem: (key, value) => store.set(key, value),
    removeItem: (key) => store.delete(key),
};
const datasets = [
    {
        id: "original",
        coverage: "runs/fixed.json",
        start: "2026-08-01",
        end: "2026-10-31",
        purchases: 1081,
        covered: 1080,
        contracts: 125,
        unknown_awarded: 749,
        excluded: 1,
    },
];
let requests = [];
const result = {
    question: "Qual é o resumo da cobertura?",
    provider: "fallback",
    status: "answered",
    selected_provider: { model: "qwen/test" },
    trace: [{ step: "plan", plan: { action: "summary" } }],
    evidence: {
        question: "summary",
        coverage: {
            purchases: 1081,
            covered_purchases: 1080,
            contracts: 125,
            purchases_with_contracts: 85,
            none_returned: 995,
            unknown_awarded_values: 749,
        },
        scope: {
            uf: "PI",
            modality: 6,
            date_start: "2026-08-01",
            date_end: "2026-10-31",
        },
        sources: { coverage_report: "runs/fixed.json" },
        coverage_report_sha256: "a".repeat(64),
        result: [],
    },
};
const context = {
    document: {
        getElementById: get,
        querySelectorAll: (selector) =>
            selector === "[data-i]"
                ? localized
                : selector.includes("dateShort")
                  ? localized.filter((el) => el.dataset.i === "dateShort")
                  : [],
        querySelector: () => get("h1"),
        createElement: (tag) => new Element(tag),
        createTextNode: (s) => s,
        documentElement: {},
        body: new Element(),
    },
    fetch: async (url, options) => {
        requests.push({ url, options });
        return {
            ok: true,
            json: async () =>
                url === "/api/session"
                    ? {
                          token: "test-session-token",
                          datasets,
                          default_dataset: "original",
                      }
                    : structuredClone(result),
        };
    },
    URL: { createObjectURL: () => "", revokeObjectURL() {} },
    Blob,
    matchMedia: () => ({ matches: true }),
    setTimeout: () => {},
    Date,
    console,
    sessionStorage: storage,
    Intl,
};
vm.createContext(context);
vm.runInContext(fs.readFileSync("web/formatters.js", "utf8"), context);
vm.runInContext(fs.readFileSync("web/app.js", "utf8"), context);
(async () => {
    await new Promise((resolve) => setImmediate(resolve));
    assert.equal(get("discovery").children.length, 6);
    assert.equal(get("submit").disabled, false);
    assert.equal(
        localized.filter((el) => el.textContent === el.dataset.i).length,
        0,
        "Every displayed label has a translation",
    );
    get("discovery").children[0].click();
    assert.match(get("question").value, /cobertura/);
    await get("ask-form").requestSubmit();
    assert.equal(requests.filter((r) => r.url === "/api/ask").length, 1);
    assert.equal(get("asked-question").textContent, result.question);
    assert.match(get("answer").textContent, /125/);
    assert.equal(get("next-questions").children.length, 2);
    assert.equal(get("history").children.length, 1);
    assert.equal(get("thinking").hidden, true);
    assert.equal(get("submit").disabled, false);
    get("language").click();
    assert.match(get("answer").textContent, /dataset/);
    assert.equal(context.document.documentElement.lang, "en");
    get("next-questions").children[0].click();
    assert.match(get("question").value, /municípios/);
    get("history").children[0].click();
    assert.match(get("answer").textContent, /125/);
    const saved = JSON.parse(store.get("asktrace.session.v1"));
    assert.equal(saved.entries.length, 1);
    assert.equal(saved.entries[0].dataset, "original");
    const before = requests.length;
    vm.runInContext(
        "sessionHistory=[];latest=null;initializeDatasets({datasets:" +
            JSON.stringify(datasets) +
            ",default_dataset:'original'})",
        context,
    );
    assert.equal(get("history").children.length, 1);
    assert.match(get("answer").textContent, /125/);
    assert.equal(
        requests.length,
        before,
        "Restoring history makes no API request",
    );
    const priorRequests = requests.filter((r) => r.url === "/api/ask").length;
    vm.runInContext(
        'render({question:"Resumo da cobertura",provider:"fallback",status:"error",tool_calls:0,llm_attempts:0,trace:[{step:"provider_attempt",candidate:"groq-qwen",reason:"cooldown",not_before_epoch:2100000000}]})',
        context,
    );
    assert.equal(get("source-panel").hidden, true);
    assert.equal(get("coverage").hidden, true);
    assert.equal(get("recovery-actions").hidden, false);
    assert.match(get("answer").textContent, /did not query the database/);
    assert.equal(
        requests.filter((r) => r.url === "/api/ask").length,
        priorRequests,
        "Rendering cooldown must not silently retry",
    );
    get("recovery-actions").children[0].click();
    await new Promise((resolve) => setImmediate(resolve));
    assert.equal(
        JSON.parse(
            requests.filter((r) => r.url === "/api/ask").at(-1).options.body,
        ).provider,
        "baseline",
    );
    assert.equal(get("source-panel").hidden, false);
    assert.equal(get("recovery-actions").hidden, true);
    const requestCount = requests.length;
    vm.runInContext(
        "showAvailability({can_attempt_ai:false,candidates:[]})",
        context,
    );
    assert.equal(
        get("availability-notice").hidden,
        true,
        "Welcome/success is not a failed question",
    );
    vm.runInContext(
        'latest={question:"Resumo",status:"error",availability:{component:"ai_planner"}};$("provider").value="fallback";showAvailability(serviceAvailability)',
        context,
    );
    assert.equal(get("availability-notice").hidden, false);
    assert.match(
        get("availability-text").textContent,
        /shared across sessions/,
    );
    get("choose-local").click();
    assert.equal(
        get("availability-notice").hidden,
        true,
        "Local mode must not display AI error",
    );
    assert.equal(get("provider").value, "baseline");
    assert.equal(requests.length, requestCount);
    vm.runInContext(
        "showAvailability({can_attempt_ai:true,candidates:[]})",
        context,
    );
    assert.equal(get("availability-notice").hidden, true);
    get("new-session").click();
    assert.equal(get("question").value, "");
    assert.equal(get("conversation").hidden, true);
    assert.equal(
        get("history").children[0].textContent,
        "Your questions will appear here.",
    );
    assert.equal(
        JSON.parse(store.get("asktrace.session.v1")).entries.length,
        0,
    );
    store.set("asktrace.session.v1", "not-json");
    assert.equal(vm.runInContext("readSession()", context), null);
    store.set(
        "asktrace.session.v1",
        JSON.stringify({ version: 999, entries: [] }),
    );
    assert.equal(vm.runInContext("readSession()", context), null);
    store.set(
        "asktrace.session.v1",
        JSON.stringify({
            version: 1,
            entries: [
                {
                    id: "bad",
                    dataset: "original",
                    data: {
                        question: "Resumo",
                        status: "answered",
                        trace: [],
                        evidence: {},
                    },
                },
            ],
        }),
    );
    assert.equal(
        vm.runInContext("readSession().entries.length", context),
        0,
        "Corrupt evidence is not restored",
    );
    assert.equal(
        vm.runInContext(
            'validStoredResult({question:"Resumo",status:"error",trace:[{step:"plan"}]})',
            context,
        ),
        false,
    );
    const savedFetch = context.fetch;
    context.fetch = async () => {
        throw new Error("offline");
    };
    await get("refresh-availability").events.click[0]();
    assert.equal(get("refresh-availability").disabled, false);
    assert.match(get("status").textContent, /question was not sent/);
    context.fetch = savedFetch;
    vm.runInContext(
        "latest=null;showAvailability({can_attempt_ai:false})",
        context,
    );
    assert.equal(
        get("availability-notice").hidden,
        true,
        "Fresh welcome must not display shared cooldown as an error",
    );
    const formattedResult = structuredClone(result);
    formattedResult.evidence.question = "municipalities";
    formattedResult.evidence.result = [
        {
            municipality_ibge: "2211001",
            municipality_name: "Teresina",
            purchases: 2537,
            unknown_estimates: 0,
            estimated_value: "1571718049.25000000",
            unknown_awarded_values: 187,
        },
        {
            municipality_ibge: "2209104",
            municipality_name: "Santa Cruz do Piauí",
            purchases: 55,
            unknown_estimates: 1,
            estimated_value: null,
            unknown_awarded_values: 4,
        },
    ];
    context.formattedResult = formattedResult;
    const originalJSON = JSON.stringify(formattedResult);
    vm.runInContext('lang="pt";latest=formattedResult;render(latest)', context);
    let rows = get("result-table").children[0].children[1].children;
    assert.equal(rows[0].children[0].textContent, "2211001");
    assert.equal(rows[0].children[2].textContent, "2.537");
    assert.equal(
        rows[0].children[4].textContent.replaceAll("\u00a0", " "),
        "R$ 1.571.718.049,25",
    );
    assert.equal(rows[0].children[4].className, "numeric-cell");
    assert.equal(rows[1].children[4].textContent, "Não informado");
    get("language").click();
    assert.match(get("dataset").children[0].textContent, /08\/01\/2026/);
    rows = get("result-table").children[0].children[1].children;
    assert.equal(rows[0].children[4].textContent, "R$1,571,718,049.25");
    assert.equal(rows[1].children[4].textContent, "Not reported");
    assert.equal(
        JSON.stringify(formattedResult),
        originalJSON,
        "Formatting never changes evidence or downloadable data",
    );
    formattedResult.evidence.question = "purchase";
    formattedResult.evidence.result = [
        {
            control_id: "01612601000118-1-000044/2026",
            publication_date: "2026-11-04",
            contracts: [
                {
                    contract_id: "original-contract-id",
                    initial_value: "1234.50",
                    global_value: null,
                    source_record_index: 0,
                },
            ],
        },
    ];
    vm.runInContext("render(formattedResult)", context);
    const purchaseRows = get("result-table").children[0].children[0].children;
    assert.equal(purchaseRows[1].children[1].textContent, "11/04/2026");
    const contractRows =
        purchaseRows[2].children[1].children[0].children[1].children;
    assert.equal(
        contractRows[0].children[0].textContent,
        "original-contract-id",
    );
    assert.equal(contractRows[0].children[1].textContent, "R$1,234.50");
    assert.equal(contractRows[0].children[2].textContent, "Not reported");
    const currentCoverage = structuredClone(result);
    Object.assign(currentCoverage.evidence.coverage, {
        purchases: 2537,
        covered_purchases: 100,
        contracts: 21,
        none_returned: 83,
        unknown_awarded_values: 1354,
    });
    currentCoverage.evidence.scope.date_start = "2026-05-01";
    currentCoverage.evidence.sources.coverage_report = "runs/expanded.json";
    context.currentCoverage = currentCoverage;
    vm.runInContext(
        'datasetCatalog.push({id:"expanded",coverage:"runs/expanded.json",purchases:2537,covered:100,excluded:1,start:"2026-05-01",end:"2026-10-31"});selectedDataset="expanded";lang="pt";latest=currentCoverage;render(latest)',
        context,
    );
    assert.equal(get("coverage").children.length, 6);
    assert.equal(get("coverage").children[2].children[0].textContent, "2.436");
    assert.equal(get("coverage").children[5].children[0].textContent, "1");
    let explanation = get("insight")
        .children[1].children.map((item) => item.textContent)
        .join(" ");
    assert.match(explanation, /2\.436 compras/);
    assert.match(explanation, /ano.*inválido/);
    assert.match(explanation, /não a quantidade de perguntas/);
    get("language").click();
    explanation = get("insight")
        .children[1].children.map((item) => item.textContent)
        .join(" ");
    assert.match(explanation, /2,436 purchases/);
    assert.match(explanation, /not the number of questions/);
    vm.runInContext(
        'selectedDataset="original";latest=' +
            JSON.stringify(result) +
            ";render(latest)",
        context,
    );
    assert.equal(get("coverage").children[2].children[0].textContent, "0");
    explanation = get("insight")
        .children[1].children.map((item) => item.textContent)
        .join(" ");
    assert.match(explanation, /All eligible purchases/);
    currentCoverage.evidence.scope.date_start = "2020-01-01";
    vm.runInContext(
        'selectedDataset="expanded";render(currentCoverage)',
        context,
    );
    assert.equal(
        get("coverage").children.length,
        4,
        "Different snapshots must not borrow catalog exclusions",
    );
    explanation = get("insight")
        .children[1].children.map((item) => item.textContent)
        .join(" ");
    assert.match(
        explanation,
        /does not distinguish pending searches from exclusions/,
    );
    for (const filename of ["web/index.html", "web/app.js", "web/app.css"]) {
        assert.doesNotMatch(
            fs.readFileSync(filename, "utf8"),
            /portf[oó]lio|por luiz|by luiz/i,
            "Application must use product-facing language",
        );
    }
    const analyticsResult = structuredClone(result);
    analyticsResult.evidence.question = "monthly";
    analyticsResult.evidence.result = [
        {
            publication_month: "2026-05",
            purchases: 505,
            estimated_value: "1234.50000000",
            unknown_estimates: 0,
            unknown_awarded_values: 123,
        },
    ];
    context.analyticsResult = analyticsResult;
    vm.runInContext('lang="pt";latest=analyticsResult;render(latest)', context);
    let analyticsRows = get("result-table").children[0].children[1].children;
    assert.match(analyticsRows[0].children[0].textContent, /2026/);
    assert.equal(
        analyticsRows[0].children[2].textContent.replaceAll("\u00a0", " "),
        "R$ 1.234,50",
    );
    assert.equal(get("download-csv").hidden, false);
    let exported;
    context.URL.createObjectURL = (blob) => {
        exported = blob;
        return "blob:test";
    };
    get("download-csv").click();
    const exportText = await exported.text();
    assert.match(exportText, /coverage_report_sha256/);
    assert.match(exportText, /1234\.50000000/);
    assert.equal(
        exportText.includes("R$ 1.234,50"),
        false,
        "CSV uses original monetary precision",
    );
    analyticsResult.evidence.question = "quality";
    analyticsResult.evidence.result = [
        {
            purchases: 1081,
            unknown_estimates: 0,
            zero_estimates: 4,
            unknown_awarded_values: 749,
        },
    ];
    vm.runInContext("render(analyticsResult)", context);
    assert.match(get("answer").textContent, /podem se sobrepor/);
    assert.equal(
        get("result-table").children[0].children[0].children.length,
        4,
    );
    analyticsResult.status = "error";
    vm.runInContext("render(analyticsResult)", context);
    assert.equal(get("download-csv").hidden, true);
    get("discovery").children[4].click();
    assert.match(get("question").value, /órgãos/);
    datasets[0].coverage_sha256 = "b".repeat(64);
    context.updatedDatasets = datasets;
    context.savedResult = result;
    store.set(
        "asktrace.session.v1",
        JSON.stringify({
            version: 1,
            dataset: "original",
            language: "pt",
            entries: [{ id: "old-result", dataset: "original", data: result }],
        }),
    );
    vm.runInContext(
        'latest=null;initializeDatasets({datasets:updatedDatasets,default_dataset:"original"})',
        context,
    );
    assert.equal(
        vm.runInContext("latest===null", context),
        true,
        "Outdated answers must not auto-restore as current",
    );
    get("history").children[0].click();
    assert.equal(get("result-freshness").hidden, false);
    assert.match(get("result-freshness").textContent, /versão anterior/);
    assert.equal(
        JSON.stringify(result.evidence.coverage_report_sha256),
        JSON.stringify("a".repeat(64)),
        "History stays immutable",
    );
    vm.runInContext('lang="en";render(savedResult)', context);
    assert.match(
        get("result-freshness").textContent,
        /earlier dataset version/,
    );
    console.log(
        "Assistant session persistence and DOM contract passed: discovery, submit, response, suggestions, history, language, reset, session.",
    );
})().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
