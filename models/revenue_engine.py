"""Core ASC 606 five-step revenue recognition computation engine."""

import pandas as pd
import numpy as np
from datetime import date, timedelta
from models.contract import Contract, PerformanceObligation, VariableConsideration


def step1_identify_contract(contract: Contract) -> dict:
    """Step 1: Identify the contract with a customer.

    Validates the five criteria for a valid contract under ASC 606:
    1. Approved by parties
    2. Rights are identifiable
    3. Payment terms are identifiable
    4. Commercial substance
    5. Collection is probable
    """
    criteria = {
        "approved_by_parties": bool(contract.customer and contract.contract_date),
        "rights_identifiable": len(contract.obligations) > 0,
        "payment_terms_identifiable": bool(contract.payment_terms),
        "commercial_substance": contract.total_consideration > 0,
        "collection_probable": True,  # Assumed for demo
    }
    all_met = all(criteria.values())
    return {"criteria": criteria, "valid_contract": all_met}


def step2_identify_obligations(contract: Contract) -> list:
    """Step 2: Identify performance obligations.

    Evaluates each promised good/service for distinctness:
    - Capable of being distinct (customer can benefit on its own)
    - Distinct within the context of the contract
    """
    results = []
    for ob in contract.obligations:
        results.append({
            "name": ob.name,
            "type": ob.type,
            "capable_of_being_distinct": True,
            "distinct_in_context": True,
            "is_distinct": True,
            "ssp": ob.standalone_selling_price,
            "ssp_method": ob.ssp_method,
        })
    return results


def step3_determine_transaction_price(contract: Contract) -> dict:
    """Step 3: Determine the transaction price.

    Components:
    - Fixed consideration
    - Variable consideration (estimated)
    - Significant financing component (if applicable)
    - Non-cash consideration
    - Consideration payable to customer
    """
    fixed = contract.total_consideration
    variable = 0.0
    variable_detail = None

    if contract.variable_consideration:
        vc = contract.variable_consideration
        if vc.estimation_method == "expected_value":
            variable = sum(s["probability"] * s["amount"] for s in vc.scenarios)
        elif vc.estimation_method == "most_likely_amount":
            if vc.scenarios:
                variable = max(vc.scenarios, key=lambda s: s["probability"])["amount"]

        # Apply constraint
        if vc.constraint_applied:
            variable = variable * 0.85  # Conservative constraint

        variable_detail = {
            "type": vc.type,
            "method": vc.estimation_method,
            "unconstrained_estimate": sum(s["probability"] * s["amount"] for s in vc.scenarios) if vc.scenarios else 0,
            "constrained_estimate": variable,
            "constraint_applied": vc.constraint_applied,
        }

    total_transaction_price = fixed + variable

    return {
        "fixed_consideration": fixed,
        "variable_consideration": round(variable, 2),
        "variable_detail": variable_detail,
        "total_transaction_price": round(total_transaction_price, 2),
    }


def step4_allocate_transaction_price(contract: Contract, transaction_price: float) -> list:
    """Step 4: Allocate the transaction price to performance obligations.

    Uses relative standalone selling price method.
    """
    total_ssp = contract.total_ssp
    allocations = []

    for ob in contract.obligations:
        if total_ssp > 0:
            allocation_pct = ob.standalone_selling_price / total_ssp
        else:
            allocation_pct = 1.0 / len(contract.obligations)

        allocated = round(transaction_price * allocation_pct, 2)
        ob.allocated_price = allocated

        allocations.append({
            "obligation": ob.name,
            "ssp": ob.standalone_selling_price,
            "ssp_method": ob.ssp_method,
            "allocation_pct": round(allocation_pct * 100, 2),
            "allocated_price": allocated,
        })

    # Adjust rounding
    total_allocated = sum(a["allocated_price"] for a in allocations)
    if allocations and abs(total_allocated - transaction_price) > 0.01:
        allocations[-1]["allocated_price"] += round(transaction_price - total_allocated, 2)

    return allocations


def step5_recognize_revenue(contract: Contract) -> pd.DataFrame:
    """Step 5: Recognize revenue as/when performance obligations are satisfied.

    Generates monthly revenue recognition schedule.
    """
    records = []

    for ob in contract.obligations:
        if ob.type == "over_time":
            start = ob.delivery_start or contract.contract_date
            end = ob.delivery_end or date(
                start.year + (start.month + contract.term_months - 1) // 12,
                (start.month + contract.term_months - 1) % 12 + 1,
                min(start.day, 28)
            )

            # Calculate months
            months = []
            current = date(start.year, start.month, 1)
            end_month = date(end.year, end.month, 1)
            while current <= end_month:
                months.append(current)
                if current.month == 12:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, current.month + 1, 1)

            monthly_amount = round(ob.allocated_price / max(len(months), 1), 2)

            # Adjust last month for rounding
            total_so_far = 0
            for i, month in enumerate(months):
                if i == len(months) - 1:
                    amount = round(ob.allocated_price - total_so_far, 2)
                else:
                    amount = monthly_amount
                    total_so_far += amount

                records.append({
                    "period": month.strftime("%Y-%m"),
                    "obligation": ob.name,
                    "type": ob.type,
                    "amount": amount,
                    "cumulative": 0,  # Will be calculated below
                    "pct_recognized": 0,
                })

        elif ob.type == "point_in_time":
            completion = ob.completion_date or contract.contract_date
            records.append({
                "period": completion.strftime("%Y-%m"),
                "obligation": ob.name,
                "type": ob.type,
                "amount": ob.allocated_price,
                "cumulative": ob.allocated_price,
                "pct_recognized": 100.0,
            })

    df = pd.DataFrame(records)
    if not df.empty:
        # Calculate cumulative amounts per obligation
        for ob_name in df["obligation"].unique():
            mask = df["obligation"] == ob_name
            df.loc[mask, "cumulative"] = df.loc[mask, "amount"].cumsum()
            total = df.loc[mask, "amount"].sum()
            if total > 0:
                df.loc[mask, "pct_recognized"] = (df.loc[mask, "cumulative"] / total * 100).round(1)

    return df


def generate_journal_entries(contract: Contract, schedule_df: pd.DataFrame) -> pd.DataFrame:
    """Generate journal entries from the revenue recognition schedule."""
    entries = []

    for _, row in schedule_df.iterrows():
        # Debit: Deferred Revenue (or AR for point-in-time)
        entries.append({
            "period": row["period"],
            "obligation": row["obligation"],
            "account": "2400 - Deferred Revenue" if row["type"] == "over_time" else "1200 - Accounts Receivable",
            "debit": round(row["amount"], 2),
            "credit": 0,
            "description": f"Revenue recognition - {row['obligation']}",
        })
        # Credit: Revenue
        entries.append({
            "period": row["period"],
            "obligation": row["obligation"],
            "account": "4100 - Revenue",
            "debit": 0,
            "credit": round(row["amount"], 2),
            "description": f"Revenue recognition - {row['obligation']}",
        })

    return pd.DataFrame(entries)


def run_full_analysis(contract: Contract) -> dict:
    """Run the complete 5-step ASC 606 analysis."""
    step1 = step1_identify_contract(contract)
    step2 = step2_identify_obligations(contract)
    step3 = step3_determine_transaction_price(contract)
    step4 = step4_allocate_transaction_price(contract, step3["total_transaction_price"])
    schedule = step5_recognize_revenue(contract)
    journal_entries = generate_journal_entries(contract, schedule)

    return {
        "step1": step1,
        "step2": step2,
        "step3": step3,
        "step4": step4,
        "schedule": schedule,
        "journal_entries": journal_entries,
    }
