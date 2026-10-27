# Aegis Pricing Intelligence Center

A Python and Streamlit insurance pricing application that evaluates premium adequacy through claim frequency, severity, loss ratio, combined ratio, portfolio segmentation, and forward-looking scenario analysis.

## Features

- Executive pricing and profitability KPIs
- Loss-ratio analysis by product, state, risk tier, and channel
- Claim frequency and severity diagnostics
- Transparent indicated-rate calculations
- Interactive severity, frequency, premium, and expense scenarios
- Reproducible synthetic P&C portfolio with no customer information
- CSV export of the filtered analytical dataset

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push this folder to a public GitHub repository.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Select **Create app** and choose the repository.
4. Set the main file path to `app.py`.
5. Deploy the application.

## Portfolio description

Developed a Python-based insurance pricing and portfolio analytics application that evaluates premium adequacy using claim frequency, severity, expected loss, loss ratio, and expense assumptions. Built interactive segmentation and scenario analysis to identify underpriced business, estimate indicated rate changes, and support risk-based pricing decisions.

