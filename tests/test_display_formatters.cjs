"use strict";
const fs = require("node:fs"),
    vm = require("node:vm"),
    assert = require("node:assert/strict");
const context = vm.createContext({ Intl, Date });
vm.runInContext(fs.readFileSync("web/formatters.js", "utf8"), context);
const display = vm.runInContext("displayFormat", context);
const normalize = (value) => value.replaceAll("\u00a0", " ");
const amounts = [
    ["1571718049.25000000", "R$ 1.571.718.049,25", "R$1,571,718,049.25"],
    ["35112001.75000000", "R$ 35.112.001,75", "R$35,112,001.75"],
    ["0", "R$ 0,00", "R$0.00"],
    ["9.995", "R$ 10,00", "R$10.00"],
    ["1.005", "R$ 1,01", "R$1.01"],
    ["1.004", "R$ 1,00", "R$1.00"],
    ["-0.005", "-R$ 0,01", "-R$0.01"],
    ["-0.004", "R$ 0,00", "R$0.00"],
    ["-1234.567", "-R$ 1.234,57", "-R$1,234.57"],
    [
        "9007199254740993.99",
        "R$ 9.007.199.254.740.993,99",
        "R$9,007,199,254,740,993.99",
    ],
];
for (const [raw, pt, en] of amounts) {
    assert.equal(normalize(display.money(raw, "pt")), pt, raw);
    assert.equal(normalize(display.money(raw, "en")), en, raw);
}
for (const value of [
    null,
    undefined,
    "not-money",
    "NaN",
    "Infinity",
    "",
    "9".repeat(121),
]) {
    assert.equal(display.money(value, "pt"), "Não informado");
}
assert.equal(display.integer(2537, "pt"), "2.537");
assert.equal(
    display.integer("9007199254740993", "en"),
    "9,007,199,254,740,993",
);
assert.equal(display.field("municipality_ibge", "02211001", "pt"), "02211001");
assert.equal(
    display.field("control_id", "01612601000118-1-000044/2026", "pt"),
    "01612601000118-1-000044/2026",
);
assert.equal(
    display.field("outcome", "none_returned", "pt"),
    "Nenhuma publicação retornada",
);
assert.equal(display.field("unknown_estimates", 0, "pt"), "0");
assert.equal(display.field("estimated_value", null, "en"), "Not reported");
assert.equal(display.date("2026-11-04", "pt"), "04/11/2026");
assert.equal(display.date("2026-11-04", "en"), "11/04/2026");
assert.equal(display.date("2024-02-29", "pt"), "29/02/2024");
for (const date of ["2026-02-29", "2026-11-31", "2026-11-04T00:00:00Z", null]) {
    assert.equal(display.date(date, "pt"), "Não informado");
}
console.log(
    "Display formatting passed: PT/EN, exact decimals, rounding, zero/null, IDs, counts and UTC dates.",
);
