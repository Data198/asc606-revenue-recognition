"""Interactive ASC 606 Five-Step Model Walkthrough."""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.contract import Contract, PerformanceObligation, VariableConsideration
from models.revenue_engine import (
    step1_identify_contract, step2_identify_obligations,
    step3_determine_transaction_price, step4_allocate_transaction_price,
    step5_recognize_revenue, generate_journal_entries,
)
from components.charts import (
    revenue_waterfall_chart, cumulative_recognition_chart,
    deferred_revenue_chart, ssp_allocation_pie,
)
from utils.formatters import fmt_currency

st.set_page_config(page_title="5-Step Model | ASC 606", page_icon="📋", layout="wide")
st.title("📋 ASC 606 Five-Step Revenue Recognition Model")
st.caption("Interactive walkthrough of the ASC 606 revenue recognition framework")

# Initialize session state
if "obligations" not in st.session_state:
    st.session_state.obligations = []
if "current_step" not in st.session_state:
    st.session_state.current_step = 1

# --- Step 1: Identify the Contract ---
st.header("Step 1: Identify the Contract")
st.markdown("""
A contract exists when all five criteria are met (ASC 606-09):
1. Approved by the parties
2. Each party's rights are identifiable
3. Payment terms are identifiable
4. The contract has commercial substance
5. Collection of consideration is probable
""")

col1, col2 = st.columns(2)
with col1:
    contract_id = st.text_input("Contract ID", value="CON-001")
    customer = st.text_input("Customer Name", value="NovaCRM Client Inc.")
    contract_date = st.date_input("Contract Date", value=date(2025, 1, 1))
with col2:
    term_months = st.number_input("Contract Term (months)", value=36, min_value=1, max_value=120)
    total_consideration = st.number_input("Total Fixed Consideration ($)", value=360000.0, min_value=0.0, step=1000.0)
    payment_terms = st.selectbox("Payment Terms", ["Annual upfront", "Quarterly installments", "Monthly", "Monthly in arrears"])

# Validate Step 1
step1_valid = bool(customer and contract_date and total_consideration > 0 and payment_terms)
if step1_valid:
    st.success("All Step 1 criteria met. Contract is valid under ASC 606.")
else:
    st.warning("Please complete all fields to satisfy Step 1 criteria.")

# --- Step 2: Identify Performance Obligations ---
st.divider()
st.header("Step 2: Identify Performance Obligations")
st.markdown("""
Identify each distinct performance obligation in the contract.
A good or service is **distinct** if both criteria are met:
- The customer can benefit from it on its own or with readily available resources
- It is separately identifiable from other promises in the contract
""")

with st.expander("Add Performance Obligation", expanded=len(st.session_state.obligations) == 0):
    ob_col1, ob_col2 = st.columns(2)
    with ob_col1:
        ob_name = st.text_input("Obligation Name", value="Cloud Platform Subscription", key="ob_name")
        ob_type = st.selectbox("Recognition Pattern", ["over_time", "point_in_time"],
                               format_func=lambda x: "Over Time" if x == "over_time" else "Point in Time")
        ob_ssp = st.number_input("Standalone Selling Price ($)", value=10000.0, min_value=0.0, step=500.0)
    with ob_col2:
        ob_ssp_method = st.selectbox("SSP Method", ["observable", "adjusted_market", "residual"],
                                     format_func=lambda x: x.replace("_", " ").title())
        if ob_type == "over_time":
            ob_start = st.date_input("Delivery Start", value=contract_date, key="ob_start")
            ob_end = st.date_input("Delivery End",
                                   value=contract_date + timedelta(days=term_months * 30),
                                   key="ob_end")
            ob_completion = None
        else:
            ob_start = None
            ob_end = None
            ob_completion = st.date_input("Completion Date", value=contract_date + timedelta(days=90),
                                          key="ob_completion")

    if st.button("Add Obligation"):
        st.session_state.obligations.append({
            "name": ob_name,
            "type": ob_type,
            "ssp": ob_ssp,
            "ssp_method": ob_ssp_method,
            "start": str(ob_start) if ob_start else None,
            "end": str(ob_end) if ob_end else None,
            "completion": str(ob_completion) if ob_completion else None,
        })
        st.rerun()

# Display current obligations
if st.session_state.obligations:
    st.subheader(f"Performance Obligations ({len(st.session_state.obligations)})")
    ob_df = pd.DataFrame(st.session_state.obligations)
    ob_df["ssp"] = ob_df["ssp"].apply(lambda x: fmt_currency(x))
    st.dataframe(ob_df, use_container_width=True, hide_index=True)

    if st.button("Clear All Obligations"):
        st.session_state.obligations = []
        st.rerun()

# --- Step 3: Determine Transaction Price ---
st.divider()
st.header("Step 3: Determine the Transaction Price")

has_variable = st.checkbox("Contract includes variable consideration")

vc = None
if has_variable:
    st.markdown("**Variable Consideration Estimation**")
    vc_col1, vc_col2 = st.columns(2)
    with vc_col1:
        vc_type = st.selectbox("Type", ["usage_based", "discount", "rebate", "penalty"],
                               format_func=lambda x: x.replace("_", " ").title())
        vc_description = st.text_input("Description", value="API overage charges")
    with vc_col2:
        vc_method = st.selectbox("Estimation Method", ["expected_value", "most_likely_amount"],
                                 format_func=lambda x: x.replace("_", " ").title())
        vc_constraint = st.checkbox("Apply constraint (ASC 606-56)", value=True)

    st.markdown("**Possible Outcomes:**")
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        s1_prob = st.number_input("Scenario 1 Probability", value=0.3, min_value=0.0, max_value=1.0, step=0.05)
        s1_amt = st.number_input("Scenario 1 Amount ($)", value=5000.0, step=1000.0)
    with sc2:
        s2_prob = st.number_input("Scenario 2 Probability", value=0.5, min_value=0.0, max_value=1.0, step=0.05)
        s2_amt = st.number_input("Scenario 2 Amount ($)", value=15000.0, step=1000.0)
    with sc3:
        s3_prob = st.number_input("Scenario 3 Probability", value=0.2, min_value=0.0, max_value=1.0, step=0.05)
        s3_amt = st.number_input("Scenario 3 Amount ($)", value=25000.0, step=1000.0)

    vc = VariableConsideration(
        type=vc_type,
        description=vc_description,
        estimation_method=vc_method,
        scenarios=[
            {"probability": s1_prob, "amount": s1_amt},
            {"probability": s2_prob, "amount": s2_amt},
            {"probability": s3_prob, "amount": s3_amt},
        ],
        constraint_applied=vc_constraint,
    )

# --- Run Analysis ---
st.divider()
if st.session_state.obligations and step1_valid:
    st.header("Steps 4 & 5: Allocate & Recognize Revenue")

    # Build Contract object
    obs = []
    for ob_data in st.session_state.obligations:
        obs.append(PerformanceObligation(
            name=ob_data["name"],
            type=ob_data["type"],
            standalone_selling_price=ob_data["ssp"] if isinstance(ob_data["ssp"], (int, float)) else float(ob_data["ssp"].replace("$", "").replace(",", "")),
            ssp_method=ob_data["ssp_method"],
            delivery_start=date.fromisoformat(ob_data["start"]) if ob_data.get("start") else None,
            delivery_end=date.fromisoformat(ob_data["end"]) if ob_data.get("end") else None,
            completion_date=date.fromisoformat(ob_data["completion"]) if ob_data.get("completion") else None,
        ))

    contract = Contract(
        id=contract_id,
        customer=customer,
        contract_date=contract_date,
        term_months=term_months,
        total_consideration=total_consideration,
        payment_terms=payment_terms,
        obligations=obs,
        variable_consideration=vc,
    )

    # Step 3: Transaction Price
    tp_result = step3_determine_transaction_price(contract)

    tp_cols = st.columns(3)
    tp_cols[0].metric("Fixed Consideration", fmt_currency(tp_result["fixed_consideration"]))
    tp_cols[1].metric("Variable Consideration", fmt_currency(tp_result["variable_consideration"]))
    tp_cols[2].metric("Total Transaction Price", fmt_currency(tp_result["total_transaction_price"]))

    if tp_result["variable_detail"]:
        with st.expander("Variable Consideration Detail"):
            vd = tp_result["variable_detail"]
            st.write(f"**Method:** {vd['method'].replace('_', ' ').title()}")
            st.write(f"**Unconstrained Estimate:** {fmt_currency(vd['unconstrained_estimate'])}")
            st.write(f"**Constrained Estimate:** {fmt_currency(vd['constrained_estimate'])}")
            st.write(f"**Constraint Applied:** {'Yes' if vd['constraint_applied'] else 'No'}")

    # Step 4: Allocation
    st.subheader("Step 4: Transaction Price Allocation")
    allocations = step4_allocate_transaction_price(contract, tp_result["total_transaction_price"])

    alloc_col1, alloc_col2 = st.columns([3, 2])
    with alloc_col1:
        alloc_df = pd.DataFrame(allocations)
        alloc_df["ssp"] = alloc_df["ssp"].apply(lambda x: fmt_currency(x))
        alloc_df["allocated_price"] = alloc_df["allocated_price"].apply(lambda x: fmt_currency(x))
        alloc_df["allocation_pct"] = alloc_df["allocation_pct"].apply(lambda x: f"{x:.1f}%")
        alloc_df.columns = ["Obligation", "SSP", "SSP Method", "Allocation %", "Allocated Price"]
        st.dataframe(alloc_df, use_container_width=True, hide_index=True)
    with alloc_col2:
        st.plotly_chart(ssp_allocation_pie(allocations), use_container_width=True)

    # Step 5: Revenue Schedule
    st.subheader("Step 5: Revenue Recognition Schedule")
    schedule = step5_recognize_revenue(contract)

    if not schedule.empty:
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.plotly_chart(
                revenue_waterfall_chart(schedule, "Monthly Revenue Recognition by Obligation"),
                use_container_width=True,
            )
        with chart_col2:
            st.plotly_chart(
                cumulative_recognition_chart(schedule, tp_result["total_transaction_price"]),
                use_container_width=True,
            )

        st.plotly_chart(
            deferred_revenue_chart(schedule, tp_result["total_transaction_price"]),
            use_container_width=True,
        )

        with st.expander("Full Revenue Schedule"):
            display_schedule = schedule.copy()
            display_schedule["amount"] = display_schedule["amount"].apply(lambda x: fmt_currency(x))
            display_schedule["cumulative"] = display_schedule["cumulative"].apply(lambda x: fmt_currency(x))
            st.dataframe(display_schedule, use_container_width=True, hide_index=True)

        # Journal Entries
        st.subheader("Journal Entries")
        je = generate_journal_entries(contract, schedule)
        if not je.empty:
            je_display = je.copy()
            je_display["debit"] = je_display["debit"].apply(lambda x: fmt_currency(x) if x > 0 else "")
            je_display["credit"] = je_display["credit"].apply(lambda x: fmt_currency(x) if x > 0 else "")
            st.dataframe(je_display, use_container_width=True, hide_index=True)

            csv = je.to_csv(index=False)
            st.download_button("Download Journal Entries (CSV)", csv,
                               f"journal_entries_{contract_id}.csv", "text/csv")
else:
    st.info("Complete Steps 1-2 (contract details and at least one performance obligation) to see the full analysis.")
