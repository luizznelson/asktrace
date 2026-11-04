"""One-step router: a validated plan, at most one read-only query, grounded rendering."""

import argparse
import json
import re
import time
import unicodedata
from pathlib import Path

from asktrace.query import answer, serialize

ACTIONS = {"summary", "municipalities", "purchase", "refuse"}
ID = re.compile(r"\b\d{14}-1-\d{6}/\d{4,5}\b")


def normalized(text):
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", text.lower())
        if not unicodedata.combining(char)
    )


def policy(question):
    text = normalized(question)
    if any(
        term in text
        for term in (
            "ignore",
            "ignora",
            "desconsidere",
            "instrucao",
            "instrucoes",
            "system prompt",
            "senha",
            "password",
            "api key",
            "chave api",
            "delete",
            "drop table",
            "apague",
            "altere",
            "escreva sql",
            "execute sql",
            "fraud",
            "irregular",
            "corrup",
            "superfatur",
            "economia",
            "economiz",
            "pagamento",
            "pagou",
            "pago",
            "pagos",
            "paga",
            "lucro",
            "fornecedor",
            "cpf",
            "cnpj",
            "2025",
            "2027",
            "maranhao",
            "ceara",
            "brasil inteiro",
            "todo o brasil",
            "todos os contratos do piaui",
            "todas as modalidades",
        )
    ):
        return "unsupported_or_unsafe_request"
    return None


def baseline(question):
    text = normalized(question)
    identifier = ID.search(question)
    if identifier:
        return {"action": "purchase", "purchase_id": identifier.group()}
    if "municip" in text or "cidade" in text:
        return {"action": "municipalities", "purchase_id": None}
    if any(
        term in text
        for term in (
            "cobertura",
            "resumo",
            "quant",
            "total",
            "ausent",
            "desconhecid",
            "faltam",
            "nulo",
            "homologado",
        )
    ):
        return {"action": "summary", "purchase_id": None}
    return {"action": "refuse", "purchase_id": None}


def validate_plan(plan, question):
    if (
        not isinstance(plan, dict)
        or set(plan) != {"action", "purchase_id"}
        or not isinstance(plan["action"], str)
        or plan["action"] not in ACTIONS
    ):
        raise ValueError("invalid_plan")
    identifier = plan["purchase_id"]
    if plan["action"] == "purchase":
        if not isinstance(identifier, str) or identifier not in ID.findall(question):
            raise ValueError("identifier_not_in_question")
    elif identifier is not None:
        raise ValueError("unexpected_identifier")
    return plan


def render(result):
    if result["status"] == "not_found_in_scope":
        return "Compra não encontrada neste recorte. Isso não afirma ausência no PNCP."
    if result["question"] == "summary":
        row = result["result"][0]
        return (
            f"O recorte tem {row['purchases']} compras; {row['covered_purchases']} têm consulta "
            f"de contratos confirmada. Retornaram {row['contracts']} contratos vinculados a "
            f"{row['purchases_with_contracts']} compras. Em {row['none_returned']} compras, "
            f"não retornou publicação. Há {row['unknown_awarded_values']} compras com valor "
            "homologado desconhecido. Publicação não comprova pagamento."
        )
    if result["question"] == "municipalities":
        return (
            f"A tabela apresenta {len(result['result'])} grupos de município, no máximo 20, "
            "ordenados por quantidade de compras. Estimativas são somadas uma vez por compra; "
            "valores desconhecidos permanecem nulos. A tabela não representa pagamentos."
        )
    row = result["result"][0]
    count = len(row["contracts"] or [])
    return (
        f"A compra {row['control_id']} tem {count} contratos neste snapshot. "
        f"Situação da consulta: {row['outcome'] or 'não coberta'}. "
        "Os identificadores e hashes abaixo permitem conferir a origem. Não são pagamentos."
    )


def run(root, report, question, provider="baseline", planner=None, tool=answer):
    started = time.perf_counter()
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 1000:
        raise ValueError("question_length_must_be_1_to_1000")
    if provider not in {"baseline", "gemini"}:
        raise ValueError("unsupported_provider")
    trace = []
    result = {
        "question": question,
        "provider": provider,
        "status": "refused",
        "answer": "Não posso responder com as consultas e o recorte disponíveis.",
        "trace": trace,
        "llm_attempts": 0,
        "tool_calls": 0,
    }
    reason = policy(question)
    if reason:
        trace.append({"step": "policy", "outcome": "refused", "reason": reason})
    else:
        try:
            if planner is None:
                if provider == "gemini":
                    from asktrace.gemini import plan as provider_plan

                    def planner(text):
                        return provider_plan(root, text)
                else:
                    planner = baseline
            result["llm_attempts"] = int(provider == "gemini")
            proposal = planner(question)
            usage = None
            if isinstance(proposal, tuple):
                proposal, usage = proposal
            plan = validate_plan(proposal, question)
            trace.append({"step": "plan", "plan": plan, "usage": usage})
            if plan["action"] != "refuse":
                result["tool_calls"] = 1
                data = tool(root, report, plan["action"], plan["purchase_id"])
                # Free text is not sent to the model or included in the public answer.
                for row in data["result"]:
                    row.pop("object_text", None)
                scope = data.get("scope")
                prefix = (
                    f"Recorte: {scope['uf']}, modalidade {scope['modality']}, "
                    f"publicação de {scope['date_start']} a {scope['date_end']}. "
                    if scope
                    else ""
                )
                result.update(status=data["status"], answer=prefix + render(data), evidence=data)
                trace.append(
                    {
                        "step": "read_only_query",
                        "action": plan["action"],
                        "outcome": data["status"],
                        "coverage_report_sha256": data["coverage_report_sha256"],
                    }
                )
        except Exception as error:
            # Never expose provider bodies, credentials or database connection messages.
            result.update(status="error", answer="A consulta não pôde ser concluída com segurança.")
            trace.append(
                {
                    "step": "failure",
                    "error_type": type(error).__name__,
                    "provider_http_status": getattr(error, "http_status", None),
                    "provider_limits": getattr(error, "limits", None),
                }
            )
    result["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("--coverage", required=True, type=Path)
    parser.add_argument("--provider", choices=["baseline", "gemini"], default="baseline")
    args = parser.parse_args()
    try:
        result = run(Path.cwd(), args.coverage, args.question, args.provider)
        print(json.dumps(result, default=serialize, ensure_ascii=False, indent=2))
        return int(result["status"] == "error")
    except Exception as error:
        print(f"Agent operation failed: {type(error).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
