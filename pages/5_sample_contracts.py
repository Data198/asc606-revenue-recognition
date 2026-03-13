"""Sample Contract Library Page."""

import streamlit as st
import pandas as pd
import json
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.contract import Contract, PerformanceObligation, VariableConsideration
from models.revenue_engine import run_full_analysis
from utils.formatters import fmt_currency

st.set_page_config(page_title="Sample Contracts | ASC 606", page_icon="📚", layout="wide")
st.title("📚 Sample Contract Library")
st.caption("Pre-loaded SaaS contract scenarios demonstrating various ASC 606 patterns")

# Load sample contracts
data_path = Path(__file__).parent.parent / "data" / "sample_contracts.json"
with open(data_path) as f:
    sample_data = json.load(f)

# Overview table
st.subheader("Contract Overview")

overview = []
for c in sample_data["contracts"]:
    overview.append({
        "ID": c["id"],
        "Contract": c["name"],
        "Customer": c["customer"],
        "Term": f"{c['term_months']} months",
        "Consideration": fmt_currency(c["total_consideration"]),
        "Obligations": len(c["obligations"]),
        "Variable": "Yes" if c.get("variable_consideration") else "No",
        "Payment": c["payment_terms"],
    })

st.dataframe(pd.DataFrame(overview), use_container_width=True, hide_index=True)

# Detailed view per contract
st.divider()
for contract_data in sample_data["contracts"]:
    with st.expander(f"📄 {contract_data['name']} ({contract_data['id']})"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            **Customer:** {contract_data['customer']}
            **Contract Date:** {contract_data['contract_date']}
            **Term:** {contract_data['term_months']} months
            **Total Consideration:** {fmt_currency(contract_data['total_consideration'])}
            **Payment Terms:** {contract_data['payment_terms']}
            """)

        with col2:
            if contract_data.get("variable_consideration"):
                vc = contract_data["variable_consideration"]
                st.markdown(f"""
                **Variable Consideration:**
                - Type: {vc['type'].replace('_', ' ').title()}
                - Description: {vc['description']}
                - Method: {vc['estimation_method'].replace('_', ' ').title()}
                - Constraint: {'Applied' if vc['constraint_applied'] else 'Not applied'}
                """)
            else:
                st.markdown("**Variable Consideration:** None")

        # Obligations table
        st.markdown("**Performance Obligations:**")
        ob_data = []
        for ob in contract_data["obligations"]:
            entry = {
                "Name": ob["name"],
                "Type": "Over Time" if ob["type"] == "over_time" else "Point in Time",
                "SSP": fmt_currency(ob["standalone_selling_price"]),
                "SSP Method": ob["ssp_method"].replace("_", " ").title(),
            }
            if ob["type"] == "over_time":
                entry["Period"] = f"{ob.get('delivery_start', 'N/A')} to {ob.get('delivery_end', 'N/A')}"
            else:
                entry["Period"] = ob.get("completion_date", "N/A")
            ob_data.append(entry)

        st.dataframe(pd.DataFrame(ob_data), use_container_width=True, hide_index=True)

        # Run quick analysis
        obs = []
        for ob in contract_data["obligations"]:
            obs.append(PerformanceObligation(
                name=ob["name"],
                type=ob["type"],
                standalone_selling_price=ob["standalone_selling_price"],
                ssp_method=ob["ssp_method"],
                delivery_start=date.fromisoformat(ob["delivery_start"]) if ob.get("delivery_start") else None,
                delivery_end=date.fromisoformat(ob["delivery_end"]) if ob.get("delivery_end") else None,
                completion_date=date.fromisoformat(ob["completion_date"]) if ob.get("completion_date") else None,
            ))

        vc_obj = None
        if contract_data.get("variable_consideration"):
            vc_d = contract_data["variable_consideration"]
            vc_obj = VariableConsideration(
                type=vc_d["type"], description=vc_d["description"],
                estimation_method=vc_d["estimation_method"],
                scenarios=vc_d["scenarios"],
                constraint_applied=vc_d["constraint_applied"],
            )

        contract = Contract(
            id=contract_data["id"], customer=contract_data["customer"],
            contract_date=date.fromisoformat(contract_data["contract_date"]),
            term_months=contract_data["term_months"],
            total_consideration=contract_data["total_consideration"],
            payment_terms=contract_data["payment_terms"],
            obligations=obs, variable_consideration=vc_obj,
        )

        analysis = run_full_analysis(contract)

        # Quick metrics
        m_cols = st.columns(4)
        m_cols[0].metric("Transaction Price", fmt_currency(analysis["step3"]["total_transaction_price"]))
        m_cols[1].metric("Variable Consideration", fmt_currency(analysis["step3"]["variable_consideration"]))
        m_cols[2].metric("Schedule Periods", str(len(analysis["schedule"]["period"].unique())) if not analysis["schedule"].empty else "0")
        m_cols[3].metric("Journal Entries", str(len(analysis["journal_entries"])))

# ASC 606 Key Concepts Reference
st.divider()
st.subheader("ASC 606 Quick Reference")

st.markdown("""
| Concept | Description |
|---------|-------------|
| **Over Time** | Revenue recognized as the obligation is satisfied over the contract period (e.g., SaaS subscriptions) |
| **Point in Time** | Revenue recognized when control transfers at a specific moment (e.g., software license delivery) |
| **SSP - Observable** | Standalone selling price based on actual prices charged to customers |
| **SSP - Adjusted Market** | Estimated based on market pricing with adjustments for entity-specific factors |
| **SSP - Residual** | Transaction price minus sum of other observable SSPs (used when highly variable) |
| **Expected Value** | Probability-weighted sum of possible outcomes for variable consideration |
| **Most Likely Amount** | Single most likely outcome — best for binary outcomes (bonus/no bonus) |
| **Constraint** | Variable consideration included only if significant reversal is not probable |
""")
