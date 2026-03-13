"""SSP allocation, proration, and date math utilities."""

from datetime import date


def months_between(start: date, end: date) -> int:
    """Calculate the number of months between two dates."""
    return (end.year - start.year) * 12 + (end.month - start.month) + 1


def prorate_amount(total: float, start: date, end: date, target_month: date) -> float:
    """Prorate an amount for a specific month within a date range."""
    total_months = months_between(start, end)
    if total_months <= 0:
        return 0.0
    return round(total / total_months, 2)


def allocate_by_ssp(obligations: list, transaction_price: float) -> list:
    """Allocate transaction price using relative SSP method.

    obligations: list of dicts with 'name' and 'ssp' keys
    Returns list of dicts with 'name', 'ssp', 'allocation_pct', 'allocated_price'
    """
    total_ssp = sum(o["ssp"] for o in obligations)
    if total_ssp == 0:
        return obligations

    result = []
    allocated_sum = 0
    for i, ob in enumerate(obligations):
        pct = ob["ssp"] / total_ssp
        if i == len(obligations) - 1:
            allocated = round(transaction_price - allocated_sum, 2)
        else:
            allocated = round(transaction_price * pct, 2)
            allocated_sum += allocated

        result.append({
            **ob,
            "allocation_pct": round(pct * 100, 2),
            "allocated_price": allocated,
        })

    return result
