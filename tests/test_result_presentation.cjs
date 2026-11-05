"use strict";
const fs = require("node:fs"),
    vm = require("node:vm"),
    assert = require("node:assert/strict");
const ctx = vm.createContext({ Intl, Date });
vm.runInContext(fs.readFileSync("web/formatters.js", "utf8"), ctx);
vm.runInContext(fs.readFileSync("web/presentation.js", "utf8"), ctx);
const build = vm.runInContext("resultPresentation.build", ctx);
const sample = {
    status: "answered",
    evidence: {
        question: "monthly",
        coverage: { purchases: 2537 },
        result: [
            { publication_month: "2026-05", purchases: 505 },
            { publication_month: "2026-06", purchases: 527 },
            { publication_month: "2026-07", purchases: 424 },
            { publication_month: "2026-08", purchases: 412 },
            { publication_month: "2026-09", purchases: 373 },
            { publication_month: "2026-10", purchases: 296 },
        ],
    },
};
let result = build(sample, "pt");
assert.match(result.lead, /527 compras/);
assert.match(result.lead, /jun/);
assert.equal(result.metrics[0].value, "2.537");
assert.equal(result.chart.items.length, 6);
assert.deepEqual(
    JSON.parse(JSON.stringify(result.chart.items.map((item) => item.count))),
    [505, 527, 424, 412, 373, 296],
);
assert.match(build(sample, "en").lead, /527 purchases/);
assert.match(build(sample, "en").chart.items[1].label, /Jun/);
const before = JSON.stringify(sample);
build(sample, "pt");
assert.equal(JSON.stringify(sample), before);
sample.evidence.result[0].purchases = 527;
assert.match(build(sample, "pt").lead, /2 grupos/);
assert.doesNotMatch(build(sample, "pt").lead, /tem o maior/);
sample.evidence.result[0].purchases = -1;
assert.equal(build(sample, "pt").chart, null);
sample.evidence.result = [];
assert.equal(build(sample, "pt").chart, null);
sample.status = "error";
assert.equal(build(sample, "pt").metrics.length, 0);
sample.status = "answered";
sample.evidence.question = "organizations";
sample.evidence.result = Array.from({ length: 20 }, (_, i) => ({
    org_name: i ? "Organization " + i : null,
    purchases: 100 - i,
}));
result = build(sample, "en");
assert.equal(result.chart.items.length, 5);
assert.equal(
    result.metrics.length,
    2,
    "Do not sum a truncated ranking as a dataset total",
);
assert.match(result.chart.note, /up to 20/);
assert.equal(result.chart.items[0].label, "Organization name not reported");
sample.evidence.result = sample.evidence.result.map((row) => ({
    ...row,
    purchases: 0,
}));
assert.match(build(sample, "pt").lead, /20 grupos/);
sample.evidence.question = "quality";
sample.evidence.result = [
    {
        purchases: 2537,
        unknown_awarded_values: 1354,
        unknown_estimates: 0,
        zero_estimates: 8,
    },
];
assert.match(build(sample, "pt").lead, /1\.354 das 2\.537/);
assert.match(build(sample, "pt").lead, /podem se sobrepor/);
assert.equal(build(sample, "pt").metrics[0].value, "0");
assert.equal(build(sample, "pt").chart, null);
sample.evidence.question = "purchase";
assert.equal(build(sample, "pt").lead, null);
console.log(
    "Result presentation passed: measured monthly peak, ties, null names, zero, top-five scope, immutable inputs and bilingual output.",
);
