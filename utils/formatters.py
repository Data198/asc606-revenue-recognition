"""Formatting utilities."""


def fmt_currency(value, decimals=0, prefix="$"):
    if value is None:
        return f"{prefix}0"
    return f"{prefix}{value:,.{decimals}f}"


def fmt_pct(value, decimals=1):
    if value is None:
        return "0.0%"
    return f"{value:.{decimals}f}%"
