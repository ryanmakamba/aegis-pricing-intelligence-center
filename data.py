from __future__ import annotations

import numpy as np
import pandas as pd


LINES = {
    "Personal Auto": (1_580, 0.102, 8_100),
    "Homeowners": (1_920, 0.061, 18_600),
    "Commercial Property": (8_750, 0.044, 82_000),
    "General Liability": (5_400, 0.052, 46_000),
    "Workers' Compensation": (7_250, 0.069, 51_500),
}


def generate_portfolio(rows: int = 4_800, seed: int = 42) -> pd.DataFrame:
    """Create a reproducible, synthetic P&C portfolio for demonstration purposes."""
    rng = np.random.default_rng(seed)
    line_names = list(LINES)
    lines = rng.choice(line_names, rows, p=[0.29, 0.23, 0.17, 0.16, 0.15])
    states = rng.choice(["CT", "NY", "MA", "NJ", "RI"], rows, p=[0.30, 0.23, 0.20, 0.17, 0.10])
    tiers = rng.choice(["Preferred", "Standard", "Non-standard"], rows, p=[0.31, 0.50, 0.19])
    channels = rng.choice(["Independent Agent", "Broker", "Direct"], rows, p=[0.48, 0.30, 0.22])
    years = rng.choice([2023, 2024, 2025, 2026], rows, p=[0.20, 0.24, 0.27, 0.29])
    exposure = rng.uniform(0.55, 1.0, rows)

    tier_factor = pd.Series(tiers).map({"Preferred": 0.82, "Standard": 1.0, "Non-standard": 1.38}).to_numpy()
    state_factor = pd.Series(states).map({"CT": 1.0, "NY": 1.16, "MA": 0.95, "NJ": 1.10, "RI": 0.91}).to_numpy()
    year_factor = pd.Series(years).map({2023: 0.94, 2024: 1.0, 2025: 1.07, 2026: 1.13}).to_numpy()

    base_premium = np.array([LINES[line][0] for line in lines], dtype=float)
    base_frequency = np.array([LINES[line][1] for line in lines], dtype=float)
    base_severity = np.array([LINES[line][2] for line in lines], dtype=float)

    written_premium = base_premium * tier_factor * state_factor * year_factor * rng.lognormal(0, 0.17, rows)
    earned_premium = written_premium * exposure
    expected_claims = base_frequency * exposure * tier_factor * state_factor * year_factor
    claim_count = rng.poisson(expected_claims)
    severity = base_severity * tier_factor * year_factor * rng.lognormal(0, 0.48, rows)
    incurred_loss = claim_count * severity
    # Add catastrophe and large-loss volatility without overwhelming the portfolio.
    large_loss = rng.random(rows) < 0.008
    incurred_loss += large_loss * rng.lognormal(np.log(95_000), 0.65, rows)
    paid_ratio = rng.beta(4.2, 2.0, rows)
    paid_loss = incurred_loss * paid_ratio
    expense_ratio = np.clip(rng.normal(0.27, 0.025, rows), 0.20, 0.35)

    return pd.DataFrame(
        {
            "policy_id": [f"AG-{year}-{i:05d}" for i, year in enumerate(years, start=1)],
            "policy_year": years,
            "line_of_business": lines,
            "state": states,
            "risk_tier": tiers,
            "distribution_channel": channels,
            "exposure": exposure.round(3),
            "written_premium": written_premium.round(2),
            "earned_premium": earned_premium.round(2),
            "claim_count": claim_count,
            "paid_loss": paid_loss.round(2),
            "incurred_loss": incurred_loss.round(2),
            "expense_ratio": expense_ratio.round(4),
        }
    )

