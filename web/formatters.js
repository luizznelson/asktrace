"use strict";

// Presentation only. API responses, evidence downloads and stored results stay unchanged.
const displayFormat = (() => {
    const locale = (language) => (language === "pt" ? "pt-BR" : "en-US");
    const missing = (language) =>
        language === "pt" ? "Não informado" : "Not reported";
    const moneyFields = new Set([
        "estimated_value",
        "awarded_value",
        "initial_value",
        "global_value",
    ]);
    const countFields = new Set([
        "purchases",
        "unknown_estimates",
        "unknown_awarded_values",
        "source_record_index",
    ]);

    function integer(value, language) {
        const raw = String(value);
        if (!/^-?\d+$/.test(raw)) return missing(language);
        return new Intl.NumberFormat(locale(language)).format(BigInt(raw));
    }

    function money(value, language) {
        if (value === null || value === undefined) return missing(language);
        const raw = String(value);
        // Decimal strings are never converted to floating point. Round half away from
        // zero to two display decimals, including carry into the integer portion.
        const match = /^(-?)(\d+)(?:\.(\d+))?$/.exec(raw);
        if (!match || raw.length > 120) return missing(language);
        const fraction = (match[3] || "").padEnd(3, "0");
        let cents = BigInt(match[2]) * 100n + BigInt(fraction.slice(0, 2));
        if (fraction[2] >= "5") cents += 1n;
        const whole = cents / 100n;
        const negative = match[1] === "-" && cents !== 0n;
        const signed = negative ? -(whole || 1n) : whole;
        return new Intl.NumberFormat(locale(language), {
            style: "currency",
            currency: "BRL",
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        })
            .formatToParts(signed)
            .map((part) => {
                if (part.type === "fraction")
                    return String(cents % 100n).padStart(2, "0");
                if (part.type === "integer" && negative && whole === 0n)
                    return "0";
                return part.value;
            })
            .join("");
    }

    function date(value, language) {
        if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value))
            return missing(language);
        const parsed = new Date(value + "T00:00:00Z");
        if (
            !Number.isFinite(parsed.getTime()) ||
            parsed.toISOString().slice(0, 10) !== value
        )
            return missing(language);
        return new Intl.DateTimeFormat(locale(language), {
            timeZone: "UTC",
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
        }).format(parsed);
    }

    function field(key, value, language) {
        if (value === null || value === undefined) return missing(language);
        if (moneyFields.has(key)) return money(value, language);
        if (countFields.has(key)) return integer(value, language);
        if (key === "publication_date") return date(value, language);
        if (key === "outcome") {
            const labels =
                language === "pt"
                    ? {
                          with_contracts: "Com contratos publicados",
                          none_returned: "Nenhuma publicação retornada",
                      }
                    : {
                          with_contracts: "Published contracts found",
                          none_returned: "No publication returned",
                      };
            return labels[value] || String(value);
        }
        return typeof value === "object"
            ? JSON.stringify(value, null, 2)
            : String(value);
    }

    return {
        money,
        integer,
        date,
        field,
        numeric: (key) => moneyFields.has(key) || countFields.has(key),
    };
})();
