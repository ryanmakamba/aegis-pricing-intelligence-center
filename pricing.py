from __future__ import annotations

import numpy as np
import pandas as pd


TARGET_LOSS_RATIO = 0.65
DEFAULT_EXPENSE_RATIO = 0.27


def add_pricing_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Return policy-level pricing metrics used throughout the application."""
    result = df.copy()
    result["claim_frequency"] = result["claim_count"] / result["exposure"].clip(lower=0.01)
    result["claim_severity"] = np.where(
        result["claim_count"] > 0,
        result["incurred_loss"] / result["claim_count"],
        0.0,
    )
    result["loss_ratio"] = result["incurred_loss"] / result["earned_premium"].clip(lower=1)
    result["combined_ratio"] = result["loss_ratio"] + result["expense_ratio"]
    result["underwriting_result"] = result["earned_premium"] - result["incurred_loss"] - (
        result["earned_premium"] * result["expense_ratio"]
    )
    result["risk_status"] = pd.cut(
        result["loss_ratio"],
        bins=[-np.inf, 0.55, 0.70, np.inf],
        labels=["Profitable", "Monitor", "Corrective action"],
    ).astype(str)
    return result


def portfolio_summary(df: pd.DataFrame, target_loss_ratio: float = TARGET_LOSS_RATIO) -> dict[str, float]:
    premium = float(df["earned_premium"].sum())
    losses = float(df["incurred_loss"].sum())
    claims = int(df["claim_count"].sum())
    exposure = float(df["exposure"].sum())
    expense_ratio = float(np.average(df["expense_ratio"], weights=df["earned_premium"]))
    loss_ratio = losses / premium if premium else 0.0
    frequency = claims / exposure if exposure else 0.0
    severity = losses / claims if claims else 0.0
    indicated_change = (loss_ratio / target_loss_ratio) - 1
    return {
        "premium": premium,
        "losses": losses,
        "claims": claims,
        "exposure": exposure,
        "loss_ratio": loss_ratio,
        "expense_ratio": expense_ratio,
        "combined_ratio": loss_ratio + expense_ratio,
        "frequency": frequency,
        "severity": severity,
        "underwriting_result": premium - losses - (premium * expense_ratio),
        "indicated_change": indicated_change,
    }


def segment_summary(df: pd.DataFrame, dimension: str, target_loss_ratio: float) -> pd.DataFrame:
    grouped = (
        df.groupby(dimension, observed=True)
        .agg(
            earned_premium=("earned_premium", "sum"),
            incurred_loss=("incurred_loss", "sum"),
            claim_count=("claim_count", "sum"),
            exposure=("exposure", "sum"),
        )
        .reset_index()
    )
    grouped["loss_ratio"] = grouped["incurred_loss"] / grouped["earned_premium"]
    grouped["frequency"] = grouped["claim_count"] / grouped["exposure"]
    grouped["severity"] = np.where(
        grouped["claim_count"] > 0,
        grouped["incurred_loss"] / grouped["claim_count"],
        0,
    )
    grouped["indicated_rate_change"] = (grouped["loss_ratio"] / target_loss_ratio) - 1
    grouped["pricing_action"] = np.select(
        [grouped["indicated_rate_change"] > 0.10, grouped["indicated_rate_change"] < -0.05],
        ["Increase", "Review for growth"],
        default="Maintain",
    )
    return grouped.sort_values("loss_ratio", ascending=False)


def run_scenario(
    df: pd.DataFrame,
    severity_trend: float,
    frequency_trend: float,
    premium_change: float,
    expense_ratio: float,
    target_loss_ratio: float,
) -> dict[str, float]:
    baseline = portfolio_summary(df, target_loss_ratio)
    projected_losses = baseline["losses"] * (1 + severity_trend) * (1 + frequency_trend)
    projected_premium = baseline["premium"] * (1 + premium_change)
    projected_lr = projected_losses / projected_premium if projected_premium else 0
    combined = projected_lr + expense_ratio
    indicated_change = (projected_lr / target_loss_ratio) - 1
    underwriting_result = projected_premium - projected_losses - (projected_premium * expense_ratio)
    return {
        "premium": projected_premium,
        "losses": projected_losses,
        "loss_ratio": projected_lr,
        "combined_ratio": combined,
        "indicated_change": indicated_change,
        "underwriting_result": underwriting_result,
    }

