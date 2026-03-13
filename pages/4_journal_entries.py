"""Journal Entry Generator Page."""

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
    step5_recognize_revenue, generate_journal_entries,
)
from utils.formatters import fmt_currency

st.set_page_config(page_title="Journal Entries | ASC 606", page_icon="📝", layout="wide")
st.title("📝 Journal Entry Generator")
st.caption("Generate proper debit/credit entries for ASC 606 revenue recognition")

# Load sample contracts
data_path = Path(__file__).parent.parent / "data" / "sample_contracts.json"
with open(data_path) as f:
    sample_data = json.load(f)

contract_names = [c["name"] for c in sample_data["contracts"]]
selected_name = st.selectbox("Select Contract", contract_names)

selected_contract_data = next(c for c in sample_data["contracts"] if c["name"] == selected_name)

# Build contract
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

# Run analysis
tp = step3_determine_transaction_price(contract)
step4_allocate_transaction_price(contract, tp["total_transaction_price"])
schedule = step5_recognize_revenue(contract)
journal_entries = generate_journal_entries(contract, schedule)

# --- Initial Contract Booking ---
st.divider()
st.subheader("Initial Contract Booking Entry")
st.caption("Entry recorded at contract inception to establish the receivable and deferred revenue")

booking_entries = pd.DataFrame([
    {"Account": "1200 - Accounts Receivable", "Debit": tp["total_transaction_price"], "Credit": 0,
     "Description": f"Initial booking - {contract.customer}"},
    {"Account": "2400 - Deferred Revenue", "Debit": 0, "Credit": tp["total_transaction_price"],
     "Description": f"Initial booking - {contract.customer}"},
])

booking_display = booking_entries.copy()
booking_display["Debit"] = booking_display["Debit"].apply(lambda x: fmt_currency(x) if x > 0 else "")
booking_display["Credit"] = booking_display["Credit"].apply(lambda x: fmt_currency(x) if x > 0 else "")
st.dataframe(booking_display, use_container_width=True, hide_index=True)

total_debits = booking_entries["Debit"].sum()
total_credits = booking_entries["Credit"].sum()
balanced = abs(total_debits - total_credits) < 0.01
st.markdown(f"**Total Debits:** {fmt_currency(total_debits)} | **Total Credits:** {fmt_currency(total_credits)} | "
            f"**Balanced:** {'✅ Yes' if balanced else '❌ No'}")

# --- Monthly Recognition Entries ---
st.divider()
st.subheader("Monthly Revenue Recognition Entries")

# Filter by period
if not journal_entries.empty:
    periods = sorted(journal_entries["period"].unique())
    selected_period = st.selectbox("Filter by Period", ["All Periods"] + periods)

    if selected_period != "All Periods":
        je_filtered = journal_entries[journal_entries["period"] == selected_period]
    else:
        je_filtered = journal_entries

    je_display = je_filtered.copy()
    je_display["debit"] = je_display["debit"].apply(lambda x: fmt_currency(x) if x > 0 else "")
    je_display["credit"] = je_display["credit"].apply(lambda x: fmt_currency(x) if x > 0 else "")
    je_display.columns = ["Period", "Obligation", "Account", "Debit", "Credit", "Description"]

    st.dataframe(je_display, use_container_width=True, hide_index=True)

    # Balance check
    total_d = je_filtered["debit"].sum()
    total_c = je_filtered["credit"].sum()
    is_balanced = abs(total_d - total_c) < 0.01

    st.markdown(
        f"**Total Debits:** {fmt_currency(total_d)} | **Total Credits:** {fmt_currency(total_c)} | "
        f"**Balanced:** {'✅ Yes' if is_balanced else '❌ No'}"
    )

    # Summary by period
    st.divider()
    st.subheader("Journal Entry Summary by Period")
    summary = journal_entries.groupby("period").agg(
        total_debits=("debit", "sum"),
        total_credits=("credit", "sum"),
        entry_count=("debit", "count"),
    ).reset_index()
    summary["total_debits"] = summary["total_debits"].apply(lambda x: fmt_currency(x))
    summary["total_credits"] = summary["total_credits"].apply(lambda x: fmt_currency(x))
    summary["entry_count"] = summary["entry_count"] // 2  # Pairs of debit/credit
    summary.columns = ["Period", "Total Debits", "Total Credits", "Entry Pairs"]
    st.dataframe(summary, use_container_width=True, hide_index=True)

    # Export
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        csv_recognition = journal_entries.to_csv(index=False)
        st.download_button(
            "Download Recognition Entries (CSV)",
            csv_recognition,
            f"recognition_entries_{contract.id}.csv",
            "text/csv",
        )
    with col2:
        all_entries = pd.concat([booking_entries.rename(columns={"Account": "account", "Debit": "debit", "Credit": "credit", "Description": "description"}),
                                  journal_entries], ignore_index=True)
        csv_all = all_entries.to_csv(index=False)
        st.download_button(
            "Download All Entries (CSV)",
            csv_all,
            f"all_entries_{contract.id}.csv",
            "text/csv",
        )
