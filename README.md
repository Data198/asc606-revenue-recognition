# 📋 ASC 606 Revenue Recognition Analyzer

An interactive tool that applies the **ASC 606 five-step revenue recognition model** to SaaS contracts. Input contract parameters, identify performance obligations, allocate transaction prices, and generate proper revenue schedules with balanced journal entries.

**🔗 [Live Demo](https://asc606-revenue-recognit-6yoxyehl4e5kdnwalnqmtb.streamlit.app)**

![Built with Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-ff4b4b?logo=streamlit)
![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python)

---

## Features

| Module | Description |
|--------|-------------|
| **Five-Step Model** | Interactive walkthrough — build a contract and see the complete ASC 606 analysis |
| **Principal vs. Agent** | Determine gross vs. net revenue recognition with indicator-based assessment |
| **Revenue Waterfall** | Visualize revenue recognition patterns for sample contracts |
| **Journal Entries** | Generate debit/credit entries with automatic balance validation |
| **Sample Contracts** | 4 pre-loaded SaaS contract scenarios covering common patterns |

## Key Capabilities

- **Performance Obligation Builder** — Add and configure distinct obligations with SSP methods
- **Variable Consideration Estimator** — Expected value & most likely amount methods with constraint
- **SSP Allocation Engine** — Relative standalone selling price allocation with rounding precision
- **Principal vs. Agent Analysis** — Checklist-based control assessment with gross/net comparison
- **Revenue Schedule Generator** — Over time and point-in-time recognition with monthly detail
- **Journal Entry Output** — Balanced debit/credit entries exportable to CSV for ERP upload

## Tech Stack

- **Python** · **Streamlit** · **Pandas** · **Plotly** · **NumPy**

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Sample Data

Includes 4 pre-loaded SaaS contract scenarios:
1. Annual subscription with implementation and variable consideration
2. Multi-year enterprise license with point-in-time and over-time obligations
3. Usage-based platform contract with most-likely-amount estimation
4. Complex SaaS bundle with 4 obligations and volume discount

---

*Built by a Senior Revenue Accountant to demonstrate accounting automation expertise.*
