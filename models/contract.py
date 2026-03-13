"""Contract and Performance Obligation data models."""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class PerformanceObligation:
    name: str
    type: str  # "over_time" or "point_in_time"
    standalone_selling_price: float
    ssp_method: str  # "observable", "adjusted_market", "residual"
    delivery_start: Optional[date] = None
    delivery_end: Optional[date] = None
    completion_date: Optional[date] = None
    allocated_price: float = 0.0


@dataclass
class VariableConsideration:
    type: str  # "usage_based", "discount", "rebate", "penalty"
    description: str
    estimation_method: str  # "expected_value" or "most_likely_amount"
    scenarios: list = field(default_factory=list)
    constraint_applied: bool = True
    estimated_amount: float = 0.0


@dataclass
class Contract:
    id: str
    customer: str
    contract_date: date
    term_months: int
    total_consideration: float
    payment_terms: str
    obligations: list = field(default_factory=list)
    variable_consideration: Optional[VariableConsideration] = None

    @property
    def end_date(self):
        from dateutil.relativedelta import relativedelta
        return self.contract_date + relativedelta(months=self.term_months)

    @property
    def total_ssp(self):
        return sum(o.standalone_selling_price for o in self.obligations)
