"""Revenue Waterfall Visualization Page."""

import streamlit as st
import pandas as pd
import json
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.contract import Contract, PerformanceObligation, VariableConsideration
from models.revenue_engine import (
    step3_determine_transaction_price, step4_allocate_transaction_price,
    step5_recognize_revenue,
)
from components.charts import (
    revenue_waterfall_chart, cumulative_recognition_chart,
    deferred_revenue_chart,
)
from utils.formatters import fmt_currency

st.set_page_config(page_title="Revenue Waterfall | ASC 606", page_icon="📊", layout="wide")
st.title("📊 Revenue Waterfall Visualization")
st.caption("Compare revenue recognition patterns across sample contracts")

# Load sample contracts
data_path = Path(__file__).parent.parent / "data" / "sample_contracts.json"
with open(data_path) as f:
    sample_data = json.load(f)

# Contract selector
contract_names = [c["name"] for c in sample_data["contracts"]]
selected_name = st.selectbox("Select Contract", contract_names)

selected_contract_data = next(c for c in sample_data["contracts"] if c["name"] == selected_name)

# Build contract object
obs = []
for ob_data in selected_contract_data["obligations"]:
    obs.append(PerformanceObligation(
        name=ob_data["name"],
        type=ob_data["type"],
        standalone_selling_price=ob_data["standalone_selling_price"],
        ssp_method=ob_data["ssp_method"],
        delivery_start=date.fromisoformat(ob_data["delivery_start"]) if ob_data.get("delivery_start") else None,
        delivery_end=date.fromisoformat(ob_data["delivery_end"]) if ob_data.get("delivery_end") else None,
        completion_date=date.fromisoformat(ob_data["completion_date"]) if ob_data.get("completion_date") else None,
    ))

vc = None
if selected_contract_data.get("variable_consideration"):
    vc_data = selected_contract_data["variable_consideration"]
    vc = VariableConsideration(
        type=vc_data["type"],
        description=vc_data["description"],
        estimation_method=vc_data["estimation_method"],
        scenarios=vc_data["scenarios"],
        constraint_applied=vc_data["constraint_applied"],
    )

contract = Contract(
    id=selected_contract_data["id"],
    customer=selected_contract_data["customer"],
    contract_date=date.fromisoformat(selected_contract_data["contract_date"]),
    term_months=selected_contract_data["term_months"],
    total_consideration=selected_contract_data["total_consideration"],
    payment_terms=selected_contract_data["payment_terms"],
    obligations=obs,
    variable_consideration=vc,
)

# Contract Summary
st.divider()
st.subheader("Contract Summary")

info_cols = st.columns(4)
info_cols[0].metric("Customer", contract.customer)
info_cols[1].metric("Term", f"{contract.term_months} months")
info_cols[2].metric("Fixed Consideration", fmt_currency(contract.total_consideration))
info_cols[3].metric("Payment Terms", contract.payment_terms)

# Performance Obligations
st.subheader("Performance Obligations")
ob_data_display = []
for ob in contract.obligations:
    ob_data_display.append({
        "Obligation": ob.name,
        "Type": "Over Time" if ob.type == "over_time" else "Point in Time",
        "SSP": fmt_currency(ob.standalone_selling_price),
        "Method": ob.ssp_method.replace("_", " ").title(),
    })
st.dataframe(pd.DataFrame(ob_data_display), use_container_width=True, hide_index=True)

# Run analysis
tp = step3_determine_transaction_price(contract)
allocations = step4_allocate_transaction_price(contract, tp["total_transaction_price"])
schedule = step5_recognize_revenue(contract)

# KPIs
st.divider()
kpi_cols = st.columns(4)
kpi_cols[0].metric("Total Transaction Price", fmt_currency(tp["total_transaction_price"]))
kpi_cols[1].metric("Obligations", str(len(contract.obligations)))
over_time_pct = sum(1 for o in contract.obligations if o.type == "over_time") / len(contract.obligations) * 100
kpi_cols[2].metric("Over Time %", f"{over_time_pct:.0f}%")
if tp["variable_consideration"] > 0:
    kpi_cols[3].metric("Variable Consideration", fmt_currency(tp["variable_consideration"]))
else:
    kpi_cols[3].metric("Variable Consideration", "None")

# Charts
st.divider()
st.subheader("Revenue Recognition Waterfall")

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.plotly_chart(
        revenue_waterfall_chart(schedule, "Monthly Revenue by Obligation"),
        use_container_width=True,
    )
with chart_col2:
    st.plotly_chart(
        cumulative_recognition_chart(schedule, tp["total_transaction_price"],
                                     "Cumulative Revenue vs Transaction Price"),
        use_container_width=True,
    )

st.plotly_chart(
    deferred_revenue_chart(schedule, tp["total_transaction_price"],
                           "Deferred Revenue Drawdown"),
    use_container_width=True,
)

# Detailed Schedule
with st.expander("Detailed Revenue Recognition Schedule"):
    if not schedule.empty:
        display = schedule.copy()
        display["amount"] = display["amount"].apply(lambda x: fmt_currency(x))
        display["cumulative"] = display["cumulative"].apply(lambda x: fmt_currency(x))
        display["pct_recognized"] = display["pct_recognized"].apply(lambda x: f"{x:.1f}%")
        st.dataframe(display, use_container_width=True, hide_index=True)
