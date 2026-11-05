"use strict";

// Deterministic explanations of returned rows. No extra API call or model inference.
const resultPresentation = (() => {
    const count = (value) => Number.isSafeInteger(value) && value >= 0;
    function build(data, language) {
        const pt = language === "pt",
            e = data.evidence;
        const empty = { lead: null, metrics: [], chart: null };
        if (data.status !== "answered" || !e || !Array.isArray(e.result))
            return empty;
        const n = (value) => displayFormat.integer(value, language);
        const metric = (value, label) => ({ value: n(value), label });
        const c = e.coverage || {};
        if (e.question === "summary") {
            if (
                ![
                    c.purchases,
                    c.contracts,
                    c.purchases_with_contracts,
                    c.covered_purchases,
                ].every(count)
            )
                return empty;
            return {
                lead: pt
                    ? `O recorte reúne ${n(c.purchases)} compras e ${n(c.contracts)} contratos vinculados a ${n(c.purchases_with_contracts)} compras.`
                    : `This dataset contains ${n(c.purchases)} purchases and ${n(c.contracts)} contracts linked to ${n(c.purchases_with_contracts)} purchases.`,
                metrics: [
                    metric(
                        c.purchases,
                        pt ? "Compras no recorte" : "Purchases in scope",
                    ),
                    metric(
                        c.contracts,
                        pt ? "Contratos encontrados" : "Contracts found",
                    ),
                    metric(
                        c.purchases_with_contracts,
                        pt
                            ? "Compras com contratos"
                            : "Purchases with contracts",
                    ),
                ],
                chart: null,
            };
        }
        if (e.question === "quality") {
            const row = e.result[0];
            if (
                !row ||
                !count(row.purchases) ||
                !count(row.unknown_awarded_values)
            )
                return empty;
            return {
                lead: pt
                    ? `A fonte não informou o valor homologado de ${n(row.unknown_awarded_values)} das ${n(row.purchases)} compras. Os indicadores podem se sobrepor; não devem ser somados.`
                    : `The source did not report awarded amounts for ${n(row.unknown_awarded_values)} of ${n(row.purchases)} purchases. These indicators can overlap and must not be added together.`,
                metrics: [
                    [
                        row.unknown_estimates,
                        pt ? "Sem valor estimado" : "Missing estimates",
                    ],
                    [
                        row.unknown_awarded_values,
                        pt ? "Sem valor homologado" : "Missing awarded amounts",
                    ],
                    [
                        row.zero_estimates,
                        pt
                            ? "Estimativa explicitamente zero"
                            : "Explicitly zero estimates",
                    ],
                ]
                    .filter(([value]) => count(value))
                    .map(([value, label]) => metric(value, label)),
                chart: null,
            };
        }
        if (
            !["monthly", "municipalities", "organizations"].includes(e.question)
        )
            return empty;
        const rows = e.result.filter((row) => count(row.purchases));
        if (!rows.length || rows.length !== e.result.length) return empty;
        const monthly = e.question === "monthly";
        const label = (row) =>
            monthly
                ? displayFormat.field(
                      "publication_month",
                      row.publication_month,
                      language,
                  )
                : e.question === "municipalities"
                  ? row.municipality_name ||
                    (pt
                        ? "Município não informado"
                        : "Municipality not reported")
                  : row.org_name ||
                    (pt
                        ? "Órgão sem nome informado"
                        : "Organization name not reported");
        const max = Math.max(...rows.map((row) => row.purchases));
        const leaders = rows.filter((row) => row.purchases === max);
        let lead;
        if (leaders.length > 1)
            lead = pt
                ? `O maior volume na tabela é de ${n(max)} compras, compartilhado por ${n(leaders.length)} grupos.`
                : `The largest count in this table is ${n(max)} purchases, shared by ${n(leaders.length)} groups.`;
        else
            lead = pt
                ? `${label(leaders[0])} tem o maior volume ${monthly ? "mensal de publicações" : "na tabela"}: ${n(max)} compras.`
                : `${label(leaders[0])} has the largest ${monthly ? "monthly publication count" : "count in this table"}: ${n(max)} purchases.`;
        const total = rows.reduce(
            (sum, row) => sum + BigInt(row.purchases),
            0n,
        );
        const metrics = monthly
            ? [
                  metric(
                      total,
                      pt
                          ? "Publicações na série"
                          : "Publications in this series",
                  ),
                  metric(
                      rows.length,
                      pt ? "Meses com publicações" : "Months with publications",
                  ),
                  metric(
                      max,
                      pt ? "Maior volume mensal" : "Highest monthly count",
                  ),
              ]
            : [
                  metric(
                      max,
                      pt ? "Maior quantidade listada" : "Highest listed count",
                  ),
                  metric(
                      rows.length,
                      pt
                          ? "Grupos listados · até 20"
                          : "Listed groups · up to 20",
                  ),
              ];
        return {
            lead,
            metrics,
            chart: {
                title: pt
                    ? monthly
                        ? "Compras por mês de publicação"
                        : "Prévia dos cinco primeiros grupos"
                    : monthly
                      ? "Purchases by publication month"
                      : "First five groups",
                note: pt
                    ? monthly
                        ? "Quantidade de compras por publicação no PNCP. Não representa pagamentos ou execução financeira."
                        : "A prévia mostra até cinco dos grupos retornados. A tabela contém até 20; não é o total da base."
                    : monthly
                      ? "Purchase counts by PNCP publication month. This does not represent payments or financial execution."
                      : "This preview shows up to five returned groups. The table contains up to 20 and is not the dataset total.",
                items: (monthly ? rows : rows.slice(0, 5)).map((row) => ({
                    label: String(label(row)),
                    count: row.purchases,
                })),
            },
        };
    }
    return { build };
})();
