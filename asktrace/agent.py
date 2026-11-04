"""One-step router: a validated plan, at most one read-only query, grounded rendering."""

import argparse
import json
import re
import time
import unicodedata
from pathlib import Path

from asktrace.planning import ACTIVE_SCOPE, PLAN_ACTIONS
from asktrace.providers import MODES, select
from asktrace.query import answer, serialize

ACTIONS = set(PLAN_ACTIONS)
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
    monthly = bool(re.search(r"\bmes(?:es)?\b|\bmensal\b|\bevolucao\b", text))
    organization = "orgao" in text or "entidade" in text
    municipality = "municip" in text or "cidade" in text
    if sum((monthly, organization, municipality)) > 1:
        return {"action": "refuse", "purchase_id": None}
    if monthly:
        return {"action": "monthly", "purchase_id": None}
    if organization:
        return {"action": "organizations", "purchase_id": None}
    if municipality:
        return {"action": "municipalities", "purchase_id": None}
    if any(term in text for term in ("qualidade", "lacuna", "completude", "preenchimento")):
        return {"action": "quality", "purchase_id": None}
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
    if result["question"] in {"monthly", "organizations", "quality"}:
        descriptions = {
            "monthly": "Evolução por mês de publicação; não representa execução ou pagamentos.",
            "organizations": (
                "Até 20 órgãos por quantidade de compras; somas usam apenas valores informados."
            ),
            "quality": (
                "Preenchimento: valores ausentes são distintos de zero. "
                "Não é classificação de irregularidades."
            ),
        }
        return descriptions[result["question"]] + " Confira a tabela, o recorte e as fontes."
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
    if provider not in MODES:
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
        scope_token = None
        try:
            if planner is None and report.exists() and provider != "baseline":
                from asktrace.query import dataset

                manifest, _, _, _ = dataset(root, report)
                scope_token = ACTIVE_SCOPE.set(manifest)
            if planner is None:
                if provider == "gemini":
                    from asktrace.gemini import plan as provider_plan

                    def planner(text):
                        return provider_plan(root, text)
                elif provider == "baseline":
                    planner = baseline
                else:

                    def planner(text):
                        return select(
                            root, text, validate_plan, None if provider == "fallback" else provider
                        )

            result["llm_attempts"] = int(provider == "gemini")
            proposal = planner(question)
            usage = None
            if isinstance(proposal, tuple):
                proposal, usage = proposal
            if usage and "provider_events" in usage:
                result["llm_attempts"] = usage["attempt_count"]
                result["selected_provider"] = {
                    key: usage[key] for key in ("candidate", "provider", "model")
                }
                trace.extend(
                    {"step": "provider_attempt", **event} for event in usage["provider_events"]
                )
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
            if hasattr(error, "provider_events"):
                result["llm_attempts"] = error.attempt_count
                trace.extend(
                    {"step": "provider_attempt", **event} for event in error.provider_events
                )
            result.update(status="error", answer="A consulta não pôde ser concluída com segurança.")
            if hasattr(error, "provider_events") and result["tool_calls"] == 0:
                cooldowns = [
                    event["not_before_epoch"]
                    for event in error.provider_events
                    if event.get("reason") == "cooldown"
                    and isinstance(event.get("not_before_epoch"), (int, float))
                ]
                result["availability"] = {
                    "component": "ai_planner",
                    "reason": "cooldown"
                    if cooldowns and error.attempt_count == 0
                    else "provider_unavailable",
                    "next_candidate_retry_epoch": min(cooldowns) if cooldowns else None,
                    "local_rules_available_to_try": True,
                    "database_checked": False,
                }
            trace.append(
                {
                    "step": "failure",
                    "error_type": type(error).__name__,
                    "provider_http_status": getattr(error, "http_status", None),
                    "provider_limits": getattr(error, "limits", None),
                }
            )
        finally:
            if scope_token is not None:
                ACTIVE_SCOPE.reset(scope_token)
    result["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("--coverage", required=True, type=Path)
    parser.add_argument("--provider", choices=MODES, default="baseline")
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
