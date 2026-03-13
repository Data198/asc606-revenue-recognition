"""Variable consideration estimation methods under ASC 606."""


def expected_value(scenarios):
    """Expected value method: probability-weighted sum of possible outcomes.

    Best used when there are multiple possible outcomes.
    ASC 606-32(a)
    """
    return sum(s["probability"] * s["amount"] for s in scenarios)


def most_likely_amount(scenarios):
    """Most likely amount method: single most likely outcome.

    Best used when there are only two possible outcomes (e.g., bonus or no bonus).
    ASC 606-32(b)
    """
    if not scenarios:
        return 0
    return max(scenarios, key=lambda s: s["probability"])["amount"]


def apply_constraint(estimated_amount, constraint_factor=0.85):
    """Apply the variable consideration constraint.

    Include variable consideration only to the extent it is probable
    that a significant reversal of cumulative revenue will not occur.
    ASC 606-56 through 606-58
    """
    return round(estimated_amount * constraint_factor, 2)


def assess_constraint_factors():
    """Return the factors to consider when applying the constraint.

    Per ASC 606-57, factors that increase the likelihood of a revenue reversal.
    """
    return [
        "Amount is highly susceptible to external factors (market volatility, weather, etc.)",
        "Uncertainty not expected to be resolved for a long period",
        "Limited experience with similar contracts",
        "Broad range of possible consideration amounts",
        "Practice of offering price concessions or changing payment terms",
    ]
