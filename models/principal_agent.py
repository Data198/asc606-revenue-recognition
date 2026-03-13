"""Principal vs. Agent analysis module under ASC 606."""


CONTROL_INDICATORS = [
    {
        "id": "primary_responsibility",
        "name": "Primary responsibility for fulfillment",
        "description": "The entity is primarily responsible for fulfilling the promise to provide the specified good or service.",
        "weight": "strong",
    },
    {
        "id": "inventory_risk",
        "name": "Inventory risk",
        "description": "The entity has inventory risk before the good or service is transferred to a customer, or after transfer of control (e.g., return rights).",
        "weight": "strong",
    },
    {
        "id": "pricing_discretion",
        "name": "Discretion in establishing price",
        "description": "The entity has discretion in establishing the price for the specified good or service.",
        "weight": "moderate",
    },
    {
        "id": "credit_risk",
        "name": "Credit risk",
        "description": "The entity bears the customer's credit risk for the receivable.",
        "weight": "supporting",
    },
    {
        "id": "directs_use",
        "name": "Directs the use of the good/service",
        "description": "The entity can direct the use of the good or service and obtain substantially all remaining benefits.",
        "weight": "strong",
    },
]


def evaluate_principal_agent(responses: dict) -> dict:
    """Evaluate whether an entity is acting as principal or agent.

    Args:
        responses: dict mapping indicator IDs to boolean values
                  (True = indicator is present, False = not present)

    Returns:
        dict with conclusion, score, and analysis details
    """
    total_score = 0
    max_score = 0
    analysis = []

    weight_values = {"strong": 3, "moderate": 2, "supporting": 1}

    for indicator in CONTROL_INDICATORS:
        ind_id = indicator["id"]
        weight = weight_values[indicator["weight"]]
        max_score += weight
        present = responses.get(ind_id, False)

        if present:
            total_score += weight

        analysis.append({
            "indicator": indicator["name"],
            "description": indicator["description"],
            "weight": indicator["weight"],
            "present": present,
            "score": weight if present else 0,
        })

    score_pct = (total_score / max_score * 100) if max_score > 0 else 0

    if score_pct >= 60:
        conclusion = "Principal"
        revenue_treatment = "Gross"
        rationale = (
            "Based on the indicators assessed, the entity controls the good or service "
            "before transfer to the customer. The entity should recognize revenue on a "
            "gross basis (total consideration from the customer)."
        )
    else:
        conclusion = "Agent"
        revenue_treatment = "Net"
        rationale = (
            "Based on the indicators assessed, the entity arranges for the provision of "
            "goods or services by another party. The entity should recognize revenue on a "
            "net basis (fee or commission earned)."
        )

    return {
        "conclusion": conclusion,
        "revenue_treatment": revenue_treatment,
        "score": total_score,
        "max_score": max_score,
        "score_pct": round(score_pct, 1),
        "rationale": rationale,
        "analysis": analysis,
    }


def generate_memo(evaluation: dict, transaction_description: str = "") -> str:
    """Generate a principal vs. agent analysis memo."""
    lines = [
        "PRINCIPAL VS. AGENT ANALYSIS MEMO",
        "=" * 50,
        "",
    ]

    if transaction_description:
        lines.extend([
            f"Transaction: {transaction_description}",
            "",
        ])

    lines.extend([
        f"Conclusion: {evaluation['conclusion']} ({evaluation['revenue_treatment']} Revenue Recognition)",
        f"Score: {evaluation['score']}/{evaluation['max_score']} ({evaluation['score_pct']}%)",
        "",
        "INDICATOR ASSESSMENT:",
        "-" * 50,
    ])

    for item in evaluation["analysis"]:
        status = "YES" if item["present"] else "NO"
        lines.append(f"  [{status}] {item['indicator']} (Weight: {item['weight']})")
        lines.append(f"        {item['description']}")
        lines.append("")

    lines.extend([
        "RATIONALE:",
        "-" * 50,
        evaluation["rationale"],
        "",
        "Note: This analysis is a decision-support tool. Final determination requires",
        "professional judgment considering all relevant facts and circumstances.",
    ])

    return "\n".join(lines)
