"""ASC 606 SaaS Revenue Recognition Analyzer.

Interactive tool for applying the ASC 606 five-step revenue recognition
model to SaaS contracts, built by a Senior Revenue Accountant.
"""

import streamlit as st

st.set_page_config(
    page_title="ASC 606 Revenue Recognition Analyzer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📋 ASC 606 Revenue Recognition Analyzer")
st.subheader("SaaS Contract Revenue Recognition Tool")

st.markdown("""
An interactive tool that walks through the **ASC 606 five-step revenue recognition model**
for SaaS contracts. Input contract parameters, identify performance obligations, and
generate proper revenue schedules with journal entries.

---

### Tool Pages

| Page | Description |
|------|-------------|
| **Five-Step Model** | Interactive walkthrough — build a contract and see the complete ASC 606 analysis |
| **Principal vs. Agent** | Determine gross vs. net revenue recognition with indicator-based assessment |
| **Revenue Waterfall** | Visualize revenue recognition patterns for sample contracts |
| **Journal Entries** | Generate debit/credit entries with balance validation |
| **Sample Contracts** | Pre-loaded SaaS contract scenarios covering common patterns |

---

### ASC 606 Five-Step Model

| Step | Description |
|------|-------------|
| **Step 1** | Identify the contract with a customer |
| **Step 2** | Identify performance obligations |
| **Step 3** | Determine the transaction price |
| **Step 4** | Allocate the transaction price |
| **Step 5** | Recognize revenue as obligations are satisfied |

---

### Key Capabilities

- **Performance Obligation Builder** — Add and configure distinct obligations with SSP methods
- **Variable Consideration Estimator** — Expected value and most likely amount methods with constraint
- **SSP Allocation Engine** — Relative standalone selling price allocation with rounding precision
- **Principal vs. Agent Analysis** — Checklist-based control assessment with gross/net comparison
- **Revenue Schedule Generator** — Over time and point-in-time recognition with monthly detail
- **Journal Entry Output** — Balanced debit/credit entries exportable to CSV for ERP upload

---

### Sample Data

This tool includes 4 pre-loaded SaaS contract scenarios:
1. Annual subscription with implementation and variable consideration
2. Multi-year enterprise license with point-in-time and over-time obligations
3. Usage-based platform contract with most-likely-amount estimation
4. Complex SaaS bundle with 4 obligations and volume discount

---

*Built with Python, Streamlit, Pandas, and Plotly*
""")

st.sidebar.success("Select a page above to explore the tool.")
