"""Principal vs. Agent Analysis Page."""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.principal_agent import (
    CONTROL_INDICATORS, evaluate_principal_agent, generate_memo,
)
from components.charts import principal_agent_gauge

st.set_page_config(page_title="Principal vs. Agent | ASC 606", page_icon="⚖️", layout="wide")
st.title("⚖️ Principal vs. Agent Analysis")
st.caption("Determine whether an entity is acting as principal or agent under ASC 606-36 through 606-40")

st.markdown("""
The principal vs. agent determination affects whether revenue is reported **gross** (principal)
or **net** (agent). The key question: does the entity **control** the good or service before
it is transferred to the customer?
""")

# Transaction Description
st.subheader("Transaction Description")
transaction_desc = st.text_area(
    "Describe the transaction being analyzed:",
    value="NovaCRM provides a marketplace where third-party vendors sell add-on integrations to NovaCRM platform customers. NovaCRM facilitates the transaction, handles billing, and provides the platform infrastructure.",
    height=100,
)

st.divider()
st.subheader("Control Indicator Assessment")
st.markdown("Evaluate each indicator of control. Indicators present suggest **Principal** status.")

# Collect responses
responses = {}
for indicator in CONTROL_INDICATORS:
    col1, col2, col3 = st.columns([2, 4, 1])
    with col1:
        weight_colors = {"strong": "🔴", "moderate": "🟡", "supporting": "🟢"}
        st.markdown(f"{weight_colors[indicator['weight']]} **{indicator['name']}**")
        st.caption(f"Weight: {indicator['weight'].title()}")
    with col2:
        st.markdown(f"*{indicator['description']}*")
    with col3:
        responses[indicator["id"]] = st.checkbox("Present", key=indicator["id"])

# Run evaluation
st.divider()
if st.button("Run Analysis", type="primary"):
    evaluation = evaluate_principal_agent(responses)

    st.subheader("Assessment Results")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.plotly_chart(
            principal_agent_gauge(evaluation["score_pct"]),
            use_container_width=True,
        )

    with col2:
        conclusion_color = "green" if evaluation["conclusion"] == "Principal" else "orange"
        st.markdown(f"""
        ### Conclusion: :{conclusion_color}[{evaluation['conclusion']}]

        **Revenue Treatment:** {evaluation['revenue_treatment']} Basis

        **Score:** {evaluation['score']}/{evaluation['max_score']} ({evaluation['score_pct']}%)

        ---

        {evaluation['rationale']}
        """)

    # Detailed analysis table
    st.divider()
    st.subheader("Detailed Indicator Analysis")

    for item in evaluation["analysis"]:
        status = "✅" if item["present"] else "❌"
        st.markdown(f"{status} **{item['indicator']}** (Weight: {item['weight']}) — Score: {item['score']}")

    # Gross vs. Net comparison
    st.divider()
    st.subheader("Gross vs. Net Revenue Impact")

    gross_net_col1, gross_net_col2 = st.columns(2)

    sample_gross = st.number_input("Total transaction amount ($)", value=100000.0, step=1000.0)
    sample_commission = st.number_input("Commission/fee earned ($)", value=15000.0, step=1000.0)

    with gross_net_col1:
        st.markdown("**If Principal (Gross):**")
        st.metric("Revenue Recognized", f"${sample_gross:,.0f}")
        st.metric("COGS", f"${sample_gross - sample_commission:,.0f}")
        st.metric("Gross Profit", f"${sample_commission:,.0f}")

    with gross_net_col2:
        st.markdown("**If Agent (Net):**")
        st.metric("Revenue Recognized", f"${sample_commission:,.0f}")
        st.metric("COGS", "$0")
        st.metric("Gross Profit", f"${sample_commission:,.0f}")

    st.info("Note: Gross profit is the same under both methods. The difference is in the top-line revenue and COGS presentation.")

    # Generate memo
    st.divider()
    st.subheader("Analysis Memo")
    memo = generate_memo(evaluation, transaction_desc)
    st.text(memo)

    st.download_button(
        "Download Memo (TXT)",
        memo,
        "principal_agent_memo.txt",
        "text/plain",
    )
